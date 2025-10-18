#!/bin/bash
# Wrapper script to run tournament processor with venv Python

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Use venv Python if available, otherwise fall back to system Python
if [ -f "./venv/bin/python3" ]; then
    PYTHON="./venv/bin/python3"
else
    PYTHON="python3"
fi

# Run the tournament processor with all arguments passed through
$PYTHON process_tournament_complete.py "$@"
