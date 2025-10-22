#!/bin/bash

# Deploy workflow transition fix v2 to staging
# This fix ensures proper exit from Data Analysis V3 agent to main workflow

echo "🚀 Deploying workflow transition fix v2 to staging..."
echo "📝 Changes: Fixed sessionStorage checks to prevent routing back to Data Analysis after exit"

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

KEY_PATH="~/.ssh/chatmrpt-key.pem"

# Deploy to each staging instance
for ip in "${STAGING_IPS[@]}"; do
    echo "📦 Deploying to staging instance: $ip"
    
    # Copy files
    for file in "${FILES[@]}"; do
        echo "  📄 Copying $file..."
        scp -i $KEY_PATH "$file" "ec2-user@$ip:/home/ec2-user/ChatMRPT/$file"
    done
    
    # Restart service
    echo "  🔄 Restarting ChatMRPT service..."
    ssh -i $KEY_PATH "ec2-user@$ip" "sudo systemctl restart chatmrpt"
    
    echo "  ✅ Deployment to $ip complete"
done

echo "🎉 Workflow transition fix deployed to all staging instances!"
echo ""
echo "📝 Test Instructions:"
echo "1. Upload TPR data in Data Analysis tab"
echo "2. Complete TPR workflow and say 'yes' to proceed"
echo "3. Verify system switches to main ChatMRPT workflow"
echo "4. Check that 'Check data quality' uses main workflow, not Data Analysis agent"
echo ""
echo "Access staging at: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"