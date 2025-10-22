#!/bin/bash

# User data script for GPU instance - runs automatically on launch
exec > >(tee /var/log/user-data.log)
exec 2>&1

echo "Starting GPU instance setup..."
echo "Time: $(date)"

# Update system
yum update -y

# Install NVIDIA drivers and CUDA
echo "Installing NVIDIA drivers..."
yum install -y gcc kernel-devel-$(uname -r)

# Install NVIDIA driver
curl -fSsl -O https://us.download.nvidia.com/tesla/535.161.08/NVIDIA-Linux-x86_64-535.161.08.run
sh NVIDIA-Linux-x86_64-535.161.08.run -s

# Install CUDA toolkit
yum-config-manager --add-repo https://developer.download.nvidia.com/compute/cuda/repos/rhel9/x86_64/cuda-rhel9.repo
yum clean all
yum install -y cuda-toolkit-12-3

# Install Docker (for containerized deployment option)
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -aG docker ec2-user

# Install Python 3.11
yum install -y python3.11 python3.11-pip python3.11-devel

# Install git
yum install -y git

# Switch to ec2-user for remaining setup
su - ec2-user << 'EOF_USER'

# Clone ChatMRPT repo to get scripts
cd /home/ec2-user
git clone https://github.com/yourusername/ChatMRPT.git || echo "Repo not available"

# Create vLLM setup script
cat > /home/ec2-user/setup_vllm_qwen3.sh << 'VLLM_SCRIPT'
#!/bin/bash

# Setup vLLM with Qwen 3 Models
echo "=========================================="
echo "vLLM Setup with Qwen 3 Models"
echo "=========================================="

# Check GPU
nvidia-smi

# Get GPU memory
GPU_MEMORY=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
GPU_MEMORY_GB=$((GPU_MEMORY / 1024))
echo "GPU Memory: ${GPU_MEMORY_GB}GB"

# Select model based on memory
if [ $GPU_MEMORY_GB -ge 20 ]; then
    MODEL="Qwen/Qwen3-8B"
    echo "Using Qwen3-8B"
else
    MODEL="Qwen/Qwen3-4B"
    echo "Using Qwen3-4B (limited memory)"
fi

# Create virtual environment
python3.11 -m venv vllm_env
source vllm_env/bin/activate

# Install vLLM
pip install --upgrade pip
pip install vllm transformers accelerate torch

# Create start script
cat > start_vllm.sh << 'START_SCRIPT'
#!/bin/bash
source /home/ec2-user/vllm_env/bin/activate

python -m vllm.entrypoints.openai.api_server \
    --model $MODEL \
    --port 8000 \
    --host 0.0.0.0 \
    --max-model-len 32768 \
    --gpu-memory-utilization 0.90 \
    --dtype auto \
    --trust-remote-code
START_SCRIPT

chmod +x start_vllm.sh

# Create systemd service
sudo tee /etc/systemd/system/vllm.service > /dev/null << 'SERVICE'
[Unit]
Description=vLLM Server with Qwen 3
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user
ExecStart=/home/ec2-user/start_vllm.sh
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable vllm

echo "Setup complete! Start with: sudo systemctl start vllm"
VLLM_SCRIPT

chmod +x /home/ec2-user/setup_vllm_qwen3.sh

# Create a simple test script
cat > /home/ec2-user/test_vllm.sh << 'TEST_SCRIPT'
#!/bin/bash
echo "Testing vLLM endpoint..."
curl -s http://localhost:8000/v1/models | python3 -m json.tool
echo ""
echo "Testing generation..."
curl -s http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3-8B",
    "prompt": "What is malaria TPR?",
    "max_tokens": 100,
    "temperature": 0.7
  }' | python3 -m json.tool
TEST_SCRIPT

chmod +x /home/ec2-user/test_vllm.sh

echo "GPU instance setup complete!"
echo "Next: Run /home/ec2-user/setup_vllm_qwen3.sh"

EOF_USER

echo "User data script complete at $(date)"