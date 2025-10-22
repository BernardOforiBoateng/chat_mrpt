#!/bin/bash

# Script to create a new stable ChatMRPT instance
# This will create a separate EC2 instance with its own IP address

echo "=== Creating New Stable ChatMRPT Instance ==="
echo "This script will help you create a new EC2 instance for stable access"
echo ""

# Instance configuration (based on existing instance)
INSTANCE_TYPE="t3.large"  # Using t3.large to save costs (original is t3.xlarge)
AMI_ID="ami-02c0a366899ceb8d2"
SECURITY_GROUP="sg-0b21586985a0bbfbe"
SUBNET_ID="subnet-0713ee8d5af26578a"
KEY_NAME="chatmrpt-key"
INSTANCE_NAME="ChatMRPT-Stable-$(date +%Y%m%d)"

echo "Configuration:"
echo "  Instance Type: $INSTANCE_TYPE"
echo "  AMI: $AMI_ID"
echo "  Security Group: $SECURITY_GROUP"
echo "  Subnet: $SUBNET_ID"
echo "  Key Pair: $KEY_NAME"
echo ""

# AWS CLI command to launch the instance
cat << 'EOF' > launch_stable_instance.sh
#!/bin/bash

# Launch new EC2 instance
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id ami-02c0a366899ceb8d2 \
    --instance-type t3.large \
    --key-name chatmrpt-key \
    --security-group-ids sg-0b21586985a0bbfbe \
    --subnet-id subnet-0713ee8d5af26578a \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=ChatMRPT-Stable},{Key=Purpose,Value=StableProduction},{Key=CreatedDate,Value=$(date +%Y%m%d)}]" \
    --user-data '#!/bin/bash
    yum update -y
    yum install -y git python3 python3-pip
    ' \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "Instance launched: $INSTANCE_ID"

# Wait for instance to be running
echo "Waiting for instance to start..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "Instance is running!"
echo "Instance ID: $INSTANCE_ID"
echo "Public IP: $PUBLIC_IP"
echo ""
echo "Next steps:"
echo "1. Wait 2-3 minutes for initialization"
echo "2. SSH to the instance: ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$PUBLIC_IP"
echo "3. Run the setup script to copy ChatMRPT"
EOF

echo "To launch the instance, run:"
echo "  chmod +x launch_stable_instance.sh"
echo "  ./launch_stable_instance.sh"