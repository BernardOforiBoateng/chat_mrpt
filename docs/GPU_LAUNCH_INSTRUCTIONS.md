# Launch GPU Instance - Step by Step Guide

## Quick Launch via AWS Console

### 1. Open AWS EC2 Console
- Go to: https://console.aws.amazon.com/ec2
- Select Region: **us-east-2 (Ohio)**

### 2. Launch Instance
Click "Launch Instance" and use these settings:

#### Name and tags
- **Name**: `ChatMRPT-GPU-Arena`
- **Tag**: `Purpose: vLLM-Arena`

#### AMI (Amazon Machine Image)
- Search for: "Deep Learning Base GPU AMI"
- Select: **Deep Learning Base GPU AMI (Ubuntu 20.04)**
- AMI ID: `ami-0ea1e092d32de89ed`

#### Instance type
- **Type**: `g5.2xlarge`
- Specs: 1 GPU (A10G), 24GB VRAM, 8 vCPUs, 32GB RAM
- Cost: ~$1.21/hour

#### Key pair
- Select: **chatmrpt-key** (existing)

#### Network settings
- **VPC**: Use same as current instances
- **Subnet**: `subnet-0713ee8d5af26578a` (same as Instance 2)
- **Security group**: `launch-wizard-1` (existing)
- **Auto-assign public IP**: Enable

#### Storage
- **Size**: 200 GB
- **Type**: gp3
- **Delete on termination**: Yes

#### Advanced details - User data
Copy and paste this script:

```bash
#!/bin/bash
# GPU Setup Script - Runs automatically on launch

# Log output
exec > >(tee -a /var/log/userdata.log)
exec 2>&1

echo "Starting GPU setup..."
apt-get update && apt-get upgrade -y

# Install Python and CUDA dependencies
apt-get install -y python3.10 python3.10-venv python3-pip git nvidia-cuda-toolkit

# Create venv
python3.10 -m venv /opt/vllm_env
source /opt/vllm_env/bin/activate

# Install PyTorch and vLLM
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install vllm==0.5.0 transformers accelerate huggingface-hub fastapi uvicorn

# Create models directory
mkdir -p /opt/models
chown ubuntu:ubuntu /opt/models

# Set HF token
echo 'export HF_TOKEN="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"' >> /home/ubuntu/.bashrc

# Create download script
cat > /home/ubuntu/download_models.py << 'EOF'
#!/opt/vllm_env/bin/python
import os
from huggingface_hub import snapshot_download

os.environ["HF_TOKEN"] = "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"

models = [
    ("meta-llama/Meta-Llama-3.1-8B-Instruct", "/opt/models/llama-3.1-8b"),
    ("mistralai/Mistral-7B-Instruct-v0.3", "/opt/models/mistral-7b"),
    ("Qwen/Qwen3-8B-Instruct", "/opt/models/qwen-3-8b"),
    ("BioMistral/BioMistral-7B", "/opt/models/biomistral-7b"),
    ("google/gemma-2-9b-it", "/opt/models/gemma-2-9b")
]

print("Downloading 5 models for Arena...")
for repo, path in models:
    print(f"Downloading {repo}...")
    try:
        snapshot_download(repo, local_dir=path, token=os.environ["HF_TOKEN"], resume_download=True)
        print(f"✓ {repo} complete")
    except Exception as e:
        print(f"✗ {repo} failed: {e}")
EOF

chmod +x /home/ubuntu/download_models.py
chown -R ubuntu:ubuntu /home/ubuntu /opt/models

echo "Setup complete! Models ready to download."
```

### 3. Launch the Instance
Click **"Launch instance"**

### 4. Wait for Instance to Start
- Takes 2-3 minutes to launch
- Note down the **Instance ID** and **IPs**

### 5. Connect via SSH
Once running, get the Public IP and connect:
```bash
ssh -i aws_files/chatmrpt-key.pem ubuntu@<PUBLIC_IP>
```

### 6. Download Models (30-60 minutes)
```bash
# Check GPU is working
nvidia-smi

# Activate venv
source /opt/vllm_env/bin/activate

# Download all 5 models
python3 /home/ubuntu/download_models.py
```

### 7. Copy vLLM Server Script
From your local machine:
```bash
scp -i aws_files/chatmrpt-key.pem vllm_arena_server.py ubuntu@<PUBLIC_IP>:~/
```

### 8. Start vLLM Server
```bash
source /opt/vllm_env/bin/activate
python3 ~/vllm_arena_server.py
```

### 9. Update Application Configuration

#### Update .env file:
```
VLLM_BASE_URL=http://<PRIVATE_IP>:8000
USE_ARENA=true
ARENA_MODE=enabled
ARENA_MODELS=llama-3.1-8b,mistral-7b,qwen-3-8b,biomistral-7b,gemma-2-9b
```

#### Update ALB Target Group:
1. Go to EC2 → Target Groups
2. Find your ALB target group
3. Register targets:
   - Add new GPU instance (use Private IP, port 80)
   - Deregister old Instance 2 (18.220.103.20)

### 10. Test Arena Mode
1. Deploy updated code to Instance 1
2. Access ChatMRPT
3. Toggle Arena mode in navigation
4. Test model responses

### 11. Clean Up Old Instance 2
After confirming everything works:
- Terminate Instance 2 (i-0f3b25b72f18a5037)
- This saves ~$35/month

## Cost Summary
- **Before**: ~$100/month (2 CPU instances)
- **After**: ~$942/month (1 CPU + 1 GPU)
- **Increase**: ~$842/month
- **Benefit**: Run 5 models locally, reduce OpenAI API costs

## Troubleshooting

### If models won't download:
```bash
# Check disk space
df -h

# Check HF token
echo $HF_TOKEN

# Try manual download
huggingface-cli download meta-llama/Meta-Llama-3.1-8B-Instruct --local-dir /opt/models/llama-3.1-8b --token $HF_TOKEN
```

### If vLLM won't start:
```bash
# Check GPU memory
nvidia-smi

# Try with single model first
python3 -c "from vllm import LLM; llm = LLM(model='/opt/models/mistral-7b')"
```

### To save costs:
- Stop GPU instance when not in use
- Consider spot instances (70% cheaper but can be interrupted)
- Use g5.xlarge instead (half the price, but need model swapping)