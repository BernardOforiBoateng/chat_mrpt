#!/bin/bash
# Deploy fix for risk analysis after TPR

echo "🚀 Deploying Risk Analysis Fix"
echo "================================"
echo "Fix: Keep data analysis mode after TPR to ensure tools execute"
echo ""

# Production IPs
INSTANCE1="3.21.167.170"
INSTANCE2="18.220.103.20"
KEY_PATH="/tmp/chatmrpt-key2.pem"

# Copy key if needed
if [ ! -f "$KEY_PATH" ]; then
    cp aws_files/chatmrpt-key.pem "$KEY_PATH"
    chmod 600 "$KEY_PATH"
fi

# Files to deploy
FILES="app/data_analysis_v3/core/tpr_workflow_handler.py app/tools/complete_analysis_tools.py"

echo "📦 Deploying to Instance 1 ($INSTANCE1)..."
for file in $FILES; do
    echo "   Copying $file..."
    scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$file" "ec2-user@$INSTANCE1:/home/ec2-user/ChatMRPT/$file"
done

echo "📦 Deploying to Instance 2 ($INSTANCE2)..."
for file in $FILES; do
    echo "   Copying $file..."
    scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$file" "ec2-user@$INSTANCE2:/home/ec2-user/ChatMRPT/$file"
done

echo ""
echo "♻️ Restarting services..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "ec2-user@$INSTANCE1" "sudo systemctl restart chatmrpt"
echo "   Instance 1 restarted"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "ec2-user@$INSTANCE2" "sudo systemctl restart chatmrpt"
echo "   Instance 2 restarted"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔍 What was fixed:"
echo "   - TPR now stays in data analysis mode (exit_data_analysis_mode: false)"
echo "   - This ensures risk analysis requests go through the correct endpoint"
echo "   - Tool functions will now execute properly with KMO/Bartlett tests"
echo ""
echo "📝 Test by:"
echo "   1. Running TPR analysis"
echo "   2. Requesting 'Run malaria risk analysis'"
echo "   3. Should see proper KMO/Bartlett test results"
