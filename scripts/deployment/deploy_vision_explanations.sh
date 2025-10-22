#!/bin/bash
# Deploy Dynamic Vision Explanations to AWS Production
# This script enables AI-powered explanations for visualizations with smart caching

echo "🚀 Deploying Dynamic Vision Explanations to AWS..."

# Production Instance IPs (Current Active Environment)
INSTANCE1="3.21.167.170"
INSTANCE2="18.220.103.20"

# Key location
KEY="/tmp/chatmrpt-key2.pem"

# Files to deploy
BACKEND_FILES=(
    "app/services/universal_viz_explainer.py"
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

    # Deploy backend files
    echo "  Deploying backend files..."
    for FILE in "${BACKEND_FILES[@]}"; do
        echo "    - Copying $FILE"
        scp -i "$KEY" "$FILE" "ec2-user@$INSTANCE_IP:/home/ec2-user/ChatMRPT/$FILE"
        if [ $? -ne 0 ]; then
            echo "❌ Failed to copy $FILE to $INSTANCE_NAME"
            exit 1
        fi
    done

    # Build React locally and deploy built files
    if [ ${#FRONTEND_FILES[@]} -gt 0 ]; then
        echo "  Building React frontend locally..."

        # Build React locally first
        cd frontend
        if [ -f "package.json" ]; then
            npm run build
            if [ $? -ne 0 ]; then
                echo "❌ Failed to build React locally"
                exit 1
            fi
            cd ..

            # Copy built React files to AWS
            echo "    - Copying built React files..."
            scp -i "$KEY" -r frontend/dist/* "ec2-user@$INSTANCE_IP:/home/ec2-user/ChatMRPT/app/static/react/"
            if [ $? -ne 0 ]; then
                echo "❌ Failed to copy React build to $INSTANCE_NAME"
                exit 1
            fi
        else
            echo "  ⚠️  No frontend/package.json found, skipping React build"
            cd ..
        fi
    fi

    # Create cache directory
    echo "  Creating cache directory..."
    ssh -i "$KEY" "ec2-user@$INSTANCE_IP" << 'EOF'
mkdir -p /home/ec2-user/ChatMRPT/instance/cache/explanations
chmod 755 /home/ec2-user/ChatMRPT/instance/cache
chmod 755 /home/ec2-user/ChatMRPT/instance/cache/explanations
EOF

    # Set environment variable for vision explanations
    echo "  Setting environment variables..."
    ssh -i "$KEY" "ec2-user@$INSTANCE_IP" << 'EOF'
# Add environment variable to systemd service
sudo tee -a /etc/systemd/system/chatmrpt.service.d/override.conf > /dev/null << EOL
[Service]
Environment="ENABLE_VISION_EXPLANATIONS=true"
EOL

# Reload systemd
sudo systemctl daemon-reload
EOF

    # Restart service
    echo "  Restarting ChatMRPT service..."
    ssh -i "$KEY" "ec2-user@$INSTANCE_IP" "sudo systemctl restart chatmrpt"

    # Verify service is running
    sleep 3
    ssh -i "$KEY" "ec2-user@$INSTANCE_IP" "sudo systemctl status chatmrpt --no-pager | head -10"

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
echo "3. ✅ Implemented progressive enhancement (instant fallback + AI update)"
echo "4. ✅ Set ENABLE_VISION_EXPLANATIONS=true environment variable"
echo "5. ✅ Created cache directories for explanation storage"
echo ""
echo "🧪 To test the new features:"
echo "1. Go to: https://d225ar6c86586s.cloudfront.net"
echo "2. Generate any important visualization (TPR, vulnerability map, etc.)"
echo "3. Click the purple '✨ Explain' button"
echo "4. You'll see:"
echo "   - Instant basic explanation"
echo "   - 'Enhancing...' indicator while AI analyzes"
echo "   - Full AI-powered explanation when ready"
echo "5. Click Explain again - should be instant (cached)"
echo ""
echo "💡 Performance notes:"
echo "- Important visualizations use GPT-4o vision by default"
echo "- Other visualizations use fallback unless ENABLE_VISION_EXPLANATIONS=true"
echo "- Cached explanations are served instantly for 24 hours"
echo "- Progressive enhancement ensures users always see something immediately"
echo ""
echo "⚠️  CloudFront cache may need clearing:"
echo "   aws cloudfront create-invalidation --distribution-id E1KWB0L3N9T1OT --paths '/*'"