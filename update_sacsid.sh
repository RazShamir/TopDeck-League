#!/bin/bash
# Simple script to update SACSID cookie

set -e

cd "$(dirname "$0")"

if [ $# -ne 1 ]; then
    echo "Usage: $0 <sacsid-value>"
    echo ""
    echo "To get your SACSID:"
    echo "1. Open https://mtgarena.appspot.com in browser"
    echo "2. Press F12 → Application → Cookies"
    echo "3. Copy SACSID value"
    echo ""
    exit 1
fi

SACSID="$1"
API_TOKEN=$(grep API_TOKEN .env | cut -d'=' -f2)

echo "Updating SACSID..."

response=$(curl -s -X POST "http://localhost:8000/auth/set-sacsid" \
    -H "Content-Type: application/json" \
    -H "X-API-Token: ${API_TOKEN}" \
    -d "{\"sacsid\": \"${SACSID}\"}")

if echo "$response" | grep -q '"ok":true'; then
    masked=$(echo "$response" | grep -o '"sacsid_masked":"[^"]*"' | cut -d'"' -f4)
    echo "✓ SACSID updated successfully: ${masked}"
else
    echo "✗ Failed to update SACSID"
    echo "Response: $response"
    echo ""
    echo "Make sure the server is running: ./start_server.sh"
    exit 1
fi
