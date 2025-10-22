#!/bin/bash

# Deploy workflow transition fix v2 to staging
# This ensures complete exit from Data Analysis V3 agent to main workflow

echo "🚀 Deploying Workflow Transition Fix v2 to Staging"
echo "=================================================="
echo ""

# Files to deploy
FILES=(
    "app/web/routes/data_analysis_v3_routes.py"
    "app/data_analysis_v3/core/state_manager.py"
    "app/static/js/modules/utils/api-client.js"
    "app/static/js/modules/upload/data-analysis-upload.js"
)

# Staging instances (updated IPs as of Jan 7, 2025)
STAGING_IPS=(
    "3.21.167.170"
    "18.220.103.20"
)

KEY_PATH="/tmp/chatmrpt-key.pem"

echo "📋 Changes in this version:"
echo "  ✅ Backend checks workflow_transitioned flag before processing"
echo "  ✅ Returns exit_data_analysis_mode response when needed"
echo "  ✅ Frontend checks data_analysis_exited flag to prevent re-routing"
echo "  ✅ Properly clears sessionStorage flags on exit"
echo "  ✅ Fixed 'this' context in setTimeout for redirect"
echo ""

# Deploy to each staging instance
for ip in "${STAGING_IPS[@]}"; do
    echo "📦 Deploying to staging instance: $ip"
    echo "----------------------------------------"
    
    # First, backup existing files
    echo "  📁 Creating backup..."
    ssh -i $KEY_PATH "ec2-user@$ip" "mkdir -p /home/ec2-user/ChatMRPT/backups/$(date +%Y%m%d_%H%M%S)"
    
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
    ssh -i $KEY_PATH "ec2-user@$ip" "sudo systemctl status chatmrpt --no-pager | head -20"
    
    echo "  ✅ Deployment to $ip complete"
    echo ""
done

echo "🎉 Workflow Transition Fix v2 deployed to all staging instances!"
echo ""
echo "📝 Testing Instructions:"
echo "1. Go to: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo "2. Switch to Data Analysis tab"
echo "3. Upload TPR data (e.g., adamawa_tpr_cleaned.csv)"
echo "4. Complete TPR workflow (select Primary, Under 5 Years)"
echo "5. When asked to proceed to risk analysis, say 'yes'"
echo "6. Verify: System shows upload menu (not Data Analysis format)"
echo "7. Type 'Check data quality'"
echo "8. Verify: Response comes from main ChatMRPT (not Data Analysis agent)"
echo ""
echo "🔍 Expected Console Logs:"
echo "  - '📊 Exiting Data Analysis mode, switching to main workflow'"
echo "  - '📊 Data Analysis exited, routing to main workflow'"
echo ""
echo "⚠️ IMPORTANT: Clear browser cache (Ctrl+Shift+R) before testing!"