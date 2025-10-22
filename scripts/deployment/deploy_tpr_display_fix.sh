#!/bin/bash
# Deploy TPR display fixes to both AWS production instances

echo "🚀 Deploying TPR display fixes to AWS production instances..."

# Production Instance IPs (public)
INSTANCE1="3.21.167.170"
INSTANCE2="18.220.103.20"

# Key location
KEY="/tmp/chatmrpt-key2.pem"

# Files to deploy
FILES=(
    "app/data_analysis_v3/tools/tpr_analysis_tool.py"
    "app/data_analysis_v3/core/tpr_workflow_handler.py"
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
echo "📋 Summary of fixes:"
echo "1. ✅ Fixed TPR visualization width (set to 1200px with responsive sizing)"
echo "2. ✅ Fixed TPR summary text display (preserves full message with statistics)"
echo "3. ✅ Summary now shows:"
echo "   - State name and selections"
echo "   - Overall statistics (mean, median, max TPR)"
echo "   - High-risk wards list"
echo "   - Total tested and positive counts"
echo ""
echo "🧪 To test:"
echo "1. Go to: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo "2. Upload TPR data and complete the workflow"
echo "3. Check that the summary text appears above the visualization"
echo "4. Verify the map width is properly sized (not compressed)"
echo ""
echo "⚠️  CloudFront URL: https://d225ar6c86586s.cloudfront.net"