#!/bin/bash

echo "🚀 Deploying HTML template fix to production..."
echo "================================================"

# Configuration
KEY_PATH="/tmp/chatmrpt-key2.pem"
PROD_IPS=("172.31.44.52" "172.31.43.200")
FILE_TO_DEPLOY="app/templates/index.html"

# Copy key to /tmp if needed
if [ ! -f "$KEY_PATH" ]; then
    cp aws_files/chatmrpt-key.pem "$KEY_PATH"
    chmod 600 "$KEY_PATH"
fi

# Deploy to each production instance
for i in "${!PROD_IPS[@]}"; do
    IP="${PROD_IPS[$i]}"
    INSTANCE_NUM=$((i + 1))
    
    echo ""
    echo "📦 Deploying to Production Instance $INSTANCE_NUM ($IP)..."
    echo "----------------------------------------"
    
    # First SSH to staging, then to production
    echo "1. Copying file via staging server..."
    
    # Copy file to staging first
    scp -i "$KEY_PATH" "$FILE_TO_DEPLOY" ec2-user@3.21.167.170:/tmp/index.html
    
    # From staging, copy to production instance
    ssh -i "$KEY_PATH" ec2-user@3.21.167.170 "scp -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem /tmp/index.html ec2-user@$IP:/home/ec2-user/ChatMRPT/app/templates/"
    
    echo "2. Restarting service on instance $INSTANCE_NUM..."
    ssh -i "$KEY_PATH" ec2-user@3.21.167.170 "ssh -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem ec2-user@$IP 'sudo systemctl restart chatmrpt'"
    
    echo "✅ Instance $INSTANCE_NUM deployed successfully"
done

echo ""
echo "🎯 Deployment complete! Verifying changes..."
echo "============================================"

# Wait for services to restart
sleep 5

# Verify the deployment
echo ""
echo "📋 Verification:"
curl -s http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com | grep -o "Data Analysis" | head -1 && echo "✅ HTML updated successfully - showing 'Data Analysis'" || echo "❌ Still showing old version"

echo ""
echo "🔍 Quick Check:"
echo "The tab should now show 'Data Analysis' instead of 'TPR Analysis'"
echo "URL: http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"