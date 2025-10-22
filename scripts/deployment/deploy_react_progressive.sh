#!/bin/bash
# Deploy React Frontend with Progressive Enhancement

echo "🚀 Deploying React with Progressive Enhancement..."

# Production Instance IPs
INSTANCE1="3.21.167.170"
INSTANCE2="18.220.103.20"

# Key location
KEY="/tmp/chatmrpt-key2.pem"

# React build files
REACT_FILES=(
    "app/static/react/index.html"
    "app/static/react/assets/index-DnA1lEls.js"
    "app/static/react/assets/index-5VTsL_Rt.css"
)

# Copy key if not already there
if [ ! -f "$KEY" ]; then
    echo "📋 Copying SSH key..."
    cp aws_files/chatmrpt-key.pem "$KEY"
    chmod 600 "$KEY"
fi

# Function to deploy to an instance
deploy_to_instance() {
    local INSTANCE_IP=$1
    local INSTANCE_NAME=$2

    echo ""
    echo "📦 Deploying to $INSTANCE_NAME ($INSTANCE_IP)..."

    # First, remove old React assets
    echo "  - Cleaning old React assets..."
    ssh -i "$KEY" "ec2-user@$INSTANCE_IP" << 'EOF'
# Remove old JS/CSS files but keep directory structure
rm -f /home/ec2-user/ChatMRPT/app/static/react/assets/*.js
rm -f /home/ec2-user/ChatMRPT/app/static/react/assets/*.css
EOF

    # Deploy new React files
    for FILE in "${REACT_FILES[@]}"; do
        echo "  - Copying $FILE"
        scp -i "$KEY" "$FILE" "ec2-user@$INSTANCE_IP:/home/ec2-user/ChatMRPT/$FILE"
        if [ $? -ne 0 ]; then
            echo "❌ Failed to copy $FILE to $INSTANCE_NAME"
            exit 1
        fi
    done

    # Restart service
    echo "  - Restarting ChatMRPT service..."
    ssh -i "$KEY" "ec2-user@$INSTANCE_IP" "sudo systemctl restart chatmrpt"

    # Verify service
    sleep 2
    echo "  - Verifying service..."
    ssh -i "$KEY" "ec2-user@$INSTANCE_IP" "sudo systemctl is-active chatmrpt"

    echo "✅ Deployment complete for $INSTANCE_NAME"
}

# Deploy to both instances
deploy_to_instance "$INSTANCE1" "Instance 1"
deploy_to_instance "$INSTANCE2" "Instance 2"

echo ""
echo "🎉 React Progressive Enhancement deployed!"
echo ""
echo "⚠️  IMPORTANT: Clear CloudFront cache to see changes immediately:"
echo "   aws cloudfront create-invalidation --distribution-id E1KWB0L3N9T1OT --paths '/*'"
echo ""
echo "   Or manually:"
echo "   1. Go to AWS Console > CloudFront"
echo "   2. Select distribution E1KWB0L3N9T1OT"
echo "   3. Invalidations tab > Create Invalidation"
echo "   4. Add path: /*"
echo ""
echo "🧪 Test at: https://d225ar6c86586s.cloudfront.net"
echo "   - Generate a visualization (TPR, EVI map, etc.)"
echo "   - Click '✨ Explain' button"
echo "   - Should see instant fallback + 'Enhancing...' indicator"
echo "   - Then full AI explanation replaces it"