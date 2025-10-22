#!/bin/bash
# Deploy LangGraph Tool Usage Fixes to Production
# Fixes the critical issue where model generates text instead of executing code

echo "=== Deploying LangGraph Tool Usage Fixes ==="
echo "Date: $(date)"
echo ""

# Production instances
INSTANCE1="3.21.167.170"
INSTANCE2="18.220.103.20"
KEY_PATH="~/.ssh/chatmrpt-key.pem"

# Check for key
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
)

echo "📦 Files to deploy:"
for file in "${FILES_TO_COPY[@]}"; do
    echo "  - $file"
done
echo ""

echo "🔧 Key fixes being deployed:"
echo "  1. Force tool usage with tool_choice='required'"
echo "  2. Simplified system prompt (47 lines vs 419)"
echo "  3. Fixed tool binding order to match original"
echo "  4. Added query preprocessing to enforce tools"
echo "  5. Added retry mechanism for failed tool calls"
echo ""

# Deploy to Instance 1
echo "🚀 Deploying to Instance 1 ($INSTANCE1)..."
for file in "${FILES_TO_COPY[@]}"; do
    echo "  Copying $file..."
    scp -i $KEY_PATH "$file" ec2-user@$INSTANCE1:/home/ec2-user/ChatMRPT/$file
done

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
echo "=== Deployment Complete ===="
echo ""
echo "✅ LangGraph tool usage fixes deployed!"
echo ""
echo "Expected behavior after fix:"
echo "  • Model will ALWAYS use analyze_data tool"
echo "  • No more hallucinated numbers (like 961K tests)"
echo "  • Browser console will show '🔧 Tool calls generated'"
echo "  • Actual Python code execution for every query"
echo ""
echo "Test at:"
echo "  - CloudFront: https://d225ar6c86586s.cloudfront.net"
echo "  - ALB: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "To verify fix:"
echo "1. Upload adamawa_tpr_cleaned.csv"
echo "2. Select Option 1 (Data Analysis)"
echo "3. Ask 'Show me a summary of the data'"
echo "4. Check browser console for '🔧 Tool calls generated'"
echo "5. Response should show actual df.describe() output"