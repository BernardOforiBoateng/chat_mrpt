#!/bin/bash

echo "🚀 Deploying BOTH Critical Fixes to Staging"
echo "=========================================="
echo ""
echo "Fix 1: Workflow transition check for ALL sessions (not just with flag)"
echo "Fix 2: Add __DATA_UPLOADED__ trigger for clean transition"
echo ""

STAGING_IPS=("3.21.167.170" "18.220.103.20")
KEY_PATH="/tmp/chatmrpt-key.pem"

for ip in "${STAGING_IPS[@]}"; do
    echo "📦 Deploying to $ip..."
    
    # Deploy request_interpreter.py fix
    scp -i $KEY_PATH app/core/request_interpreter.py ec2-user@$ip:/home/ec2-user/ChatMRPT/app/core/request_interpreter.py
    
    # Deploy tpr_workflow_handler.py fix  
    scp -i $KEY_PATH app/data_analysis_v3/core/tpr_workflow_handler.py ec2-user@$ip:/home/ec2-user/ChatMRPT/app/data_analysis_v3/core/tpr_workflow_handler.py
    
    # Restart service
    ssh -i $KEY_PATH ec2-user@$ip "sudo systemctl restart chatmrpt"
    
    echo "✅ Done with $ip"
done

echo ""
echo "🎉 Both fixes deployed!"
echo ""
echo "What's fixed:"
echo "✅ Workflow transition now checked for ALL sessions"
echo "✅ __DATA_UPLOADED__ trigger added for clean transition"
echo ""
echo "Test it:"
echo "1. Upload TPR data"
echo "2. Complete TPR calculation"
echo "3. Say 'yes' to proceed"
echo "4. Should transition cleanly to main ChatMRPT!"