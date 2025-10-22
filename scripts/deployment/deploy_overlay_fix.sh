#!/bin/bash

# Deploy Overlay Fix to Production
# This script deploys the emergency fix for the blocking overlay issue

echo "🚨 Deploying Emergency Overlay Fix to Production..."

# Production instances (formerly staging)
INSTANCE1_IP="3.21.167.170"
INSTANCE2_IP="18.220.103.20"
KEY_PATH="$HOME/.ssh/chatmrpt-key.pem"

# Check if key exists
if [ ! -f "$KEY_PATH" ]; then
    echo "❌ SSH key not found at $KEY_PATH"
    echo "Trying alternative path..."
    KEY_PATH="/tmp/chatmrpt-key2.pem"
    if [ ! -f "$KEY_PATH" ]; then
        echo "❌ SSH key not found. Please ensure the key is at ~/.ssh/chatmrpt-key.pem"
        exit 1
    fi
fi

# Files to deploy
FILES=(
    "app/static/css/overlay-fix.css"
    "app/static/js/overlay-removal.js"
    "app/templates/index.html"
)

echo "📦 Files to deploy:"
for file in "${FILES[@]}"; do
    echo "  - $file"
done

# Deploy to both instances
for IP in $INSTANCE1_IP $INSTANCE2_IP; do
    echo ""
    echo "🚀 Deploying to instance: $IP"
    
    # Copy files
    for file in "${FILES[@]}"; do
        echo "  📄 Copying $file..."
        scp -i "$KEY_PATH" "$file" "ec2-user@$IP:/home/ec2-user/ChatMRPT/$file"
        if [ $? -ne 0 ]; then
            echo "  ❌ Failed to copy $file"
            exit 1
        fi
    done
    
    # Restart the service
    echo "  🔄 Restarting ChatMRPT service..."
    ssh -i "$KEY_PATH" "ec2-user@$IP" "sudo systemctl restart chatmrpt"
    
    if [ $? -eq 0 ]; then
        echo "  ✅ Successfully deployed to $IP"
    else
        echo "  ❌ Failed to restart service on $IP"
    fi
done

echo ""
echo "✅ Overlay fix deployed to all production instances!"
echo ""
echo "🔍 Please test the application at:"
echo "  - CloudFront: https://d225ar6c86586s.cloudfront.net"
echo "  - ALB: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "The black circular overlay should now be removed and the app should be interactive."