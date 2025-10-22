#!/bin/bash

# Revert Overlay Fix from Production
# This script removes the overlay fix and restores original state

echo "🔄 Reverting Overlay Fix from Production..."

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

echo "📦 Reverting index.html to original state..."

# Deploy to both instances
for IP in $INSTANCE1_IP $INSTANCE2_IP; do
    echo ""
    echo "🚀 Deploying to instance: $IP"
    
    # Copy reverted index.html
    echo "  📄 Copying reverted index.html..."
    scp -i "$KEY_PATH" "app/templates/index.html" "ec2-user@$IP:/home/ec2-user/ChatMRPT/app/templates/index.html"
    if [ $? -ne 0 ]; then
        echo "  ❌ Failed to copy index.html"
        exit 1
    fi
    
    # Optionally remove the fix files (but keeping them doesn't hurt)
    echo "  🗑️  Removing overlay fix files..."
    ssh -i "$KEY_PATH" "ec2-user@$IP" "rm -f /home/ec2-user/ChatMRPT/app/static/css/overlay-fix.css /home/ec2-user/ChatMRPT/app/static/js/overlay-removal.js"
    
    # Restart the service
    echo "  🔄 Restarting ChatMRPT service..."
    ssh -i "$KEY_PATH" "ec2-user@$IP" "sudo systemctl restart chatmrpt"
    
    if [ $? -eq 0 ]; then
        echo "  ✅ Successfully reverted on $IP"
    else
        echo "  ❌ Failed to restart service on $IP"
    fi
done

echo ""
echo "✅ Overlay fix has been reverted on all production instances!"
echo ""
echo "⚠️  WARNING: The black circular overlay issue may return."
echo "The application is back to its original state."