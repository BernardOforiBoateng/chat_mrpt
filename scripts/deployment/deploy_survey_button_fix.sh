#!/bin/bash

echo "=== Deploying Survey Button Fix to Production ==="
echo "Date: $(date)"
echo ""

# Production instance IPs (current active instances)
INSTANCE_1="3.21.167.170"
INSTANCE_2="18.220.103.20"

# SSH key
KEY_FILE="~/.ssh/chatmrpt-key.pem"

# File to deploy
FILE_TO_DEPLOY="app/static/js/survey_button.js"

echo "📋 Deploying to Production Instances..."
echo ""

# Deploy to Instance 1
echo "Deploying to Instance 1 ($INSTANCE_1)..."
scp -i $KEY_FILE -o StrictHostKeyChecking=no $FILE_TO_DEPLOY ec2-user@$INSTANCE_1:/home/ec2-user/ChatMRPT/$FILE_TO_DEPLOY
if [ $? -eq 0 ]; then
    echo "✅ File copied to Instance 1"
    # Restart service
    ssh -i $KEY_FILE -o StrictHostKeyChecking=no ec2-user@$INSTANCE_1 'sudo systemctl restart chatmrpt'
    if [ $? -eq 0 ]; then
        echo "✅ Service restarted on Instance 1"
    else
        echo "⚠️  Failed to restart service on Instance 1"
    fi
else
    echo "❌ Failed to copy file to Instance 1"
fi

echo ""

# Deploy to Instance 2
echo "Deploying to Instance 2 ($INSTANCE_2)..."
scp -i $KEY_FILE -o StrictHostKeyChecking=no $FILE_TO_DEPLOY ec2-user@$INSTANCE_2:/home/ec2-user/ChatMRPT/$FILE_TO_DEPLOY
if [ $? -eq 0 ]; then
    echo "✅ File copied to Instance 2"
    # Restart service
    ssh -i $KEY_FILE -o StrictHostKeyChecking=no ec2-user@$INSTANCE_2 'sudo systemctl restart chatmrpt'
    if [ $? -eq 0 ]; then
        echo "✅ Service restarted on Instance 2"
    else
        echo "⚠️  Failed to restart service on Instance 2"
    fi
else
    echo "❌ Failed to copy file to Instance 2"
fi

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "📋 Next Step: Clear CloudFront cache"
echo "Run: ./invalidate_cloudfront.sh"
echo ""
echo "Test the changes at:"
echo "  - https://d225ar6c86586s.cloudfront.net"
echo "  - http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"

