#!/bin/bash

# Manual TPR Workflow Test Script
# Tests the complete workflow with formatter fixes

BASE_URL="https://d225ar6c86586s.cloudfront.net"
SESSION_COOKIE="tpr_test_session_$(date +%s)"

echo "============================================================"
echo "  MANUAL TPR WORKFLOW TEST"
echo "  Session: $SESSION_COOKIE"
echo "============================================================"
echo ""

# Function to send message and display response
send_message() {
    local message="$1"
    local step_desc="$2"

    echo "-----------------------------------------------------------"
    echo "[$step_desc]"
    echo "Sending: '$message'"
    echo ""

    response=$(curl -s -X POST "$BASE_URL/data_analysis_v3/chat" \
        -H "Content-Type: application/json" \
        -H "Cookie: session=$SESSION_COOKIE" \
        -d "{\"message\": \"$message\"}" \
        --max-time 60)

    # Extract message field
    msg=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('message', 'ERROR: ' + str(data)))" 2>/dev/null)

    if [ $? -eq 0 ]; then
        echo "Response:"
        echo "$msg" | head -30
        echo ""
    else
        echo "ERROR: Failed to parse response"
        echo "$response" | head -10
        echo ""
        return 1
    fi
}

echo "NOTE: Please upload TPR data first through the web interface"
echo "Go to: $BASE_URL and upload a TPR CSV file"
echo ""
read -p "Press Enter after uploading data..."

echo ""
echo "Starting TPR workflow tests..."
echo ""

# Test 1: TPR Introduction
send_message "tpr" "STEP 1: TPR Introduction"
sleep 2

# Test 2: Confirmation
send_message "yes" "STEP 2: Confirmation"
sleep 2

# Test 3: Check facility statistics
send_message "what are the options?" "STEP 3: View Facility Options"
sleep 2

# Test 4: Select primary
send_message "primary" "STEP 4: Select Primary Facilities"
sleep 2

# Test 5: Check age group statistics
send_message "show me the age groups" "STEP 5: View Age Group Options"
sleep 2

# Test 6: Test visualization phrase
send_message "show charts" "STEP 6: Request Visualizations"
sleep 2

# Test 7: Select U5
send_message "u5" "STEP 7: Select Under-5 Age Group"
sleep 3

# Test 8: Transition to risk
send_message "continue" "STEP 8: Transition to Risk Analysis"
sleep 2

echo "============================================================"
echo "  TEST COMPLETE"
echo "============================================================"
echo ""
echo "Review the responses above to verify:"
echo "  ✓ Statistics are displayed for facility levels"
echo "  ✓ Test counts are NOT zero"
echo "  ✓ Recommended markers appear"
echo "  ✓ Visualizations show on request"
echo "  ✓ Workflow completes successfully"
echo ""
