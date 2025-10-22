#!/bin/bash

echo "======================================"
echo "Deploying Llama fixes to AWS Staging"
echo "======================================"

# AWS staging IPs (updated)
STAGING_IPS="3.21.167.170 18.220.103.20"

# Files to deploy
FILES_TO_DEPLOY="
app/core/llm_adapter.py
app/services/container.py
"

echo "Files to deploy:"
echo "$FILES_TO_DEPLOY"
echo ""

# Copy key to temp location with proper permissions
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key.pem
chmod 600 /tmp/chatmrpt-key.pem

# Deploy to each staging instance
for IP in $STAGING_IPS; do
    echo "======================================"
    echo "Deploying to staging instance: $IP"
    echo "======================================"
    
    # Copy files
    for FILE in $FILES_TO_DEPLOY; do
        echo "Copying $FILE..."
        scp -i /tmp/chatmrpt-key.pem -o StrictHostKeyChecking=no \
            "$FILE" "ec2-user@$IP:/home/ec2-user/ChatMRPT/$FILE"
    done
    
    # Restart the service
    echo "Restarting ChatMRPT service..."
    ssh -i /tmp/chatmrpt-key.pem -o StrictHostKeyChecking=no "ec2-user@$IP" \
        "sudo systemctl restart chatmrpt"
    
    echo "Deployment to $IP complete!"
    echo ""
done

echo "======================================"
echo "Llama fixes deployed to all staging instances!"
echo "======================================"
echo ""
echo "Test the chat at:"
echo "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"