#!/bin/bash

# Deploy workflow transition fix v3 to staging
# This fixes the flag file removal and prevents re-routing to Data Analysis V3

echo "🚀 Deploying Workflow Transition Fix v3 to Staging"
echo "=================================================="
echo ""

# Files to deploy
FILES=(
    "app/data_analysis_v3/core/tpr_workflow_handler.py"
    "app/core/request_interpreter.py"
    "app/static/js/modules/chat/core/message-handler.js"
)

# Staging instances (updated IPs as of Jan 7, 2025)
STAGING_IPS=(
    "3.21.167.170"
    "18.220.103.20"
)

KEY_PATH="/tmp/chatmrpt-key.pem"

echo "📋 Critical fixes in this version:"
echo "  ✅ Flag file (.data_analysis_mode) is now removed on transition"
echo "  ✅ request_interpreter checks workflow_transitioned state"
echo "  ✅ Frontend properly handles exit_data_analysis_mode signal"
echo "  ✅ Visualization debug logging added"
echo ""

# Deploy to each staging instance
for ip in "${STAGING_IPS[@]}"; do
    echo "📦 Deploying to staging instance: $ip"
    echo "----------------------------------------"
    
    # Copy files
    for file in "${FILES[@]}"; do
        echo "  📄 Copying $file..."
        scp -i $KEY_PATH "$file" "ec2-user@$ip:/home/ec2-user/ChatMRPT/$file"
        if [ $? -eq 0 ]; then
            echo "     ✅ Success"
        else
            echo "     ❌ Failed to copy $file"
            exit 1
        fi
    done
    
    # Clear browser cache by updating version
    echo "  🔄 Updating JS cache version..."
    ssh -i $KEY_PATH "ec2-user@$ip" << 'REMOTE_CMD'
    cd /home/ec2-user/ChatMRPT
    # Update cache buster in index.html
    sed -i "s/v=[0-9]*/v=$(date +%s)/g" app/templates/index.html 2>/dev/null || true
REMOTE_CMD
    
    # Restart service
    echo "  🔄 Restarting ChatMRPT service..."
    ssh -i $KEY_PATH "ec2-user@$ip" "sudo systemctl restart chatmrpt"
    
    # Wait for service to start
    echo "  ⏳ Waiting for service to start..."
    sleep 5
    
    # Check service status
    echo "  🔍 Checking service status..."
    ssh -i $KEY_PATH "ec2-user@$ip" "sudo systemctl status chatmrpt --no-pager | head -10"
    
    echo "  ✅ Deployment to $ip complete"
    echo ""
done

echo "🎉 Workflow Transition Fix v3 deployed successfully!"
echo ""
echo "📝 What was fixed:"
echo "1. ✅ Flag file removal: .data_analysis_mode is deleted on transition"
echo "2. ✅ State checking: request_interpreter respects workflow_transitioned"
echo "3. ✅ Frontend handling: Properly exits Data Analysis mode"
echo "4. ✅ Visualization debugging: Added console logs for troubleshooting"
echo ""
echo "🧪 Testing Instructions:"
echo "1. Go to: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo "2. Switch to Data Analysis tab"
echo "3. Upload TPR data (e.g., adamawa_tpr_cleaned.csv)"
echo "4. Complete TPR workflow (select Primary, Under 5 Years)"
echo "5. When asked to proceed to risk analysis, say 'yes'"
echo "6. Type 'Check data quality'"
echo ""
echo "✅ Expected Result: Response from main ChatMRPT (not Data Analysis V3)"
echo "❌ If still routing to V3: Check browser console for debug logs"
echo ""
echo "⚠️ IMPORTANT: Clear browser cache (Ctrl+Shift+R) before testing!"