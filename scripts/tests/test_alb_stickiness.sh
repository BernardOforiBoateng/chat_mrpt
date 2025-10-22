#!/bin/bash

echo "=== TESTING ALB SESSION STICKINESS ==="
echo "This will test if the ALB routes requests with the same cookie to the same backend"
echo ""

# Create a temporary cookie file
COOKIE_FILE="/tmp/alb_test_cookie.txt"

# First request - get a session cookie
echo "1. Getting initial session cookie..."
curl -s -c $COOKIE_FILE -o /dev/null http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com/api/session/status
echo "Cookie obtained:"
cat $COOKIE_FILE | grep chatmrpt_session

echo -e "\n2. Making 5 requests with the SAME session cookie..."
echo "If ALB has sticky sessions, all should show the same worker/state"
for i in {1..5}; do
    echo -n "Request $i: "
    curl -s -b $COOKIE_FILE http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com/api/session/verify-tpr | jq -c '{tpr_active: .tpr_workflow_active}'
    sleep 0.5
done

echo -e "\n3. Testing TPR upload flow..."
# Upload a dummy TPR file and check session state
echo "Simulating TPR activation..."

rm -f $COOKIE_FILE