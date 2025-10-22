#!/bin/bash

# Deploy TPR One-Tool Pattern to NEW Staging IPs
echo "========================================"
echo "Deploying TPR One-Tool Pattern to Staging"
echo "NEW Staging IPs detected from AWS Console"
echo "========================================"

# Step 1: Copy key to /tmp
echo "Setting up SSH key..."
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# NEW Staging IPs from context.md
STAGING_IP1="3.21.167.170"    # ChatMRPT-Staging (i-0994615951d0b9563)
STAGING_IP2="18.220.103.20"   # chatmrpt-staging-2 (i-0f3b25b72f18a5037)

echo "Using NEW staging IPs:"
echo "  - Instance 1: $STAGING_IP1"
echo "  - Instance 2: $STAGING_IP2"

# Step 2: Create deployment package
echo "Creating deployment package..."
tar -czf /tmp/tpr_deployment.tar.gz \
    app/tpr_module/conversation.py \
    app/tpr_module/integration/llm_tpr_handler.py \
    app/tpr_module/prompts.py \
    app/tpr_module/sandbox.py \
    app/tpr_module/data/geopolitical_zones.py

# Function to deploy to a single instance
deploy_to_instance() {
    local IP=$1
    local NAME=$2
    
    echo ""
    echo "Deploying to $NAME ($IP)..."
    
    # Copy files
    echo "Copying files to $IP..."
    scp -i /tmp/chatmrpt-key2.pem -o StrictHostKeyChecking=no \
        /tmp/tpr_deployment.tar.gz \
        ec2-user@$IP:/tmp/
    
    if [ $? -ne 0 ]; then
        echo "Failed to copy to $IP - may not be accessible"
        return 1
    fi
    
    # Deploy on server
    ssh -i /tmp/chatmrpt-key2.pem -o StrictHostKeyChecking=no ec2-user@$IP << 'REMOTE_COMMANDS'
        set -e
        
        echo "Extracting files..."
        cd /home/ec2-user/ChatMRPT
        tar -xzf /tmp/tpr_deployment.tar.gz
        
        echo "Files updated:"
        ls -la app/tpr_module/*.py | tail -5
        
        echo "Restarting ChatMRPT service..."
        sudo systemctl restart chatmrpt
        
        sleep 5
        
        if sudo systemctl is-active --quiet chatmrpt; then
            echo "✅ Service restarted successfully"
            echo "Workers running: $(ps aux | grep gunicorn | grep -v grep | wc -l)"
        else
            echo "❌ Service failed to start"
            sudo journalctl -u chatmrpt -n 10 --no-pager
            exit 1
        fi
        
        echo "Testing health endpoint..."
        curl -s -o /dev/null -w "Health check HTTP status: %{http_code}\n" http://localhost:5000/ping
        
        echo "Checking for Ollama..."
        if command -v ollama &> /dev/null; then
            echo "✅ Ollama is installed"
            ollama list 2>/dev/null | head -3 || echo "Ollama list failed"
        else
            echo "⚠️ Ollama not found - will use OpenAI API"
        fi
        
        echo ""
        echo "Deployment complete on this instance!"
REMOTE_COMMANDS
    
    return $?
}

# Deploy to both staging instances
SUCCESS_COUNT=0
FAIL_COUNT=0

deploy_to_instance "$STAGING_IP1" "ChatMRPT-Staging"
if [ $? -eq 0 ]; then
    ((SUCCESS_COUNT++))
else
    ((FAIL_COUNT++))
fi

deploy_to_instance "$STAGING_IP2" "chatmrpt-staging-2"
if [ $? -eq 0 ]; then
    ((SUCCESS_COUNT++))
else
    ((FAIL_COUNT++))
fi

# Summary
echo ""
echo "========================================"
echo "Deployment Summary:"
echo "✅ Successful: $SUCCESS_COUNT instances"
if [ $FAIL_COUNT -gt 0 ]; then
    echo "❌ Failed: $FAIL_COUNT instances"
fi
echo "========================================"

if [ $SUCCESS_COUNT -gt 0 ]; then
    echo ""
    echo "✅ TPR One-Tool Pattern Deployed!"
    echo ""
    echo "Access staging at:"
    echo "  - Instance 1: http://$STAGING_IP1:5000"
    echo "  - Instance 2: http://$STAGING_IP2:5000"
    echo "  - ALB: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
    echo ""
    echo "To test the TPR workflow:"
    echo "  1. Upload a TPR Excel/CSV file"
    echo "  2. The system will use the one-tool pattern where:"
    echo "     - LLM decides all actions dynamically"
    echo "     - No hardcoded tools or columns"
    echo "     - Interactive ward matching when needed"
    echo "     - Automatic TPR calculation and map generation"
else
    echo ""
    echo "❌ Deployment failed on all instances!"
    echo "Please check network connectivity and SSH access"
    exit 1
fi

# Cleanup
rm -f /tmp/tpr_deployment.tar.gz
echo "Cleanup complete"