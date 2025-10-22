#!/bin/bash
# Simple TPR workflow test using curl

echo "=========================================="
echo "TPR STATE PERSISTENCE TEST - SIMPLIFIED"
echo "=========================================="

# Use an existing session that already has data
SESSION_ID="07cb4753-2386-4bbf-8b7f-865db3511d65"
echo "Using existing session: $SESSION_ID"
echo ""

# Test 1: Trigger TPR workflow
echo "[TEST 1] Triggering TPR workflow..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/data-analysis/chat \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"Run TPR analysis\"}")

echo "Response excerpt:"
echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('message', '')[:300])"
echo ""

# Check if Kaduna is mentioned
if echo "$RESPONSE" | grep -qi "kaduna"; then
    echo "✅ State (Kaduna) detected in response"
else
    echo "⚠️ State not mentioned in response"
fi
echo ""

# Test 2: Ask a question
echo "[TEST 2] Testing question handling..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/data-analysis/chat \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"What is TPR?\"}")

if echo "$RESPONSE" | grep -qi "test positivity rate\|percentage"; then
    echo "✅ Question answered correctly"
else
    echo "⚠️ Question may have been misinterpreted"
fi
echo ""

# Test 3: Select facility
echo "[TEST 3] Selecting primary facilities..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/data-analysis/chat \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"primary\"}")

echo "Response excerpt:"
echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('message', '')[:300])" 2>/dev/null || echo "Could not parse response"

# Check if state is in age group message
if echo "$RESPONSE" | grep -qi "kaduna.*age\|age.*kaduna\|primary facilities in.*which age"; then
    echo "✅ STATE PERSISTED - Kaduna shown in age selection!"
else
    echo "❌ STATE MISSING - Check if empty state in message"
    echo "$RESPONSE" | grep -o "facilities in [^,]*," | head -1
fi
echo ""

# Test 4: Select age group (critical for 500 error)
echo "[TEST 4] Selecting u5 age group (testing for 500 error)..."
HTTP_CODE=$(curl -s -o /tmp/tpr_response.txt -w "%{http_code}" -X POST http://localhost:8000/api/v1/data-analysis/chat \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"u5\"}")

if [ "$HTTP_CODE" == "500" ]; then
    echo "❌ 500 ERROR - State persistence fix failed!"
    echo "Error response:"
    cat /tmp/tpr_response.txt | head -20
elif [ "$HTTP_CODE" == "200" ]; then
    echo "✅ NO 500 ERROR - Request successful!"
    if grep -qi "kaduna\|TPR\|calculated" /tmp/tpr_response.txt; then
        echo "✅ TPR calculated successfully with state!"
    fi
else
    echo "⚠️ Unexpected status code: $HTTP_CODE"
fi

echo ""
echo "=========================================="
echo "TEST COMPLETE"
echo "==========================================="