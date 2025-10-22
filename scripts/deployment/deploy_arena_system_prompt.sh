#!/bin/bash

# Deploy Arena System Prompt Fix to AWS Production
# This script deploys the comprehensive ChatMRPT system prompt for Arena models

echo "🚀 Deploying Arena System Prompt Fix to AWS Production..."
echo "================================================="

# Production instances (formerly staging)
INSTANCE_1="3.21.167.170"
INSTANCE_2="18.220.103.20"
KEY_PATH="$HOME/.ssh/chatmrpt-key.pem"

# Check if key exists
if [ ! -f "$KEY_PATH" ]; then
    echo "❌ SSH key not found at $KEY_PATH"
    echo "Trying alternative location..."
    KEY_PATH="/tmp/chatmrpt-key2.pem"
    
    if [ ! -f "$KEY_PATH" ]; then
        # Copy key to /tmp if needed
        if [ -f "aws_files/chatmrpt-key.pem" ]; then
            cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
            chmod 600 /tmp/chatmrpt-key2.pem
            KEY_PATH="/tmp/chatmrpt-key2.pem"
            echo "✅ Key copied to $KEY_PATH"
        else
            echo "❌ Cannot find SSH key. Please ensure aws_files/chatmrpt-key.pem exists"
            exit 1
        fi
    fi
fi

echo "📦 Files to deploy:"
echo "  - app/core/arena_system_prompt.py (NEW)"
echo "  - app/web/routes/analysis_routes.py (UPDATED)"
echo ""

# Deploy to both production instances
for instance in $INSTANCE_1 $INSTANCE_2; do
    echo "🔄 Deploying to instance: $instance"
    echo "-----------------------------------"
    
    # Create the arena_system_prompt.py file
    echo "  📝 Creating app/core/arena_system_prompt.py..."
    scp -i "$KEY_PATH" -o StrictHostKeyChecking=no \
        app/core/arena_system_prompt.py \
        ec2-user@$instance:/home/ec2-user/ChatMRPT/app/core/
    
    if [ $? -eq 0 ]; then
        echo "  ✅ arena_system_prompt.py deployed"
    else
        echo "  ❌ Failed to deploy arena_system_prompt.py"
        exit 1
    fi
    
    # Update analysis_routes.py
    echo "  📝 Updating app/web/routes/analysis_routes.py..."
    scp -i "$KEY_PATH" -o StrictHostKeyChecking=no \
        app/web/routes/analysis_routes.py \
        ec2-user@$instance:/home/ec2-user/ChatMRPT/app/web/routes/
    
    if [ $? -eq 0 ]; then
        echo "  ✅ analysis_routes.py updated"
    else
        echo "  ❌ Failed to update analysis_routes.py"
        exit 1
    fi
    
    # Restart the service
    echo "  🔄 Restarting ChatMRPT service..."
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$instance \
        "sudo systemctl restart chatmrpt && echo '  ✅ Service restarted' || echo '  ❌ Service restart failed'"
    
    # Check service status
    echo "  📊 Checking service status..."
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$instance \
        "sudo systemctl is-active chatmrpt | grep -q active && echo '  ✅ Service is running' || echo '  ⚠️ Service may not be running properly'"
    
    echo ""
done

echo "✅ Deployment complete to both production instances!"
echo ""
echo "📋 Deployment Summary:"
echo "  - Instance 1 ($INSTANCE_1): Updated"
echo "  - Instance 2 ($INSTANCE_2): Updated"
echo "  - Files deployed:"
echo "    • app/core/arena_system_prompt.py (new module)"
echo "    • app/web/routes/analysis_routes.py (updated to use system prompt)"
echo ""
echo "🧪 Test URLs:"
echo "  - CloudFront: https://d225ar6c86586s.cloudfront.net"
echo "  - ALB: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "🎯 What to test:"
echo "  1. Go to the application"
echo "  2. Ask 'Who are you?' in chat"
echo "  3. Arena models should respond as ChatMRPT"
echo "  4. Check that models identify with malaria expertise"
echo ""
echo "✨ Arena models now use comprehensive ChatMRPT system prompt!"