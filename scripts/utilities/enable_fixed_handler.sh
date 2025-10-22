#!/bin/bash
# Enable the fixed visualization handler

echo "🚀 Deploying Fixed Visualization Handler..."

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

# Function to enable on instance
enable_fixed() {
    local INSTANCE_IP=$1
    local INSTANCE_NAME=$2

    echo ""
    echo "📦 Deploying to $INSTANCE_NAME ($INSTANCE_IP)..."

    # Copy the fixed handler
    echo "  - Copying fixed visualization_handler.js..."
    scp -i "$KEY" app/static/js/visualization_handler_fixed.js "ec2-user@$INSTANCE_IP:/home/ec2-user/ChatMRPT/app/static/js/visualization_handler.js"

    # Restart service
    ssh -i "$KEY" "ec2-user@$INSTANCE_IP" << 'EOF'
cd /home/ec2-user/ChatMRPT

# Remove the disabled backup if it exists
rm -f app/static/js/visualization_handler.js.disabled 2>/dev/null

# Clear caches
echo "  - Clearing caches..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Restart service
echo "  - Restarting service..."
sudo systemctl restart chatmrpt
sleep 3

echo "  - Service status:"
sudo systemctl status chatmrpt | grep Active
EOF

    echo "✅ Enabled on $INSTANCE_NAME"
}

# Enable on both instances
enable_fixed "$INSTANCE1" "Instance 1"
enable_fixed "$INSTANCE2" "Instance 2"

echo ""
echo "🎆 FIXED HANDLER DEPLOYED!"
echo ""
echo "✅ What's fixed:"
echo "  - Only enhances existing iframes (no duplication)"
echo "  - Wraps existing iframe with nice header"
echo "  - Adds Explain, Fullscreen, and New Tab buttons"
echo "  - Never creates duplicate visualizations"
echo ""
echo "📊 Test now at: https://d225ar6c86586s.cloudfront.net"
echo ""
echo "You should see:"
echo "  - ONE visualization with the nice header and Explain button"
echo "  - NO duplicates"
echo "  - Working Explain functionality"
echo ""
echo "Clear browser cache (Ctrl+Shift+R) before testing!"