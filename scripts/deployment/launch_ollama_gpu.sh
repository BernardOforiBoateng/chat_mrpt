#!/bin/bash

# Launch GPU Instance for Ollama with Arena Models
echo "=========================================="
echo "Launching GPU Instance for Ollama Arena"
echo "=========================================="

# Configuration
INSTANCE_TYPE="g5.xlarge"  # 1x A10G GPU with 24GB memory (good for 3 models)
AMI_ID="ami-0c803b171269e2d72"  # Amazon Linux 2023 in us-east-2
KEY_NAME="chatmrpt-key"
SECURITY_GROUP="launch-wizard-1"
SUBNET_ID="subnet-0713ee8d5af26578a"
INSTANCE_NAME="ChatMRPT-Ollama-GPU"

echo "Configuration:"
echo "  Instance Type: $INSTANCE_TYPE"
echo "  AMI: Amazon Linux 2023"
echo "  Region: us-east-2"
echo ""

# Check if AWS CLI is available
if ! command -v aws &> /dev/null; then
    echo "AWS CLI not found. Please install it first."
    exit 1
fi

# Create user data script for Ollama setup
cat << 'EOF' > /tmp/ollama_userdata.sh
#!/bin/bash
# Ollama GPU Setup Script

# Update system
sudo yum update -y

# Install NVIDIA drivers
sudo yum install -y nvidia-driver-latest-dkms
sudo yum install -y cuda-drivers

# Install Docker
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
sudo systemctl start ollama
sudo systemctl enable ollama

# Configure Ollama to listen on all interfaces
sudo mkdir -p /etc/systemd/system/ollama.service.d/
sudo tee /etc/systemd/system/ollama.service.d/override.conf > /dev/null << 'INNEREOF'
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
INNEREOF

sudo systemctl daemon-reload
sudo systemctl restart ollama

# Wait for Ollama to be ready
sleep 10

# Pull the 3 required models for Arena
echo "Pulling Arena models..."
ollama pull llama3.1:8b
ollama pull mistral:7b
ollama pull phi3:mini

# Create a script to check GPU usage
cat > /home/ec2-user/check_gpu.sh << 'SCRIPTEOF'
#!/bin/bash
echo "=== GPU Status ==="
nvidia-smi
echo ""
echo "=== Ollama Models ==="
ollama list
echo ""
echo "=== Ollama Service ==="
sudo systemctl status ollama | head -10
SCRIPTEOF
chmod +x /home/ec2-user/check_gpu.sh

echo "Ollama setup complete!" > /home/ec2-user/ollama_setup.log
EOF

# Launch the instance
echo "Launching GPU instance..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-groups $SECURITY_GROUP \
    --subnet-id $SUBNET_ID \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" \
    --user-data file:///tmp/ollama_userdata.sh \
    --query 'Instances[0].InstanceId' \
    --output text \
    --region us-east-2)

if [ -z "$INSTANCE_ID" ]; then
    echo "❌ Failed to launch instance"
    exit 1
fi

echo "✅ Instance launched: $INSTANCE_ID"
echo "Waiting for instance to be running..."

# Wait for instance to be running
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region us-east-2

# Get IPs
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text \
    --region us-east-2)

PRIVATE_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PrivateIpAddress' \
    --output text \
    --region us-east-2)

# Save IPs to file for later use
echo "OLLAMA_GPU_INSTANCE_ID=$INSTANCE_ID" > aws_files/ollama_gpu_info.txt
echo "OLLAMA_GPU_PUBLIC_IP=$PUBLIC_IP" >> aws_files/ollama_gpu_info.txt
echo "OLLAMA_GPU_PRIVATE_IP=$PRIVATE_IP" >> aws_files/ollama_gpu_info.txt

echo ""
echo "=========================================="
echo "✅ Ollama GPU Instance Launched!"
echo "=========================================="
echo ""
echo "Instance ID: $INSTANCE_ID"
echo "Public IP: $PUBLIC_IP"
echo "Private IP: $PRIVATE_IP (use this for production)"
echo ""
echo "⏰ Wait 5-10 minutes for setup to complete, then:"
echo ""
echo "1. SSH to check status:"
echo "   ssh -i /tmp/chatmrpt-key2.pem ec2-user@$PUBLIC_IP"
echo "   ./check_gpu.sh"
echo ""
echo "2. Test Ollama from local:"
echo "   curl http://$PUBLIC_IP:11434/api/tags"
echo ""
echo "3. Update production instances:"
echo "   Add to .env: AWS_OLLAMA_HOST=$PRIVATE_IP"
echo ""
echo "4. Open port 11434 in security group if needed:"
echo "   - From: Production instances (172.31.0.0/16)"
echo "   - To: Port 11434"
echo ""
echo "Estimated costs:"
echo "  - g5.xlarge: ~\$1.006/hour"
echo "  - Storage: 100GB gp3 ~\$8/month"

# Clean up temp file
rm -f /tmp/ollama_userdata.sh