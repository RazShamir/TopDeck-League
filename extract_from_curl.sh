#!/bin/bash
# Extract encoded tournament ID from curl command

# Read from stdin
INPUT=$(cat)

if [ -z "$INPUT" ]; then
    echo "Usage: Pipe a curl command to this script"
    echo ""
    echo "Example:"
    echo "  1. In Chrome DevTools Network tab, right-click tournament request"
    echo "  2. Copy → Copy as cURL"
    echo "  3. Run: pbpaste | ./extract_from_curl.sh"
    echo "  or: cat curl_command.txt | ./extract_from_curl.sh"
    exit 1
fi

# Extract the encoded ID from the payload
ENCODED_ID=$(echo "$INPUT" | grep -oP 'java\.lang\.Long/4227064769\|1\|2\|3\|4\|1\|5\|5\|\K[^|]+' | head -1)

if [ -z "$ENCODED_ID" ]; then
    echo "✗ Could not find encoded tournament ID in curl command"
    echo ""
    echo "Make sure the curl command includes the --data-raw parameter"
    echo "with the GWT-RPC payload"
    exit 1
fi

echo "✓ Found encoded ID: $ENCODED_ID"
echo ""
echo "Test with:"
echo "  ./test_with_browser_payload.sh $ENCODED_ID"
