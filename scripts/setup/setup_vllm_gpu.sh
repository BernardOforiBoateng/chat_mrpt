#!/bin/bash

# Setup vLLM on GPU Instance for ChatMRPT
echo "=========================================="
echo "vLLM GPU Setup for ChatMRPT"
echo "=========================================="

# This script should be run on a GPU instance (g4dn.xlarge or g5.xlarge)

# Step 1: Check for GPU
echo "Checking for GPU..."
if ! command -v nvidia-smi &> /dev/null; then
    echo "❌ No GPU detected. This script requires a GPU instance."
    echo "Please launch a g4dn.xlarge or g5.xlarge instance first."
    exit 1
fi

nvidia-smi
echo ""

# Step 2: Install Python 3.10+ if needed
echo "Checking Python version..."
python3 --version

# Step 3: Create virtual environment for vLLM
echo "Creating vLLM environment..."
python3 -m venv vllm_env
source vllm_env/bin/activate

# Step 4: Install vLLM
echo "Installing vLLM..."
pip install --upgrade pip
pip install vllm

# Step 5: Install additional dependencies
echo "Installing additional dependencies..."
pip install transformers torch accelerate

# Step 6: Create vLLM service script
echo "Creating vLLM service..."
cat > /home/ec2-user/start_vllm.sh << 'EOF'
#!/bin/bash
source /home/ec2-user/vllm_env/bin/activate

# Start vLLM server with Qwen 3 model
# Using Qwen3-32B for g5.12xlarge (4x A10G with 96GB total)
# For smaller instances, use Qwen3-8B
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen3-32B \
    --port 8000 \
    --host 0.0.0.0 \
    --max-model-len 32768 \
    --gpu-memory-utilization 0.90 \
    --dtype auto \
    --trust-remote-code
EOF

chmod +x /home/ec2-user/start_vllm.sh

# Step 7: Create systemd service
echo "Creating systemd service..."
sudo tee /etc/systemd/system/vllm.service > /dev/null << 'EOF'
[Unit]
Description=vLLM Server
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
EOF

# Step 8: Enable and start service
echo "Starting vLLM service..."
sudo systemctl daemon-reload
sudo systemctl enable vllm
sudo systemctl start vllm

sleep 5

# Step 9: Check status
echo "Checking vLLM status..."
sudo systemctl status vllm | head -10

# Step 10: Test vLLM endpoint
echo "Testing vLLM endpoint..."
sleep 10
curl -s http://localhost:8000/v1/models | python3 -m json.tool

echo ""
echo "=========================================="
echo "vLLM Setup Complete!"
echo "=========================================="
echo ""
echo "vLLM is now running on port 8000"
echo ""
echo "To use vLLM in ChatMRPT, set these environment variables:"
echo "  export USE_VLLM=true"
echo "  export VLLM_BASE_URL=http://localhost:8000"
echo "  export VLLM_MODEL=Qwen/Qwen2.5-7B-Instruct"
echo ""
echo "Or if vLLM is on a separate instance:"
echo "  export VLLM_BASE_URL=http://<gpu-instance-ip>:8000"
echo ""
echo "The model will download on first run (may take 10-15 minutes)"