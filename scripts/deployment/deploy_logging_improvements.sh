#!/bin/bash

echo "🚀 Deploying Logging Improvements to Staging"
echo "========================================="

# Files to deploy
FILES="app/data_analysis_v3/tools/python_tool.py app/data_analysis_v3/core/executor.py"

# Staging IPs
STAGING_IPS="3.21.167.170 18.220.103.20"

for ip in $STAGING_IPS; do
    echo ""
    echo "📦 Deploying to $ip..."
    
    # Copy files
    for file in $FILES; do
        echo "  - Copying $file"
        scp -i /tmp/chatmrpt-key2.pem "$file" "ec2-user@$ip:~/ChatMRPT/$file"
    done
    
    # Restart service
    echo "  - Restarting service..."
    ssh -i /tmp/chatmrpt-key2.pem "ec2-user@$ip" 'sudo systemctl restart chatmrpt'
    
    echo "  ✅ Deployed to $ip"
done

echo ""
echo "✅ Deployment complete!"
echo "Now we can see detailed logs of what's happening during tool execution."