#!/bin/bash

# Configure AWS Production Instances with Ollama GPU Host

echo "=========================================="
echo "Configuring AWS Instances for Ollama Arena"
echo "=========================================="

# Check if Ollama GPU info exists
if [ ! -f aws_files/ollama_gpu_info.txt ]; then
    echo "❌ Ollama GPU info not found. Run launch_ollama_gpu.sh first."
    exit 1
fi

# Load Ollama GPU info
source aws_files/ollama_gpu_info.txt

echo "Using Ollama GPU Instance:"
echo "  Private IP: $OLLAMA_GPU_PRIVATE_IP"
echo ""

# Copy key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# Function to configure an instance
configure_instance() {
    local IP=$1
    local NAME=$2
    
    echo "Configuring $NAME ($IP)..."
    
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$IP << ENDSSH
        cd /home/ec2-user/ChatMRPT
        
        # Update .env file
        echo "Updating .env with Ollama host..."
        
        # Remove old Ollama settings
        sed -i '/AWS_OLLAMA_HOST=/d' .env 2>/dev/null
        sed -i '/OLLAMA_HOST=/d' .env 2>/dev/null
        
        # Add new Ollama settings
        echo "" >> .env
        echo "# Ollama GPU Instance Configuration" >> .env
        echo "AWS_OLLAMA_HOST=$OLLAMA_GPU_PRIVATE_IP" >> .env
        echo "OLLAMA_HOST=$OLLAMA_GPU_PRIVATE_IP" >> .env
        echo "OLLAMA_PORT=11434" >> .env
        
        # Update arena models in .env
        sed -i 's/ARENA_MODELS=.*/ARENA_MODELS=llama3.1:8b,mistral:7b,phi3:mini/' .env
        
        # Restart service
        echo "Restarting ChatMRPT service..."
        sudo systemctl restart chatmrpt
        
        echo "✅ Configuration complete on \$(hostname)"
ENDSSH
}

# Configure both production instances
echo ""
echo "Configuring Production Instances..."
echo "=========================================="

configure_instance "3.21.167.170" "Production Instance 1"
configure_instance "18.220.103.20" "Production Instance 2"

echo ""
echo "Testing Ollama connectivity from production..."
echo "=========================================="

# Test from first instance
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'ENDSSH'
    echo "Testing Ollama connection..."
    source /home/ec2-user/ChatMRPT/.env
    curl -s "http://$AWS_OLLAMA_HOST:11434/api/tags" | head -5
    if [ $? -eq 0 ]; then
        echo "✅ Ollama is accessible from production"
    else
        echo "❌ Cannot reach Ollama. Check security group settings."
    fi
ENDSSH

# Clean up
rm -f /tmp/chatmrpt-key2.pem

echo ""
echo "=========================================="
echo "✅ Configuration Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Test the Arena endpoint:"
echo "   curl https://d225ar6c86586s.cloudfront.net/api/arena/ollama-status"
echo ""
echo "2. Test Arena mode in the UI:"
echo "   - Go to https://d225ar6c86586s.cloudfront.net"
echo "   - Ask a general question (not data-specific)"
echo "   - Should see 3 model comparisons"
echo ""
echo "3. Monitor GPU usage:"
echo "   ssh -i /tmp/chatmrpt-key2.pem ec2-user@$OLLAMA_GPU_PUBLIC_IP"
echo "   nvidia-smi"