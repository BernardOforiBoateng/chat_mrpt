#!/bin/bash
# Deploy LangGraph fixes to production instances

echo "=== Deploying LangGraph Fixes to Production ==="
echo "Date: $(date)"
echo ""

# Production instances (former staging)
INSTANCE1="3.21.167.170"
INSTANCE2="18.220.103.20"
KEY_PATH="~/.ssh/chatmrpt-key.pem"

# If running from local, copy key first
if [ ! -f ~/.ssh/chatmrpt-key.pem ]; then
    echo "📋 Copying SSH key..."
    cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key.pem
    chmod 600 /tmp/chatmrpt-key.pem
    KEY_PATH="/tmp/chatmrpt-key.pem"
fi

# Files to deploy
FILES_TO_COPY=(
    "app/data_analysis_v3/core/agent.py"
    "app/data_analysis_v3/prompts/system_prompt.py"
    "app/web/routes/data_analysis_v3_routes.py"
)

echo "📦 Files to deploy:"
for file in "${FILES_TO_COPY[@]}"; do
    echo "  - $file"
done
echo ""

# Deploy to Instance 1
echo "🚀 Deploying to Instance 1 ($INSTANCE1)..."
for file in "${FILES_TO_COPY[@]}"; do
    echo "  Copying $file..."
    scp -i $KEY_PATH "$file" ec2-user@$INSTANCE1:/home/ec2-user/ChatMRPT/$file
done

# Restart service on Instance 1
echo "  Restarting service..."
ssh -i $KEY_PATH ec2-user@$INSTANCE1 'sudo systemctl restart chatmrpt'
echo "✅ Instance 1 deployed"
echo ""

# Deploy to Instance 2
echo "🚀 Deploying to Instance 2 ($INSTANCE2)..."
for file in "${FILES_TO_COPY[@]}"; do
    echo "  Copying $file..."
    scp -i $KEY_PATH "$file" ec2-user@$INSTANCE2:/home/ec2-user/ChatMRPT/$file
done

# Restart service on Instance 2
echo "  Restarting service..."
ssh -i $KEY_PATH ec2-user@$INSTANCE2 'sudo systemctl restart chatmrpt'
echo "✅ Instance 2 deployed"
echo ""

# Invalidate CloudFront cache
echo "🌐 Invalidating CloudFront cache..."
aws cloudfront create-invalidation \
    --distribution-id E2JKF6HJUA7TQW \
    --paths "/*" \
    --region us-east-1 2>/dev/null || echo "  (CloudFront invalidation may require AWS CLI configuration)"

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "✅ LangGraph fixes deployed!"
echo ""
echo "What was fixed:"
echo "1. Tool binding order (tools bound before template)"
echo "2. Option 1 handler added"
echo "3. System prompt simplified to match AgenticDataAnalysis"
echo "4. ToolNode properly integrated"
echo ""
echo "Test at:"
echo "  - CloudFront: https://d225ar6c86586s.cloudfront.net"
echo "  - ALB: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "To verify:"
echo "1. Upload data (e.g., adamawa_tpr_cleaned.csv)"
echo "2. Select Option 1 (Data Analysis)"
echo "3. Ask 'Show me a summary of the data'"
echo "4. Check browser console for tool calls"