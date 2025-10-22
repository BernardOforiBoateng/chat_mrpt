#!/bin/bash
# Script to check GPU instance status and download all 5 models

set -e

echo "================================================"
echo "  ChatMRPT Arena - Model Status & Download"
echo "================================================"

# Configuration
GPU_IP="172.31.45.157"
SSH_KEY="~/.ssh/chatmrpt-key.pem"
HF_TOKEN="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"

# Copy key to temp location for WSL
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key.pem
chmod 600 /tmp/chatmrpt-key.pem
SSH_KEY="/tmp/chatmrpt-key.pem"

echo "Step 1: Checking GPU instance connectivity..."
echo "Testing connection to ${GPU_IP}..."

# Test connection
if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -i ${SSH_KEY} ec2-user@${GPU_IP} "echo 'Connected successfully'" 2>/dev/null; then
    echo "✅ Connected to GPU instance"
else
    echo "❌ Cannot connect to GPU instance at ${GPU_IP}"
    echo "Please ensure the instance is running and security group allows SSH (port 22)"
    exit 1
fi

echo ""
echo "Step 2: Checking GPU status..."
ssh -i ${SSH_KEY} ec2-user@${GPU_IP} << 'EOF'
echo "GPU Information:"
nvidia-smi --query-gpu=name,memory.total,memory.free,memory.used --format=csv
echo ""
echo "CUDA Version:"
nvidia-smi | grep "CUDA Version"
EOF

echo ""
echo "Step 3: Checking existing models..."
ssh -i ${SSH_KEY} ec2-user@${GPU_IP} << 'EOF'
echo "Checking /opt/models directory..."
if [ -d /opt/models ]; then
    echo "Models directory exists. Contents:"
    du -sh /opt/models/* 2>/dev/null || echo "No models downloaded yet"
else
    echo "Models directory does not exist. Creating it..."
    sudo mkdir -p /opt/models
    sudo chown ec2-user:ec2-user /opt/models
fi
EOF

echo ""
echo "Step 4: Setting up Python environment and downloading models..."

# Create the download script on the remote server
cat << 'DOWNLOAD_SCRIPT' | ssh -i ${SSH_KEY} ec2-user@${GPU_IP} 'cat > ~/download_arena_models.py'
#!/usr/bin/env python3
"""
Download all 5 models for ChatMRPT Arena
"""
import os
import sys
from pathlib import Path
from huggingface_hub import snapshot_download, hf_hub_download
import subprocess

# Set HF token
os.environ["HF_TOKEN"] = "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"

# Models to download
MODELS = [
    {
        "name": "llama-3.1-8b",
        "repo": "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "path": "/opt/models/llama-3.1-8b"
    },
    {
        "name": "mistral-7b",
        "repo": "mistralai/Mistral-7B-Instruct-v0.3",
        "path": "/opt/models/mistral-7b"
    },
    {
        "name": "qwen-3-8b",
        "repo": "Qwen/Qwen3-8B-Instruct",  # Qwen 3, NOT Qwen 2.5
        "path": "/opt/models/qwen-3-8b"
    },
    {
        "name": "biomistral-7b",
        "repo": "BioMistral/BioMistral-7B",
        "path": "/opt/models/biomistral-7b"
    },
    {
        "name": "gemma-2-9b",
        "repo": "google/gemma-2-9b-it",
        "path": "/opt/models/gemma-2-9b"
    }
]

def check_model_exists(path):
    """Check if model is already downloaded"""
    model_path = Path(path)
    if model_path.exists():
        # Check if it has actual model files
        has_safetensors = any(model_path.glob("*.safetensors"))
        has_bin = any(model_path.glob("*.bin"))
        has_config = (model_path / "config.json").exists()
        
        if has_config and (has_safetensors or has_bin):
            # Get size
            total_size = sum(f.stat().st_size for f in model_path.rglob('*') if f.is_file())
            size_gb = total_size / (1024**3)
            return True, f"{size_gb:.2f}GB"
    return False, "0GB"

def download_model(model_info):
    """Download a single model"""
    exists, size = check_model_exists(model_info["path"])
    
    if exists:
        print(f"✅ {model_info['name']} already downloaded ({size})")
        return True
    
    print(f"📥 Downloading {model_info['name']} from {model_info['repo']}...")
    print(f"   Target: {model_info['path']}")
    
    try:
        # Create directory
        Path(model_info["path"]).mkdir(parents=True, exist_ok=True)
        
        # Download using snapshot_download
        snapshot_download(
            repo_id=model_info["repo"],
            local_dir=model_info["path"],
            local_dir_use_symlinks=False,
            token=os.environ.get("HF_TOKEN"),
            resume_download=True,
            max_workers=4
        )
        
        # Check download success
        exists, size = check_model_exists(model_info["path"])
        if exists:
            print(f"✅ {model_info['name']} downloaded successfully ({size})")
            return True
        else:
            print(f"❌ {model_info['name']} download may have failed")
            return False
            
    except Exception as e:
        print(f"❌ Error downloading {model_info['name']}: {e}")
        return False

def main():
    print("=" * 60)
    print("ChatMRPT Arena - Model Download Manager")
    print("=" * 60)
    print()
    
    # Check Python version
    print(f"Python version: {sys.version}")
    print()
    
    # Check if huggingface-hub is installed
    try:
        import huggingface_hub
        print(f"✅ huggingface-hub version: {huggingface_hub.__version__}")
    except ImportError:
        print("Installing huggingface-hub...")
        subprocess.run([sys.executable, "-m", "pip", "install", "huggingface-hub"])
        import huggingface_hub
    
    print()
    print("Models to manage:")
    print("-" * 40)
    for i, model in enumerate(MODELS, 1):
        exists, size = check_model_exists(model["path"])
        status = f"✅ Downloaded ({size})" if exists else "❌ Not downloaded"
        print(f"{i}. {model['name']}: {status}")
    
    print()
    print("Starting download process...")
    print("-" * 40)
    
    success_count = 0
    failed = []
    
    for model in MODELS:
        if download_model(model):
            success_count += 1
        else:
            failed.append(model["name"])
    
    print()
    print("=" * 60)
    print("Download Summary:")
    print(f"✅ Successfully downloaded/verified: {success_count}/{len(MODELS)}")
    if failed:
        print(f"❌ Failed: {', '.join(failed)}")
        print("\nTo retry failed downloads, run this script again.")
    else:
        print("\n🎉 All models ready for Arena!")
    
    # Show disk usage
    print()
    print("Disk usage:")
    os.system("df -h /opt/models")
    print()
    print("Model sizes:")
    os.system("du -sh /opt/models/*")

if __name__ == "__main__":
    main()
DOWNLOAD_SCRIPT

echo ""
echo "Step 5: Installing dependencies and running download..."
ssh -i ${SSH_KEY} ec2-user@${GPU_IP} << 'EOF'
# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Installing Python 3..."
    sudo yum install -y python3 python3-pip || sudo apt-get install -y python3 python3-pip
fi

# Install huggingface-hub if not already installed
echo "Installing huggingface-hub..."
pip3 install --user huggingface-hub tqdm

# Make script executable
chmod +x ~/download_arena_models.py

# Run the download script
echo ""
echo "Starting model downloads (this may take 30-60 minutes)..."
python3 ~/download_arena_models.py
EOF

echo ""
echo "Step 6: Setting up vLLM server..."
ssh -i ${SSH_KEY} ec2-user@${GPU_IP} << 'EOF'
# Check if vLLM is installed
if python3 -c "import vllm" 2>/dev/null; then
    echo "✅ vLLM is already installed"
else
    echo "Installing vLLM..."
    pip3 install --user vllm torch transformers accelerate
fi

# Create a simple test script
cat > ~/test_vllm.py << 'SCRIPT'
#!/usr/bin/env python3
import sys
print(f"Python: {sys.version}")

try:
    import vllm
    print(f"✅ vLLM version: {vllm.__version__ if hasattr(vllm, '__version__') else 'installed'}")
except ImportError:
    print("❌ vLLM not found")

try:
    import torch
    print(f"✅ PyTorch version: {torch.__version__}")
    print(f"✅ CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"✅ CUDA version: {torch.version.cuda}")
        print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
except ImportError:
    print("❌ PyTorch not found")
SCRIPT

python3 ~/test_vllm.py
EOF

echo ""
echo "================================================"
echo "  Setup Status Summary"
echo "================================================"
echo ""
echo "✅ GPU instance is accessible at ${GPU_IP}"
echo "✅ Model download script deployed"
echo ""
echo "Next steps:"
echo "1. Models are downloading in the background"
echo "2. Monitor progress: ssh -i ${SSH_KEY} ec2-user@${GPU_IP} 'tail -f ~/download_arena_models.log'"
echo "3. Once complete, start vLLM server"
echo ""
echo "To manually check model status:"
echo "ssh -i ${SSH_KEY} ec2-user@${GPU_IP} 'python3 ~/download_arena_models.py'"