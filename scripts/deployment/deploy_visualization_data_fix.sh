#!/bin/bash
echo "🚀 Deploying Visualization Display and Data Access Fixes"
echo "========================================================"
echo ""
echo "This deployment fixes:"
echo "✅ TPR map visualization display in chat"
echo "✅ Data access in main workflow after V3 transition"
echo "✅ Proper data quality checks with actual data"
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
    echo "  • Uploading fixed api-client.js (with visualization passing)..."
    scp -i $KEY_PATH app/static/js/modules/utils/api-client.js ec2-user@$ip:/home/ec2-user/ChatMRPT/app/static/js/modules/utils/
    
    # Deploy fixed Python files
    echo "  • Uploading tpr_workflow_handler.py (with data_loaded flag)..."
    scp -i $KEY_PATH app/data_analysis_v3/core/tpr_workflow_handler.py ec2-user@$ip:/home/ec2-user/ChatMRPT/app/data_analysis_v3/core/
    
    echo "  • Uploading request_interpreter.py (with session_data check)..."
    scp -i $KEY_PATH app/core/request_interpreter.py ec2-user@$ip:/home/ec2-user/ChatMRPT/app/core/
    
    # Clear Python cache
    echo "  • Clearing Python cache..."
    ssh -i $KEY_PATH ec2-user@$ip "cd /home/ec2-user/ChatMRPT && find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true"
    
    # Update cache busting timestamp
    echo "  • Updating cache busting..."
    ssh -i $KEY_PATH ec2-user@$ip "cd /home/ec2-user/ChatMRPT && sed -i 's/app\.js?v=[0-9]*/app.js?v=$(date +%s)/' app/templates/index.html 2>/dev/null || true"
    
    # Restart service
    echo "  • Restarting service..."
    ssh -i $KEY_PATH ec2-user@$ip "sudo systemctl restart chatmrpt"
    
    echo "✅ Deployment complete for $ip"
    echo ""
done

echo "🎉 All fixes deployed to staging!"
echo ""
echo "⚠️  IMPORTANT: Users need to hard refresh (Ctrl+F5)"
echo ""
echo "Test the complete workflow:"
echo "1. Go to http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo "2. Upload TPR data through Data Analysis tab"
echo "3. Complete TPR calculation"
echo "4. ✅ CHECK: TPR map should display in chat"
echo "5. Say 'yes' to proceed to risk analysis"
echo "6. ✅ CHECK: Exploration menu appears ONCE"
echo "7. Ask to 'Check data quality'"
echo "8. ✅ CHECK: Should analyze ACTUAL data, not give generic response"
echo ""
echo "Expected Results:"
echo "• TPR map visualization appears as iframe in chat"
echo "• Data quality check shows actual column names and statistics"
echo "• No duplicate messages"