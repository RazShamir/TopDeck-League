#!/bin/bash
# Start the TopDeck League API server

cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Start the server
echo "Starting TopDeck League API..."
echo "Server will be available at: http://127.0.0.1:8000"
echo "API docs available at: http://127.0.0.1:8000/docs"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

uvicorn app:app --host 127.0.0.1 --port 8000 --reload
