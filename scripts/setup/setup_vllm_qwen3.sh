#!/bin/bash

# Setup vLLM with Qwen 3 Models
echo "=========================================="
echo "vLLM Setup with Qwen 3 Models"
echo "=========================================="

# Check GPU availability and memory
echo "Checking GPU resources..."
if ! command -v nvidia-smi &> /dev/null; then
    echo "❌ No GPU detected. This script requires a GPU instance."
    exit 1
fi

# Get GPU memory in GB
GPU_MEMORY=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
GPU_MEMORY_GB=$((GPU_MEMORY / 1024))
GPU_COUNT=$(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l)

echo "Detected: $GPU_COUNT GPU(s) with ${GPU_MEMORY_GB}GB memory each"
TOTAL_MEMORY=$((GPU_MEMORY_GB * GPU_COUNT))
echo "Total GPU memory: ${TOTAL_MEMORY}GB"

# Select appropriate Qwen 3 model based on available memory
if [ $TOTAL_MEMORY -ge 200 ]; then
    MODEL="Qwen/Qwen3-235B-A22B"  # MoE model, needs 200GB+
    echo "✅ Using Qwen3-235B-A22B (Best model, MoE with 22B active params)"
    TENSOR_PARALLEL=$GPU_COUNT
elif [ $TOTAL_MEMORY -ge 96 ]; then
    MODEL="Qwen/Qwen3-32B"  # Dense model, needs ~64GB
    echo "✅ Using Qwen3-32B (High quality dense model)"
    TENSOR_PARALLEL=$((GPU_COUNT > 2 ? 2 : GPU_COUNT))
elif [ $TOTAL_MEMORY -ge 48 ]; then
    MODEL="Qwen/Qwen3-14B"  # Medium model
    echo "✅ Using Qwen3-14B (Balanced performance)"
    TENSOR_PARALLEL=1
elif [ $TOTAL_MEMORY -ge 24 ]; then
    MODEL="Qwen/Qwen3-8B"  # Smaller but still powerful
    echo "✅ Using Qwen3-8B (Efficient model)"
    TENSOR_PARALLEL=1
else
    MODEL="Qwen/Qwen3-4B"  # Smallest Qwen 3
    echo "⚠️ Using Qwen3-4B (Limited GPU memory)"
    TENSOR_PARALLEL=1
fi

# Install vLLM if not already installed
echo ""
echo "Setting up vLLM environment..."
if [ ! -d "vllm_env" ]; then
    python3 -m venv vllm_env
fi
source vllm_env/bin/activate

echo "Installing vLLM and dependencies..."
pip install --upgrade pip
pip install vllm transformers accelerate

# Create start script
echo ""
echo "Creating vLLM start script..."
cat > start_vllm.sh << EOF
#!/bin/bash
source vllm_env/bin/activate

echo "Starting vLLM with $MODEL"
python -m vllm.entrypoints.openai.api_server \\
    --model $MODEL \\
    --port 8000 \\
    --host 0.0.0.0 \\
    --max-model-len 32768 \\
    --gpu-memory-utilization 0.90 \\
    --dtype auto \\
    $([ $TENSOR_PARALLEL -gt 1 ] && echo "--tensor-parallel-size $TENSOR_PARALLEL") \\
    --trust-remote-code
EOF

chmod +x start_vllm.sh

# Create systemd service
echo "Creating systemd service..."
sudo tee /etc/systemd/system/vllm.service > /dev/null << EOF
[Unit]
Description=vLLM Server with Qwen 3
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD
ExecStart=$PWD/start_vllm.sh
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment="CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7"

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
echo ""
echo "Starting vLLM service..."
sudo systemctl daemon-reload
sudo systemctl enable vllm
sudo systemctl start vllm

sleep 5

# Check status
echo ""
echo "Checking service status..."
sudo systemctl status vllm | head -15

# Update ChatMRPT configuration
echo ""
echo "Updating ChatMRPT configuration..."
if [ -f "/home/ec2-user/ChatMRPT/.env" ]; then
    cd /home/ec2-user/ChatMRPT
    
    # Backup .env
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    
    # Update to use vLLM with selected model
    cat >> .env << EOF

# vLLM Configuration (Auto-configured)
USE_VLLM=true
USE_OLLAMA=false
VLLM_MODEL=$MODEL
VLLM_BASE_URL=http://localhost:8000
TPR_USE_LOCAL_MODEL=true
EOF
    
    echo "✅ ChatMRPT configured to use vLLM with $MODEL"
    
    # Restart ChatMRPT if running
    if sudo systemctl is-active --quiet chatmrpt; then
        echo "Restarting ChatMRPT service..."
        sudo systemctl restart chatmrpt
    fi
fi

echo ""
echo "=========================================="
echo "vLLM Setup Complete!"
echo "=========================================="
echo ""
echo "Model: $MODEL"
echo "Endpoint: http://localhost:8000"
echo "Tensor Parallel Size: $TENSOR_PARALLEL"
echo ""
echo "Test with:"
echo "  curl http://localhost:8000/v1/models"
echo ""
echo "Note: Model download may take 10-30 minutes on first run"
echo ""
echo "Qwen 3 Features:"
echo "  - Thinking mode for complex reasoning"
echo "  - 119 language support"
echo "  - 32K native context (up to 131K with YaRN)"
echo "  - MoE efficiency (if using 235B-A22B model)"