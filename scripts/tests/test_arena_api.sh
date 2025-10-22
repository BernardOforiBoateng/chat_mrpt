#!/bin/bash

# Test Progressive Arena API Endpoints
# This script tests the new arena endpoints via curl

echo "================================================"
echo "Testing Progressive Arena API Endpoints"
echo "================================================"

# Base URL - use CloudFront
BASE_URL="https://d225ar6c86586s.cloudfront.net"

# Test message
TEST_MESSAGE="What is the capital of France?"

echo ""
echo "1. Testing Arena Status..."
echo "----------------------------------------"
curl -s "$BASE_URL/api/arena/status" | python3 -m json.tool | head -20

echo ""
echo "2. Starting Progressive Battle..."
echo "----------------------------------------"
RESPONSE=$(curl -s -X POST "$BASE_URL/api/arena/start_progressive" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"$TEST_MESSAGE\", \"num_models\": 3}")

echo "$RESPONSE" | python3 -m json.tool

# Extract battle_id from response
BATTLE_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('battle_id', ''))" 2>/dev/null)

if [ -z "$BATTLE_ID" ]; then
    echo "❌ Failed to start battle"
    exit 1
fi

echo ""
echo "Battle ID: $BATTLE_ID"

echo ""
echo "3. Getting Model Responses..."
echo "----------------------------------------"
echo "(This may take 30-60 seconds as models generate responses...)"

RESPONSES=$(curl -s -X POST "$BASE_URL/api/arena/get_progressive_responses" \
  -H "Content-Type: application/json" \
  -d "{\"battle_id\": \"$BATTLE_ID\"}")

echo "$RESPONSES" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if 'error' in data:
    print(f'❌ Error: {data[\"error\"]}')
else:
    print(f'✅ Got responses from models!')
    print(f'Round: {data.get(\"current_round\", 0)}')
    print(f'Model A: {data.get(\"model_a\", \"unknown\")}')
    print(f'Model B: {data.get(\"model_b\", \"unknown\")}')
    print(f'Response A preview: {data.get(\"response_a\", \"\")[:100]}...')
    print(f'Response B preview: {data.get(\"response_b\", \"\")[:100]}...')
    print(f'Remaining comparisons: {data.get(\"remaining_comparisons\", 0)}')
"

echo ""
echo "4. Submitting Choice (choosing left)..."
echo "----------------------------------------"

CHOICE_RESULT=$(curl -s -X POST "$BASE_URL/api/arena/submit_progressive_choice" \
  -H "Content-Type: application/json" \
  -d "{\"battle_id\": \"$BATTLE_ID\", \"choice\": \"left\"}")

echo "$CHOICE_RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if 'error' in data:
    print(f'❌ Error: {data[\"error\"]}')
else:
    status = data.get('status', 'unknown')
    if status == 'continue':
        print(f'✅ Choice recorded! Moving to next round...')
        print(f'Eliminated model: {data.get(\"eliminated_model\", \"unknown\")}')
        print(f'Next matchup: {data.get(\"model_a\", \"\")} vs {data.get(\"model_b\", \"\")}')
    elif status == 'completed':
        print(f'✅ Battle completed!')
        print(f'Final ranking: {data.get(\"final_ranking\", [])}')
        print(f'Winner: {data.get(\"winner\", \"unknown\")}')
    else:
        print(f'Status: {status}')
"

echo ""
echo "================================================"
echo "API Test Complete!"
echo "================================================"