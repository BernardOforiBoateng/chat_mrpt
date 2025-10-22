#!/bin/bash
# vLLM Arena Setup Script for 5 Models
# Updated with Qwen 3 (not 2.5) and all required models

set -e

echo "================================================"
echo "  vLLM Arena Setup - 5 Models for ChatMRPT"
echo "================================================"

# Configuration - Using current AWS infrastructure
INSTANCE_TYPE="g5.4xlarge"  # 1x A10G (24GB) with 16 vCPUs, 64GB RAM
AMI_ID="ami-0c02fb55731490381"  # Deep Learning AMI
KEY_NAME="chatmrpt-key"
SECURITY_GROUP="sg-existing"  # Use your existing security group
SUBNET_ID="subnet-existing"  # Use your existing subnet
HF_TOKEN="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"

echo "IMPORTANT: You may need to increase to g5.12xlarge (4x A10G) for all 5 models"
echo "Current selection: ${INSTANCE_TYPE}"
read -p "Continue with this instance type? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please edit INSTANCE_TYPE in the script and re-run"
    exit 1
fi

# Create the Python vLLM server script that will run all 5 models
cat > vllm_arena_server.py << 'EOF'
#!/usr/bin/env python3
"""
vLLM Arena Server - Serves 5 models for blind A/B testing
Uses model multiplexing to fit all models in 24GB GPU memory
"""
import os
import asyncio
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from vllm import AsyncLLMEngine, AsyncEngineArgs, SamplingParams
import torch
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set HF token
os.environ["HF_TOKEN"] = "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"

# Model configurations for all 5 models
MODELS_CONFIG = {
    'llama-3.1-8b': {
        'model': 'meta-llama/Meta-Llama-3.1-8B-Instruct',
        'max_model_len': 4096,  # Reduced for memory
        'gpu_memory_utilization': 0.18,  # ~4.3GB per model
    },
    'mistral-7b': {
        'model': 'mistralai/Mistral-7B-Instruct-v0.3',
        'max_model_len': 4096,
        'gpu_memory_utilization': 0.18,
    },
    'qwen-3-8b': {
        'model': 'Qwen/Qwen3-8B-Instruct',  # Qwen 3, NOT Qwen 2.5
        'max_model_len': 8192,  # Qwen 3 supports longer context
        'gpu_memory_utilization': 0.18,
    },
    'biomistral-7b': {
        'model': 'BioMistral/BioMistral-7B',
        'max_model_len': 4096,
        'gpu_memory_utilization': 0.18,
    },
    'gemma-2-9b': {
        'model': 'google/gemma-2-9b-it',
        'max_model_len': 4096,
        'gpu_memory_utilization': 0.18,
    }
}

app = FastAPI(title="ChatMRPT Arena vLLM Server")

# Global engine storage (loaded one at a time)
current_engine = None
current_model = None
engines_cache = {}

class ChatRequest(BaseModel):
    model: str
    messages: List[Dict[str, str]]
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.95

class CompletionRequest(BaseModel):
    model: str
    prompt: str
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.95

async def load_model(model_name: str):
    """Load a model, unloading the current one if necessary"""
    global current_engine, current_model
    
    if current_model == model_name and current_engine:
        return current_engine
    
    logger.info(f"Loading model: {model_name}")
    
    # Unload current model to free memory
    if current_engine:
        logger.info(f"Unloading model: {current_model}")
        del current_engine
        torch.cuda.empty_cache()
        current_engine = None
    
    # Load new model
    config = MODELS_CONFIG[model_name]
    engine_args = AsyncEngineArgs(
        model=config['model'],
        max_model_len=config['max_model_len'],
        gpu_memory_utilization=config['gpu_memory_utilization'],
        trust_remote_code=True,
        download_dir="/opt/models",
        tensor_parallel_size=1,
        dtype="float16",  # Use FP16 for memory efficiency
    )
    
    current_engine = AsyncLLMEngine.from_engine_args(engine_args)
    current_model = model_name
    logger.info(f"Successfully loaded: {model_name}")
    
    return current_engine

@app.get("/")
async def root():
    return {
        "service": "ChatMRPT Arena vLLM Server",
        "models": list(MODELS_CONFIG.keys()),
        "total_models": len(MODELS_CONFIG),
        "current_loaded": current_model
    }

@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": model_name,
                "object": "model",
                "owned_by": "arena",
                "loaded": model_name == current_model
            }
            for model_name in MODELS_CONFIG.keys()
        ]
    }

@app.post("/v1/chat/completions")
async def chat_completion(request: ChatRequest):
    if request.model not in MODELS_CONFIG:
        raise HTTPException(status_code=404, detail=f"Model {request.model} not found")
    
    # Load the requested model
    engine = await load_model(request.model)
    
    # Format messages into prompt
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
    prompt += "Assistant:"
    
    # Generate response
    sampling_params = SamplingParams(
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        top_p=request.top_p,
    )
    
    request_id = f"{request.model}-{asyncio.get_event_loop().time()}"
    results = await engine.generate(prompt, sampling_params, request_id)
    
    output_text = results.outputs[0].text
    
    return JSONResponse({
        "id": request_id,
        "object": "chat.completion",
        "model": request.model,
        "choices": [{
            "message": {
                "role": "assistant",
                "content": output_text
            },
            "finish_reason": "stop",
            "index": 0
        }],
        "usage": {
            "prompt_tokens": len(prompt.split()),
            "completion_tokens": len(output_text.split()),
            "total_tokens": len(prompt.split()) + len(output_text.split())
        }
    })

@app.post("/v1/completions")
async def completion(request: CompletionRequest):
    if request.model not in MODELS_CONFIG:
        raise HTTPException(status_code=404, detail=f"Model {request.model} not found")
    
    # Load the requested model
    engine = await load_model(request.model)
    
    # Generate response
    sampling_params = SamplingParams(
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        top_p=request.top_p,
    )
    
    request_id = f"{request.model}-{asyncio.get_event_loop().time()}"
    results = await engine.generate(request.prompt, sampling_params, request_id)
    
    output_text = results.outputs[0].text
    
    return JSONResponse({
        "id": request_id,
        "object": "text_completion",
        "model": request.model,
        "choices": [{
            "text": output_text,
            "finish_reason": "stop",
            "index": 0
        }],
        "usage": {
            "prompt_tokens": len(request.prompt.split()),
            "completion_tokens": len(output_text.split()),
            "total_tokens": len(request.prompt.split()) + len(output_text.split())
        }
    })

@app.post("/v1/arena/get_all_responses")
async def get_all_arena_responses(data: dict):
    """Get responses from all 5 models for Arena comparison"""
    message = data.get("message", "")
    responses = {}
    
    for model_name in MODELS_CONFIG.keys():
        try:
            # Load and generate from each model
            engine = await load_model(model_name)
            
            sampling_params = SamplingParams(
                temperature=0.7,
                max_tokens=2048,
                top_p=0.95,
            )
            
            request_id = f"arena-{model_name}-{asyncio.get_event_loop().time()}"
            results = await engine.generate(f"User: {message}\nAssistant:", sampling_params, request_id)
            
            responses[model_name] = {
                "content": results.outputs[0].text,
                "model": model_name
            }
            
        except Exception as e:
            logger.error(f"Error generating from {model_name}: {e}")
            responses[model_name] = {
                "content": f"Error: Failed to generate response from {model_name}",
                "model": model_name
            }
    
    return JSONResponse({
        "success": True,
        "responses": responses
    })

if __name__ == "__main__":
    # Pre-download all models on first run
    print("Downloading all 5 models (this will take 30-60 minutes)...")
    from huggingface_hub import snapshot_download
    
    for model_name, config in MODELS_CONFIG.items():
        print(f"Downloading {model_name}: {config['model']}")
        snapshot_download(
            config['model'],
            cache_dir="/opt/models",
            token=os.environ.get("HF_TOKEN")
        )
    
    print("All models downloaded! Starting server...")
    
    # Start the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

# Create setup script for EC2 instance
cat > ec2_setup.sh << 'EOF'
#!/bin/bash
# EC2 instance setup script

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python 3.10 and dependencies
sudo apt-get install -y python3.10 python3.10-venv python3-pip

# Create virtual environment
python3.10 -m venv /home/ubuntu/vllm_env
source /home/ubuntu/vllm_env/bin/activate

# Install PyTorch and vLLM
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install vllm==0.5.0
pip install fastapi uvicorn[standard] pydantic huggingface-hub

# Create models directory
mkdir -p /opt/models
sudo chown ubuntu:ubuntu /opt/models

# Copy the server script
cp vllm_arena_server.py /home/ubuntu/

# Create systemd service
sudo cat > /etc/systemd/system/vllm-arena.service << 'INNER_EOF'
[Unit]
Description=vLLM Arena Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu
Environment="PATH=/home/ubuntu/vllm_env/bin:$PATH"
Environment="HF_TOKEN=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"
ExecStart=/home/ubuntu/vllm_env/bin/python /home/ubuntu/vllm_arena_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
INNER_EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable vllm-arena
sudo systemctl start vllm-arena

echo "Setup complete! Check status with: sudo systemctl status vllm-arena"
EOF

chmod +x ec2_setup.sh

echo "================================================"
echo "Setup Scripts Created!"
echo "================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Launch a GPU instance (g5.4xlarge recommended):"
echo "   - Use existing AWS infrastructure"
echo "   - Security group must allow port 8000"
echo ""
echo "2. Copy files to the instance:"
echo "   scp -i ~/.ssh/chatmrpt-key.pem vllm_arena_server.py ec2-user@<PUBLIC_IP>:~/"
echo "   scp -i ~/.ssh/chatmrpt-key.pem ec2_setup.sh ec2-user@<PUBLIC_IP>:~/"
echo ""
echo "3. SSH to instance and run setup:"
echo "   ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@<PUBLIC_IP>"
echo "   chmod +x ec2_setup.sh"
echo "   ./ec2_setup.sh"
echo ""
echo "4. Update your .env file:"
echo "   VLLM_BASE_URL=http://<PUBLIC_IP>:8000"
echo "   USE_ARENA=true"
echo "   ARENA_MODE=enabled"
echo ""
echo "Models included:"
echo "1. Llama 3.1 8B - General purpose"
echo "2. Mistral 7B v0.3 - Fast inference"
echo "3. Qwen 3 8B - 131K context, multilingual (NOT Qwen 2.5)"
echo "4. BioMistral 7B - Medical expertise"
echo "5. Gemma 2 9B - Google quality"
echo ""
echo "NOTE: The server uses model swapping to fit all 5 models"
echo "in 24GB GPU memory. Only one model is loaded at a time."
echo "For simultaneous loading, upgrade to g5.12xlarge (4x GPUs)."