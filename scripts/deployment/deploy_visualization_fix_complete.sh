#!/bin/bash
# Deploy complete visualization handler fix

echo "🚀 Deploying Complete Visualization Handler Fix..."

# Production Instance IPs
INSTANCE1="3.21.167.170"
INSTANCE2="18.220.103.20"

# Key location
KEY="/tmp/chatmrpt-key2.pem"

# Copy key if not already there
if [ ! -f "$KEY" ]; then
    echo "📋 Copying SSH key..."
    cp aws_files/chatmrpt-key.pem "$KEY"
    chmod 600 "$KEY"
fi

# Function to deploy to instance
deploy_viz_fix() {
    local INSTANCE_IP=$1
    local INSTANCE_NAME=$2

    echo ""
    echo "📦 Deploying to $INSTANCE_NAME ($INSTANCE_IP)..."

    # Copy the updated files
    echo "  - Copying updated React HTML with script inclusion..."
    scp -i "$KEY" app/static/react/index.html "ec2-user@$INSTANCE_IP:/home/ec2-user/ChatMRPT/app/static/react/"

    echo "  - Copying debugged visualization_handler.js..."
    scp -i "$KEY" app/static/js/visualization_handler.js "ec2-user@$INSTANCE_IP:/home/ec2-user/ChatMRPT/app/static/js/"

    # Restart and verify
    ssh -i "$KEY" "ec2-user@$INSTANCE_IP" << 'EOF'
cd /home/ec2-user/ChatMRPT

# Clear any caches
echo "  - Clearing caches..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Restart service
echo "  - Restarting service..."
sudo systemctl restart chatmrpt
sleep 5

echo "  - Service status:"
sudo systemctl status chatmrpt | grep Active

# Verify the script is accessible
echo "  - Verifying visualization_handler.js is accessible:"
curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/static/js/visualization_handler.js
echo " (should be 200)"
EOF

    echo "✅ Done for $INSTANCE_NAME"
}

# Deploy to both instances
deploy_viz_fix "$INSTANCE1" "Instance 1"
deploy_viz_fix "$INSTANCE2" "Instance 2"

echo ""
echo "🎆 CRITICAL FIX DEPLOYED!"
echo ""
echo "🔄 IMPORTANT: Clear your browser cache or use incognito mode!"
echo ""
echo "📊 How to test:"
echo "1. Go to: https://d225ar6c86586s.cloudfront.net (incognito recommended)"
echo "2. Open browser console (F12 > Console)"
echo "3. Look for: '🚀 Visualization Handler v2 initialized'"
echo "4. Generate any visualization"
echo "5. Look for: '🎨 Found visualization URLs'"
echo "6. Click '✨ Explain' button"
echo "7. Watch for debug messages in console"
echo ""
echo "If you don't see the initialization message, the script isn't loading!"