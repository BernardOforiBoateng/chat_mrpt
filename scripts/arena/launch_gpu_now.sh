#!/bin/bash
# Launch GPU Instance for vLLM Arena (Replace Instance 2)

set -e

echo "================================================"
echo "  Launching GPU Instance for ChatMRPT Arena"
echo "================================================"
echo ""
echo "Instance Type: g5.2xlarge (1x A10G GPU, 24GB VRAM)"
echo "Purpose: Run 5 local models for Arena mode"
echo "Cost: ~$1.21/hour (~$875/month)"
echo ""

# Check for AWS CLI
if ! command -v aws &> /dev/null; then
    echo "ERROR: AWS CLI not found!"
    echo "Please install: pip install awscli"
    echo "Then configure: aws configure"
    exit 1
fi

# Configuration
INSTANCE_TYPE="g5.2xlarge"
AMI_ID="ami-0ea1e092d32de89ed"  # Deep Learning Base GPU AMI (Ubuntu 20.04) in us-east-2
KEY_NAME="chatmrpt-key"
SECURITY_GROUP_NAME="launch-wizard-1"
SUBNET_ID="subnet-0713ee8d5af26578a"
REGION="us-east-2"

echo "Getting security group ID..."
SECURITY_GROUP_ID=$(aws ec2 describe-security-groups \
    --group-names "$SECURITY_GROUP_NAME" \
    --region $REGION \
    --query 'SecurityGroups[0].GroupId' \
    --output text 2>/dev/null || echo "")

if [ -z "$SECURITY_GROUP_ID" ]; then
    echo "ERROR: Security group not found. Using default."
    SECURITY_GROUP_ID="sg-default"
fi

echo "Security Group ID: $SECURITY_GROUP_ID"

# Create user data script
cat > gpu_userdata.sh << 'EOF'
#!/bin/bash
# GPU Instance Setup Script

# Log all output
exec > >(tee -a /var/log/userdata.log)
exec 2>&1

echo "Starting GPU instance setup..."
date

# Update system
apt-get update
apt-get upgrade -y

# Install Python 3.10 and dependencies
apt-get install -y python3.10 python3.10-venv python3-pip git

# Create vLLM environment
python3.10 -m venv /opt/vllm_env
source /opt/vllm_env/bin/activate

# Install PyTorch with CUDA
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install vLLM and dependencies
pip install vllm==0.5.0
pip install transformers accelerate huggingface-hub
pip install fastapi uvicorn[standard]

# Create models directory
mkdir -p /opt/models
chown ubuntu:ubuntu /opt/models

# Set HF token in environment
echo 'export HF_TOKEN="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"' >> /home/ubuntu/.bashrc
echo 'export PATH="/opt/vllm_env/bin:$PATH"' >> /home/ubuntu/.bashrc

# Create model download script
cat > /home/ubuntu/download_models.py << 'SCRIPT'
#!/opt/vllm_env/bin/python
import os
import sys
from huggingface_hub import snapshot_download

os.environ["HF_TOKEN"] = "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"

models = [
    ("meta-llama/Meta-Llama-3.1-8B-Instruct", "/opt/models/llama-3.1-8b"),
    ("mistralai/Mistral-7B-Instruct-v0.3", "/opt/models/mistral-7b"),
    ("Qwen/Qwen3-8B-Instruct", "/opt/models/qwen-3-8b"),
    ("BioMistral/BioMistral-7B", "/opt/models/biomistral-7b"),
    ("google/gemma-2-9b-it", "/opt/models/gemma-2-9b")
]

print("Starting model downloads...")
for repo, path in models:
    print(f"Downloading {repo}...")
    try:
        snapshot_download(repo, local_dir=path, token=os.environ["HF_TOKEN"])
        print(f"✓ {repo} complete")
    except Exception as e:
        print(f"✗ {repo} failed: {e}")

print("Downloads complete!")
SCRIPT

chmod +x /home/ubuntu/download_models.py
chown ubuntu:ubuntu /home/ubuntu/download_models.py

echo "GPU instance setup complete!"
date
EOF

echo ""
echo "Launching GPU instance..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $SECURITY_GROUP_ID \
    --subnet-id $SUBNET_ID \
    --region $REGION \
    --block-device-mappings '[{
        "DeviceName": "/dev/sda1",
        "Ebs": {
            "VolumeSize": 200,
            "VolumeType": "gp3",
            "DeleteOnTermination": true
        }
    }]' \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ChatMRPT-GPU-Arena},{Key=Purpose,Value=vLLM-Arena},{Key=ReplacesInstance2,Value=true}]' \
    --user-data file://gpu_userdata.sh \
    --query 'Instances[0].InstanceId' \
    --output text)

if [ -z "$INSTANCE_ID" ]; then
    echo "ERROR: Failed to launch instance!"
    exit 1
fi

echo "✅ GPU Instance launched: $INSTANCE_ID"
echo ""
echo "Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION

# Get instance details
echo "Getting instance details..."
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --region $REGION \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

PRIVATE_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --region $REGION \
    --query 'Reservations[0].Instances[0].PrivateIpAddress' \
    --output text)

echo ""
echo "================================================"
echo "  GPU INSTANCE LAUNCHED SUCCESSFULLY!"
echo "================================================"
echo ""
echo "Instance ID: $INSTANCE_ID"
echo "Public IP:   $PUBLIC_IP"
echo "Private IP:  $PRIVATE_IP"
echo "Type:        g5.2xlarge (24GB GPU)"
echo ""
echo "NEXT STEPS:"
echo ""
echo "1. Wait 5-10 minutes for initial setup"
echo ""
echo "2. SSH to the instance:"
echo "   ssh -i aws_files/chatmrpt-key.pem ubuntu@$PUBLIC_IP"
echo ""
echo "3. Download models (30-60 minutes):"
echo "   python3 /home/ubuntu/download_models.py"
echo ""
echo "4. Start vLLM server:"
echo "   python3 /home/ubuntu/vllm_arena_server.py"
echo ""
echo "5. Update your .env file:"
echo "   VLLM_BASE_URL=http://$PRIVATE_IP:8000"
echo "   USE_ARENA=true"
echo "   ARENA_MODE=enabled"
echo ""
echo "6. Update ALB target group:"
echo "   - Remove: 18.220.103.20 (old Instance 2)"
echo "   - Add: $PRIVATE_IP (new GPU instance)"
echo ""
echo "7. After testing, terminate old Instance 2:"
echo "   Instance 2 ID: i-0f3b25b72f18a5037"
echo ""
echo "Instance details saved to: gpu_instance_info.txt"

# Save instance details
cat > gpu_instance_info.txt << INFO
GPU Instance Information
========================
Instance ID: $INSTANCE_ID
Public IP:   $PUBLIC_IP
Private IP:  $PRIVATE_IP
Type:        g5.2xlarge
Region:      $REGION
Launched:    $(date)

SSH Access:
ssh -i aws_files/chatmrpt-key.pem ubuntu@$PUBLIC_IP

Cost: ~$1.21/hour (~$875/month)

Models:
1. Llama 3.1 8B
2. Mistral 7B v0.3
3. Qwen 3 8B (NOT 2.5)
4. BioMistral 7B
5. Gemma 2 9B

Old Instance 2 (to terminate):
ID: i-0f3b25b72f18a5037
IP: 18.220.103.20
INFO