#!/bin/bash

# vLLM Setup Script for ChatMRPT Arena Mode
# This script launches a GPU instance and sets up vLLM with multiple models

set -e

echo "================================================"
echo "  vLLM Arena Setup for ChatMRPT"
echo "================================================"

# Configuration
INSTANCE_TYPE="g5.xlarge"  # 1x NVIDIA A10G GPU (24GB VRAM)
AMI_ID="ami-0c02fb55731490381"  # Deep Learning AMI (Amazon Linux 2)
KEY_NAME="chatmrpt-key"
SECURITY_GROUP="sg-0abc123def456789"  # Update with your SG
SUBNET_ID="subnet-0abc123def456789"  # Update with your subnet

# Step 1: Launch GPU Instance
echo "Step 1: Launching GPU instance..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $SECURITY_GROUP \
    --subnet-id $SUBNET_ID \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ChatMRPT-vLLM-Arena}]' \
    --user-data file://vllm_userdata.sh \
    --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":200,"VolumeType":"gp3"}}]' \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "Instance launched: $INSTANCE_ID"

# Wait for instance to be running
echo "Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "Instance is running at: $PUBLIC_IP"

# Step 2: Create user data script for vLLM setup
cat > vllm_userdata.sh << 'EOF'
#!/bin/bash

# Update system
yum update -y

# Install Docker
yum install -y docker
service docker start
usermod -a -G docker ec2-user

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.repo | \
    tee /etc/yum.repos.d/nvidia-docker.repo
yum clean expire-cache
yum install -y nvidia-container-toolkit
systemctl restart docker

# Install Python 3.11
yum install -y python3.11 python3.11-pip

# Create vLLM environment
python3.11 -m venv /opt/vllm_env
source /opt/vllm_env/bin/activate

# Install vLLM with CUDA support
pip install --upgrade pip
pip install vllm torch==2.1.2+cu121 -f https://download.pytorch.org/whl/torch_stable.html
pip install transformers accelerate

# Download models using Hugging Face CLI
pip install huggingface-hub
export HF_HOME=/opt/models

# Download all required models
echo "Downloading models..."
huggingface-cli download meta-llama/Llama-3.1-8B-Instruct \
    --local-dir /opt/models/llama-3.1-8b \
    --local-dir-use-symlinks False

huggingface-cli download mistralai/Mistral-7B-Instruct-v0.3 \
    --local-dir /opt/models/mistral-7b \
    --local-dir-use-symlinks False

huggingface-cli download Qwen/Qwen2.5-7B-Instruct \
    --local-dir /opt/models/qwen-2.5-7b \
    --local-dir-use-symlinks False

# Create systemd service for each model
# Service 1: Llama 3.1
cat > /etc/systemd/system/vllm-llama.service << 'INNER_EOF'
[Unit]
Description=vLLM Llama 3.1 8B Service
After=network.target

[Service]
Type=simple
User=ec2-user
Environment="PATH=/opt/vllm_env/bin:$PATH"
Environment="CUDA_VISIBLE_DEVICES=0"
ExecStart=/opt/vllm_env/bin/python -m vllm.entrypoints.openai.api_server \
    --model /opt/models/llama-3.1-8b \
    --host 0.0.0.0 \
    --port 8001 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.3 \
    --served-model-name llama-3.1-8b
Restart=always

[Install]
WantedBy=multi-user.target
INNER_EOF

# Service 2: Mistral
cat > /etc/systemd/system/vllm-mistral.service << 'INNER_EOF'
[Unit]
Description=vLLM Mistral 7B Service
After=network.target

[Service]
Type=simple
User=ec2-user
Environment="PATH=/opt/vllm_env/bin:$PATH"
Environment="CUDA_VISIBLE_DEVICES=0"
ExecStart=/opt/vllm_env/bin/python -m vllm.entrypoints.openai.api_server \
    --model /opt/models/mistral-7b \
    --host 0.0.0.0 \
    --port 8002 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.3 \
    --served-model-name mistral-7b
Restart=always

[Install]
WantedBy=multi-user.target
INNER_EOF

# Service 3: Qwen
cat > /etc/systemd/system/vllm-qwen.service << 'INNER_EOF'
[Unit]
Description=vLLM Qwen 2.5 7B Service
After=network.target

[Service]
Type=simple
User=ec2-user
Environment="PATH=/opt/vllm_env/bin:$PATH"
Environment="CUDA_VISIBLE_DEVICES=0"
ExecStart=/opt/vllm_env/bin/python -m vllm.entrypoints.openai.api_server \
    --model /opt/models/qwen-2.5-7b \
    --host 0.0.0.0 \
    --port 8003 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.3 \
    --served-model-name qwen-2.5-7b
Restart=always

[Install]
WantedBy=multi-user.target
INNER_EOF

# Create a model router service using nginx
yum install -y nginx
cat > /etc/nginx/conf.d/vllm.conf << 'INNER_EOF'
upstream llama_backend {
    server localhost:8001;
}

upstream mistral_backend {
    server localhost:8002;
}

upstream qwen_backend {
    server localhost:8003;
}

server {
    listen 8000;
    server_name _;

    # Route based on model name in request
    location /v1/llama {
        rewrite ^/v1/llama(.*)$ /v1$1 break;
        proxy_pass http://llama_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /v1/mistral {
        rewrite ^/v1/mistral(.*)$ /v1$1 break;
        proxy_pass http://mistral_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /v1/qwen {
        rewrite ^/v1/qwen(.*)$ /v1$1 break;
        proxy_pass http://qwen_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Default route
    location / {
        proxy_pass http://llama_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
INNER_EOF

# Enable and start services
systemctl daemon-reload
systemctl enable vllm-llama vllm-mistral vllm-qwen nginx
systemctl start vllm-llama
sleep 30  # Wait for first model to load
systemctl start vllm-mistral
sleep 30
systemctl start vllm-qwen
systemctl restart nginx

# Create health check script
cat > /usr/local/bin/check_vllm.sh << 'INNER_EOF'
#!/bin/bash
echo "Checking vLLM services..."
curl -s http://localhost:8001/v1/models | jq .
curl -s http://localhost:8002/v1/models | jq .
curl -s http://localhost:8003/v1/models | jq .
INNER_EOF
chmod +x /usr/local/bin/check_vllm.sh

echo "vLLM setup complete!"
EOF

# Step 3: Wait for setup to complete
echo "Waiting for vLLM setup (this will take 10-15 minutes)..."
echo "You can SSH to the instance to monitor progress:"
echo "ssh -i ~/.ssh/${KEY_NAME}.pem ec2-user@${PUBLIC_IP}"
echo ""
echo "Check logs with:"
echo "sudo journalctl -u vllm-llama -f"
echo ""
echo "Once ready, update your .env file:"
echo "VLLM_BASE_URL=http://${PUBLIC_IP}:8000"
echo "USE_VLLM=true"

# Output instance details
cat << EOF > vllm_instance_info.txt
vLLM Arena Instance Information
================================
Instance ID: $INSTANCE_ID
Public IP: $PUBLIC_IP
Instance Type: $INSTANCE_TYPE

Model Endpoints:
- Llama 3.1: http://${PUBLIC_IP}:8001
- Mistral 7B: http://${PUBLIC_IP}:8002
- Qwen 2.5: http://${PUBLIC_IP}:8003
- Router: http://${PUBLIC_IP}:8000

SSH Access:
ssh -i ~/.ssh/${KEY_NAME}.pem ec2-user@${PUBLIC_IP}

To check status:
curl http://${PUBLIC_IP}:8001/v1/models
curl http://${PUBLIC_IP}:8002/v1/models
curl http://${PUBLIC_IP}:8003/v1/models
EOF

echo "Setup script complete! Instance info saved to vllm_instance_info.txt"