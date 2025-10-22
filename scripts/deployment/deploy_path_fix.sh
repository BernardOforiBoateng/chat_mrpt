#!/bin/bash
# Deploy path fix for vision API

echo "🚀 Deploying Path Fix for Vision API..."

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

    # Copy the updated visualization routes file
    echo "  - Copying fixed visualization_routes.py (path construction)..."
    scp -i "$KEY" app/web/routes/visualization_routes.py "ec2-user@$INSTANCE_IP:/home/ec2-user/ChatMRPT/app/web/routes/"

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

# Check logs for path errors
echo "  - Checking for path issues:"
sudo journalctl -u chatmrpt -n 10 | grep -E "uploads.*uploads|Vision API Error" || echo "No path errors found"
EOF

    echo "✅ Done for $INSTANCE_NAME"
}

# Deploy to both instances
deploy_fix "$INSTANCE1" "Instance 1"
deploy_fix "$INSTANCE2" "Instance 2"

echo ""
echo "🎆 PATH FIX DEPLOYED!"
echo ""
echo "🔧 FIXES:"
echo "✅ Session ID no longer duplicated in file paths"
echo "✅ Vision API should now find the visualization files"
echo ""
echo "📊 Testing instructions:"
echo "1. Go to: https://d225ar6c86586s.cloudfront.net"
echo "2. Upload TPR data and generate visualization"
echo "3. Click '✨ Explain' button"
echo "4. Should now get real AI explanation (not error)"
echo ""
echo "Note: Two visualizations appearing is a separate React rendering issue"