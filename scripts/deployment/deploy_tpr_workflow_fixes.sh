#!/bin/bash

# Deploy TPR workflow fixes to staging
# Fixes:
# 1. Markdown parsing in streaming (frontend)
# 2. TPR workflow state checking in agent
# 3. Column detection for TPR calculation
# 4. State name passing through workflow

echo "🚀 Deploying TPR workflow fixes to staging..."

# Files to deploy
FILES=(
    "app/static/js/modules/chat/core/message-handler.js"
    "app/data_analysis_v3/core/agent.py"
    "app/core/tpr_utils.py"
    "app/data_analysis_v3/core/tpr_data_analyzer.py"
    "app/data_analysis_v3/core/formatters.py"
)

# Staging instances (new IPs as of Jan 7, 2025)
STAGING_IPS=("3.21.167.170" "18.220.103.20")

# Key location
KEY_PATH="/tmp/chatmrpt-key2.pem"

# Copy key if not exists
if [ ! -f "$KEY_PATH" ]; then
    cp aws_files/chatmrpt-key.pem "$KEY_PATH"
    chmod 600 "$KEY_PATH"
fi

echo "📋 Files to deploy:"
for file in "${FILES[@]}"; do
    echo "  - $file"
done

# Deploy to each staging instance
for ip in "${STAGING_IPS[@]}"; do
    echo ""
    echo "📦 Deploying to staging instance: $ip"
    
    # Copy files
    for file in "${FILES[@]}"; do
        echo "  Copying $file..."
        scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$file" "ec2-user@$ip:/home/ec2-user/ChatMRPT/$file"
        if [ $? -eq 0 ]; then
            echo "  ✅ $file deployed"
        else
            echo "  ❌ Failed to deploy $file"
        fi
    done
    
    # Restart service
    echo "  🔄 Restarting ChatMRPT service..."
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "ec2-user@$ip" "sudo systemctl restart chatmrpt"
    
    # Check status
    echo "  📊 Checking service status..."
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "ec2-user@$ip" "sudo systemctl is-active chatmrpt"
done

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📝 Test the fixes at:"
echo "  http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "🧪 Testing checklist:"
echo "  1. Upload TPR data (adamawa_tpr_cleaned.csv)"
echo "  2. Select option 2 for TPR workflow"
echo "  3. Verify markdown formatting (bold text shows correctly)"
echo "  4. Select 'Primary' and verify workflow continues (not restarting)"
echo "  5. Check that state name shows 'Adamawa' (not 'this state')"
echo "  6. Verify TPR calculation returns actual results (not 0)"