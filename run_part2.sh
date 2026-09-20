#!/usr/bin/env bash
# Thin wrapper: one command, whole part (ARCHITECTURE.md §7.1).
#
# The SQL execution order is the file number in sql/ (§7.2). The rendering order
# lives in src/part2_funnel/render_part2.py, not here.
#
#   GOOGLE_CLOUD_PROJECT=<your sandbox project> ./run_part2.sh
#
# §8 keeps the project id in the environment and out of every committed file.
# Authentication is user credentials only -- `gcloud auth login` plus
# `gcloud auth application-default login` -- and no credential file of any kind
# is ever written into this repository.
#
# No query here is gated on another query's result, so unlike Part 1 there is no
# gate step in this wrapper. §10.7.5's per-dimension constancy triggers (A-154)
# are applied in the rendering layer from query 32's shares, so that no line of
# committed SQL depends on a number a query produced (A-169).
set -euo pipefail

cd "$(dirname "$0")"

if [[ -z "${GOOGLE_CLOUD_PROJECT:-}" ]]; then
  echo "GOOGLE_CLOUD_PROJECT is unset. §8 keeps the project id in the environment," >&2
  echo "never in a committed file:" >&2
  echo "  GOOGLE_CLOUD_PROJECT=<project id> ./run_part2.sh" >&2
  exit 78
fi
if ! command -v bq >/dev/null 2>&1; then
  echo "The bq CLI is not on PATH. Part 2 queries BigQuery through bq (A-160)," >&2
  echo "so that nothing is added to the environment Part 3's lock file describes." >&2
  exit 78
fi
if [[ ! -x .venv/bin/python ]]; then
  echo "No .venv found. Create it at the interpreter pinned in .python-version:" >&2
  echo "  brew install python@3.12 && /opt/homebrew/bin/python3.12 -m venv .venv" >&2
  echo "  ./.venv/bin/python -m pip install -r requirements.lock.txt" >&2
  exit 78
fi

RUN="src/part2_funnel/run_query.sh"
RANGE="20180612-20181003 (114 shards)"

# --- the queries, in the order their numbers state (§7.2) --------------------
"${RUN}" sql/30_part2_population_and_vocabulary.sql        part2_q30_population_and_vocabulary        "${RANGE}"
"${RUN}" sql/31_part2_progression_matrix_and_funnel.sql    part2_q31_progression_matrix_and_funnel    "${RANGE}"
"${RUN}" sql/32_part2_segment_constancy.sql                part2_q32_segment_constancy                "${RANGE}"
"${RUN}" sql/33_part2_funnel_by_segment.sql                part2_q33_funnel_by_segment                "${RANGE}"

# --- render, then verify and audit -------------------------------------------
exec ./.venv/bin/python -m src.part2_funnel.render_part2 "$@"
