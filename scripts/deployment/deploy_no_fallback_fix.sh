#!/bin/bash
# Deploy visualization fixes - no fallback messages + fixed duplicate buttons

echo "🚀 Deploying No-Fallback Visualization Fix..."

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

    # Copy the updated files
    echo "  - Copying updated universal_viz_explainer.py (no fallbacks)..."
    scp -i "$KEY" app/services/universal_viz_explainer.py "ec2-user@$INSTANCE_IP:/home/ec2-user/ChatMRPT/app/services/"

    echo "  - Copying fixed visualization_handler.js (no duplicate buttons)..."
    scp -i "$KEY" app/static/js/visualization_handler.js "ec2-user@$INSTANCE_IP:/home/ec2-user/ChatMRPT/app/static/js/"

    # Restart and verify
    ssh -i "$KEY" "ec2-user@$INSTANCE_IP" << 'EOF'
cd /home/ec2-user/ChatMRPT

# Clear any caches
echo "  - Clearing caches..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
rm -rf instance/cache/explanations/* 2>/dev/null || true

# Restart service
echo "  - Restarting service..."
sudo systemctl restart chatmrpt
sleep 5

echo "  - Service status:"
sudo systemctl status chatmrpt | grep Active

# Check logs for errors
echo "  - Recent logs (checking for vision errors):"
sudo journalctl -u chatmrpt -n 20 | grep -E "ERROR|FAILED|Vision" || echo "No errors found"
EOF

    echo "✅ Done for $INSTANCE_NAME"
}

# Deploy to both instances
deploy_fix "$INSTANCE1" "Instance 1"
deploy_fix "$INSTANCE2" "Instance 2"

echo ""
echo "🎆 NO-FALLBACK FIX DEPLOYED!"
echo ""
echo "🔥 IMPORTANT CHANGES:"
echo "1. ❌ Fallback messages removed - errors will now be visible"
echo "2. ✅ Duplicate button issue fixed with better detection"
echo "3. 💥 Any vision API failures will now throw errors"
echo ""
echo "📊 Testing instructions:"
echo "1. Go to: https://d225ar6c86586s.cloudfront.net"
echo "2. Generate a visualization"
echo "3. Click '✨ Explain' button"
echo "4. Watch console for error messages (F12)"
echo ""
echo "⚠️ EXPECTED BEHAVIOR:"
echo "- If vision API fails, you'll see error messages"
echo "- No more generic 'This visualization shows...' fallbacks"
echo "- Only ONE Explain button per visualization"
echo ""
echo "If you see errors, that's GOOD - it means we can now debug the real issue!"