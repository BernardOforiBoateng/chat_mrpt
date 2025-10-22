#!/bin/bash

# Test debug logging by making requests to the API

echo "Testing Debug Logging for Risk Analysis Flow"
echo "==========================================="

# Production URL
URL="https://d225ar6c86586s.cloudfront.net"

# Test session ID (use a known session with data)
SESSION_ID="847e36e9-ad20-4641-afd5-bda1b5c8225a"

echo ""
echo "1. Testing risk analysis request..."
curl -X POST "${URL}/send_message" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Run the malaria risk analysis\",
    \"session_id\": \"${SESSION_ID}\"
  }" | jq '.'

echo ""
echo "2. Testing vulnerability map request..."
curl -X POST "${URL}/send_message" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"plot me the vulnerability map\",
    \"session_id\": \"${SESSION_ID}\"
  }" | jq '.'

echo ""
echo "3. Testing variable distribution request..."
curl -X POST "${URL}/send_message" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Plot me the map distribution for the evi variable\",
    \"session_id\": \"${SESSION_ID}\"
  }" | jq '.'

echo ""
echo "Now check the logs on AWS with:"
echo "ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@3.21.167.170 'sudo journalctl -u chatmrpt -f | grep "🔍 DEBUG"'"
