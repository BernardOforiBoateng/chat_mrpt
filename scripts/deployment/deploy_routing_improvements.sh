#!/bin/bash

# Deploy Mistral routing improvements to production
echo "=========================================="
echo "Deploying Mistral Routing Improvements"
echo "=========================================="

# Files to deploy
FILES=(
    "app/web/routes/analysis_routes.py"
    "app/core/tool_capabilities.py"
    "app/core/arena_context_manager.py"
    "app/tools/data_description_tools.py"
    "app/tools/__init__.py"
)

# Production instances (former staging environment)
INSTANCE1="3.21.167.170"
INSTANCE2="18.220.103.20"

KEY_FILE="/tmp/chatmrpt-key2.pem"

# Check key file
if [ ! -f "$KEY_FILE" ]; then
    echo "❌ Key file not found at $KEY_FILE"
    exit 1
fi

echo "📦 Files to deploy:"
for file in "${FILES[@]}"; do
    echo "  - $file"
done

echo ""
echo "🎯 Target instances:"
echo "  - Instance 1: $INSTANCE1"
echo "  - Instance 2: $INSTANCE2"
echo ""

# Deploy to both instances
for INSTANCE in $INSTANCE1 $INSTANCE2; do
    echo "=========================================="
    echo "Deploying to $INSTANCE"
    echo "=========================================="
    
    # Copy files
    for FILE in "${FILES[@]}"; do
        echo "📤 Copying $FILE..."
        scp -i "$KEY_FILE" -o StrictHostKeyChecking=no "$FILE" "ec2-user@$INSTANCE:/home/ec2-user/ChatMRPT/$FILE"
        
        if [ $? -eq 0 ]; then
            echo "  ✅ Success"
        else
            echo "  ❌ Failed to copy $FILE"
            exit 1
        fi
    done
    
    # Restart service
    echo "🔄 Restarting ChatMRPT service..."
    ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no "ec2-user@$INSTANCE" "sudo systemctl restart chatmrpt"
    
    if [ $? -eq 0 ]; then
        echo "  ✅ Service restarted"
    else
        echo "  ❌ Failed to restart service"
        exit 1
    fi
    
    # Check service status
    echo "🔍 Checking service status..."
    ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no "ec2-user@$INSTANCE" "sudo systemctl is-active chatmrpt"
    
    echo "✅ Deployment to $INSTANCE complete"
    echo ""
done

echo "=========================================="
echo "✨ Deployment Complete!"
echo "=========================================="
echo ""
echo "🚀 Improvements deployed:"
echo "  1. Mistral now sees all 28 tools with descriptions"
echo "  2. New data description tool available"
echo "  3. Arena has column information in context"
echo "  4. Better routing accuracy for all requests"
echo ""
echo "📍 Access points:"
echo "  - CloudFront: https://d225ar6c86586s.cloudfront.net"
echo "  - ALB: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
