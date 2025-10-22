#!/bin/bash
# Deploy routing fixes to production instances

set -e

echo "=== Deploying Routing Fixes to Production ==="
echo "Date: $(date)"
echo ""

# Copy SSH key to temp location
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key.pem
chmod 600 /tmp/chatmrpt-key.pem

# Production instances (new active ones)
INSTANCE1="3.21.167.170"
INSTANCE2="18.220.103.20"

# File to deploy
FILE="app/web/routes/analysis_routes.py"

echo "📋 Deploying $FILE to production instances..."
echo ""

# Deploy to Instance 1
echo "Deploying to Instance 1 ($INSTANCE1)..."
scp -i /tmp/chatmrpt-key.pem -o StrictHostKeyChecking=no $FILE ec2-user@$INSTANCE1:/home/ec2-user/ChatMRPT/$FILE
if [ $? -eq 0 ]; then
    echo "✅ File copied to Instance 1"
else
    echo "❌ Failed to copy to Instance 1"
fi

# Deploy to Instance 2
echo "Deploying to Instance 2 ($INSTANCE2)..."
scp -i /tmp/chatmrpt-key.pem -o StrictHostKeyChecking=no $FILE ec2-user@$INSTANCE2:/home/ec2-user/ChatMRPT/$FILE
if [ $? -eq 0 ]; then
    echo "✅ File copied to Instance 2"
else
    echo "❌ Failed to copy to Instance 2"
fi

echo ""
echo "🔄 Restarting services on both instances..."

# Restart service on Instance 1
echo "Restarting service on Instance 1..."
ssh -i /tmp/chatmrpt-key.pem -o StrictHostKeyChecking=no ec2-user@$INSTANCE1 "sudo systemctl restart chatmrpt"
if [ $? -eq 0 ]; then
    echo "✅ Service restarted on Instance 1"
else
    echo "❌ Failed to restart service on Instance 1"
fi

# Restart service on Instance 2
echo "Restarting service on Instance 2..."
ssh -i /tmp/chatmrpt-key.pem -o StrictHostKeyChecking=no ec2-user@$INSTANCE2 "sudo systemctl restart chatmrpt"
if [ $? -eq 0 ]; then
    echo "✅ Service restarted on Instance 2"
else
    echo "❌ Failed to restart service on Instance 2"
fi

echo ""
echo "=== Deployment Complete ==="
echo "Test the routing at: https://d225ar6c86586s.cloudfront.net"
echo ""
echo "Test commands:"
echo "1. General question (should go to Arena): 'What is malaria?'"
echo "2. Tool request (should go to Tools): 'Run the malaria risk analysis'"
echo ""

# Clean up temp key
rm -f /tmp/chatmrpt-key.pem