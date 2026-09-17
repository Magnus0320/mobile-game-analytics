#!/usr/bin/env bash
# Thin wrapper: one command, whole part (ARCHITECTURE.md §7.1).
#
# The SQL execution order is the file number in sql/ (§7.2). The rendering order
# lives in src/part1_retention/render_part1.py, not here.
#
#   GOOGLE_CLOUD_PROJECT=<your sandbox project> ./run_part1.sh
#
# §8 keeps the project id in the environment and out of every committed file.
# Authentication is user credentials only -- `gcloud auth login` plus
# `gcloud auth application-default login` -- and no credential file of any kind
# is ever written into this repository.
set -euo pipefail

cd "$(dirname "$0")"

if [[ -z "${GOOGLE_CLOUD_PROJECT:-}" ]]; then
  echo "GOOGLE_CLOUD_PROJECT is unset. §8 keeps the project id in the environment," >&2
  echo "never in a committed file:" >&2
  echo "  GOOGLE_CLOUD_PROJECT=<project id> ./run_part1.sh" >&2
  exit 78
fi
if ! command -v bq >/dev/null 2>&1; then
  echo "The bq CLI is not on PATH. Part 1 queries BigQuery through bq (A-131)," >&2
  echo "so that nothing is added to the environment Part 3's lock file describes." >&2
  exit 78
fi
if [[ ! -x .venv/bin/python ]]; then
  echo "No .venv found. Create it at the interpreter pinned in .python-version:" >&2
  echo "  brew install python@3.12 && /opt/homebrew/bin/python3.12 -m venv .venv" >&2
  echo "  ./.venv/bin/python -m pip install -r requirements.lock.txt" >&2
  exit 78
fi

RUN="src/part1_retention/run_query.sh"
RANGE="20180612-20181003 (114 shards)"

# --- the queries, in the order their numbers state (§7.2) --------------------
"${RUN}" sql/10_part1_population_and_duplicates.sql   part1_q10_population_and_duplicates  "${RANGE}"
"${RUN}" sql/11_part1_day_key_offset.sql              part1_q11_day_key_offset             "${RANGE}"
"${RUN}" sql/12_part1_cohort_inventory.sql            part1_q12_cohort_inventory           "${RANGE}"
"${RUN}" sql/13_part1_classic_retention.sql           part1_q13_classic_retention          "${RANGE}"
"${RUN}" sql/14_part1_rolling_retention.sql           part1_q14_rolling_retention          "${RANGE}"
"${RUN}" sql/15_part1_segment_constancy.sql           part1_q15_segment_constancy          "${RANGE}"
"${RUN}" sql/16_part1_retention_by_segment.sql        part1_q16_retention_by_segment       "${RANGE}"
"${RUN}" sql/17_part1_first_open_time_agreement.sql   part1_q17_first_open_time_agreement  "${RANGE}"

# --- §10.7.3's gate. Query 18 runs only if the agreement clears 99.0% --------
echo "==> §10.7.3 gate"
if ./.venv/bin/python -m src.part1_retention.gate; then
  "${RUN}" sql/18_part1_first_open_time_sensitivity.sql part1_q18_first_open_time_sensitivity "${RANGE}"
else
  echo "    The sensitivity check is omitted and the observed agreement share is"
  echo "    reported in its place (§10.7.3). Query 18 is not run."
fi

# --- render, then verify -----------------------------------------------------
exec ./.venv/bin/python -m src.part1_retention.render_part1 "$@"
