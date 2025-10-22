#!/bin/bash

# Deploy Arena Frontend UI Changes to AWS Production
# This fixes the UI to show "Assistant A/B" and proper voting buttons

echo "🚀 Deploying Arena Frontend UI Changes to AWS Production..."
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

echo "📦 Frontend files to deploy:"
echo "  - app/static/js/modules/chat/core/message-handler.js"
echo "  - app/static/css/style.css (if modified)"
echo ""

# Deploy to both production instances
for instance in $INSTANCE_1 $INSTANCE_2; do
    echo "🔄 Deploying to instance: $instance"
    echo "-----------------------------------"
    
    # Deploy message-handler.js
    echo "  📝 Updating message-handler.js..."
    scp -i "$KEY_PATH" -o StrictHostKeyChecking=no \
        app/static/js/modules/chat/core/message-handler.js \
        ec2-user@$instance:/home/ec2-user/ChatMRPT/app/static/js/modules/chat/core/
    
    if [ $? -eq 0 ]; then
        echo "  ✅ message-handler.js deployed"
    else
        echo "  ❌ Failed to deploy message-handler.js"
        exit 1
    fi
    
    # Deploy style.css if it exists and has Arena-specific changes
    if [ -f "app/static/css/style.css" ]; then
        echo "  📝 Updating style.css..."
        scp -i "$KEY_PATH" -o StrictHostKeyChecking=no \
            app/static/css/style.css \
            ec2-user@$instance:/home/ec2-user/ChatMRPT/app/static/css/
        
        if [ $? -eq 0 ]; then
            echo "  ✅ style.css deployed"
        else
            echo "  ⚠️ Warning: style.css deployment failed (non-critical)"
        fi
    fi
    
    # Clear browser cache hint - no server restart needed for static files
    echo "  🔄 Static files updated (no restart needed)"
    
    # Optional: Clear any server-side cache if exists
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$instance \
        "cd /home/ec2-user/ChatMRPT && find app/static -name '*.pyc' -delete 2>/dev/null || true"
    
    echo "  ✅ Deployment complete for $instance"
    echo ""
done

echo "✅ Frontend deployment complete to both production instances!"
echo ""
echo "📋 Deployment Summary:"
echo "  - Instance 1 ($INSTANCE_1): Frontend updated"
echo "  - Instance 2 ($INSTANCE_2): Frontend updated"
echo "  - Files deployed:"
echo "    • app/static/js/modules/chat/core/message-handler.js"
echo "    • app/static/css/style.css (if exists)"
echo ""
echo "🧪 Test URLs:"
echo "  - CloudFront: https://d225ar6c86586s.cloudfront.net"
echo "  - ALB: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "⚠️ IMPORTANT: Clear your browser cache!"
echo "  1. Hard refresh: Ctrl+Shift+R (or Cmd+Shift+R on Mac)"
echo "  2. Clear browser cache and cookies for the domain"
echo "  3. Try incognito/private browsing mode to test"
echo ""
echo "🎯 What you should see:"
echo "  ✅ 'Assistant A' and 'Assistant B' labels (not Response A/B)"
echo "  ✅ Voting buttons: 'Left is Better', 'Right is Better', etc."
echo "  ✅ Clean Arena UI with proper styling"
echo ""
echo "✨ Arena frontend UI updates deployed!"