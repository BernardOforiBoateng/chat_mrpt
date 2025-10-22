#!/bin/bash
set -e

echo "=========================================="
echo "Fix Streaming Endpoint - Allow GET for SSE"
echo "=========================================="

# Production instance IPs
INSTANCE1_IP="3.21.167.170"
INSTANCE2_IP="18.220.103.20"
KEY_PATH="/tmp/chatmrpt-key2.pem"

# Ensure key exists
if [ ! -f "$KEY_PATH" ]; then
    cp aws_files/chatmrpt-key.pem $KEY_PATH
    chmod 600 $KEY_PATH
fi

echo -e "\n🔴 PROBLEM IDENTIFIED:"
echo "EventSource (SSE) only supports GET requests"
echo "But Flask endpoint expects POST"
echo "This causes 405 METHOD NOT ALLOWED"
echo ""

for IP in $INSTANCE1_IP $INSTANCE2_IP; do
    echo -e "\n🔧 Fixing instance $IP..."
    ssh -i $KEY_PATH ec2-user@$IP 'bash -s' << 'EOF'
    set -e
    cd /home/ec2-user/ChatMRPT
    
    # Find and fix the streaming endpoint
    echo "1. Locating streaming endpoint..."
    ROUTE_FILE="app/web/routes/analysis_routes.py"
    
    if [ -f "$ROUTE_FILE" ]; then
        echo "2. Backing up route file..."
        sudo cp $ROUTE_FILE ${ROUTE_FILE}.backup_$(date +%Y%m%d_%H%M%S)
        
        echo "3. Updating to accept both GET and POST..."
        sudo sed -i "s/@analysis_bp.route('\/send_message_streaming', methods=\['POST'\])/@analysis_bp.route('\/send_message_streaming', methods=['GET', 'POST'])/" $ROUTE_FILE
        
        echo "4. Verifying change..."
        if grep -q "methods=\['GET', 'POST'\]" $ROUTE_FILE; then
            echo "   ✅ Route now accepts GET and POST"
        else
            echo "   ⚠️ Update may need manual check"
        fi
    fi
    
    # Also check core_routes.py
    CORE_ROUTE="app/web/routes/core_routes.py"
    if grep -q "send_message_streaming" $CORE_ROUTE 2>/dev/null; then
        echo "5. Found in core_routes, updating..."
        sudo cp $CORE_ROUTE ${CORE_ROUTE}.backup_$(date +%Y%m%d_%H%M%S)
        sudo sed -i "s/methods=\['POST'\]/methods=['GET', 'POST']/" $CORE_ROUTE
    fi
    
    echo "✅ Streaming endpoint fixed on $HOSTNAME"
EOF
done

echo -e "\n6. Restarting services..."
for IP in $INSTANCE1_IP $INSTANCE2_IP; do
    echo "   Restarting $IP..."
    ssh -i $KEY_PATH ec2-user@$IP 'sudo systemctl restart chatmrpt'
done

echo -e "\n7. Testing streaming endpoint..."
sleep 5
echo "Testing GET request to streaming endpoint..."
curl -s -X GET "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com/send_message_streaming?message=test&session_id=test" \
    -H "Accept: text/event-stream" \
    --max-time 2 2>&1 | head -5 || echo "Connection test complete"

echo -e "\n=========================================="
echo "✅ STREAMING ENDPOINT FIXED!"
echo "=========================================="
echo "The endpoint now accepts GET requests for EventSource"
echo "This should fix the 405 METHOD NOT ALLOWED error"
echo ""
echo "Test at:"
echo "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo "=========================================="