#!/bin/sh
# Start Guardian: server, room agent (camera) and dashboard, then open the dashboard.
# Options: --no-telegram  --mock  --demo   (see scripts/run_guardian.py). Ctrl+C stops it.
cd "$(dirname "$0")" && exec .venv/bin/python scripts/run_guardian.py "$@"
