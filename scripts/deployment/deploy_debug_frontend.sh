#!/bin/bash
# Deploy debugged frontend to both AWS instances

echo "🔧 Deploying Debugged Frontend..."

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
deploy_debug() {
    local INSTANCE_IP=$1
    local INSTANCE_NAME=$2

    echo ""
    echo "📦 Deploying to $INSTANCE_NAME ($INSTANCE_IP)..."

    # Copy the debugged visualization handler
    echo "  - Copying debugged visualization_handler.js..."
    scp -i "$KEY" app/static/js/visualization_handler.js "ec2-user@$INSTANCE_IP:/home/ec2-user/ChatMRPT/app/static/js/"

    # Clear browser cache by updating version
    ssh -i "$KEY" "ec2-user@$INSTANCE_IP" << 'EOF'
cd /home/ec2-user/ChatMRPT

# Update the js file timestamp to force browser reload
touch app/static/js/visualization_handler.js

# Restart service to ensure changes take effect
echo "  - Restarting service..."
sudo systemctl restart chatmrpt
sleep 5

echo "  - Service status:"
sudo systemctl status chatmrpt | grep Active
EOF

    echo "✅ Done for $INSTANCE_NAME"
}

# Deploy to both instances
deploy_debug "$INSTANCE1" "Instance 1"
deploy_debug "$INSTANCE2" "Instance 2"

echo ""
echo "🎉 Debug Frontend Deployed!"
echo ""
echo "📊 How to use:"
echo "1. Go to: https://d225ar6c86586s.cloudfront.net"
echo "2. Open browser console (F12 > Console tab)"
echo "3. Generate any visualization"
echo "4. Click '✨ Explain' button"
echo "5. Watch for these debug messages:"
echo "   🟢 DEBUG: Explain button clicked!"
echo "   🔵 DEBUG: explainVisualization called"
echo "   🔵 DEBUG: Request payload: ..."
echo "   🔵 DEBUG: Response data: ..."
echo "   ✅ DEBUG: Got REAL AI-powered explanation!"
echo "   OR"
echo "   ⚠️ DEBUG: WARNING - Got FALLBACK message"
echo ""
echo "Share the console output to diagnose what's happening!"