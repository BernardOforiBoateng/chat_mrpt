#!/bin/bash

# Test script to verify Data Analysis upload issue
# This simulates what the frontend does and shows the missing link

echo "======================================"
echo "Data Analysis Upload Issue Test"
echo "======================================"
echo ""

# Test file
TEST_FILE="test_data.csv"
SESSION_ID="test_session_$(date +%s)"

# Create a simple test CSV
echo "Creating test CSV file..."
cat > $TEST_FILE << EOF
State,LGA,Ward,Value
Lagos,Ikeja,Ward1,100
Lagos,Ikeja,Ward2,200
Lagos,Ikeja,Ward3,150
EOF

echo "Test file created: $TEST_FILE"
echo ""

# Step 1: Upload file
echo "Step 1: Uploading file to /api/data-analysis/upload..."
UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:5000/api/data-analysis/upload \
  -F "file=@$TEST_FILE" \
  -F "session_id=$SESSION_ID")

echo "Upload Response:"
echo "$UPLOAD_RESPONSE" | python3 -m json.tool
echo ""

# Extract session_id from response
BACKEND_SESSION=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('session_id', ''))")

if [ -z "$BACKEND_SESSION" ]; then
  echo "ERROR: No session_id in upload response"
  exit 1
fi

echo "Backend Session ID: $BACKEND_SESSION"
echo ""

# Step 2: Trigger analysis
echo "Step 2: Triggering analysis via /api/v1/data-analysis/chat..."
ANALYSIS_RESPONSE=$(curl -s -X POST http://localhost:5000/api/v1/data-analysis/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"analyze uploaded data\", \"session_id\": \"$BACKEND_SESSION\"}")

echo "Analysis Response:"
echo "$ANALYSIS_RESPONSE" | python3 -m json.tool
echo ""

# Step 3: Check if response has data
if echo "$ANALYSIS_RESPONSE" | grep -q "success.*true"; then
  echo "✅ Backend returned success with analysis data"
  echo ""
  echo "📍 THE ISSUE:"
  echo "The frontend receives this response but doesn't display it!"
  echo "It only does: console.log('Data analysis triggered successfully:', responseData)"
  echo "But never adds the message to the chat store."
else
  echo "❌ Backend did not return success"
fi

echo ""
echo "======================================"
echo "Test Complete"
echo "======================================"

# Cleanup
rm -f $TEST_FILE