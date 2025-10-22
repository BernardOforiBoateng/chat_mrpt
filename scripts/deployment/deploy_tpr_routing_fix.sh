#!/bin/bash

echo "==========================================="
echo "   Deploying TPR Routing Fix to Staging   "
echo "==========================================="
echo ""

# Staging instances from CLAUDE.md (Public IPs as of Jan 7, 2025)
STAGING_IPS="3.21.167.170 18.220.103.20"
KEY_FILE="/tmp/deploy-key.pem"
REMOTE_USER="ec2-user"
REMOTE_PATH="/home/ec2-user/ChatMRPT"

# Files to deploy
FILES_TO_DEPLOY="app/data_analysis_v3/core/agent.py"

echo "Target instances: 2"
echo "- Instance 1: 3.21.167.170"
echo "- Instance 2: 18.220.103.20"
echo ""

# Deploy to each instance
for IP in $STAGING_IPS; do
    echo "----------------------------------------"
    echo "Deploying to $IP..."
    
    # Copy the fixed file
    echo "Copying agent.py..."
    scp -o StrictHostKeyChecking=no -i "$KEY_FILE" \
        $FILES_TO_DEPLOY \
        "$REMOTE_USER@$IP:$REMOTE_PATH/app/data_analysis_v3/core/" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "✅ File copied successfully"
        
        # Restart the service
        echo "Restarting ChatMRPT service..."
        ssh -o StrictHostKeyChecking=no -i "$KEY_FILE" \
            "$REMOTE_USER@$IP" \
            "sudo systemctl restart chatmrpt" 2>/dev/null
        
        if [ $? -eq 0 ]; then
            echo "✅ Service restarted on $IP"
        else
            echo "⚠️  Service restart may have failed on $IP"
        fi
    else
        echo "❌ Failed to copy files to $IP"
    fi
done

echo ""
echo "==========================================="
echo "Deployment Complete!"
echo ""
echo "Test the fix at:"
echo "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "Expected behavior:"
echo "1. Upload data file"
echo "2. See 2 clear options (not 4)"
echo "3. 'Show me test positivity trends' goes to general agent"
echo "4. Option '1' starts guided TPR workflow"
echo "==========================================="