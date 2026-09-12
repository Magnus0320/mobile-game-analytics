#!/usr/bin/env bash
# The dry-run budget checker for the Parts 1 and 2 recon pass.
#
# ARCHITECTURE.md §10.1 and A-085 fix the rules this file implements:
#   - every query is dry-run first, and the estimate is the ONLY pre-flight gate,
#     because it is the only number available before a query runs;
#   - the running total accumulates ACTUAL bytes billed, never estimates;
#   - every divergence between the two is a finding, in both directions;
#   - the pass halts on a billed overrun, and never on an under-billing.
#
# Sourced by run_recon_query.sh. Not executable on its own.

set -euo pipefail

# --- Ceilings, fixed by §10.1 and unchanged by A-085 -------------------------
readonly PER_QUERY_CEILING=53687091200    # 50 GiB
readonly TOTAL_CEILING=214748364800       # 200 GiB
readonly HALT_RATIO=2                     # billed > 2x estimate, AND ...
readonly HALT_ABSOLUTE=10737418240        # ... billed - estimate > 10 GiB
readonly STOP_REMAINING=53687091200       # stop the pass below 50 GiB remaining

# Resolve the repository root from this file's own location. BASH_SOURCE is
# unset when a non-bash shell sources this file, so fall back to $0 and then to
# an explicit override, rather than silently resolving to "/".
_budget_self="${BASH_SOURCE[0]:-${0}}"
if [[ -n "${RECON_REPO_ROOT:-}" ]]; then
  REPO_ROOT="${RECON_REPO_ROOT}"
else
  REPO_ROOT="$(cd "$(dirname "${_budget_self}")/../.." && pwd)"
fi
unset _budget_self
if [[ ! -f "${REPO_ROOT}/ARCHITECTURE.md" ]]; then
  echo "budget.sh: resolved REPO_ROOT=${REPO_ROOT}, which holds no ARCHITECTURE.md." >&2
  echo "Run this through bash from the repository, or set RECON_REPO_ROOT." >&2
  return 1 2>/dev/null || exit 1
fi
readonly REPO_ROOT
readonly LEDGER="${REPO_ROOT}/outputs/tables/recon_budget_ledger.csv"
readonly LEDGER_HEADER="seq,query_file,job_id,job_date_utc,shard_range,dry_run_estimate_bytes,bytes_processed,bytes_billed,divergence_bytes,divergence_ratio,running_total_billed_bytes,remaining_total_bytes,note"

# JSON is read with the macOS system interpreter and the standard library only.
# Nothing is installed: the project venv and both requirements files belong to
# Part 3 and §7.5's clean-checkout guarantee, and are not this session's to move.
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
  echo $(( TOTAL_CEILING - spent ))
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

human() {  # bytes -> a readable figure for the console only; the files keep bytes
  awk -v b="$1" 'BEGIN {
    if (b >= 1073741824) printf "%.2f GiB", b/1073741824;
    else if (b >= 1048576) printf "%.2f MiB", b/1048576;
    else if (b >= 1024) printf "%.2f KiB", b/1024;
    else printf "%d B", b;
  }'
}

# --- the pre-flight gate: estimate only (§10.1) -------------------------------
gate_check() {  # gate_check <estimate_bytes>; non-zero return blocks the query
  local estimate="$1" remaining
  remaining="$(ledger_remaining)"

  if (( remaining < STOP_REMAINING )); then
    echo "GATE: remaining total $(human "${remaining}") is below the 50 GiB floor." >&2
    echo "§10.1 stops the pass here rather than running a partial query set." >&2
    return 2
  fi
  if (( estimate > PER_QUERY_CEILING )); then
    echo "GATE: estimate $(human "${estimate}") exceeds the 50 GiB per-query ceiling." >&2
    echo "Narrow the query and dry-run again. Never raise the ceiling (§10.1)." >&2
    return 1
  fi
  if (( estimate > remaining )); then
    echo "GATE: estimate $(human "${estimate}") exceeds the remaining $(human "${remaining}")." >&2
    return 1
  fi
  return 0
}

# --- the halt rule (A-085): billed only, never estimates ----------------------
halt_check() {  # halt_check <estimate_bytes> <billed_bytes>
  local estimate="$1" billed="$2" excess

  if (( billed > PER_QUERY_CEILING )); then
    echo "HALT: billed $(human "${billed}") exceeds the 50 GiB per-query ceiling," >&2
    echo "whatever it was estimated at (§10.1 halt rule, second condition)." >&2
    return 1
  fi
  # Both conditions are required, so the per-table minimum inflating a trivially
  # small query halts nothing. Under-billing never halts: it is recorded, it
  # changes item 12's conclusion, and it costs nothing.
  if (( estimate > 0 )) && (( billed > HALT_RATIO * estimate )); then
    excess=$(( billed - estimate ))
    if (( excess > HALT_ABSOLUTE )); then
      echo "HALT: billed $(human "${billed}") exceeds estimate $(human "${estimate}")" >&2
      echo "by more than 2x AND by more than 10 GiB. The pre-flight gate is the only" >&2
      echo "cost control this pass has and it is estimate-based; once the estimate is" >&2
      echo "not predictive at this magnitude, every later gate decision is unreliable." >&2
      return 1
    fi
  fi
  return 0
}

ledger_append() {
  # ledger_append <query_file> <job_id> <job_date> <shard_range> <estimate> <processed> <billed> <note>
  local query_file="$1" job_id="$2" job_date="$3" shard_range="$4"
  local estimate="$5" processed="$6" billed="$7" note="${8:-}"
  local seq divergence ratio running remaining
  ledger_ensure
  seq="$(ledger_next_seq)"

  if [[ "${estimate}" =~ ^[0-9]+$ ]]; then
    divergence=$(( billed - estimate ))
    if (( estimate > 0 )); then
      ratio="$(awk -v b="${billed}" -v e="${estimate}" 'BEGIN { printf "%.4f", b/e }')"
    else
      # A free metadata query estimates zero and bills zero. The divergence is
      # zero and the ratio is 0/0, which is undefined rather than any number --
      # so it is recorded as undefined rather than invented.
      ratio="undefined"
    fi
  else
    # The two pre-session console queries were never dry-run, so no estimate
    # exists for them and their divergence is not computable. Recorded as such.
    divergence="not_taken"; ratio="not_taken"
  fi

  running=$(( $(ledger_total_billed) + billed ))
  remaining=$(( TOTAL_CEILING - running ))
  printf '%s,"%s",%s,%s,"%s",%s,%s,%s,%s,%s,%s,%s,"%s"\n' \
    "${seq}" "${query_file}" "${job_id}" "${job_date}" "${shard_range}" \
    "${estimate}" "${processed}" "${billed}" "${divergence}" "${ratio}" \
    "${running}" "${remaining}" "${note}" >> "${LEDGER}"
}

# --- seeding: the two pre-session console queries -----------------------------
# They were run manually before this session existed, were not dry-run, and are
# recorded in no file. §10.1 counts the running total in actuals, so their ACTUAL
# billed bytes are recovered from job history rather than approximated.
seed_ledger() {
  require_project || return 1
  ledger_ensure
  if "${JSON_PY}" - "${LEDGER}" <<'PY'
import csv, sys
with open(sys.argv[1], newline="") as fh:
    hit = any("prior" in (r.get("note") or "") for r in csv.DictReader(fh))
sys.exit(0 if hit else 1)
PY
  then
    echo "Ledger already seeded; leaving it alone." >&2
    return 0
  fi

  local tmp; tmp="$(mktemp)"
  if ! bq --project_id="${GOOGLE_CLOUD_PROJECT}" --format=prettyjson \
        ls -j --max_results=200 --all > "${tmp}" 2>/dev/null; then
    echo "seed_ledger: 'bq ls -j' failed; the prior queries cannot be recovered." >&2
    rm -f "${tmp}"; return 1
  fi

  "${JSON_PY}" - "${tmp}" <<'PY' > "${tmp}.rows"
import json, sys, datetime
with open(sys.argv[1]) as fh:
    jobs = json.load(fh)
for job in jobs:
    stats = job.get("statistics", {}) or {}
    query = stats.get("query", {}) or {}
    if not query:
        continue
    billed = query.get("totalBytesBilled")
    processed = query.get("totalBytesProcessed")
    if billed is None:
        continue
    created = stats.get("creationTime")
    when = (datetime.datetime.fromtimestamp(int(created) / 1000, datetime.timezone.utc)
            .strftime("%Y-%m-%dT%H:%M:%SZ") if created else "unknown")
    job_id = (job.get("jobReference", {}) or {}).get("jobId", "unknown")
    print("\t".join([job_id, when, str(processed), str(billed)]))
PY

  local count=0 job_id when processed billed
  while IFS=$'\t' read -r job_id when processed billed; do
    [[ -z "${job_id}" ]] && continue
    ledger_append "(console, not committed)" "${job_id}" "${when}" "unrecorded" \
      "not_taken" "${processed}" "${billed}" \
      "prior manual console query, run before this session and outside §10.1's protocol: no dry run was taken, so no estimate and no divergence exist"
    count=$(( count + 1 ))
  done < <(sort -t$'\t' -k2,2 "${tmp}.rows")
  rm -f "${tmp}" "${tmp}.rows"
  echo "Seeded ${count} prior query job(s) into the ledger." >&2
}

# --- direct invocation -------------------------------------------------------
# So the checker can be run without being sourced:
#   bash src/recon/budget.sh seed | total | remaining | gate <bytes>
if [[ "${BASH_SOURCE[0]:-}" == "${0}" ]]; then
  case "${1:-}" in
    seed)      seed_ledger ;;
    total)     ledger_total_billed ;;
    remaining) ledger_remaining ;;
    gate)      gate_check "${2:?gate needs an estimate in bytes}" ;;
    *) echo "usage: bash src/recon/budget.sh {seed|total|remaining|gate <bytes>}" >&2; exit 64 ;;
  esac
fi
