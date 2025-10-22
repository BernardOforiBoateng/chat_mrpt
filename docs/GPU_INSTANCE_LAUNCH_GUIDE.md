# GPU Instance Launch Guide for vLLM with Qwen 3

## Quick Launch via AWS Console

### 1. Launch Instance
1. Go to [EC2 Console](https://us-east-2.console.aws.amazon.com/ec2/v2/home?region=us-east-2#Instances:)
2. Click **"Launch instances"**

### 2. Configure Instance
**Name**: `ChatMRPT-vLLM-GPU`

**AMI**: Amazon Linux 2023 (already selected)

**Instance Type**: 
- Choose **`g5.2xlarge`** (1x NVIDIA A10G with 24GB) - $1.21/hour
- Or **`g5.xlarge`** if budget conscious ($0.42/hour, still runs Qwen3-4B well)

**Key pair**: Select `chatmrpt-key` (existing)

**Network settings**:
- VPC: Default
- Subnet: No preference
- Auto-assign public IP: **Enable**
- Security group: Select existing → `launch-wizard-1`

**Storage**: 
- Change to **100 GB gp3**

**Advanced details** → **User data** (paste this):
```bash
#!/bin/bash
# Install NVIDIA drivers
yum update -y
yum install -y gcc kernel-devel-$(uname -r)

# Install CUDA
dnf config-manager --add-repo https://developer.download.nvidia.com/compute/cuda/repos/rhel9/x86_64/cuda-rhel9.repo
dnf clean all
dnf module install -y nvidia-driver:latest-dkms
dnf install -y cuda-toolkit

# Install Python and pip
yum install -y python3.11 python3.11-pip git

# Setup for ec2-user
su - ec2-user << 'EOF'
# Create vLLM setup
cd ~
python3.11 -m venv vllm_env
source vllm_env/bin/activate
pip install --upgrade pip
pip install vllm transformers torch accelerate

# Create start script
cat > start_vllm.sh << 'SCRIPT'
#!/bin/bash
source ~/vllm_env/bin/activate
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen3-8B \
    --port 8000 \
    --host 0.0.0.0 \
    --max-model-len 16384 \
    --gpu-memory-utilization 0.90 \
    --dtype auto \
    --trust-remote-code
SCRIPT
chmod +x start_vllm.sh

echo "Setup complete! Run ./start_vllm.sh to start vLLM"
EOF
```

### 3. Launch
Click **"Launch instance"**

### 4. Wait for Initialization
- Instance will take ~5 minutes to initialize
- Note the **Public IP** from the console

### 5. Connect and Start vLLM

SSH to the instance:
```bash
# Copy key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# SSH (replace with your instance IP)
ssh -i /tmp/chatmrpt-key2.pem ec2-user@<PUBLIC_IP>
```

On the GPU instance:
```bash
# Check GPU
nvidia-smi

# Start vLLM
cd ~
./start_vllm.sh
```

### 6. Configure Staging to Use vLLM

SSH to staging instances and update configuration:
```bash
# SSH to staging
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170

# Update .env
cd /home/ec2-user/ChatMRPT
nano .env

# Add/update these lines:
USE_VLLM=true
USE_OLLAMA=false
VLLM_BASE_URL=http://<GPU_PRIVATE_IP>:8000
VLLM_MODEL=Qwen/Qwen3-8B
TPR_USE_LOCAL_MODEL=true

# Restart service
sudo systemctl restart chatmrpt
```

Repeat for second staging instance (18.220.103.20).

## Verify Setup

1. **Test vLLM directly**:
```bash
curl http://<GPU_PUBLIC_IP>:8000/v1/models
```

2. **Test from staging**:
```bash
curl http://<GPU_PRIVATE_IP>:8000/v1/models
```

3. **Test TPR workflow**:
- Go to http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com
- Upload a TPR file
- System should now use Qwen3-8B via vLLM

## Cost Management

- **g5.xlarge**: $0.42/hour (~$300/month if running 24/7)
- **g5.2xlarge**: $1.21/hour (~$870/month if running 24/7)
- **Tip**: Stop instance when not in use
- **Auto-shutdown**: Set up CloudWatch alarm to stop after inactivity

## Model Options by Instance Type

| Instance | GPU Memory | Recommended Model | Performance |
|----------|-----------|------------------|-------------|
| g5.xlarge | 24GB | Qwen3-4B | Good |
| g5.2xlarge | 24GB | Qwen3-8B | Better |
| g5.12xlarge | 96GB | Qwen3-32B | Best |

## Troubleshooting

If vLLM fails to start:
```bash
# Check logs
journalctl -u vllm -n 50

# Check GPU
nvidia-smi

# Test with smaller model
sed -i 's/Qwen3-8B/Qwen3-4B/g' start_vllm.sh
./start_vllm.sh
```

## Next Steps

After instance is running with vLLM:
1. ✅ Test TPR workflow with local model
2. ✅ Verify no data goes to OpenAI
3. ✅ Monitor performance and costs
4. ✅ Set up auto-scaling if needed