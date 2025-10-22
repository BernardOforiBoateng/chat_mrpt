#!/bin/bash

# Fix security group for vLLM GPU instance
echo "Fixing security group for vLLM access..."

# Get the security group ID for the GPU instance
INSTANCE_ID="i-04e982a254c260972"
REGION="us-east-2"

# Get security group ID
SG_ID=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --region $REGION \
    --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' \
    --output text)

echo "Security Group ID: $SG_ID"

# Get VPC CIDR
VPC_ID=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --region $REGION \
    --query 'Reservations[0].Instances[0].VpcId' \
    --output text)

VPC_CIDR=$(aws ec2 describe-vpcs \
    --vpc-ids $VPC_ID \
    --region $REGION \
    --query 'Vpcs[0].CidrBlock' \
    --output text)

echo "VPC CIDR: $VPC_CIDR"

# Add rule to allow port 8000 from VPC
echo "Adding rule for port 8000..."
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 8000 \
    --cidr $VPC_CIDR \
    --region $REGION \
    --description "vLLM API access from VPC" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✓ Security group rule added successfully"
else
    echo "Rule might already exist, checking..."
    aws ec2 describe-security-groups \
        --group-ids $SG_ID \
        --region $REGION \
        --query 'SecurityGroups[0].IpPermissions[?FromPort==`8000`]' \
        --output json
fi

echo ""
echo "Testing connectivity from staging servers..."

# Test from staging servers
for IP in 3.21.167.170 18.220.103.20; do
    echo "Testing from $IP..."
    ssh -o StrictHostKeyChecking=no -i /tmp/chatmrpt-key2.pem ec2-user@$IP \
        "curl -s --connect-timeout 5 http://172.31.45.157:8000/v1/models | python3 -m json.tool | grep -q 'Qwen3-8B' && echo '  ✓ Connected successfully' || echo '  ✗ Connection failed'"
done

echo ""
echo "Security group configuration complete!"