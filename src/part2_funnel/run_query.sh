#!/usr/bin/env bash
# The query runner for the Part 2 build session.
#
# One query, end to end, under ARCHITECTURE.md §10.1 as reset in v1.5:
#   dry run -> predict billed -> pre-flight gate on the prediction -> execute ->
#   read the ACTUAL bytes billed from job statistics -> write the result and its
#   provenance sidecar -> accumulate actuals into the running total -> evaluate
#   the halt rule.
#
# Executes through the bq CLI (A-087's pattern, A-131's precedent, A-160's
# decision). No BigQuery Python client is installed: .venv, requirements.txt and
# requirements.lock.txt describe the environment Part 3's clean-checkout
# guarantee rests on (§7.5), and two completed parts now reproduce from it.
#
# usage: src/part2_funnel/run_query.sh <sql-file> <output-basename> <shard-range-label>
#   e.g. src/part2_funnel/run_query.sh sql/31_part2_progression_matrix_and_funnel.sql \
#          part2_q31_progression_matrix_and_funnel "20180612-20181003 (114 shards)"
#
# Re-running a query bills again and appends a further ledger row. That is the
# honest record: the bytes were spent twice.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./budget.sh
source "${HERE}/budget.sh"

if (( $# < 3 )); then
  sed -n '2,22p' "${BASH_SOURCE[0]}" >&2
  exit 64
fi

SQL_FILE="$1"; OUT_BASE="$2"; SHARD_RANGE="$3"
[[ -f "${SQL_FILE}" ]] || { echo "No such SQL file: ${SQL_FILE}" >&2; exit 66; }
require_project

readonly TABLES_DIR="${REPO_ROOT}/outputs/tables"
readonly OUT_CSV="${TABLES_DIR}/${OUT_BASE}.csv"
readonly OUT_META="${TABLES_DIR}/${OUT_BASE}.meta.json"
mkdir -p "${TABLES_DIR}"
ledger_ensure

# The query is fed on stdin, never as a positional argument: these files open
# with "--" comment lines, and bq's flag parser reads a leading "--" as a flag
# name rather than as query text.
QUERY_FILE_REL="${SQL_FILE#"${REPO_ROOT}/"}"
JOB_ID="part2_$(basename "${OUT_BASE}")_$(date -u +%Y%m%dT%H%M%SZ)_$$"
WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

echo "==> ${QUERY_FILE_REL}"

# --- 1. dry run. The estimate is the only number available before execution,
#        so it authorises the query and is used for nothing else (§10.1).
if ! bq --project_id="${GOOGLE_CLOUD_PROJECT}" --format=json \
      query --dry_run --use_legacy_sql=false < "${SQL_FILE}" \
      > "${WORK}/dry.json" 2> "${WORK}/dry.err"; then
  echo "Dry run failed. The query is not run: §10.1 forbids executing a query" >&2
  echo "whose estimate was never taken." >&2
  sed -n '1,40p' "${WORK}/dry.err" >&2
  exit 65
fi

ESTIMATE="$(json_get "${WORK}/dry.json" statistics.query.totalBytesProcessed "")"
if [[ ! "${ESTIMATE}" =~ ^[0-9]+$ ]]; then
  ESTIMATE="$(json_get "${WORK}/dry.json" statistics.totalBytesProcessed "")"
fi
if [[ ! "${ESTIMATE}" =~ ^[0-9]+$ ]]; then
  ESTIMATE="$(grep -oE '[0-9]+ bytes' "${WORK}/dry.err" | head -1 | grep -oE '[0-9]+' || true)"
fi
if [[ ! "${ESTIMATE}" =~ ^[0-9]+$ ]]; then
  echo "Could not read a dry-run estimate. The query is not run." >&2
  cat "${WORK}/dry.json" "${WORK}/dry.err" >&2
  exit 65
fi

PREDICTED="$(predict_billed "${ESTIMATE}")"
PRIOR="$(prior_sessions_billed)"
echo "    dry-run estimate : $(human "${ESTIMATE}")  (${ESTIMATE} bytes)"
echo "    predicted billed : $(human "${PREDICTED}")  = max(10 MiB, ceil(estimate -> MiB))"
echo "    session spent    : $(human "$(ledger_total_billed)") of 20 GiB"
echo "    pair spent       : $(human "$(( PRIOR + $(ledger_total_billed) ))") of 40 GiB (Part 1: $(human "${PRIOR}"))"

# --- 2. the pre-flight gate, on the prediction and the accumulated actuals.
if ! gate_check "${ESTIMATE}"; then
  echo "    NOT RUN. Narrow the query and dry-run again, or record the item" >&2
  echo "    unanswered with this estimate and escalate (§10.1)." >&2
  exit 70
fi

# --- 3. execute. Cache is disabled (A-161): a cache hit bills zero, which would
#        miss A-126's prediction by the whole prediction and halt the session on
#        a query that was correct. --max_rows is explicit because bq query
#        truncates at 100 rows by default and would silently return a partial
#        result.
if ! bq --project_id="${GOOGLE_CLOUD_PROJECT}" --format=csv \
      query --use_legacy_sql=false --nouse_cache --max_rows=200000 \
      --job_id="${JOB_ID}" < "${SQL_FILE}" \
      > "${WORK}/result.csv" 2> "${WORK}/run.err"; then
  echo "Query execution failed." >&2
  sed -n '1,60p' "${WORK}/run.err" >&2
  exit 65
fi

# --- 4. actuals, from job statistics.
bq --project_id="${GOOGLE_CLOUD_PROJECT}" --format=prettyjson \
   show -j "${JOB_ID}" > "${WORK}/job.json" 2>/dev/null

PROCESSED="$(json_get "${WORK}/job.json" statistics.query.totalBytesProcessed "unknown")"
BILLED="$(json_get "${WORK}/job.json" statistics.query.totalBytesBilled "unknown")"
CREATED_MS="$(json_get "${WORK}/job.json" statistics.creationTime "")"
if [[ ! "${BILLED}" =~ ^[0-9]+$ ]]; then
  echo "Job statistics did not expose totalBytesBilled for ${JOB_ID}." >&2
  echo "§10.1 makes the running total untrackable in actuals without it; this" >&2
  echo "requires a superseding decision, not a silent fallback to the estimate." >&2
  exit 65
fi
JOB_DATE="$(
  if [[ "${CREATED_MS}" =~ ^[0-9]+$ ]]; then
    "${JSON_PY}" -c 'import sys,datetime;print(datetime.datetime.fromtimestamp(int(sys.argv[1])/1000,datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))' "${CREATED_MS}"
  else date -u +%Y-%m-%dT%H:%M:%SZ; fi
)"

ROW_COUNT="$("${JSON_PY}" - "${WORK}/result.csv" <<'PY'
import csv, sys
with open(sys.argv[1], newline="") as fh:
    rows = list(csv.reader(fh))
print(max(len(rows) - 1, 0))   # data rows, excluding the header
PY
)"

echo "    bytes processed  : $(human "${PROCESSED}")"
echo "    bytes BILLED     : $(human "${BILLED}")  (${BILLED} bytes)"
echo "    rows returned    : ${ROW_COUNT}"
if (( ROW_COUNT >= 200000 )); then
  echo "    WARNING: row count is at the --max_rows cap; the result may be truncated." >&2
fi

# --- 5. publish the result and its provenance sidecar (A-080, A-086, A-093).
cp "${WORK}/result.csv" "${OUT_CSV}"
"${JSON_PY}" - "${OUT_META}" "${QUERY_FILE_REL}" "${JOB_ID}" "${JOB_DATE}" \
  "${SHARD_RANGE}" "${ESTIMATE}" "${PROCESSED}" "${BILLED}" "${ROW_COUNT}" \
  "${OUT_BASE}.csv" "${PREDICTED}" <<'PY'
import json, sys
(out, query_file, job_id, job_date, shard_range,
 estimate, processed, billed, row_count, csv_name, predicted) = sys.argv[1:12]
estimate, processed, billed, predicted = int(estimate), int(processed), int(billed), int(predicted)
meta = {
    "result_file": csv_name,
    "query_file": query_file,
    "shard_range_covered": shard_range,
    "query_job_date": job_date,
    "dry_run_estimate_bytes": estimate,
    "predicted_billed_bytes": predicted,
    "actual_bytes_billed": billed,
    "row_count": int(row_count),
    "bytes_processed": processed,
    "divergence_bytes": billed - estimate,
    "divergence_ratio": (round(billed / estimate, 4) if estimate else "undefined"),
    "prediction_delta_bytes": billed - predicted,
    "job_id": job_id,
    "note": ("Provenance per ARCHITECTURE.md §10.1 and A-086. The source is an "
             "external table that no checksum covers, so this file records what "
             "authorised the query and what it cost, in place of §7.5's "
             "cross-machine byte-identity rule (§9 open question 7). "
             "predicted_billed_bytes is A-126's rule "
             "max(10 MiB, ceil(estimate -> MiB)); prediction_delta_bytes is what "
             "the halt rule tests against 1 MiB."),
}
with open(out, "w") as fh:
    json.dump(meta, fh, indent=2, sort_keys=True)
    fh.write("\n")
PY

# --- 6. record, accumulate actuals, then evaluate the halt rule.
ledger_append "${QUERY_FILE_REL}" "${JOB_ID}" "${JOB_DATE}" "${SHARD_RANGE}" \
  "${ESTIMATE}" "${PROCESSED}" "${BILLED}" ""

DIVERGENCE=$(( BILLED - ESTIMATE ))
DELTA=$(( BILLED - PREDICTED ))
if (( ESTIMATE > 0 )); then
  echo "    divergence       : $(human "${DIVERGENCE#-}") $( (( DIVERGENCE < 0 )) && echo under || echo over ) estimate, ratio $(awk -v b="${BILLED}" -v e="${ESTIMATE}" 'BEGIN{printf "%.4f", b/e}')"
fi
echo "    prediction delta : ${DELTA} bytes (halt band is +/- 1 MiB)"
echo "    session total    : $(human "$(ledger_total_billed)") of 20 GiB"
echo "    pair total       : $(human "$(( PRIOR + $(ledger_total_billed) ))") of 40 GiB"

if ! halt_check "${ESTIMATE}" "${BILLED}"; then
  echo "    The session stops here. Record the divergence and what it implies about" >&2
  echo "    the planner, then escalate to the architecture session (§10.1)." >&2
  exit 75
fi
echo "    ok"
