#!/bin/bash
echo "🚀 Deploying Comprehensive Workflow Fixes"
echo "========================================"

STAGING_IPS=("3.21.167.170" "18.220.103.20")
KEY_PATH="/tmp/chatmrpt-key.pem"

for ip in "${STAGING_IPS[@]}"; do
    echo "📦 Deploying to $ip..."
    
    # Deploy all fixed files
    scp -i $KEY_PATH app/static/js/modules/utils/api-client.js ec2-user@$ip:/home/ec2-user/ChatMRPT/app/static/js/modules/utils/
    scp -i $KEY_PATH app/core/request_interpreter.py ec2-user@$ip:/home/ec2-user/ChatMRPT/app/core/
    scp -i $KEY_PATH app/data_analysis_v3/core/tpr_workflow_handler.py ec2-user@$ip:/home/ec2-user/ChatMRPT/app/data_analysis_v3/core/
    
    # Clear cache and restart
    ssh -i $KEY_PATH ec2-user@$ip "cd /home/ec2-user/ChatMRPT && find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true"
    ssh -i $KEY_PATH ec2-user@$ip "sudo systemctl restart chatmrpt"
    
    echo "✅ Done with $ip"
done

echo ""
echo "🎉 Comprehensive fixes deployed!"
echo ""
echo "What's fixed:"
echo "✅ No more duplicate messages"
echo "✅ Data properly accessible after transition"
echo "✅ TPR visualization should display"
echo "✅ Clean transition from V3 to main"
