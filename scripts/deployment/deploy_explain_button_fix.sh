#!/bin/bash
# Deploy explain button fix to both AWS production instances

echo "🚀 Deploying explain button fix to AWS production instances..."

# Production Instance IPs (public)
INSTANCE1="3.21.167.170"
INSTANCE2="18.220.103.20"

# Key location
KEY="/tmp/chatmrpt-key2.pem"

# Files to deploy
FILES=(
    "app/static/js/visualization_handler.js"
    "app/static/react/index.html"
)

# Copy key if not already there
if [ ! -f "$KEY" ]; then
    echo "📋 Copying SSH key..."
    cp aws_files/chatmrpt-key.pem "$KEY"
    chmod 600 "$KEY"
fi

echo ""
echo "📦 Deploying to Instance 1 ($INSTANCE1)..."
for FILE in "${FILES[@]}"; do
    echo "  - Copying $FILE"
    scp -i "$KEY" "$FILE" "ec2-user@$INSTANCE1:/home/ec2-user/ChatMRPT/$FILE"
    if [ $? -ne 0 ]; then
        echo "❌ Failed to copy $FILE to Instance 1"
        exit 1
    fi
done

echo "✅ Files copied to Instance 1"
ssh -i "$KEY" "ec2-user@$INSTANCE1" "sudo systemctl restart chatmrpt"
echo "✅ Service restarted on Instance 1"

echo ""
echo "📦 Deploying to Instance 2 ($INSTANCE2)..."
for FILE in "${FILES[@]}"; do
    echo "  - Copying $FILE"
    scp -i "$KEY" "$FILE" "ec2-user@$INSTANCE2:/home/ec2-user/ChatMRPT/$FILE"
    if [ $? -ne 0 ]; then
        echo "❌ Failed to copy $FILE to Instance 2"
        exit 1
    fi
done

echo "✅ Files copied to Instance 2"
ssh -i "$KEY" "ec2-user@$INSTANCE2" "sudo systemctl restart chatmrpt"
echo "✅ Service restarted on Instance 2"

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📋 Summary of changes:"
echo "1. Added '✨ Explain' button to all visualizations"
echo "2. Merged explain functionality from viz_injector.js into visualization_handler.js"
echo "3. Removed conflicting viz_injector.js script to prevent duplicate processing"
echo ""
echo "🧪 To test:"
echo "1. Go to: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo "2. Generate any visualization (vulnerability map, TPR map, ITN distribution, etc.)"
echo "3. Look for the purple '✨ Explain' button in the visualization header"
echo "4. Click the Explain button to get AI-powered explanations"
echo ""
echo "⚠️  Note: CloudFront cache may need to be cleared for immediate effect"
echo "   at: https://d225ar6c86586s.cloudfront.net"