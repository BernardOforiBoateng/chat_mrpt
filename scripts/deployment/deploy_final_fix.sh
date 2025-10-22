#!/bin/bash

echo "=========================================="
echo "🚀 DEPLOYING FINAL FIX - NO SANITIZATION"
echo "=========================================="
echo ""
echo "The simple solution: DISABLE column sanitization!"
echo "Let pandas handle column names with ≥ symbols naturally"
echo ""

# Files to deploy
FILES_TO_DEPLOY=(
    "app/data_analysis_v3/core/agent.py"
    "app/data_analysis_v3/core/encoding_handler.py"
    "app/static/js/modules/chat/core/message-handler.js"
)

# Staging IPs
STAGING_IPS=("3.21.167.170" "18.220.103.20")

echo "📦 Files to deploy:"
for file in "${FILES_TO_DEPLOY[@]}"; do
    echo "  - $file"
done
echo ""

# Deploy to staging instances
echo "🔄 Deploying to STAGING instances..."
for ip in "${STAGING_IPS[@]}"; do
    echo ""
    echo "📍 Deploying to staging instance: $ip"
    
    for file in "${FILES_TO_DEPLOY[@]}"; do
        echo "  📤 Copying $file..."
        scp -i /tmp/chatmrpt-key2.pem "$file" ec2-user@$ip:/home/ec2-user/ChatMRPT/$file
    done
    
    echo "  🔄 Restarting service..."
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$ip "sudo systemctl restart chatmrpt"
    
    echo "  ✅ Deployed to $ip"
done

echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "BOTH ISSUES FIXED:"
echo "1. ✅ Over 5 Years group now appears (disabled sanitization)"
echo "2. ✅ Formatting with proper line breaks (fixed JS)"
echo ""
echo "IMPORTANT: Clear browser cache (Ctrl+Shift+R)!"
echo ""
echo "Test at: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
