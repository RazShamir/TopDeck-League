#!/bin/bash
# Quick Google OAuth login to get SACSID

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Use venv Python if available
if [ -f "./venv/bin/python3" ]; then
    PYTHON="./venv/bin/python3"
else
    PYTHON="python3"
fi

echo "Running Google OAuth login..."
$PYTHON google_login.py
