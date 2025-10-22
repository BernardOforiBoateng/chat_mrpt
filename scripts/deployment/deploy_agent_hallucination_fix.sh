#!/bin/bash

echo "=========================================="
echo "   Deploying Agent Hallucination Fixes   "
echo "=========================================="
echo ""
echo "This deployment includes:"
echo "✅ Updated system prompt with data integrity principles"
echo "✅ Robust column handling for special characters"
echo "✅ Error handling to prevent hallucinations"
echo ""

# Staging instances from CLAUDE.md (Public IPs as of Jan 7, 2025)
STAGING_IPS="3.21.167.170 18.220.103.20"
KEY_FILE="/tmp/deploy-key.pem"
REMOTE_USER="ec2-user"
REMOTE_PATH="/home/ec2-user/ChatMRPT"

# Files to deploy
FILES_TO_DEPLOY="app/data_analysis_v3/prompts/system_prompt.py"

echo "Target instances: 2"
echo "- Instance 1: 3.21.167.170"
echo "- Instance 2: 18.220.103.20"
echo ""

# Prepare key
if [ -f "aws_files/chatmrpt-key.pem" ]; then
    cp aws_files/chatmrpt-key.pem "$KEY_FILE"
    chmod 600 "$KEY_FILE"
    echo "✅ SSH key prepared"
else
    echo "❌ SSH key not found at aws_files/chatmrpt-key.pem"
    exit 1
fi

# Deploy to each instance
for IP in $STAGING_IPS; do
    echo "----------------------------------------"
    echo "Deploying to $IP..."
    
    # Copy the fixed prompt file
    echo "Copying system_prompt.py..."
    scp -o StrictHostKeyChecking=no -i "$KEY_FILE" \
        $FILES_TO_DEPLOY \
        "$REMOTE_USER@$IP:$REMOTE_PATH/app/data_analysis_v3/prompts/"
    
    if [ $? -eq 0 ]; then
        echo "✅ File copied successfully"
        
        # Restart the service
        echo "Restarting ChatMRPT service..."
        ssh -o StrictHostKeyChecking=no -i "$KEY_FILE" \
            "$REMOTE_USER@$IP" \
            "sudo systemctl restart chatmrpt"
        
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
echo "=========================================="
echo "Deployment Complete!"
echo ""
echo "Test the fixes at:"
echo "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "Key improvements:"
echo "1. Agent will explore data structure when columns don't match"
echo "2. No more fake facility names or statistics"
echo "3. Handles special characters in column names"
echo "4. Reports issues transparently instead of hallucinating"
echo ""
echo "Test with the sample questions from:"
echo "sample_agent_questions_tpr_data.md"
echo "=========================================="