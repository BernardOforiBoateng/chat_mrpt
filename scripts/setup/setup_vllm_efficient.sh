#!/bin/bash

# Efficient vLLM Setup for ChatMRPT Arena Mode
# Uses single vLLM instance with dynamic model loading

set -e

echo "================================================"
echo "  Efficient vLLM Setup for ChatMRPT Arena"
echo "================================================"

# Step 1: Check current AWS setup
echo "Checking current AWS instances..."
aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=ChatMRPT*" "Name=instance-state-name,Values=running" \
    --query 'Reservations[*].Instances[*].[InstanceId,InstanceType,PublicIpAddress,Tags[?Key==`Name`].Value|[0]]' \
    --output table

echo ""
echo "Do you want to:"
echo "1) Launch a new GPU instance"
echo "2) Convert existing instance to GPU"
echo "3) Use existing instance with Ollama (not recommended)"
read -p "Enter choice (1-3): " CHOICE

if [ "$CHOICE" = "1" ]; then
    # Launch new GPU instance
    ./launch_gpu_instance.sh
elif [ "$CHOICE" = "2" ]; then
    # Stop current instance and change type
    read -p "Enter instance ID to convert: " INSTANCE_ID
    
    echo "Stopping instance..."
    aws ec2 stop-instances --instance-ids $INSTANCE_ID
    aws ec2 wait instance-stopped --instance-ids $INSTANCE_ID
    
    echo "Changing instance type to g5.xlarge..."
    aws ec2 modify-instance-attribute --instance-id $INSTANCE_ID --instance-type g5.xlarge
    
    echo "Starting instance..."
    aws ec2 start-instances --instance-ids $INSTANCE_ID
    aws ec2 wait instance-running --instance-ids $INSTANCE_ID
    
    PUBLIC_IP=$(aws ec2 describe-instances \
        --instance-ids $INSTANCE_ID \
        --query 'Reservations[0].Instances[0].PublicIpAddress' \
        --output text)
    
    echo "Instance converted! New IP: $PUBLIC_IP"
fi

# Create setup script for vLLM on the instance
cat > setup_vllm_on_instance.sh << 'EOF'
#!/bin/bash

# Install CUDA and vLLM
echo "Installing CUDA drivers..."
sudo yum install -y nvidia-driver-latest-dkms
sudo yum install -y cuda-toolkit-11-8

# Create Python environment
python3 -m venv /home/ec2-user/vllm_env
source /home/ec2-user/vllm_env/bin/activate

# Install vLLM
pip install --upgrade pip
pip install vllm transformers torch accelerate

# Create vLLM service with model switching capability
cat > /home/ec2-user/start_vllm.py << 'INNER_EOF'
#!/usr/bin/env python3
"""
vLLM Server with Dynamic Model Switching for Arena Mode
"""
import os
import sys
import argparse
from vllm import LLM, SamplingParams
from vllm.entrypoints.openai import api_server
import uvicorn

# Model configurations
MODELS = {
    'llama-3.1-8b': 'meta-llama/Llama-3.1-8B-Instruct',
    'mistral-7b': 'mistralai/Mistral-7B-Instruct-v0.3',
    'qwen-2.5-7b': 'Qwen/Qwen2.5-7B-Instruct',
}

def start_server(model_name='llama-3.1-8b', port=8000):
    """Start vLLM server with specified model"""
    model_path = MODELS.get(model_name)
    if not model_path:
        print(f"Model {model_name} not found!")
        return
    
    # Start the API server
    from vllm.entrypoints.openai.api_server import run_server
    run_server(
        model=model_path,
        host='0.0.0.0',
        port=port,
        served_model_name=model_name,
        max_model_len=4096,
        gpu_memory_utilization=0.9,  # Use most of GPU memory
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default='llama-3.1-8b', choices=MODELS.keys())
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    
    start_server(args.model, args.port)
INNER_EOF

chmod +x /home/ec2-user/start_vllm.py

# Create systemd service
sudo cat > /etc/systemd/system/vllm.service << 'INNER_EOF'
[Unit]
Description=vLLM Service
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user
Environment="PATH=/home/ec2-user/vllm_env/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/ec2-user/vllm_env/bin/python /home/ec2-user/start_vllm.py --model llama-3.1-8b --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
INNER_EOF

# Download models in background
echo "Downloading models (this will take time)..."
source /home/ec2-user/vllm_env/bin/activate
python -c "
from transformers import AutoModelForCausalLM, AutoTokenizer
import os

models = [
    'meta-llama/Llama-3.1-8B-Instruct',
    'mistralai/Mistral-7B-Instruct-v0.3',
    'Qwen/Qwen2.5-7B-Instruct'
]

for model in models:
    print(f'Downloading {model}...')
    try:
        tokenizer = AutoTokenizer.from_pretrained(model, cache_dir='/home/ec2-user/.cache/huggingface')
        # Just download, don't load into memory
        model_path = AutoModelForCausalLM.from_pretrained(
            model, 
            cache_dir='/home/ec2-user/.cache/huggingface',
            torch_dtype='auto',
            device_map='cpu'  # Just download, don't load to GPU
        )
        print(f'✓ {model} downloaded')
    except Exception as e:
        print(f'✗ Failed to download {model}: {e}')
"

# Start the service
sudo systemctl daemon-reload
sudo systemctl enable vllm
sudo systemctl start vllm

echo "vLLM setup complete!"
echo "Test with: curl http://localhost:8000/v1/models"
EOF

# Copy and run setup script on instance
if [ ! -z "$PUBLIC_IP" ]; then
    echo "Setting up vLLM on instance..."
    scp -i ~/.ssh/chatmrpt-key.pem setup_vllm_on_instance.sh ec2-user@${PUBLIC_IP}:~/
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@${PUBLIC_IP} 'chmod +x setup_vllm_on_instance.sh && ./setup_vllm_on_instance.sh'
    
    echo ""
    echo "================================================"
    echo "vLLM Setup Complete!"
    echo "================================================"
    echo "Instance IP: ${PUBLIC_IP}"
    echo "vLLM Endpoint: http://${PUBLIC_IP}:8000"
    echo ""
    echo "Update your .env file:"
    echo "VLLM_BASE_URL=http://${PUBLIC_IP}:8000"
    echo "USE_VLLM=true"
    echo ""
    echo "Test the endpoint:"
    echo "curl http://${PUBLIC_IP}:8000/v1/models"
fi