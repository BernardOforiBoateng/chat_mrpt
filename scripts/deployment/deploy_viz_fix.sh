#!/bin/bash

# Deploy TPR visualization fix
echo "🚀 Deploying TPR Visualization Fix"
echo "==================================="
echo ""
echo "🔍 ISSUE: TPR map path was incorrect (relative path issue)"
echo "✅ FIX: Use session_folder path for map file"
echo ""

# Deploy to staging
STAGING_IPS=("3.21.167.170" "18.220.103.20")
KEY_PATH="/tmp/chatmrpt-key.pem"

for ip in "${STAGING_IPS[@]}"; do
    echo "📦 Deploying to $ip..."
    scp -i $KEY_PATH "app/data_analysis_v3/core/tpr_workflow_handler.py" "ec2-user@$ip:/home/ec2-user/ChatMRPT/app/data_analysis_v3/core/tpr_workflow_handler.py"
    ssh -i $KEY_PATH "ec2-user@$ip" "sudo systemctl restart chatmrpt"
    echo "✅ Done"
done

echo ""
echo "🎉 TPR Visualization Fix Deployed!"
echo "The TPR map should now show in the chat after calculation."