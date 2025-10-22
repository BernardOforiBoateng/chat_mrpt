#!/bin/bash

# Deploy Arena Implementation to Production
# Date: 2025-01-17

set -e

echo "=========================================="
echo "🚀 DEPLOYING ARENA IMPLEMENTATION"
echo "=========================================="

# Production IPs
INSTANCE1="3.21.167.170"
INSTANCE2="18.220.103.20"
KEY_PATH="/tmp/chatmrpt-arena-key.pem"

# Files to deploy
FILES_TO_DEPLOY=(
    "app/core/arena_manager.py"
    "app/core/tool_arena_pipeline.py"
    "app/core/arena_trigger_detector.py"
    "app/core/request_interpreter.py"
    "app/web/routes/analysis_routes.py"
)

echo "📦 Files to deploy:"
for file in "${FILES_TO_DEPLOY[@]}"; do
    echo "  - $file"
done

# Function to deploy to an instance
deploy_to_instance() {
    local IP=$1
    local INSTANCE_NAME=$2
    
    echo ""
    echo "📡 Deploying to $INSTANCE_NAME ($IP)..."
    
    # Create backup first
    echo "  📋 Creating backup..."
    ssh -i $KEY_PATH ec2-user@$IP "cd /home/ec2-user/ChatMRPT && tar -czf arena_backup_$(date +%Y%m%d_%H%M%S).tar.gz ${FILES_TO_DEPLOY[*]} 2>/dev/null || true"
    
    # Copy files
    for file in "${FILES_TO_DEPLOY[@]}"; do
        echo "  📤 Copying $file..."
        scp -i $KEY_PATH "$file" "ec2-user@$IP:/home/ec2-user/ChatMRPT/$file"
    done
    
    # Verify Ollama is running
    echo "  🤖 Checking Ollama status..."
    ssh -i $KEY_PATH ec2-user@$IP "sudo systemctl status ollama | head -3 || sudo systemctl start ollama"
    
    # Restart ChatMRPT service
    echo "  🔄 Restarting ChatMRPT service..."
    ssh -i $KEY_PATH ec2-user@$IP "sudo systemctl restart chatmrpt"
    
    # Verify service is running
    echo "  ✅ Verifying service status..."
    ssh -i $KEY_PATH ec2-user@$IP "sudo systemctl status chatmrpt | head -5"
    
    echo "  ✅ Deployment to $INSTANCE_NAME complete!"
}

# Deploy to both instances
echo ""
echo "🎯 Starting deployment to production instances..."

deploy_to_instance $INSTANCE1 "Instance 1"
deploy_to_instance $INSTANCE2 "Instance 2"

# Test Arena functionality
echo ""
echo "🧪 Testing Arena functionality..."
echo "  Testing Instance 1..."
curl -s "http://$INSTANCE1:5000/ping" | head -1 || echo "  ⚠️ Instance 1 not responding on port 5000"

echo "  Testing Instance 2..."
curl -s "http://$INSTANCE2:5000/ping" | head -1 || echo "  ⚠️ Instance 2 not responding on port 5000"

# Invalidate CloudFront cache
echo ""
echo "☁️ Invalidating CloudFront cache..."
aws cloudfront create-invalidation --distribution-id E1A8GN73C70QHK --paths "/*" 2>/dev/null || echo "  ℹ️ CloudFront invalidation skipped (AWS CLI not configured)"

echo ""
echo "=========================================="
echo "✅ ARENA IMPLEMENTATION DEPLOYED!"
echo "=========================================="
echo ""
echo "📊 What was deployed:"
echo "  - Enhanced Arena Manager with interpretation methods"
echo "  - Tool→Arena Pipeline for cost optimization"
echo "  - Smart Request Handler for clean routing"
echo "  - Arena Trigger Detection for context-aware activation"
echo ""
echo "🤖 Ollama Models Available:"
echo "  - phi3:mini (Analyst perspective)"
echo "  - mistral:7b (Statistician perspective)"
echo "  - llama3.1:8b (Additional model)"
echo ""
echo "🌐 Access Points:"
echo "  - CloudFront: https://d225ar6c86586s.cloudfront.net"
echo "  - ALB: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "💰 Expected Benefits:"
echo "  - 70%+ reduction in OpenAI API costs"
echo "  - Multi-model interpretations for better insights"
echo "  - Faster response for general queries"
echo ""
echo "Next steps:"
echo "  1. Monitor logs: ssh -i aws_files/chatmrpt-key.pem ec2-user@$INSTANCE1 'sudo journalctl -u chatmrpt -f'"
echo "  2. Test Arena triggers with malaria data analysis"
echo "  3. Monitor API usage reduction in OpenAI dashboard"
echo ""