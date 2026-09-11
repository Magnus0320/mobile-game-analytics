#!/usr/bin/env bash
# Thin wrapper: one command, whole part (ARCHITECTURE.md §7.1).
# Execution order lives in src/part3_experiment/run_part3.py, not here.
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -x .venv/bin/python ]]; then
  echo "No .venv found. Create it at the interpreter pinned in .python-version:" >&2
  echo "  brew install python@3.12 && /opt/homebrew/bin/python3.12 -m venv .venv" >&2
  echo "  ./.venv/bin/python -m pip install -r requirements.lock.txt" >&2
  exit 1
fi

exec ./.venv/bin/python -m src.part3_experiment.run_part3 "$@"
