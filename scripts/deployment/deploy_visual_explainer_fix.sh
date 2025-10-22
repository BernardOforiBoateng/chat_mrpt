#!/bin/bash
# Deploy visual explainer button fix to both AWS production instances

echo "🚀 Deploying visual explainer button fix to AWS..."

# Production Instance IPs
INSTANCE1="3.21.167.170"
INSTANCE2="18.220.103.20"

# Key location
KEY="/tmp/chatmrpt-key2.pem"

# Files to deploy
FILES=(
    "app/data_analysis_v3/tools/tpr_analysis_tool.py"
    "app/static/react/index.html"
    "app/static/react/assets/index-BErlYkG8.js"
    "app/static/react/assets/index-CQUUvms1.css"
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
echo "1. ✅ Reverted TPR map width to original (no explicit width)"
echo "2. ✅ Added purple sparkle '✨ Explain' button in React"
echo "3. ✅ Implemented backend API call for explanations"
echo "4. ✅ Added explanation display area below visualizations"
echo "5. ✅ Removed redundant visualization_handler.js script"
echo ""
echo "🧪 To test:"
echo "1. Go to: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo "2. Generate any visualization (TPR map, vulnerability map, etc.)"
echo "3. Look for the purple '✨ Explain' button in the header"
echo "4. Click it to see AI-powered explanations below the visualization"
echo ""
echo "⚠️  CloudFront URL: https://d225ar6c86586s.cloudfront.net"
echo "    May need to clear browser cache or test in incognito mode"