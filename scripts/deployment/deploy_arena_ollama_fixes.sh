#!/bin/bash

# Deploy Arena Fixes to AWS Production Instances

echo "=========================================="
echo "Deploying Arena Fixes to AWS Production"
echo "=========================================="

# Copy key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# Function to deploy to an instance
deploy_to_instance() {
    local IP=$1
    local NAME=$2
    
    echo ""
    echo "Deploying to $NAME ($IP)..."
    echo "=========================================="
    
    # Copy the updated files
    echo "Copying updated files..."
    
    # Copy Ollama adapter
    scp -i /tmp/chatmrpt-key2.pem \
        app/core/ollama_adapter.py \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/core/
    
    # Copy arena routes
    scp -i /tmp/chatmrpt-key2.pem \
        app/web/routes/arena_routes.py \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/web/routes/
    
    # Copy test script
    scp -i /tmp/chatmrpt-key2.pem \
        test_arena_fixed.py \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/
    
    # Update configuration and restart
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$IP << 'ENDSSH'
        cd /home/ec2-user/ChatMRPT
        
        echo "Updating .env configuration..."
        
        # Update ARENA_MODELS in .env
        sed -i 's/ARENA_MODELS=.*/ARENA_MODELS=llama3.1:8b,mistral:7b,phi3:mini/' .env
        
        # Remove any old vLLM references
        sed -i '/VLLM_/d' .env
        
        echo "Restarting ChatMRPT service..."
        sudo systemctl restart chatmrpt
        
        echo "Checking service status..."
        sudo systemctl status chatmrpt | head -10
        
        echo " Deployment complete on $(hostname)"
ENDSSH
    
    if [ $? -eq 0 ]; then
        echo " Successfully deployed to $NAME"
    else
        echo "L Failed to deploy to $NAME"
    fi
}

# Deploy to both production instances
echo ""
echo "Starting deployment to production instances..."

deploy_to_instance "3.21.167.170" "Production Instance 1"
deploy_to_instance "18.220.103.20" "Production Instance 2"

# Clean up
rm -f /tmp/chatmrpt-key2.pem

echo ""
echo "=========================================="
echo " Arena Fixes Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Launch Ollama GPU instance:"
echo "   ./scripts/deployment/launch_ollama_gpu.sh"
echo ""
echo "2. Configure instances with Ollama host:"
echo "   ./scripts/deployment/configure_ollama_aws.sh"
echo ""
echo "3. Test arena functionality:"
echo "   curl https://d225ar6c86586s.cloudfront.net/api/arena/ollama-status"