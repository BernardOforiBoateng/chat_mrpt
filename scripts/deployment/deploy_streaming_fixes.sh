#!/bin/bash

echo "============================================"
echo "Deploying Streaming Fixes to Staging"
echo "============================================"

# Files to deploy
FILES=(
    "app/static/js/modules/chat/core/message-handler.js"
    "app/static/js/modules/utils/api-client.js"
    "app/core/llm_adapter.py"
    "app/services/container.py"
    "app/core/request_interpreter.py"
)

# Staging instances (both instances behind ALB)
STAGING_IPS=(
    "172.31.46.84"
    "172.31.24.195"
)

echo ""
echo "📦 Files to deploy:"
for file in "${FILES[@]}"; do
    echo "   - $file"
done

echo ""
echo "🎯 Target staging instances:"
for ip in "${STAGING_IPS[@]}"; do
    echo "   - $ip"
done

echo ""
echo "🚀 Starting deployment..."
echo ""

# Deploy to each staging instance
for ip in "${STAGING_IPS[@]}"; do
    echo "----------------------------------------"
    echo "Deploying to staging instance: $ip"
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
echo "✅ All Streaming Fixes Deployed to Staging!"
echo "============================================"
echo ""
echo "📋 Test Instructions:"
echo "1. Open http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo "2. Open browser console (F12)"
echo "3. Send test messages:"
echo "   - 'Hi'"
echo "   - 'Tell me about malaria'"
echo "   - 'What is urban-microstratification?'"
echo ""
echo "4. Expected behavior:"
echo "   ✅ Text appears character-by-character"
echo "   ✅ Blinking cursor during streaming"
echo "   ✅ Smooth typing effect"
echo "   ✅ No thinking tags visible"
echo "   ✅ Natural responses from Qwen3"
echo ""
echo "5. Check console for:"
echo "   - '🔥 STREAMING DEBUG: Using streaming endpoint!'"
echo "   - '🔥 API CLIENT: sendMessageStreaming called'"
echo ""
echo "If staging tests pass, run:"
echo "   ./deploy_streaming_fixes_production.sh"