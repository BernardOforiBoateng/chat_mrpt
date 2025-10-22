#!/bin/bash

# Deploy TPR One-Tool Pattern to Staging
echo "========================================"
echo "Deploying TPR One-Tool Pattern to Staging"
echo "========================================"

# Step 1: Copy key to /tmp
echo "Setting up SSH key..."
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# Step 2: Create deployment package
echo "Creating deployment package..."
tar -czf /tmp/tpr_deployment.tar.gz \
    app/tpr_module/conversation.py \
    app/tpr_module/integration/llm_tpr_handler.py \
    app/tpr_module/prompts.py \
    app/tpr_module/sandbox.py \
    app/tpr_module/data/geopolitical_zones.py

# Step 3: Copy to staging server
echo "Copying files to staging server (18.117.115.217)..."
scp -i /tmp/chatmrpt-key2.pem -o StrictHostKeyChecking=no \
    /tmp/tpr_deployment.tar.gz \
    ec2-user@18.117.115.217:/tmp/

if [ $? -ne 0 ]; then
    echo "Failed to copy files to staging server"
    echo "Please check:"
    echo "  1. Your network connection"
    echo "  2. SSH key permissions"
    echo "  3. Staging server is accessible"
    exit 1
fi

# Step 4: Deploy on staging server
echo "Deploying on staging server..."
ssh -i /tmp/chatmrpt-key2.pem -o StrictHostKeyChecking=no ec2-user@18.117.115.217 << 'REMOTE_COMMANDS'
    set -e
    
    echo "Extracting files on staging..."
    cd /home/ec2-user/ChatMRPT
    tar -xzf /tmp/tpr_deployment.tar.gz
    
    echo "Files updated:"
    ls -la app/tpr_module/*.py
    ls -la app/tpr_module/integration/*.py
    
    echo "Restarting ChatMRPT service..."
    sudo systemctl restart chatmrpt
    
    sleep 5
    
    if sudo systemctl is-active --quiet chatmrpt; then
        echo "✅ Service restarted successfully"
        echo "Workers running: $(ps aux | grep gunicorn | grep -v grep | wc -l)"
    else
        echo "❌ Service failed to start"
        sudo journalctl -u chatmrpt -n 20 --no-pager
        exit 1
    fi
    
    echo "Testing health endpoint..."
    curl -s -o /dev/null -w "Health check HTTP status: %{http_code}\n" http://localhost:5000/ping
    
    echo "Checking if Ollama is available..."
    if command -v ollama &> /dev/null; then
        echo "✅ Ollama is installed"
        ollama list | head -5
    else
        echo "⚠️ Ollama not found - will use OpenAI API"
    fi
    
    echo ""
    echo "Deployment complete on staging server!"
REMOTE_COMMANDS

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "✅ TPR One-Tool Pattern Successfully Deployed!"
    echo "========================================"
    echo ""
    echo "Access the staging environment at:"
    echo "  - Direct: http://18.117.115.217:5000"
    echo "  - ALB: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
    echo ""
    echo "To test the TPR workflow:"
    echo "  1. Upload a TPR Excel/CSV file"
    echo "  2. The system will use the one-tool pattern where:"
    echo "     - LLM decides all actions dynamically"
    echo "     - No hardcoded tools or columns"
    echo "     - Interactive ward matching when needed"
    echo "     - Automatic TPR calculation and map generation"
    echo ""
    echo "The LLM will use Ollama (if available) or OpenAI API"
else
    echo ""
    echo "❌ Deployment failed!"
    echo "Check the error messages above for details"
    exit 1
fi

# Cleanup
rm -f /tmp/tpr_deployment.tar.gz
echo "Cleanup complete"