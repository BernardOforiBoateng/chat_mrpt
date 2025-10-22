#!/bin/bash

echo "============================================"
echo "Deploying All ChatMRPT Improvements"
echo "============================================"
echo ""
echo "📋 Improvements included:"
echo "   ✅ vLLM Chat API integration (no thinking tags)"
echo "   ✅ Real-time streaming (character-by-character)"
echo "   ✅ Balanced responses (general knowledge + data analysis)"
echo "   ✅ Industry-standard system prompt with safety guidelines"
echo ""

# Files to deploy
FILES=(
    "app/core/llm_adapter.py"                              # vLLM chat API
    "app/services/container.py"                            # Streaming wrapper
    "app/core/request_interpreter.py"                      # Improved system prompt
    "app/static/js/modules/chat/core/message-handler.js"   # Frontend streaming
    "app/static/js/modules/utils/api-client.js"           # SSE handling
)

# Staging instances
STAGING_IPS=(
    "172.31.46.84"
    "172.31.24.195"
)

# Production instances
PRODUCTION_IPS=(
    "172.31.44.52"
    "172.31.43.200"
)

echo "📦 Files to deploy:"
for file in "${FILES[@]}"; do
    echo "   - $file"
done
echo ""

# Function to deploy to a set of instances
deploy_to_instances() {
    local env_name=$1
    shift
    local ips=("$@")
    
    echo "🎯 Deploying to $env_name..."
    echo ""
    
    for ip in "${ips[@]}"; do
        echo "----------------------------------------"
        echo "Deploying to $ip..."
        echo "----------------------------------------"
        
        # Copy all files
        for file in "${FILES[@]}"; do
            echo "📤 Copying $(basename $file)..."
            scp -i ~/.ssh/chatmrpt-key.pem "$file" "ec2-user@$ip:/home/ec2-user/ChatMRPT/$file" 2>/dev/null
            
            if [ $? -eq 0 ]; then
                echo "   ✅ Success"
            else
                echo "   ❌ Failed to copy $file"
                return 1
            fi
        done
        
        echo ""
        echo "🔄 Restarting service..."
        ssh -i ~/.ssh/chatmrpt-key.pem "ec2-user@$ip" "sudo systemctl restart chatmrpt" 2>/dev/null
        
        if [ $? -eq 0 ]; then
            echo "   ✅ Service restarted successfully"
        else
            echo "   ❌ Failed to restart service"
            return 1
        fi
        
        echo "✅ Deployment complete for $ip"
        echo ""
    done
    
    return 0
}

# Deploy to staging
deploy_to_instances "STAGING" "${STAGING_IPS[@]}"

if [ $? -ne 0 ]; then
    echo "❌ Staging deployment failed. Aborting."
    exit 1
fi

echo "============================================"
echo "✅ Staging Deployment Complete!"
echo "============================================"
echo ""
echo "📋 Test on Staging:"
echo "   URL: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "Test Checklist:"
echo "   1. Streaming: Send 'Hi' - should see character-by-character response"
echo "   2. No thinking tags: Check responses are clean"
echo "   3. General knowledge: Ask 'According to WHO, which countries are most affected by malaria?'"
echo "   4. Should get statistics without asking for data upload"
echo "   5. Safety: Ask for medical advice - should see disclaimer"
echo ""

read -p "Have you tested staging and want to deploy to PRODUCTION? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Production deployment cancelled."
    exit 0
fi

echo ""
echo "⚠️  Deploying to PRODUCTION..."
echo ""

deploy_to_instances "PRODUCTION" "${PRODUCTION_IPS[@]}"

if [ $? -ne 0 ]; then
    echo "❌ Production deployment failed."
    exit 1
fi

echo ""
echo "============================================"
echo "🎉 All Improvements Deployed Successfully!"
echo "============================================"
echo ""
echo "🌐 Production URLs:"
echo "   CloudFront: https://d225ar6c86586s.cloudfront.net"
echo "   Direct ALB: http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"
echo ""
echo "📊 Improvements Summary:"
echo "   ✅ Clean responses without thinking tags"
echo "   ✅ Real-time streaming with typing effect"
echo "   ✅ Balanced knowledge + data analysis"
echo "   ✅ Industry-standard safety guidelines"
echo "   ✅ Better error handling"
echo "   ✅ Chain-of-thought reasoning"
echo ""
echo "🔍 Monitor for:"
echo "   - User satisfaction with streaming"
echo "   - Response quality and accuracy"
echo "   - Any error messages in logs"
echo "   - Performance metrics"
echo ""
echo "Deployment complete! 🚀"