#!/bin/bash
# Quick test script for tournament processing
# Uses the existing tournament data

TOURNAMENT_ID="4651297216135168"
ENCODED_ID="QhlSGUAAA"

echo "Testing TopDeck Tournament Processor"
echo "======================================"
echo ""
echo "Test 1: Regular tournament (dry-run)"
echo "--------------------------------------"
python3 process_tournament_complete.py $TOURNAMENT_ID $ENCODED_ID

echo ""
echo ""
echo "Test 2: Champion event (2× points, dry-run)"
echo "--------------------------------------"
python3 process_tournament_complete.py $TOURNAMENT_ID $ENCODED_ID --champion

echo ""
echo ""
echo "======================================"
echo "Tests complete!"
echo ""
echo "To update Google Sheets, add --update-sheets flag:"
echo "  python3 process_tournament_complete.py $TOURNAMENT_ID $ENCODED_ID --update-sheets"
