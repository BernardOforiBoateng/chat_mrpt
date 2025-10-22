#!/bin/bash

# Enhanced vLLM Setup for ChatMRPT Arena Mode
# Supports multiple models running simultaneously for Arena comparison

set -e

echo "================================================"
echo "  vLLM Multi-Model Setup for ChatMRPT Arena"
echo "================================================"

# Configuration
REGION="us-east-2"
KEY_FILE="aws_files/chatmrpt-key.pem"

# Check if we have a GPU instance running
echo "Checking for existing GPU instances..."
GPU_INSTANCE=$(aws ec2 describe-instances \
    --filters "Name=tag:Purpose,Values=vLLM" "Name=instance-state-name,Values=running" \
    --region $REGION \
    --query 'Reservations[0].Instances[0].[InstanceId,PublicIpAddress,InstanceType]' \
    --output text 2>/dev/null || echo "")

if [ -z "$GPU_INSTANCE" ]; then
    echo "No GPU instance found. Launching new g4dn.xlarge instance..."
    ./launch_gpu_instance.sh
    
    # Get the new instance details
    sleep 10
    GPU_INSTANCE=$(aws ec2 describe-instances \
        --filters "Name=tag:Purpose,Values=vLLM" "Name=instance-state-name,Values=running" \
        --region $REGION \
        --query 'Reservations[0].Instances[0].[InstanceId,PublicIpAddress,InstanceType]' \
        --output text)
fi

INSTANCE_ID=$(echo $GPU_INSTANCE | awk '{print $1}')
PUBLIC_IP=$(echo $GPU_INSTANCE | awk '{print $2}')
INSTANCE_TYPE=$(echo $GPU_INSTANCE | awk '{print $3}')

echo "Using GPU Instance:"
echo "  ID: $INSTANCE_ID"
echo "  IP: $PUBLIC_IP"
echo "  Type: $INSTANCE_TYPE"

# Create the multi-model vLLM setup script
cat > vllm_multi_model_setup.sh << 'EOF'
#!/bin/bash

set -e

echo "Setting up vLLM with multiple models for Arena mode..."

# Update system
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3-pip git jq nginx

# Create vLLM environment
if [ ! -d "/home/ubuntu/vllm_env" ]; then
    python3.11 -m venv /home/ubuntu/vllm_env
fi

source /home/ubuntu/vllm_env/bin/activate

# Install vLLM and dependencies
pip install --upgrade pip
pip install vllm torch transformers accelerate huggingface_hub

# Create model directories
sudo mkdir -p /opt/models
sudo chown ubuntu:ubuntu /opt/models

# Download models (if not already present)
echo "Downloading models (this may take time)..."

# Function to download model
download_model() {
    local model_name=$1
    local model_path=$2
    local model_dir=$3
    
    if [ ! -d "/opt/models/$model_dir" ]; then
        echo "Downloading $model_name..."
        huggingface-cli download $model_path \
            --local-dir /opt/models/$model_dir \
            --local-dir-use-symlinks False \
            || echo "Failed to download $model_name, will try again later"
    else
        echo "$model_name already downloaded"
    fi
}

# Download each model
download_model "Llama 3.1 8B" "meta-llama/Llama-3.1-8B-Instruct" "llama-3.1-8b"
download_model "Mistral 7B" "mistralai/Mistral-7B-Instruct-v0.3" "mistral-7b"
download_model "Qwen 2.5 7B" "Qwen/Qwen2.5-7B-Instruct" "qwen-2.5-7b"

# Create a model manager script
cat > /home/ubuntu/vllm_model_manager.py << 'SCRIPT'
#!/usr/bin/env python3
"""
vLLM Model Manager for Arena Mode
Manages multiple models with dynamic loading
"""

import os
import sys
import json
import asyncio
import uvicorn
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from vllm import AsyncLLMEngine, AsyncEngineArgs, SamplingParams
from vllm.entrypoints.openai.protocol import ChatCompletionRequest
import torch

# Check GPU availability
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")

app = FastAPI(title="vLLM Arena Model Server")

# Model configurations
MODEL_CONFIGS = {
    "llama-3.1-8b": {
        "path": "/opt/models/llama-3.1-8b",
        "max_model_len": 4096,
        "gpu_memory_utilization": 0.3
    },
    "mistral-7b": {
        "path": "/opt/models/mistral-7b",
        "max_model_len": 4096,
        "gpu_memory_utilization": 0.3
    },
    "qwen-2.5-7b": {
        "path": "/opt/models/qwen-2.5-7b",
        "max_model_len": 4096,
        "gpu_memory_utilization": 0.3
    }
}

# Global engine storage
engines: Dict[str, AsyncLLMEngine] = {}
current_model: Optional[str] = None

class ModelLoadRequest(BaseModel):
    model_name: str

class ChatRequest(BaseModel):
    model: str
    messages: List[Dict[str, str]]
    temperature: float = 0.7
    max_tokens: int = 1024
    stream: bool = False

async def load_model(model_name: str) -> AsyncLLMEngine:
    """Load a model into memory"""
    global engines, current_model
    
    if model_name in engines:
        return engines[model_name]
    
    if model_name not in MODEL_CONFIGS:
        raise ValueError(f"Unknown model: {model_name}")
    
    config = MODEL_CONFIGS[model_name]
    
    # If we're at capacity, unload the least recently used model
    if len(engines) >= 2:  # Max 2 models in memory
        oldest = list(engines.keys())[0]
        print(f"Unloading {oldest} to make room...")
        del engines[oldest]
        torch.cuda.empty_cache()
    
    print(f"Loading {model_name}...")
    
    engine_args = AsyncEngineArgs(
        model=config["path"],
        max_model_len=config["max_model_len"],
        gpu_memory_utilization=config["gpu_memory_utilization"],
        trust_remote_code=True,
    )
    
    engine = AsyncLLMEngine.from_engine_args(engine_args)
    engines[model_name] = engine
    current_model = model_name
    
    return engine

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "loaded_models": list(engines.keys()),
        "available_models": list(MODEL_CONFIGS.keys())
    }

@app.get("/v1/models")
async def list_models():
    return {
        "data": [
            {"id": name, "object": "model", "owned_by": "arena"}
            for name in MODEL_CONFIGS.keys()
        ]
    }

@app.post("/v1/chat/completions")
async def chat_completion(request: ChatRequest):
    """OpenAI-compatible chat completion endpoint"""
    
    # Load model if needed
    engine = await load_model(request.model)
    
    # Convert messages to prompt
    prompt = ""
    for msg in request.messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system":
            prompt += f"System: {content}\n"
        elif role == "user":
            prompt += f"User: {content}\n"
        elif role == "assistant":
            prompt += f"Assistant: {content}\n"
    prompt += "Assistant: "
    
    # Set sampling parameters
    sampling_params = SamplingParams(
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )
    
    # Generate
    request_id = f"arena-{request.model}-{hash(prompt)}"
    
    if request.stream:
        # Streaming response
        async def generate():
            async for output in engine.generate(prompt, sampling_params, request_id):
                if output.outputs[0].text:
                    chunk = {
                        "choices": [{
                            "delta": {"content": output.outputs[0].text},
                            "index": 0
                        }]
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(generate(), media_type="text/event-stream")
    else:
        # Non-streaming response
        result = await engine.generate(prompt, sampling_params, request_id)
        
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": result.outputs[0].text
                },
                "index": 0
            }],
            "model": request.model
        }

@app.post("/load_model")
async def load_model_endpoint(request: ModelLoadRequest):
    """Preload a model into memory"""
    try:
        await load_model(request.model_name)
        return {"success": True, "model": request.model_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Preload first model
    asyncio.run(load_model("llama-3.1-8b"))
    
    # Start server
    uvicorn.run(app, host="0.0.0.0", port=8000)
SCRIPT

chmod +x /home/ubuntu/vllm_model_manager.py

# Create systemd service for the model manager
sudo tee /etc/systemd/system/vllm-arena.service > /dev/null << 'SERVICE'
[Unit]
Description=vLLM Arena Model Manager
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu
Environment="PATH=/home/ubuntu/vllm_env/bin:/usr/local/bin:/usr/bin:/bin"
Environment="CUDA_VISIBLE_DEVICES=0"
ExecStart=/home/ubuntu/vllm_env/bin/python /home/ubuntu/vllm_model_manager.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

# Configure nginx as reverse proxy for multiple model endpoints
sudo tee /etc/nginx/sites-available/vllm-arena > /dev/null << 'NGINX'
server {
    listen 8000;
    server_name _;
    
    client_max_body_size 100M;
    client_body_timeout 300s;
    
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for streaming
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
NGINX

sudo ln -sf /etc/nginx/sites-available/vllm-arena /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

# Start the vLLM service
sudo systemctl daemon-reload
sudo systemctl enable vllm-arena
sudo systemctl restart vllm-arena

# Create test script
cat > /home/ubuntu/test_vllm.py << 'TEST'
#!/usr/bin/env python3
import requests
import json
import time

def test_model(model_name):
    """Test a specific model"""
    print(f"\nTesting {model_name}...")
    
    url = "http://localhost:8000/v1/chat/completions"
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": "What is malaria and how is it transmitted?"}
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    start = time.time()
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        content = result['choices'][0]['message']['content']
        elapsed = time.time() - start
        
        print(f"✓ {model_name} responded in {elapsed:.2f}s")
        print(f"Response preview: {content[:100]}...")
        return True
    except Exception as e:
        print(f"✗ {model_name} failed: {e}")
        return False

# Test health endpoint
print("Testing health endpoint...")
response = requests.get("http://localhost:8000/health")
print(f"Health: {response.json()}")

# Test each model
models = ["llama-3.1-8b", "mistral-7b", "qwen-2.5-7b"]
for model in models:
    test_model(model)
    time.sleep(2)  # Give time between tests

print("\n✓ All tests complete!")
TEST

chmod +x /home/ubuntu/test_vllm.py

echo ""
echo "================================================"
echo "vLLM Multi-Model Setup Complete!"
echo "================================================"
echo ""
echo "Testing the setup..."
python3 /home/ubuntu/test_vllm.py

echo ""
echo "Service Status:"
sudo systemctl status vllm-arena --no-pager

echo ""
echo "Available at: http://$(curl -s ifconfig.me):8000"
echo "View logs: sudo journalctl -u vllm-arena -f"
EOF

# Copy and execute the setup script
echo ""
echo "Copying setup script to GPU instance..."
scp -i $KEY_FILE -o StrictHostKeyChecking=no vllm_multi_model_setup.sh ubuntu@${PUBLIC_IP}:~/

echo "Executing setup (this will take 10-20 minutes)..."
ssh -i $KEY_FILE -o StrictHostKeyChecking=no ubuntu@${PUBLIC_IP} 'chmod +x vllm_multi_model_setup.sh && ./vllm_multi_model_setup.sh'

# Create local environment file update
cat > .env.vllm << EOF
# vLLM Configuration for Arena Mode
VLLM_BASE_URL=http://${PUBLIC_IP}:8000
USE_VLLM=true
VLLM_MODELS=llama-3.1-8b,mistral-7b,qwen-2.5-7b

# Arena Configuration
ARENA_MODE_ENABLED=true
ARENA_DEFAULT_MODELS=llama-3.1-8b,mistral-7b
EOF

echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "vLLM Multi-Model Server: http://${PUBLIC_IP}:8000"
echo ""
echo "Next Steps:"
echo "1. Update your .env file with contents from .env.vllm"
echo "2. Test the endpoints:"
echo "   curl http://${PUBLIC_IP}:8000/health"
echo "   curl http://${PUBLIC_IP}:8000/v1/models"
echo ""
echo "3. Deploy Arena mode to staging:"
echo "   ./deployment/deploy_to_staging.sh"
echo ""
echo "GPU Instance Details:"
echo "  ID: $INSTANCE_ID"
echo "  IP: $PUBLIC_IP"
echo "  SSH: ssh -i $KEY_FILE ubuntu@${PUBLIC_IP}"