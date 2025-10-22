#!/bin/bash
# Deploy TPR streaming and encoding fixes to all environments
# This fixes:
# 1. 'generate_with_functions_streaming' missing method error
# 2. UTF-8 encoding issues with TPR Excel files

set -e

echo "============================================"
echo "   Deploying TPR Streaming & Encoding Fix  "
echo "============================================"
echo ""

# Configuration
STAGING_INSTANCES=(
    "172.31.46.84"   # Staging Instance 1
    "172.31.24.195"  # Staging Instance 2
)

PRODUCTION_INSTANCES=(
    "172.31.44.52"   # Production Instance 1
    "172.31.43.200"  # Production Instance 2
)

KEY_PATH="~/.ssh/chatmrpt-key.pem"
TEMP_KEY="/tmp/chatmrpt-key2.pem"

# Files that need to be deployed
FILES_TO_DEPLOY=(
    "app/services/container.py"           # Fixes streaming error
    "app/tpr_module/data/nmep_parser.py"  # Fixes encoding error
    "app/core/llm_adapter.py"             # Already has vLLM support
)

# Copy key to temp location if needed
if [ -f "aws_files/chatmrpt-key.pem" ]; then
    cp aws_files/chatmrpt-key.pem $TEMP_KEY
    chmod 600 $TEMP_KEY
    KEY_PATH=$TEMP_KEY
    echo "✅ Using key from aws_files/"
fi

# Function to deploy to an instance
deploy_to_instance() {
    local ip=$1
    local env_name=$2
    
    echo ""
    echo "📦 Deploying to $env_name instance: $ip"
    echo "----------------------------------------"
    
    # Copy files
    for file in "${FILES_TO_DEPLOY[@]}"; do
        echo "  📄 Copying $file..."
        scp -o StrictHostKeyChecking=no -i $KEY_PATH \
            "$file" \
            "ec2-user@$ip:/home/ec2-user/ChatMRPT/$file" 2>/dev/null || {
                echo "  ⚠️  Failed to copy $file (server might be down)"
                return 1
            }
    done
    
    # Restart service
    echo "  🔄 Restarting ChatMRPT service..."
    ssh -o StrictHostKeyChecking=no -i $KEY_PATH ec2-user@$ip \
        'sudo systemctl restart chatmrpt' 2>/dev/null || {
            echo "  ⚠️  Failed to restart service"
            return 1
        }
    
    echo "  ✅ Deployment complete for $ip"
    return 0
}

# Deploy to staging
echo ""
echo "🎯 DEPLOYING TO STAGING ENVIRONMENT"
echo "===================================="

staging_success=0
staging_failed=0

for ip in "${STAGING_INSTANCES[@]}"; do
    if deploy_to_instance "$ip" "STAGING"; then
        ((staging_success++))
    else
        ((staging_failed++))
    fi
done

echo ""
echo "Staging deployment summary:"
echo "  ✅ Successful: $staging_success instances"
echo "  ❌ Failed: $staging_failed instances"

# Ask if should deploy to production
echo ""
read -p "Deploy to PRODUCTION? (yes/no): " -r
if [[ $REPLY =~ ^[Yy]es$ ]]; then
    echo ""
    echo "🎯 DEPLOYING TO PRODUCTION ENVIRONMENT"
    echo "======================================"
    
    prod_success=0
    prod_failed=0
    
    for ip in "${PRODUCTION_INSTANCES[@]}"; do
        if deploy_to_instance "$ip" "PRODUCTION"; then
            ((prod_success++))
        else
            ((prod_failed++))
        fi
    done
    
    echo ""
    echo "Production deployment summary:"
    echo "  ✅ Successful: $prod_success instances"
    echo "  ❌ Failed: $prod_failed instances"
else
    echo "Skipping production deployment."
fi

echo ""
echo "============================================"
echo "           DEPLOYMENT COMPLETE              "
echo "============================================"
echo ""
echo "🔍 What was fixed:"
echo "  1. Added 'generate_with_functions_streaming' method to LLMManagerWrapper"
echo "  2. Fixed UTF-8 encoding issues in TPR Excel file parsing"
echo "  3. vLLM backend properly integrated for streaming"
echo ""
echo "📝 Test the fix:"
echo "  1. Upload a TPR Excel file"
echo "  2. The page should NOT refresh"
echo "  3. You should see the conversational interface"
echo ""
echo "🌐 Access points:"
echo "  - Staging ALB: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo "  - Production ALB: http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"
echo "  - Production CDN: https://d225ar6c86586s.cloudfront.net"

# Clean up temp key
if [ -f "$TEMP_KEY" ]; then
    rm -f $TEMP_KEY
fi