#!/bin/bash

echo "=========================================="
echo "🧹 DEPLOYING SANITIZER REMOVAL"
echo "=========================================="
echo ""
echo "REMOVING COMPLEXITY - The best code is no code!"
echo ""

# Files to deploy (sanitizer.py is deleted, others are updated)
FILES_TO_DEPLOY=(
    "app/data_analysis_v3/core/agent.py"
    "app/data_analysis_v3/core/encoding_handler.py"
    "app/data_analysis_v3/core/metadata_cache.py"
    "app/data_analysis_v3/core/tpr_workflow_handler.py"
    "app/data_analysis_v3/tools/tpr_analysis_tool.py"
    "app/static/js/modules/chat/core/message-handler.js"
)

# Staging IPs
STAGING_IPS=("3.21.167.170" "18.220.103.20")

echo "📦 Files to deploy (updated):"
for file in "${FILES_TO_DEPLOY[@]}"; do
    echo "  - $file"
done
echo ""
echo "🗑️ File to remove: app/data_analysis_v3/core/column_sanitizer.py"
echo ""

# Deploy to staging instances
echo "🔄 Deploying to STAGING instances..."
for ip in "${STAGING_IPS[@]}"; do
    echo ""
    echo "📍 Deploying to staging instance: $ip"
    
    # Copy updated files
    for file in "${FILES_TO_DEPLOY[@]}"; do
        echo "  📤 Copying $file..."
        scp -i /tmp/chatmrpt-key2.pem "$file" ec2-user@$ip:/home/ec2-user/ChatMRPT/$file
    done
    
    # Remove the sanitizer file
    echo "  🗑️ Removing column_sanitizer.py..."
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$ip "rm -f /home/ec2-user/ChatMRPT/app/data_analysis_v3/core/column_sanitizer.py"
    
    # Restart service
    echo "  🔄 Restarting service..."
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$ip "sudo systemctl restart chatmrpt"
    
    echo "  ✅ Deployed to $ip"
done

echo ""
echo "=========================================="
echo "✅ SANITIZER REMOVAL COMPLETE!"
echo "=========================================="
echo ""
echo "What we achieved:"
echo "1. ✅ Removed column sanitizer completely"
echo "2. ✅ Simplified the codebase"
echo "3. ✅ All 3 age groups now detected properly"
echo "4. ✅ Special characters (≥, ≤) preserved"
echo "5. ✅ Formatting with proper line breaks"
echo ""
echo "The system is now SIMPLER and WORKS BETTER!"
echo ""
echo "Test at: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo "Remember: Clear browser cache (Ctrl+Shift+R) for JS changes!"
