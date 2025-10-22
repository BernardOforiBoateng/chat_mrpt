#!/bin/bash
# Deploy Dynamic Vision Explanations to AWS Production
# Simplified version - backend only since React is already built

echo "🚀 Deploying Dynamic Vision Explanations to AWS..."

# Production Instance IPs (Current Active Environment)
INSTANCE1="3.21.167.170"
INSTANCE2="18.220.103.20"

# Key location
KEY="/tmp/chatmrpt-key2.pem"

# File to deploy
BACKEND_FILE="app/services/universal_viz_explainer.py"

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

    # Deploy backend file
    echo "  - Copying $BACKEND_FILE"
    scp -i "$KEY" "$BACKEND_FILE" "ec2-user@$INSTANCE_IP:/home/ec2-user/ChatMRPT/$BACKEND_FILE"
    if [ $? -ne 0 ]; then
        echo "❌ Failed to copy $BACKEND_FILE to $INSTANCE_NAME"
        exit 1
    fi

    # Create cache directory and set environment variable
    echo "  - Setting up cache and environment..."
    ssh -i "$KEY" "ec2-user@$INSTANCE_IP" << 'EOF'
# Create cache directory
mkdir -p /home/ec2-user/ChatMRPT/instance/cache/explanations
chmod 755 /home/ec2-user/ChatMRPT/instance/cache
chmod 755 /home/ec2-user/ChatMRPT/instance/cache/explanations

# Add environment variable to .env if it doesn't exist
if ! grep -q "ENABLE_VISION_EXPLANATIONS" /home/ec2-user/ChatMRPT/.env 2>/dev/null; then
    echo "" >> /home/ec2-user/ChatMRPT/.env
    echo "# Vision Explanations" >> /home/ec2-user/ChatMRPT/.env
    echo "ENABLE_VISION_EXPLANATIONS=true" >> /home/ec2-user/ChatMRPT/.env
    echo "Added ENABLE_VISION_EXPLANATIONS to .env"
else
    echo "ENABLE_VISION_EXPLANATIONS already configured"
fi
EOF

    # Restart service
    echo "  - Restarting ChatMRPT service..."
    ssh -i "$KEY" "ec2-user@$INSTANCE_IP" "sudo systemctl restart chatmrpt"

    # Verify service is running
    sleep 3
    echo "  - Verifying service status..."
    ssh -i "$KEY" "ec2-user@$INSTANCE_IP" "sudo systemctl is-active chatmrpt"

    echo "✅ Deployment complete for $INSTANCE_NAME"
}

# Deploy to both instances
deploy_to_instance "$INSTANCE1" "Instance 1"
deploy_to_instance "$INSTANCE2" "Instance 2"

echo ""
echo "🎉 Deployment complete to both production instances!"
echo ""
echo "📋 Summary of changes:"
echo "1. ✅ Enabled vision explanations for important visualization types"
echo "2. ✅ Added smart caching (24-hour cache duration)"
echo "3. ✅ Set ENABLE_VISION_EXPLANATIONS=true environment variable"
echo "4. ✅ Created cache directories for explanation storage"
echo ""
echo "🧪 To test the new features:"
echo "1. Go to: https://d225ar6c86586s.cloudfront.net"
echo "2. Generate any important visualization (TPR, vulnerability map, etc.)"
echo "3. Click the purple '✨ Explain' button"
echo "4. You'll see dynamic AI-powered explanations!"
echo ""
echo "💡 Performance notes:"
echo "- Important visualizations use GPT-4o vision by default"
echo "- Cached explanations are served instantly for 24 hours"
echo "- Progressive enhancement ensures users always see something immediately"
echo ""
echo "Note: Frontend progressive enhancement was already deployed previously"