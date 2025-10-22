#!/bin/bash
# Temporarily disable visualization_handler.js to test

echo "🔧 Temporarily disabling visualization_handler.js..."

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

# Function to disable on instance
disable_viz() {
    local INSTANCE_IP=$1
    local INSTANCE_NAME=$2

    echo ""
    echo "📦 Disabling on $INSTANCE_NAME ($INSTANCE_IP)..."

    ssh -i "$KEY" "ec2-user@$INSTANCE_IP" << 'EOF'
cd /home/ec2-user/ChatMRPT

# Rename the visualization_handler.js to disable it
echo "  - Renaming visualization_handler.js to .disabled..."
mv app/static/js/visualization_handler.js app/static/js/visualization_handler.js.disabled 2>/dev/null || true

# Create empty file so no 404 errors
echo "// Temporarily disabled" > app/static/js/visualization_handler.js

# Restart service
echo "  - Restarting service..."
sudo systemctl restart chatmrpt
sleep 3

echo "  - Service status:"
sudo systemctl status chatmrpt | grep Active
EOF

    echo "✅ Disabled on $INSTANCE_NAME"
}

# Disable on both instances
disable_viz "$INSTANCE1" "Instance 1"
disable_viz "$INSTANCE2" "Instance 2"

echo ""
echo "🔧 VISUALIZATION HANDLER DISABLED!"
echo ""
echo "Now test at: https://d225ar6c86586s.cloudfront.net"
echo "You should see:"
echo "  - How many visualizations appear WITHOUT our JS"
echo "  - Whether duplicates still exist"
echo "  - No Explain buttons (since handler is disabled)"
echo ""
echo "To re-enable, run: ./enable_viz_handler.sh"