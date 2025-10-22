#!/bin/bash
echo "🚀 Deploying Final Workflow Transition Fix"
echo "=========================================="
echo ""
echo "This deployment fixes:"
echo "✅ Removes duplicate __DATA_UPLOADED__ triggers from message-handler.js"
echo "✅ Keeps V3 agent as sole controller of transition"
echo "✅ Ensures exploration menu appears only ONCE"
echo ""

STAGING_IPS=("3.21.167.170" "18.220.103.20")
KEY_PATH="/tmp/chatmrpt-key.pem"

# Copy key if needed
if [ ! -f "$KEY_PATH" ]; then
    cp aws_files/chatmrpt-key.pem $KEY_PATH
    chmod 600 $KEY_PATH
fi

for ip in "${STAGING_IPS[@]}"; do
    echo "📦 Deploying to $ip..."
    
    # Deploy fixed JavaScript files
    echo "  • Uploading fixed message-handler.js..."
    scp -i $KEY_PATH app/static/js/modules/chat/core/message-handler.js ec2-user@$ip:/home/ec2-user/ChatMRPT/app/static/js/modules/chat/core/
    
    echo "  • Uploading api-client.js (ensure latest version)..."
    scp -i $KEY_PATH app/static/js/modules/utils/api-client.js ec2-user@$ip:/home/ec2-user/ChatMRPT/app/static/js/modules/utils/
    
    # Deploy fixed Python files
    echo "  • Uploading request_interpreter.py (with os import fix)..."
    scp -i $KEY_PATH app/core/request_interpreter.py ec2-user@$ip:/home/ec2-user/ChatMRPT/app/core/
    
    echo "  • Uploading tpr_workflow_handler.py..."
    scp -i $KEY_PATH app/data_analysis_v3/core/tpr_workflow_handler.py ec2-user@$ip:/home/ec2-user/ChatMRPT/app/data_analysis_v3/core/
    
    # Clear Python cache
    echo "  • Clearing Python cache..."
    ssh -i $KEY_PATH ec2-user@$ip "cd /home/ec2-user/ChatMRPT && find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true"
    
    # Clear browser cache by adding timestamp to static files
    echo "  • Adding cache busting to force browser refresh..."
    ssh -i $KEY_PATH ec2-user@$ip "cd /home/ec2-user/ChatMRPT && sed -i 's/app\.js?v=[0-9]*/app.js?v=$(date +%s)/' app/templates/index.html 2>/dev/null || true"
    
    # Restart service
    echo "  • Restarting service..."
    ssh -i $KEY_PATH ec2-user@$ip "sudo systemctl restart chatmrpt"
    
    echo "✅ Deployment complete for $ip"
    echo ""
done

echo "🎉 Deployment complete to all staging instances!"
echo ""
echo "⚠️  IMPORTANT: Users need to hard refresh (Ctrl+F5) to clear browser cache"
echo ""
echo "Test the fix:"
echo "1. Go to http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo "2. Upload TPR data through Data Analysis tab"
echo "3. Complete TPR calculation"
echo "4. Say 'yes' to proceed to risk analysis"
echo "5. Check that exploration menu appears ONLY ONCE"
echo ""
echo "Check console for:"
echo "✅ No 'Sending redirect message' log after transition"
echo "✅ No duplicate exploration menus"
echo "✅ Clean transition from V3 to main workflow"