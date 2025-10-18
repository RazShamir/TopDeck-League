#!/bin/bash
# Run automated tests for TopDeck API (Linux/Mac)

cd "$(dirname "$0")"

echo "Activating virtual environment..."
source venv/bin/activate

echo ""
echo "Running automated tests..."
echo ""

python scripts/run_tests.py
