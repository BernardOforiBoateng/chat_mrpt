#!/bin/bash
# Deploy no-duplication fix for visualizations

echo "🚀 Deploying No-Duplication Fix..."

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
deploy_fix() {
    local INSTANCE_IP=$1
    local INSTANCE_NAME=$2

    echo ""
    echo "📦 Deploying to $INSTANCE_NAME ($INSTANCE_IP)..."

    # Copy the updated visualization handler
    echo "  - Copying fixed visualization_handler.js (no duplication)..."
    scp -i "$KEY" app/static/js/visualization_handler.js "ec2-user@$INSTANCE_IP:/home/ec2-user/ChatMRPT/app/static/js/"

    # Restart and verify
    ssh -i "$KEY" "ec2-user@$INSTANCE_IP" << 'EOF'
cd /home/ec2-user/ChatMRPT

# Clear browser caches
echo "  - Clearing static file caches..."
find app/static -name "*.pyc" -delete 2>/dev/null || true

# Restart service
echo "  - Restarting service..."
sudo systemctl restart chatmrpt
sleep 5

echo "  - Service status:"
sudo systemctl status chatmrpt | grep Active
EOF

    echo "✅ Done for $INSTANCE_NAME"
}

# Deploy to both instances
deploy_fix "$INSTANCE1" "Instance 1"
deploy_fix "$INSTANCE2" "Instance 2"

echo ""
echo "🎆 NO-DUPLICATION FIX DEPLOYED!"
echo ""
echo "🔧 WHAT CHANGED:"
echo "✅ Frontend now enhances existing iframes instead of creating new ones"
echo "✅ No more duplicate visualizations"
echo "✅ Explain button added to original iframe"
echo ""
echo "📊 Testing:"
echo "1. Clear browser cache (Ctrl+Shift+R)"
echo "2. Go to: https://d225ar6c86586s.cloudfront.net"
echo "3. Generate a TPR visualization"
echo "4. Should see ONLY ONE visualization with Explain button"
echo ""
echo "Note: Vision API is working but only capturing colorbar, not full map"