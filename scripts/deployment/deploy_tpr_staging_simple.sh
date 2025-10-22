#!/bin/bash

# Simple TPR deployment to staging
echo "Deploying TPR One-Tool Pattern to Staging..."

# Copy key file
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# Staging server IP
STAGING_IP="18.117.115.217"

# Create tar archive of TPR files
echo "Creating archive of TPR files..."
tar -czf /tmp/tpr_update.tar.gz \
    app/tpr_module/conversation.py \
    app/tpr_module/integration/llm_tpr_handler.py \
    app/tpr_module/prompts.py \
    app/tpr_module/sandbox.py

# Copy archive to staging
echo "Copying files to staging server..."
scp -i /tmp/chatmrpt-key2.pem -o StrictHostKeyChecking=no \
    /tmp/tpr_update.tar.gz \
    ec2-user@$STAGING_IP:/tmp/

if [ $? -ne 0 ]; then
    echo "Failed to copy files to staging"
    exit 1
fi

# Deploy on staging and to internal instances
echo "Deploying on staging server and distributing to instances..."
ssh -i /tmp/chatmrpt-key2.pem -o StrictHostKeyChecking=no ec2-user@$STAGING_IP << 'ENDSSH'
    set -e
    
    # Extract files
    cd /home/ec2-user/ChatMRPT
    tar -xzf /tmp/tpr_update.tar.gz
    echo "Files extracted on staging bastion"
    
    # Now copy to internal instances if accessible
    # Note: This assumes staging bastion can reach internal instances
    
    # Restart service on bastion
    sudo systemctl restart chatmrpt
    sleep 3
    
    # Check status
    if sudo systemctl is-active --quiet chatmrpt; then
        echo "✅ Service restarted successfully on staging bastion"
        ps aux | grep gunicorn | grep -v grep | wc -l | xargs echo "Workers running:"
    else
        echo "❌ Service failed to start"
        sudo journalctl -u chatmrpt -n 10 --no-pager
        exit 1
    fi
    
    # Test endpoint
    curl -s -o /dev/null -w "Health check: %{http_code}\n" http://localhost:5000/ping
    
    echo "Deployment successful on staging bastion!"
ENDSSH

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "✅ TPR One-Tool Pattern deployed to staging!"
    echo "========================================"
    echo ""
    echo "Access staging at:"
    echo "  - http://18.117.115.217:5000"
    echo "  - http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
    echo ""
    echo "Test the TPR workflow:"
    echo "1. Upload a TPR Excel/CSV file"
    echo "2. System will use local Ollama model"
    echo "3. Test the one-tool pattern with:"
    echo "   - Dynamic column detection"
    echo "   - Ward name matching"
    echo "   - TPR calculations"
    echo "   - Map generation"
else
    echo "❌ Deployment failed"
    exit 1
fi

# Cleanup
rm -f /tmp/tpr_update.tar.gz