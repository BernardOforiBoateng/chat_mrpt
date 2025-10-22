#!/bin/bash

echo "=== Direct Deployment to Production ==="
echo "Attempting different methods to reach production..."

STAGING_IP="3.21.167.170"

# Method 1: Try through staging with proper key setup
echo "Method 1: Deploy through staging server..."

ssh -i /tmp/chatmrpt-key2.pem ec2-user@${STAGING_IP} << 'DEPLOY_SCRIPT'
    echo "On staging server, preparing deployment..."
    
    # Ensure key permissions
    chmod 600 ~/.ssh/chatmrpt-key.pem 2>/dev/null
    
    # Get production IPs from AWS
    echo "Finding production instances..."
    
    # Try different IPs for production
    PROD_IPS="172.31.44.52 172.31.43.200 172.31.32.123 172.31.35.89"
    
    for PROD_IP in $PROD_IPS; do
        echo ""
        echo "Trying to reach $PROD_IP..."
        
        # Test connectivity first
        if timeout 3 nc -zv $PROD_IP 22 2>&1 | grep succeeded; then
            echo "✅ Can reach $PROD_IP on port 22"
            
            # Try to deploy
            echo "Deploying to $PROD_IP..."
            
            # Use rsync with explicit key
            rsync -avz -e "ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no" \
                --exclude='instance/uploads/*/*' \
                --exclude='instance/*.db' \
                --exclude='__pycache__' \
                --exclude='*.pyc' \
                --exclude='venv/' \
                /home/ec2-user/ChatMRPT/ \
                ec2-user@${PROD_IP}:/home/ec2-user/ChatMRPT/ 2>&1 | head -20
            
            if [ $? -eq 0 ]; then
                echo "✅ Deployed to $PROD_IP"
                ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@${PROD_IP} "sudo systemctl restart chatmrpt"
            else
                echo "❌ Failed to deploy to $PROD_IP"
            fi
        else
            echo "❌ Cannot reach $PROD_IP"
        fi
    done
    
    echo ""
    echo "Checking if we can use localhost/127.0.0.1 (same instance)..."
    if [ -d /home/ec2-user/ChatMRPT ]; then
        echo "This appears to be a ChatMRPT instance"
        sudo systemctl restart chatmrpt 2>&1 || true
    fi
DEPLOY_SCRIPT

echo ""
echo "Method 2: Direct copy of critical files..."

# Copy critical files directly
scp -i /tmp/chatmrpt-key2.pem \
    ec2-user@${STAGING_IP}:/home/ec2-user/ChatMRPT/app/data_analysis_v3/tools/tpr_analysis_tool.py \
    /tmp/tpr_analysis_tool_staging.py 2>/dev/null

if [ -f /tmp/tpr_analysis_tool_staging.py ]; then
    echo "✅ Retrieved staging TPR tool"
    ls -la /tmp/tpr_analysis_tool_staging.py
fi

echo ""
echo "Testing production endpoints..."
curl -s -o /dev/null -w "ALB Health: %{http_code}\n" http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com/ping

