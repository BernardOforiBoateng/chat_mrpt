#!/bin/bash

# Launch g4dn.xlarge GPU instance for ChatMRPT with vLLM
# This instance has NVIDIA T4 GPU with 16GB VRAM

echo "🚀 Launching g4dn.xlarge GPU instance for ChatMRPT staging with vLLM..."

# Configuration
INSTANCE_TYPE="g4dn.xlarge"
KEY_NAME="chatmrpt-key"
REGION="us-east-2"

# Use Deep Learning AMI with pre-installed NVIDIA drivers and CUDA
# This saves hours of setup time
AMI_ID="ami-0c7ecec37c2dc10ba"  # AWS Deep Learning Base GPU AMI (Ubuntu 22.04) in us-east-2

# Security group - reuse existing or create new
SECURITY_GROUP_NAME="chatmrpt-gpu-sg"

# Create security group if it doesn't exist
echo "Creating security group..."
aws ec2 create-security-group \
    --group-name $SECURITY_GROUP_NAME \
    --description "Security group for ChatMRPT GPU staging with vLLM" \
    --region $REGION 2>/dev/null || echo "Security group already exists"

# Get security group ID
SG_ID=$(aws ec2 describe-security-groups \
    --group-names $SECURITY_GROUP_NAME \
    --region $REGION \
    --query 'SecurityGroups[0].GroupId' \
    --output text)

echo "Security Group ID: $SG_ID"

# Add inbound rules
echo "Configuring security group rules..."
# SSH access
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0 \
    --region $REGION 2>/dev/null || echo "SSH rule already exists"

# Flask/ChatMRPT port
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 5000 \
    --cidr 0.0.0.0/0 \
    --region $REGION 2>/dev/null || echo "Port 5000 rule already exists"

# vLLM API port
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 8000 \
    --cidr 0.0.0.0/0 \
    --region $REGION 2>/dev/null || echo "Port 8000 rule already exists"

# User data script to run on instance launch
cat > /tmp/user_data.sh << 'EOF'
#!/bin/bash
# Update system
apt-get update
apt-get upgrade -y

# Install Python 3.11 and pip
apt-get install -y python3.11 python3.11-venv python3-pip git

# Create ChatMRPT user
useradd -m -s /bin/bash chatmrpt

# Install vLLM with CUDA support
pip3 install vllm

# Install additional dependencies
pip3 install torch transformers accelerate

# Create systemd service for vLLM
cat > /etc/systemd/system/vllm.service << 'SERVICE'
[Unit]
Description=vLLM Model Server
After=network.target

[Service]
Type=simple
User=chatmrpt
WorkingDirectory=/home/chatmrpt
ExecStart=/usr/local/bin/python3 -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.9
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE

# Enable vLLM service
systemctl daemon-reload
systemctl enable vllm

# Log completion
echo "GPU instance setup complete" > /tmp/setup_complete.txt
date >> /tmp/setup_complete.txt
EOF

# Launch the instance
echo "Launching EC2 instance..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $SG_ID \
    --region $REGION \
    --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=100,VolumeType=gp3}" \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=chatmrpt-gpu-staging},{Key=Environment,Value=staging},{Key=Purpose,Value=vLLM}]" \
    --user-data file:///tmp/user_data.sh \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "✅ Instance launched with ID: $INSTANCE_ID"

# Wait for instance to be running
echo "Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --region $REGION \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "✅ Instance is running!"
echo "📍 Public IP: $PUBLIC_IP"
echo ""
echo "Next steps:"
echo "1. Wait 5-10 minutes for setup to complete"
echo "2. SSH into the instance: ssh -i aws_files/chatmrpt-key.pem ubuntu@$PUBLIC_IP"
echo "3. Check setup status: cat /tmp/setup_complete.txt"
echo "4. Check vLLM service: sudo systemctl status vllm"
echo ""
echo "vLLM API will be available at: http://$PUBLIC_IP:8000"
echo "ChatMRPT will be available at: http://$PUBLIC_IP:5000"
echo ""
echo "Instance details saved to: gpu_instance_details.txt"

# Save instance details
cat > gpu_instance_details.txt << EOD
GPU Instance Details
====================
Instance ID: $INSTANCE_ID
Instance Type: $INSTANCE_TYPE
Public IP: $PUBLIC_IP
Region: $REGION
Security Group: $SG_ID
AMI ID: $AMI_ID
Created: $(date)

Access:
-------
SSH: ssh -i aws_files/chatmrpt-key.pem ubuntu@$PUBLIC_IP
vLLM API: http://$PUBLIC_IP:8000
ChatMRPT: http://$PUBLIC_IP:5000

Services:
---------
Check vLLM: sudo systemctl status vllm
Restart vLLM: sudo systemctl restart vllm
View logs: sudo journalctl -u vllm -f
EOD

echo "✅ Setup script complete!"