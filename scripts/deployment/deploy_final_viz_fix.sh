#!/bin/bash
# Deploy final visualization fix - no duplication, just add Explain button

echo "🚀 Deploying Final Visualization Fix..."
echo "This fix:"
echo "  ✅ Stops moving/duplicating iframes"
echo "  ✅ Just adds Explain button to existing iframes"
echo "  ✅ Preserves React-rendered structure"

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

    # Copy ALL the updated files
    echo "  - Copying visualization_handler.js (final no-duplication fix)..."
    scp -i "$KEY" app/static/js/visualization_handler.js "ec2-user@$INSTANCE_IP:/home/ec2-user/ChatMRPT/app/static/js/"

    echo "  - Copying visualization_routes.py (path fix)..."
    scp -i "$KEY" app/web/routes/visualization_routes.py "ec2-user@$INSTANCE_IP:/home/ec2-user/ChatMRPT/app/web/routes/"

    echo "  - Copying universal_viz_explainer.py (no fallbacks)..."
    scp -i "$KEY" app/services/universal_viz_explainer.py "ec2-user@$INSTANCE_IP:/home/ec2-user/ChatMRPT/app/services/"

    # Restart and verify
    ssh -i "$KEY" "ec2-user@$INSTANCE_IP" << 'EOF'
cd /home/ec2-user/ChatMRPT

# Clear caches
echo "  - Clearing caches..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
rm -rf instance/cache/explanations/* 2>/dev/null || true

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
echo "🎆 FINAL FIX DEPLOYED!"
echo ""
echo "🔧 ALL FIXES INCLUDED:"
echo "✅ Path construction fixed - no duplicate session IDs"
echo "✅ No fallback messages - errors are visible"
echo "✅ No iframe duplication - just adds Explain button"
echo "✅ Vision API working (though only sees colorbar currently)"
echo ""
echo "📊 How to test:"
echo "1. Clear browser cache completely (Ctrl+Shift+Delete)"
echo "2. Go to: https://d225ar6c86586s.cloudfront.net"
echo "3. Upload TPR data and generate visualization"
echo "4. Should see ONLY ONE visualization with Explain button"
echo "5. Click Explain - should get AI response (may say it can't see full map)"
echo ""
echo "👀 What you should see:"
echo "- Single TPR map with Explain button header"
echo "- No duplicate maps"
echo "- Working Explain functionality"
echo ""
echo "Known issue: Vision API only captures colorbar, not full map (separate issue)"