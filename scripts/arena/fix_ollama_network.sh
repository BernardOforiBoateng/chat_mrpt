#!/bin/bash

# Fix Ollama Network Configuration
# Makes Ollama listen on all interfaces instead of just localhost

echo "========================================="
echo "Fixing Ollama Network Configuration"
echo "========================================="

# Backup current service file
echo "1. Backing up current Ollama service file..."
sudo cp /etc/systemd/system/ollama.service /etc/systemd/system/ollama.service.backup.network.$(date +%Y%m%d_%H%M%S)

# Update service file to listen on all interfaces
echo "2. Updating Ollama service to listen on all interfaces..."
sudo tee /etc/systemd/system/ollama.service > /dev/null << 'EOF'
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
Environment="OLLAMA_HOST=0.0.0.0:11434"

[Install]
WantedBy=default.target
EOF

echo "3. Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "4. Restarting Ollama service..."
sudo systemctl restart ollama

echo "5. Waiting for Ollama to start..."
sleep 5

# Check if Ollama is running
if systemctl is-active --quiet ollama; then
    echo "✅ Ollama service is running"
else
    echo "❌ Ollama service failed to start"
    sudo journalctl -u ollama -n 20 --no-pager
    exit 1
fi

# Check listening interface
echo ""
echo "6. Checking network configuration..."
LISTEN_CHECK=$(sudo netstat -tlnp 2>/dev/null | grep 11434)
echo "Listening on: $LISTEN_CHECK"

if echo "$LISTEN_CHECK" | grep -q "0.0.0.0:11434"; then
    echo "✅ Ollama is now listening on all interfaces"
else
    echo "⚠️  Ollama may still be on localhost only"
fi

# Test from localhost
echo ""
echo "7. Testing Ollama API..."
if curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
    echo "✅ Ollama API responding on localhost"
else
    echo "❌ Ollama API not responding"
fi

echo ""
echo "========================================="
echo "Network Configuration Fixed!"
echo "========================================="
echo ""
echo "Ollama should now accept connections from other servers in the VPC"