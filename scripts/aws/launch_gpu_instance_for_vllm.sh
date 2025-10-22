#!/bin/bash

# Launch GPU Instance for vLLM with Qwen 3
echo "=========================================="
echo "Launching GPU Instance for vLLM"
echo "=========================================="

# Configuration
INSTANCE_TYPE="g5.2xlarge"  # 1x A10G with 24GB GPU memory (good for Qwen3-8B)
# Alternative: g5.12xlarge for 4x A10G (96GB total) to run Qwen3-32B
AMI_ID="ami-0c803b171269e2d72"  # Amazon Linux 2023 in us-east-2
KEY_NAME="chatmrpt-key"
SECURITY_GROUP="launch-wizard-1"  # Same as staging
SUBNET_ID="subnet-0713ee8d5af26578a"  # Same subnet as other instances
INSTANCE_NAME="ChatMRPT-vLLM-GPU"

echo "Configuration:"
echo "  Instance Type: $INSTANCE_TYPE"
echo "  AMI: Amazon Linux 2023"
echo "  Region: us-east-2"
echo ""

# Check if AWS CLI is available
if ! command -v aws &> /dev/null; then
    echo "AWS CLI not found. Installing..."
    pip install awscli
fi

# Launch the instance
echo "Launching GPU instance..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-groups $SECURITY_GROUP \
    --subnet-id $SUBNET_ID \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" \
    --user-data file://setup_gpu_userdata.sh \
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

# Get public IP
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

echo ""
echo "=========================================="
echo "✅ GPU Instance Launched Successfully!"
echo "=========================================="
echo ""
echo "Instance ID: $INSTANCE_ID"
echo "Public IP: $PUBLIC_IP"
echo "Private IP: $PRIVATE_IP"
echo ""
echo "Wait 3-5 minutes for instance initialization, then:"
echo ""
echo "1. SSH to the instance:"
echo "   ssh -i /tmp/chatmrpt-key2.pem ec2-user@$PUBLIC_IP"
echo ""
echo "2. Check GPU status:"
echo "   nvidia-smi"
echo ""
echo "3. Set up vLLM with Qwen 3:"
echo "   cd /home/ec2-user"
echo "   ./setup_vllm_qwen3.sh"
echo ""
echo "4. Update staging to use this vLLM instance:"
echo "   - Edit .env on staging servers"
echo "   - Set VLLM_BASE_URL=http://$PRIVATE_IP:8000"
echo ""
echo "Estimated costs:"
echo "  - g5.2xlarge: ~\$1.21/hour"
echo "  - Storage: 100GB gp3 ~\$8/month"