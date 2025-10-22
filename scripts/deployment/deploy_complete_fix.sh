#!/bin/bash
# Deploy complete Data Analysis V3 fixes (backend + frontend)

set -e

echo "========================================="
echo "   Deploying Complete Fixes to Staging  "
echo "========================================="

# Staging instances
STAGING_IPS=(
    "3.21.167.170"    # Instance 1
    "18.220.103.20"   # Instance 2
)

KEY_PATH="/tmp/chatmrpt-key.pem"

# Deploy to each instance
for ip in "${STAGING_IPS[@]}"; do
    echo ""
    echo "Deploying to $ip..."
    echo "----------------------------------------"
    
    # Backend Python files
    echo "Deploying backend files..."
    scp -i $KEY_PATH app/data_analysis_v3/core/agent.py ec2-user@$ip:/home/ec2-user/ChatMRPT/app/data_analysis_v3/core/
    scp -i $KEY_PATH app/data_analysis_v3/core/column_validator.py ec2-user@$ip:/home/ec2-user/ChatMRPT/app/data_analysis_v3/core/
    scp -i $KEY_PATH app/data_analysis_v3/core/executor.py ec2-user@$ip:/home/ec2-user/ChatMRPT/app/data_analysis_v3/core/
    scp -i $KEY_PATH app/data_analysis_v3/prompts/system_prompt.py ec2-user@$ip:/home/ec2-user/ChatMRPT/app/data_analysis_v3/prompts/
    
    # Frontend JavaScript file (THIS WAS MISSING!)
    echo "Deploying frontend file..."
    scp -i $KEY_PATH app/static/js/modules/upload/data-analysis-upload.js ec2-user@$ip:/home/ec2-user/ChatMRPT/app/static/js/modules/upload/
    
    # Restart service
    echo "Restarting service..."
    ssh -i $KEY_PATH ec2-user@$ip "sudo systemctl restart chatmrpt"
    
    echo "✓ Deployment to $ip completed"
done

echo ""
echo "✅ Complete deployment finished!"
echo "The frontend changes are now deployed."
