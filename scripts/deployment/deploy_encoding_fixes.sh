#!/bin/bash

echo "==========================================
🚀 Deploying Dynamic Encoding Fixes
==========================================

This deployment includes:
1. ✅ Fully dynamic encoding detection (no hardcoding)
2. ✅ Automatic mojibake fixing with ftfy
3. ✅ Proper test type statistics (RDT vs Microscopy)
4. ✅ Only 3 age groups shown (no 'All Ages Combined')
5. ✅ Proper HTML formatting with line breaks
==========================================
"

# Files to deploy
FILES_TO_DEPLOY=(
    "app/data_analysis_v3/core/encoding_handler.py"
    "app/data_analysis_v3/core/tpr_data_analyzer.py"
    "app/data_analysis_v3/core/formatters.py"
    "app/data_analysis_v3/core/column_sanitizer.py"
)

# Staging IPs (updated Jan 7, 2025)
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
echo "==========================================
✅ DEPLOYMENT COMPLETE!
==========================================

Test the fixes:
1. Upload Adamawa TPR data with garbled column names
2. Verify 'Over 5 Years' group appears (was Ã¢â€°Â¥5yrs)
3. Check only 3 age groups shown (no 'All Ages Combined')
4. Verify RDT vs Microscopy stats display
5. Confirm proper formatting with line breaks

Test URLs:
- Instance 1: http://3.21.167.170
- Instance 2: http://18.220.103.20
- ALB: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com

==========================================
"