#!/usr/bin/env bash
# The dry-run budget checker for the Part 1 build session.
#
# ARCHITECTURE.md §10.1 as reset in v1.5, and A-126, fix the rules this file
# implements:
#   - every query is dry-run first, and the estimate is the ONLY pre-flight gate,
#     because it is the only number available before a query runs;
#   - billed bytes are PREDICTED, not tolerated:
#         predicted = max(10 MiB, ceil(estimate -> whole MiB))
#     which held on 13 of 13 recon jobs (A-107);
#   - the running total accumulates ACTUAL bytes billed, never estimates;
#   - the session halts if actual billed misses the prediction by more than
#     1 MiB, if one query bills more than the per-query ceiling, or if the
#     accumulated actuals reach the session ceiling -- the last checked in BOTH
#     directions, before a query as predicted-plus-accumulated and after it on
#     actuals. That last condition is the one v1.3 and v1.4 lacked entirely.
#
# This is not src/recon/budget.sh and does not call it. §8 forbids this session
# src/recon/**, and that file carries the superseded 50 GiB / 200 GiB ceilings,
# A-085's 2x-and-10 GiB divergence band, and the recon's ledger path. A-131
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

# The recon's 4.90 GiB is NOT seeded here. §10.1's table scopes 20 GiB to a
# build session and 40 GiB to the two build sessions together; the recon ran
# under its own 200 GiB ceiling and is not a build session. The pair figure is
# carried in the ledger so the Part 2 session can start from what Part 1 left.

_budget_self="${BASH_SOURCE[0]:-${0}}"
if [[ -n "${PART1_REPO_ROOT:-}" ]]; then
  REPO_ROOT="${PART1_REPO_ROOT}"
else
  REPO_ROOT="$(cd "$(dirname "${_budget_self}")/../.." && pwd)"
fi
unset _budget_self
if [[ ! -f "${REPO_ROOT}/ARCHITECTURE.md" ]]; then
  echo "budget.sh: resolved REPO_ROOT=${REPO_ROOT}, which holds no ARCHITECTURE.md." >&2
  echo "Run this through bash from the repository, or set PART1_REPO_ROOT." >&2
  return 1 2>/dev/null || exit 1
fi
readonly REPO_ROOT
readonly LEDGER="${REPO_ROOT}/outputs/tables/part1_budget_ledger.csv"
# A-094's columns, in A-094's order, with three added for A-126's prediction and
# the pair ceiling. note stays last.
readonly LEDGER_HEADER="seq,query_file,job_id,job_date_utc,shard_range,dry_run_estimate_bytes,bytes_processed,bytes_billed,divergence_bytes,divergence_ratio,running_total_billed_bytes,remaining_total_bytes,predicted_billed_bytes,prediction_delta_bytes,remaining_both_sessions_bytes,note"

# JSON is read with the macOS system interpreter and the standard library only.
# Nothing is installed: A-131 keeps .venv and both requirements files exactly as
# Part 3's clean-checkout guarantee describes them.
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

# --- A-126's prediction ------------------------------------------------------
predict_billed() {  # predict_billed <estimate_bytes>
  local estimate="$1" rounded
  # One carve-out, and it is A-107's own: the rule is stated as
  # billed = max(10 MiB, ceil(processed -> MiB)), but recon ledger row 3 --
  # sql/00_recon_shard_inventory.sql, answered from dataset metadata -- estimated
  # 0 and billed 0, not 10 MiB. A-107's body says as much: billed exceeds
  # processed "on every query that scans anything". The 10 MiB floor is the
  # minimum for a query that reads table data, so a query that reads none is
  # predicted at zero. This is not a widened band: it is the rule applied to the
  # case the rule's own evidence covers. Every Part 1 query scans the events
  # table, so this branch is not expected to be taken here.
  if (( estimate == 0 )); then echo 0; return 0; fi
  rounded=$(( ( (estimate + MIB - 1) / MIB ) * MIB ))
  if (( rounded < BILLING_FLOOR )); then echo "${BILLING_FLOOR}"; else echo "${rounded}"; fi
}

# --- ledger ------------------------------------------------------------------
ledger_ensure() {
  mkdir -p "$(dirname "${LEDGER}")"
  [[ -f "${LEDGER}" ]] || printf '%s\n' "${LEDGER_HEADER}" > "${LEDGER}"
}

ledger_total_billed() {   # sum of the bytes_billed column, in bytes
  ledger_ensure
  "${JSON_PY}" - "${LEDGER}" <<'PY'
import csv, sys
total = 0
with open(sys.argv[1], newline="") as fh:
    for row in csv.DictReader(fh):
        value = (row.get("bytes_billed") or "").strip()
        if value.isdigit():
            total += int(value)
print(total)
PY
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
  local estimate="$1" predicted remaining accumulated
  predicted="$(predict_billed "${estimate}")"
  accumulated="$(ledger_total_billed)"
  remaining=$(( SESSION_CEILING - accumulated ))

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
  if (( accumulated + predicted > PAIR_CEILING )); then
    echo "GATE: predicted plus accumulated would exceed the 40 GiB ceiling for both" >&2
    echo "build sessions together (§10.1)." >&2
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
    echo "billed = max(10 MiB, ceil(estimate -> MiB)) held on 13 of 13 recon jobs, so" >&2
    echo "a miss means the cost model is wrong and every later gate decision rests on" >&2
    echo "it. Record the divergence and what it implies about the planner, then" >&2
    echo "escalate. Widening the band or raising a ceiling are both forbidden." >&2
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
  local seq divergence ratio running remaining predicted delta remaining_pair
  ledger_ensure
  seq="$(ledger_next_seq)"
  predicted="$(predict_billed "${estimate}")"
  delta=$(( billed - predicted ))
  divergence=$(( billed - estimate ))
  if (( estimate > 0 )); then
    ratio="$(awk -v b="${billed}" -v e="${estimate}" 'BEGIN { printf "%.4f", b/e }')"
  else
    # A free metadata query estimates zero and bills zero: the ratio is 0/0,
    # which is undefined rather than any number, and is recorded as such.
    ratio="undefined"
  fi
  running=$(( $(ledger_total_billed) + billed ))
  remaining=$(( SESSION_CEILING - running ))
  remaining_pair=$(( PAIR_CEILING - running ))
  printf '%s,"%s",%s,%s,"%s",%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,"%s"\n' \
    "${seq}" "${query_file}" "${job_id}" "${job_date}" "${shard_range}" \
    "${estimate}" "${processed}" "${billed}" "${divergence}" "${ratio}" \
    "${running}" "${remaining}" "${predicted}" "${delta}" "${remaining_pair}" \
    "${note}" >> "${LEDGER}"
}

# --- direct invocation -------------------------------------------------------
#   bash src/part1_retention/budget.sh total | remaining | predict <bytes> | gate <bytes>
if [[ "${BASH_SOURCE[0]:-}" == "${0}" ]]; then
  case "${1:-}" in
    total)     ledger_total_billed ;;
    remaining) ledger_remaining ;;
    predict)   predict_billed "${2:?predict needs an estimate in bytes}" ;;
    gate)      gate_check "${2:?gate needs an estimate in bytes}" ;;
    *) echo "usage: bash src/part1_retention/budget.sh {total|remaining|predict <bytes>|gate <bytes>}" >&2; exit 64 ;;
  esac
fi
