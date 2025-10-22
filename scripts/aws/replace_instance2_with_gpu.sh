#!/bin/bash
# Replace Instance 2 (t3.medium) with GPU instance for vLLM Arena

set -e

echo "================================================"
echo "  Replace Instance 2 with GPU for Arena"
echo "================================================"
echo ""
echo "Current setup:"
echo "  Instance 1: t3.xlarge (Keep for main app)"
echo "  Instance 2: t3.medium (Replace with GPU)"
echo ""
echo "New setup will be:"
echo "  Instance 1: t3.xlarge (Main app) - $67/month"
echo "  Instance 2: g5.2xlarge (GPU/vLLM) - $875/month"
echo "  Total: ~$942/month (vs current ~$100/month)"
echo ""
read -p "Continue with replacement? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Configuration
OLD_INSTANCE_IP="18.220.103.20"
INSTANCE_TYPE="g5.2xlarge"  # 1x A10G GPU (24GB)
AMI_ID="ami-00d990e7e5d7c2b83"  # Deep Learning AMI Ubuntu 20.04 in us-east-2
KEY_NAME="chatmrpt-key"
SECURITY_GROUP="launch-wizard-1"
SUBNET_ID="subnet-0713ee8d5af26578a"

echo ""
echo "Step 1: Creating backup of Instance 2 data..."
ssh -i /tmp/chatmrpt-key2.pem ec2-user@${OLD_INSTANCE_IP} << 'EOF'
echo "Backing up critical files..."
cd /home/ec2-user
tar -czf chatmrpt_backup_$(date +%Y%m%d).tar.gz ChatMRPT/instance ChatMRPT/.env ChatMRPT/app/agent
echo "Backup created: chatmrpt_backup_$(date +%Y%m%d).tar.gz"
ls -lh chatmrpt_backup_*.tar.gz
EOF

echo ""
echo "Step 2: Downloading backup locally..."
scp -i /tmp/chatmrpt-key2.pem ec2-user@${OLD_INSTANCE_IP}:~/chatmrpt_backup_*.tar.gz ./

echo ""
echo "Step 3: Creating launch script for GPU instance..."
cat > launch_gpu_instance.sh << 'EOF'
#!/bin/bash
# Launch GPU instance with Deep Learning AMI

aws ec2 run-instances \
    --image-id ami-00d990e7e5d7c2b83 \
    --instance-type g5.2xlarge \
    --key-name chatmrpt-key \
    --security-group-ids $(aws ec2 describe-security-groups --group-names launch-wizard-1 --query 'SecurityGroups[0].GroupId' --output text) \
    --subnet-id subnet-0713ee8d5af26578a \
    --block-device-mappings '[{
        "DeviceName": "/dev/sda1",
        "Ebs": {
            "VolumeSize": 200,
            "VolumeType": "gp3",
            "DeleteOnTermination": true
        }
    }]' \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ChatMRPT-GPU-Arena}]' \
    --user-data '#!/bin/bash
# Update system
apt-get update && apt-get upgrade -y

# Install Python and dependencies
apt-get install -y python3.10 python3-pip python3.10-venv

# Create venv
python3 -m venv /opt/vllm_env
source /opt/vllm_env/bin/activate

# Install PyTorch and vLLM
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install vllm transformers accelerate huggingface-hub

# Create models directory
mkdir -p /opt/models
chown ubuntu:ubuntu /opt/models

# Set HF token
echo "export HF_TOKEN=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" >> /home/ubuntu/.bashrc
' \
    --query 'Instances[0].InstanceId' \
    --output text
EOF

chmod +x launch_gpu_instance.sh

echo ""
echo "Step 4: Instructions to complete replacement:"
echo ""
echo "1. LAUNCH GPU INSTANCE:"
echo "   ./launch_gpu_instance.sh"
echo ""
echo "2. WAIT for instance to be ready (5-10 minutes)"
echo ""
echo "3. GET NEW IP and SSH to it:"
echo "   aws ec2 describe-instances --instance-ids <INSTANCE_ID> --query 'Reservations[0].Instances[0].PublicIpAddress'"
echo "   ssh -i ~/.ssh/chatmrpt-key.pem ubuntu@<NEW_IP>"
echo ""
echo "4. COPY the model download script:"
echo "   scp -i ~/.ssh/chatmrpt-key.pem setup_vllm_5models.sh ubuntu@<NEW_IP>:~/"
echo ""
echo "5. RUN model downloads on GPU instance:"
echo "   ./setup_vllm_5models.sh"
echo ""
echo "6. UPDATE ALB Target Group:"
echo "   - Remove 18.220.103.20 from target group"
echo "   - Add new GPU instance private IP"
echo ""
echo "7. UPDATE .env file:"
echo "   VLLM_BASE_URL=http://<NEW_PRIVATE_IP>:8000"
echo ""
echo "8. TERMINATE old Instance 2 (optional, after testing):"
echo "   aws ec2 terminate-instances --instance-ids <OLD_INSTANCE_ID>"
echo ""
echo "IMPORTANT: The GPU instance will cost ~$1.21/hour ($875/month)"
echo "Consider using spot instances for 70% savings if interruptions are acceptable."