#!/bin/bash

# Fix Ollama GPU Configuration Script
# This script configures Ollama to properly use GPU memory on the NVIDIA A10G

echo "========================================="
echo "Ollama GPU Configuration Fix"
echo "========================================="

# Create backup of current service file
echo "1. Backing up current Ollama service file..."
sudo cp /etc/systemd/system/ollama.service /etc/systemd/system/ollama.service.backup.$(date +%Y%m%d_%H%M%S)

# Create new service file with GPU configuration
echo "2. Creating new Ollama service configuration with GPU support..."
cat << 'EOF' | sudo tee /etc/systemd/system/ollama.service
[Unit]
Description=Ollama Service
After=network-online.target

[Service]
ExecStart=/usr/local/bin/ollama serve
User=ollama
Group=ollama
Restart=always
RestartSec=3
Environment="PATH=/usr/local/cuda/bin:/home/ec2-user/.local/bin:/home/ec2-user/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin"
Environment="CUDA_VISIBLE_DEVICES=0"
Environment="LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH"
Environment="OLLAMA_NUM_GPU=999"
Environment="OLLAMA_GPU_LAYERS=999"

[Install]
WantedBy=default.target
EOF

echo "3. Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "4. Restarting Ollama service with GPU configuration..."
sudo systemctl restart ollama

echo "5. Waiting for Ollama to start..."
sleep 5

# Check if Ollama is running
if systemctl is-active --quiet ollama; then
    echo "✅ Ollama service is running"
else
    echo "❌ Ollama service failed to start. Checking logs..."
    sudo journalctl -u ollama -n 20 --no-pager
    exit 1
fi

echo ""
echo "6. Checking Ollama health..."
if curl -s http://localhost:11434/api/version > /dev/null; then
    echo "✅ Ollama API is responding"
else
    echo "❌ Ollama API is not responding"
    exit 1
fi

echo ""
echo "========================================="
echo "GPU Configuration Applied Successfully!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Run nvidia-smi to monitor GPU memory usage"
echo "2. Load models with GPU support"
echo "3. Verify VRAM usage increases as models load"