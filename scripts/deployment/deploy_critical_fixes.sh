#!/bin/bash

echo "=========================================="
echo "🚀 DEPLOYING CRITICAL FIXES"
echo "=========================================="
echo ""
echo "Fixing TWO CRITICAL ISSUES:"
echo "1. ✅ Over 5 Years group missing - Using EncodingHandler in agent.py"
echo "2. ✅ Formatting broken - Fixed JavaScript line break handling"
echo ""
echo "=========================================="
echo ""

# Files to deploy
FILES_TO_DEPLOY=(
    "app/data_analysis_v3/core/agent.py"
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
    
    # Copy files
    for file in "${FILES_TO_DEPLOY[@]}"; do
        echo "  📤 Copying $file..."
        scp -i /tmp/chatmrpt-key2.pem "$file" ec2-user@$ip:/home/ec2-user/ChatMRPT/$file
        if [ $? -ne 0 ]; then
            echo "  ❌ Failed to copy $file to $ip"
            exit 1
        fi
    done
    
    # Clear browser cache reminder
    echo "  📝 Note: Browser may cache JavaScript - hard refresh needed"
    
    # Restart service
    echo "  🔄 Restarting service..."
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$ip "sudo systemctl restart chatmrpt"
    if [ $? -ne 0 ]; then
        echo "  ❌ Failed to restart service on $ip"
        exit 1
    fi
    
    echo "  ✅ Successfully deployed to $ip"
done

echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "CRITICAL: Clear browser cache (Ctrl+Shift+R) to see JavaScript fixes!"
echo ""
echo "Test both fixes:"
echo "1. Upload Adamawa TPR data"
echo "2. Select 'Primary' facilities"
echo "3. Verify you see THREE age groups:"
echo "   - Under 5 Years ✅"
echo "   - Over 5 Years ✅ (THIS SHOULD NOW APPEAR!)"
echo "   - Pregnant Women ✅"
echo "4. Check formatting has proper line breaks"
echo ""
echo "Test URLs:"
echo "- Instance 1: http://3.21.167.170"
echo "- Instance 2: http://18.220.103.20"
echo "- ALB: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "=========================================="
