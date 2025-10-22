#!/bin/bash

echo "============================================"
echo "Deploying Streaming Fixes to Production"
echo "============================================"

# Files to deploy
FILES=(
    "app/static/js/modules/chat/core/message-handler.js"
    "app/static/js/modules/utils/api-client.js"
    "app/core/llm_adapter.py"
    "app/services/container.py"
    "app/core/request_interpreter.py"
)

# Production instances (both instances behind ALB)
PRODUCTION_IPS=(
    "172.31.44.52"
    "172.31.43.200"
)

echo ""
echo "⚠️  WARNING: This will deploy to PRODUCTION!"
echo "   Make sure staging tests passed successfully."
echo ""
read -p "Continue with production deployment? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""
echo "📦 Files to deploy:"
for file in "${FILES[@]}"; do
    echo "   - $file"
done

echo ""
echo "🎯 Target production instances:"
for ip in "${PRODUCTION_IPS[@]}"; do
    echo "   - $ip"
done

echo ""
echo "🚀 Starting production deployment..."
echo ""

# Deploy to each production instance
for ip in "${PRODUCTION_IPS[@]}"; do
    echo "----------------------------------------"
    echo "Deploying to production instance: $ip"
    echo "----------------------------------------"
    
    # Copy files
    for file in "${FILES[@]}"; do
        echo "📤 Copying $file..."
        scp -i ~/.ssh/chatmrpt-key.pem "$file" "ec2-user@$ip:/home/ec2-user/ChatMRPT/$file"
        
        if [ $? -eq 0 ]; then
            echo "   ✅ Success"
        else
            echo "   ❌ Failed to copy $file"
            exit 1
        fi
    done
    
    echo ""
    echo "🔄 Restarting service on $ip..."
    ssh -i ~/.ssh/chatmrpt-key.pem "ec2-user@$ip" "sudo systemctl restart chatmrpt"
    
    if [ $? -eq 0 ]; then
        echo "   ✅ Service restarted successfully"
    else
        echo "   ❌ Failed to restart service"
        exit 1
    fi
    
    echo "✅ Deployment complete for $ip"
    echo ""
done

echo "============================================"
echo "✅ Streaming Fixes Deployed to Production!"
echo "============================================"
echo ""
echo "🌐 Production URLs:"
echo "   - CloudFront: https://d225ar6c86586s.cloudfront.net"
echo "   - Direct ALB: http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"
echo ""
echo "📋 Verify deployment:"
echo "1. Test streaming with simple messages"
echo "2. Monitor for any errors in browser console"
echo "3. Check that responses appear smoothly"
echo "4. Verify no thinking tags are visible"
echo ""
echo "🎉 Deployment complete!"