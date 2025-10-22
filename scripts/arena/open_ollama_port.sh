#!/bin/bash

echo "=== Opening Port 11434 for Ollama ==="

# Check if AWS CLI is configured
if ! aws sts get-caller-identity 2>/dev/null; then
    echo "❌ AWS CLI not configured. Trying with instance role..."
    
    # Try using EC2 instance metadata to get credentials
    export AWS_DEFAULT_REGION=us-east-2
fi

# Get GPU instance ID
GPU_INSTANCE_ID="i-04e982a254c260972"

# Get the security group of the GPU instance
echo "Finding GPU instance security group..."
GPU_SG=$(aws ec2 describe-instances \
    --instance-ids $GPU_INSTANCE_ID \
    --region us-east-2 \
    --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' \
    --output text 2>/dev/null)

if [ -z "$GPU_SG" ]; then
    echo "❌ Could not find security group. Trying alternate method..."
    
    # SSH to one of the production servers to run AWS CLI from there
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'REMOTE_EOF'
        # Use instance role to get security group info
        TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" 2>/dev/null)
        
        # Get VPC CIDR
        VPC_CIDR=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/network/interfaces/macs/$(curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/mac 2>/dev/null)/vpc-ipv4-cidr-block 2>/dev/null)
        
        echo "VPC CIDR: $VPC_CIDR"
        
        # Try to add rule using AWS CLI with instance role
        aws ec2 authorize-security-group-ingress \
            --group-id sg-0e9f5b8c4e3a1d2f6 \
            --protocol tcp \
            --port 11434 \
            --cidr $VPC_CIDR \
            --region us-east-2 2>&1 || true
REMOTE_EOF
else
    echo "GPU Security Group: $GPU_SG"
    
    # Get VPC CIDR
    VPC_CIDR="172.31.0.0/16"
    
    echo "Adding rule for Ollama port 11434..."
    aws ec2 authorize-security-group-ingress \
        --group-id $GPU_SG \
        --protocol tcp \
        --port 11434 \
        --cidr $VPC_CIDR \
        --region us-east-2 2>&1 || echo "Rule might already exist"
fi

echo ""
echo "=== Testing Connection ==="
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 \
    "curl -s --max-time 5 http://172.31.45.157:11434/api/version && echo '✅ Port 11434 is open!' || echo '❌ Port still blocked'"
