#!/bin/bash

# Deploy timeout fix for large file handling

echo "🚀 Deploying timeout fix to staging servers..."

# Files to deploy
FILES="app/services/data_analysis_agent.py"

# Staging IPs
STAGING_IPS="3.21.167.170 18.220.103.20"

for IP in $STAGING_IPS; do
    echo "📦 Deploying to staging instance: $IP"
    
    # Copy files
    for FILE in $FILES; do
        echo "  📄 Copying $FILE..."
        scp -i /tmp/chatmrpt-key2.pem "$FILE" "ec2-user@$IP:/home/ec2-user/ChatMRPT/$FILE"
    done
    
    # Restart service
    echo "  🔄 Restarting service..."
    ssh -i /tmp/chatmrpt-key2.pem "ec2-user@$IP" "sudo systemctl restart chatmrpt"
    
    echo "  ✅ Deployment to $IP complete"
done

echo "✅ Timeout fix deployed!"
echo "🌐 Test at: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "📝 Changes made:"
echo "  - Increased vLLM timeout from 30s to 120s for large files"
echo "  - Optimized Excel file loading for better memory usage"
echo "  - Improved handling of multi-sheet Excel files"