#!/usr/bin/env bash
# The dry-run budget checker for the Part 2 build session.
#
# ARCHITECTURE.md §10.1 as reset in v1.5, and A-126, fix the rules this file
# implements:
#   - every query is dry-run first, and the estimate is the ONLY pre-flight gate,
#     because it is the only number available before a query runs;
#   - billed bytes are PREDICTED, not tolerated:
#         predicted = max(10 MiB, ceil(estimate -> whole MiB))
#     which held on 13 of 13 recon jobs (A-107) and 9 of 9 Part 1 jobs;
#   - the running total accumulates ACTUAL bytes billed, never estimates;
#   - the session halts if actual billed misses the prediction by more than
#     1 MiB, if one query bills more than the per-query ceiling, or if the
#     accumulated actuals reach the session ceiling.
#
# ONE THING THIS FILE DOES THAT PART 1's DID NOT (A-160). Part 1 went first, so
# its pair remainder was simply 40 GiB minus its own running total. Part 2 goes
# second, so the pair total is seeded by READING the committed Part 1 ledger at
# run time rather than by hardcoding 4,604,297,216. A budget figure that cannot
# follow its own source is the kind of number this project exists not to publish.
#
# This is neither src/recon/budget.sh nor src/part1_retention/budget.sh and calls
# neither. §8 forbids this session both paths; A-131 set the precedent and A-160
# records the choice.
#
# Sourced by run_query.sh. Not executable on its own.

set -euo pipefail

# --- Ceilings, fixed by §10.1 as reset in v1.5 (A-126) -----------------------
readonly PER_QUERY_CEILING=4294967296     # 4 GiB billed, one query
readonly SESSION_CEILING=21474836480      # 20 GiB billed, this build session
readonly PAIR_CEILING=42949672960         # 40 GiB billed, both build sessions
readonly PREDICTION_TOLERANCE=1048576     # 1 MiB; A-126's halt condition
readonly BILLING_FLOOR=10485760           # 10 MiB, per query and not per shard
readonly MIB=1048576

_budget_self="${BASH_SOURCE[0]:-${0}}"
if [[ -n "${PART2_REPO_ROOT:-}" ]]; then
  REPO_ROOT="${PART2_REPO_ROOT}"
else
  REPO_ROOT="$(cd "$(dirname "${_budget_self}")/../.." && pwd)"
fi
unset _budget_self
if [[ ! -f "${REPO_ROOT}/ARCHITECTURE.md" ]]; then
  echo "budget.sh: resolved REPO_ROOT=${REPO_ROOT}, which holds no ARCHITECTURE.md." >&2
  echo "Run this through bash from the repository, or set PART2_REPO_ROOT." >&2
  return 1 2>/dev/null || exit 1
fi
readonly REPO_ROOT
readonly LEDGER="${REPO_ROOT}/outputs/tables/part2_budget_ledger.csv"
readonly PRIOR_LEDGER="${REPO_ROOT}/outputs/tables/part1_budget_ledger.csv"
# A-094's columns, in A-094's order, with three added for A-126's prediction and
# the pair ceiling. note stays last. Identical to Part 1's header (A-162), so the
# two ledgers read as one record.
readonly LEDGER_HEADER="seq,query_file,job_id,job_date_utc,shard_range,dry_run_estimate_bytes,bytes_processed,bytes_billed,divergence_bytes,divergence_ratio,running_total_billed_bytes,remaining_total_bytes,predicted_billed_bytes,prediction_delta_bytes,remaining_both_sessions_bytes,note"

# JSON and CSV are read with the macOS system interpreter and the standard
# library only. Nothing is installed: A-160 keeps .venv and both requirements
# files exactly as Part 3's clean-checkout guarantee describes them.
readonly JSON_PY=/usr/bin/python3

# --- project id: environment only, never a committed literal (§8) ------------
require_project() {
  if [[ -z "${GOOGLE_CLOUD_PROJECT:-}" ]]; then
    echo "budget.sh: GOOGLE_CLOUD_PROJECT is unset. §8 keeps the project id in the" >&2
    echo "environment, never in a committed file. Export it and re-run." >&2
    return 1
  fi
}

json_get() {  # json_get <file> <dotted.path> [default]
  "${JSON_PY}" - "$1" "$2" "${3-}" <<'PY'
import json, sys
path_file, dotted, default = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    with open(path_file) as fh:
        node = json.load(fh)
    for key in dotted.split("."):
        node = node[key] if isinstance(node, dict) else node[int(key)]
except Exception:
    print(default); sys.exit(0)
print(default if node is None else node)
PY
}

human() {  # bytes -> a readable figure for the console only; the files keep bytes
  awk -v b="$1" 'BEGIN {
    if (b >= 1073741824) printf "%.2f GiB", b/1073741824;
    else if (b >= 1048576) printf "%.2f MiB", b/1048576;
    else if (b >= 1024) printf "%.2f KiB", b/1024;
    else printf "%d B", b;
  }'
}

_sum_billed() {  # _sum_billed <ledger path>; 0 if the file is absent
  "${JSON_PY}" - "$1" <<'PY'
import csv, os, sys
path = sys.argv[1]
total = 0
if os.path.exists(path):
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            value = (row.get("bytes_billed") or "").strip()
            if value.isdigit():
                total += int(value)
print(total)
PY
}

# --- A-160: what the earlier build session already spent ---------------------
prior_sessions_billed() {
  _sum_billed "${PRIOR_LEDGER}"
}

# --- A-126's prediction ------------------------------------------------------
predict_billed() {  # predict_billed <estimate_bytes>
  local estimate="$1" rounded
  # One carve-out, and it is A-107's own: the rule is stated as
  # billed = max(10 MiB, ceil(processed -> MiB)), but recon ledger row 3 --
  # sql/00_recon_shard_inventory.sql, answered from dataset metadata -- estimated
  # 0 and billed 0, not 10 MiB. A-107's body says as much: billed exceeds
  # processed "on every query that scans anything". The 10 MiB floor is the
  # minimum for a query that reads table data, so a query that reads none is
  # predicted at zero. Every Part 2 query scans the events table, so this branch
  # is not expected to be taken here.
  if (( estimate == 0 )); then echo 0; return 0; fi
  rounded=$(( ( (estimate + MIB - 1) / MIB ) * MIB ))
  if (( rounded < BILLING_FLOOR )); then echo "${BILLING_FLOOR}"; else echo "${rounded}"; fi
}

# --- ledger ------------------------------------------------------------------
ledger_ensure() {
  mkdir -p "$(dirname "${LEDGER}")"
  [[ -f "${LEDGER}" ]] || printf '%s\n' "${LEDGER_HEADER}" > "${LEDGER}"
}

ledger_total_billed() {   # this session's own spend, in bytes
  ledger_ensure
  _sum_billed "${LEDGER}"
}

ledger_remaining() {
  local spent; spent="$(ledger_total_billed)"
  echo $(( SESSION_CEILING - spent ))
}

ledger_next_seq() {
  ledger_ensure
  "${JSON_PY}" - "${LEDGER}" <<'PY'
import csv, sys
highest = 0
with open(sys.argv[1], newline="") as fh:
    for row in csv.DictReader(fh):
        value = (row.get("seq") or "").strip()
        if value.isdigit():
            highest = max(highest, int(value))
print(highest + 1)
PY
}

# --- the pre-flight gate: estimate only (§10.1) -------------------------------
gate_check() {  # gate_check <estimate_bytes>; non-zero return blocks the query
  local estimate="$1" predicted remaining accumulated prior pair_used
  predicted="$(predict_billed "${estimate}")"
  accumulated="$(ledger_total_billed)"
  prior="$(prior_sessions_billed)"
  remaining=$(( SESSION_CEILING - accumulated ))
  pair_used=$(( prior + accumulated ))

  if (( remaining < PER_QUERY_CEILING )); then
    echo "GATE: remaining session budget $(human "${remaining}") is below the 4 GiB" >&2
    echo "per-query ceiling. §10.1 stops the session here rather than running a" >&2
    echo "partial query set." >&2
    return 2
  fi
  if (( predicted > PER_QUERY_CEILING )); then
    echo "GATE: predicted billed $(human "${predicted}") exceeds the 4 GiB per-query" >&2
    echo "ceiling. A query estimating above it is reading more than the whole table," >&2
    echo "which takes a join blow-up or a missing predicate. Narrow it and dry-run" >&2
    echo "again. Never raise the ceiling (§10.1)." >&2
    return 1
  fi
  if (( accumulated + predicted > SESSION_CEILING )); then
    echo "GATE: predicted $(human "${predicted}") plus accumulated $(human "${accumulated}")" >&2
    echo "would exceed the 20 GiB session ceiling. This is A-126's added condition," >&2
    echo "checked before the query rather than discovered after it." >&2
    return 1
  fi
  if (( pair_used + predicted > PAIR_CEILING )); then
    echo "GATE: predicted $(human "${predicted}") plus this session's $(human "${accumulated}")" >&2
    echo "plus Part 1's $(human "${prior}") would exceed the 40 GiB ceiling for both" >&2
    echo "build sessions together (§10.1). Part 1's figure is read from its committed" >&2
    echo "ledger, not assumed (A-160)." >&2
    return 1
  fi
  return 0
}

# --- the halt rule (A-126): billed against the prediction ---------------------
halt_check() {  # halt_check <estimate_bytes> <billed_bytes>
  local estimate="$1" billed="$2" predicted delta accumulated
  predicted="$(predict_billed "${estimate}")"
  delta=$(( billed - predicted ))
  accumulated="$(ledger_total_billed)"

  if (( billed > PER_QUERY_CEILING )); then
    echo "HALT: billed $(human "${billed}") exceeds the 4 GiB per-query ceiling," >&2
    echo "whatever it was estimated at (§10.1, third halt condition)." >&2
    return 1
  fi
  if (( delta > PREDICTION_TOLERANCE || delta < -PREDICTION_TOLERANCE )); then
    echo "HALT: billed $(human "${billed}") misses the prediction $(human "${predicted}")" >&2
    echo "by $(human "${delta#-}"), more than the 1 MiB A-126 allows." >&2
    echo "billed = max(10 MiB, ceil(estimate -> MiB)) held on 13 of 13 recon jobs and" >&2
    echo "9 of 9 Part 1 jobs, so a miss means the cost model is wrong and every later" >&2
    echo "gate decision rests on it. Record the divergence and what it implies about" >&2
    echo "the planner, then escalate. Widening the band or raising a ceiling are both" >&2
    echo "forbidden." >&2
    return 1
  fi
  if (( accumulated >= SESSION_CEILING )); then
    echo "HALT: accumulated actuals $(human "${accumulated}") have reached the 20 GiB" >&2
    echo "session ceiling (§10.1, first halt condition, checked after the query)." >&2
    return 1
  fi
  return 0
}

ledger_append() {
  # ledger_append <query_file> <job_id> <job_date> <shard_range> <estimate> <processed> <billed> <note>
  local query_file="$1" job_id="$2" job_date="$3" shard_range="$4"
  local estimate="$5" processed="$6" billed="$7" note="${8:-}"
  local seq divergence ratio running remaining predicted delta remaining_pair prior
  ledger_ensure
  seq="$(ledger_next_seq)"
  predicted="$(predict_billed "${estimate}")"
  delta=$(( billed - predicted ))
  divergence=$(( billed - estimate ))
  if (( estimate > 0 )); then
    ratio="$(awk -v b="${billed}" -v e="${estimate}" 'BEGIN { printf "%.4f", b/e }')"
  else
    ratio="undefined"
  fi
  running=$(( $(ledger_total_billed) + billed ))
  remaining=$(( SESSION_CEILING - running ))
  prior="$(prior_sessions_billed)"
  # A-160: the pair remainder counts what Part 1 actually spent, read from its
  # committed ledger, so this column is the whole project's spend against 40 GiB.
  remaining_pair=$(( PAIR_CEILING - prior - running ))
  printf '%s,"%s",%s,%s,"%s",%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,"%s"\n' \
    "${seq}" "${query_file}" "${job_id}" "${job_date}" "${shard_range}" \
    "${estimate}" "${processed}" "${billed}" "${divergence}" "${ratio}" \
    "${running}" "${remaining}" "${predicted}" "${delta}" "${remaining_pair}" \
    "${note}" >> "${LEDGER}"
}

# --- direct invocation -------------------------------------------------------
if [[ "${BASH_SOURCE[0]:-}" == "${0}" ]]; then
  case "${1:-}" in
    total)     ledger_total_billed ;;
    prior)     prior_sessions_billed ;;
    remaining) ledger_remaining ;;
    predict)   predict_billed "${2:?predict needs an estimate in bytes}" ;;
    gate)      gate_check "${2:?gate needs an estimate in bytes}" ;;
    *) echo "usage: bash src/part2_funnel/budget.sh {total|prior|remaining|predict <bytes>|gate <bytes>}" >&2; exit 64 ;;
  esac
fi
