#!/bin/bash

# Deploy TPR 226 ward fix to staging environment
# This fixes the issue where 234 features were created instead of 226

echo "=================================================="
echo "Deploying TPR 226 Ward Fix to Staging"
echo "=================================================="

# Configuration
KEY_PATH="/tmp/chatmrpt-key.pem"
STAGING_IPS=("172.31.46.84" "172.31.24.195")
FILE_TO_DEPLOY="app/tpr_module/services/shapefile_extractor.py"

# Prepare SSH key
echo "Preparing SSH key..."
cp aws_files/chatmrpt-key.pem $KEY_PATH
chmod 600 $KEY_PATH

# Deploy to each staging instance
for IP in "${STAGING_IPS[@]}"; do
    echo ""
    echo "----------------------------------------"
    echo "Deploying to staging instance: $IP"
    echo "----------------------------------------"
    
    # Copy the fixed file
    echo "Copying shapefile_extractor.py..."
    scp -i $KEY_PATH -o StrictHostKeyChecking=no \
        $FILE_TO_DEPLOY \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/$FILE_TO_DEPLOY
    
    if [ $? -eq 0 ]; then
        echo "✓ File copied successfully"
    else
        echo "✗ Failed to copy file to $IP"
        continue
    fi
    
    # Restart the service
    echo "Restarting ChatMRPT service..."
    ssh -i $KEY_PATH -o StrictHostKeyChecking=no ec2-user@$IP \
        "sudo systemctl restart chatmrpt"
    
    if [ $? -eq 0 ]; then
        echo "✓ Service restarted successfully"
    else
        echo "✗ Failed to restart service on $IP"
    fi
    
    # Check service status
    echo "Checking service status..."
    ssh -i $KEY_PATH -o StrictHostKeyChecking=no ec2-user@$IP \
        "sudo systemctl status chatmrpt | head -10"
done

echo ""
echo "=================================================="
echo "Deployment Complete!"
echo "=================================================="
echo ""
echo "Test the fix at:"
echo "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "Changes deployed:"
echo "1. Added LGA+Ward join logic for precise matching"
echo "2. Added TPR data deduplication to prevent duplicates"
echo ""
echo "Expected result: Exactly 226 features for Adamawa State"