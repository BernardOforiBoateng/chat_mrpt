#!/bin/bash

# Fix VLLM Tool Calling for Llama 3.1
# This script updates the VLLM server configuration to enable tool calling

echo "============================================"
echo "Fixing VLLM Tool Calling for Data Analysis V3"
echo "============================================"
echo ""

# Configuration
GPU_IP="172.31.45.157"
KEY_PATH="aws_files/chatmrpt-key.pem"

# Ensure key has correct permissions
chmod 600 $KEY_PATH

echo "📡 Connecting to GPU instance at $GPU_IP..."
echo ""

# Step 1: Check current VLLM status
echo "Step 1: Checking current VLLM status..."
ssh -i $KEY_PATH -o StrictHostKeyChecking=no ec2-user@$GPU_IP << 'EOF'
echo "Current VLLM service status:"
sudo systemctl status vllm | head -15
echo ""
echo "Current start script:"
cat /home/ec2-user/start_vllm.sh
echo ""
echo "Checking if Llama model is downloaded:"
ls -la /home/ec2-user/.cache/huggingface/hub/ | grep -i llama || echo "Llama model not found in cache"
EOF

echo ""
echo "Step 2: Creating updated VLLM startup script with tool calling flags..."

# Step 2: Create new startup script with tool calling flags
ssh -i $KEY_PATH -o StrictHostKeyChecking=no ec2-user@$GPU_IP << 'EOF'
# Backup current script
cp /home/ec2-user/start_vllm.sh /home/ec2-user/start_vllm.sh.backup.$(date +%Y%m%d_%H%M%S)

# Create new script with tool calling flags
cat > /home/ec2-user/start_vllm.sh << 'SCRIPT'
#!/bin/bash
source /home/ec2-user/vllm_env/bin/activate

# Start vLLM server with Llama 3.1 and TOOL CALLING SUPPORT
echo "Starting vLLM with Llama 3.1 8B Instruct (with tool calling)..."
export HF_TOKEN="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"

python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Meta-Llama-3.1-8B-Instruct \
    --port 8000 \
    --host 0.0.0.0 \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.90 \
    --dtype auto \
    --trust-remote-code \
    --enable-auto-tool-choice \
    --tool-call-parser llama3_json \
    --disable-log-requests
SCRIPT

chmod +x /home/ec2-user/start_vllm.sh
echo "✅ Updated startup script created"
EOF

echo ""
echo "Step 3: Restarting VLLM service with new configuration..."

# Step 3: Restart VLLM service
ssh -i $KEY_PATH -o StrictHostKeyChecking=no ec2-user@$GPU_IP << 'EOF'
echo "Stopping current VLLM service..."
sudo systemctl stop vllm
sleep 3

echo "Starting VLLM with new configuration..."
sudo systemctl start vllm
sleep 10

echo "Checking new service status..."
sudo systemctl status vllm | head -15
EOF

echo ""
echo "Step 4: Testing VLLM endpoint..."

# Step 4: Test the endpoint
ssh -i $KEY_PATH -o StrictHostKeyChecking=no ec2-user@$GPU_IP << 'EOF'
echo "Waiting for service to be ready..."
sleep 5

echo "Testing /v1/models endpoint:"
curl -s http://localhost:8000/v1/models | python3 -m json.tool || echo "Service may still be starting..."

echo ""
echo "Testing health endpoint:"
curl -s http://localhost:8000/health || echo "No health endpoint"

echo ""
echo "Checking if tool calling parameters are accepted:"
curl -s -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Meta-Llama-3.1-8B-Instruct",
    "messages": [{"role": "user", "content": "Hi"}],
    "tools": [{"type": "function", "function": {"name": "test", "description": "Test function", "parameters": {"type": "object", "properties": {}}}}],
    "tool_choice": "auto",
    "max_tokens": 50
  }' | python3 -m json.tool | head -20 || echo "Tool calling test failed"
EOF

echo ""
echo "============================================"
echo "VLLM Tool Calling Fix Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Update .env files on staging instances"
echo "2. Test Data Analysis V3 with uploaded data"
echo ""
echo "To check logs if needed:"
echo "ssh -i $KEY_PATH ec2-user@$GPU_IP 'sudo journalctl -u vllm -f'"