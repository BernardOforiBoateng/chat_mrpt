#!/bin/bash
echo "🚀 DEPLOYING TOOL EXECUTION FIX TO STAGING"
echo "==========================================="
echo ""
echo "This deployment fixes:"
echo "✅ Tools will actually execute instead of being described"
echo "✅ Data will be loaded before tools are called"
echo "✅ Variable distribution maps will be created"
echo ""

# Staging IPs (updated Jan 7, 2025)
STAGING_IPS=("3.21.167.170" "18.220.103.20")
KEY_PATH="/tmp/chatmrpt-key.pem"

# Copy key if needed
if [ ! -f "$KEY_PATH" ]; then
    cp aws_files/chatmrpt-key.pem $KEY_PATH
    chmod 600 $KEY_PATH
    echo "✅ SSH key prepared"
fi

echo "📦 Deploying to ${#STAGING_IPS[@]} staging instances..."
echo ""

for ip in "${STAGING_IPS[@]}"; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📍 Deploying to instance: $ip"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Deploy Python fix for tool execution
    echo "  📄 Uploading request_interpreter.py (tool execution fix)..."
    scp -i $KEY_PATH -o StrictHostKeyChecking=no \
        app/core/request_interpreter.py \
        ec2-user@$ip:/home/ec2-user/ChatMRPT/app/core/
    
    # Clear Python cache
    echo "  🧹 Clearing Python cache..."
    ssh -i $KEY_PATH -o StrictHostKeyChecking=no ec2-user@$ip \
        "cd /home/ec2-user/ChatMRPT && find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true"
    
    # Restart service
    echo "  🔄 Restarting ChatMRPT service..."
    ssh -i $KEY_PATH -o StrictHostKeyChecking=no ec2-user@$ip \
        "sudo systemctl restart chatmrpt"
    
    # Check service status
    echo "  ✅ Checking service status..."
    ssh -i $KEY_PATH -o StrictHostKeyChecking=no ec2-user@$ip \
        "sudo systemctl status chatmrpt | grep Active"
    
    echo "  ✅ Deployment complete for $ip"
    echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 TOOL EXECUTION FIX DEPLOYED TO ALL INSTANCES!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 TESTING INSTRUCTIONS:"
echo "1. Go to: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo "2. Complete TPR workflow and transition to main workflow"
echo "3. Ask to 'Check data quality'"
echo "4. Ask to 'Plot me the map distribution for the evi variable'"
echo ""
echo "✅ EXPECTED RESULTS:"
echo "   • Data quality check will execute and show actual data statistics"
echo "   • Variable distribution will create an actual map (not just describe it)"
echo "   • Tools will execute with actual results, not just descriptions"
echo ""
echo "🔍 Monitor logs with:"
echo "   ssh -i $KEY_PATH ec2-user@3.21.167.170 'sudo journalctl -u chatmrpt -f | grep -E \"Tool|Loaded data|Executing\"'"