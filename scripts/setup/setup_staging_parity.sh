#!/bin/bash
# Setup staging environment to match production architecture
# This creates a true staging environment with ALB and multiple instances

set -e

echo "=== ChatMRPT Staging-Production Parity Setup ==="
echo "This script will create a staging environment identical to production"
echo ""

# Configuration
REGION="us-east-2"
STAGING_INSTANCE_ID="i-<staging-instance-id>"  # Current staging instance
VPC_ID="<vpc-id>"  # Get from AWS console
SUBNET_1="<subnet-1-id>"  # Get from AWS console
SUBNET_2="<subnet-2-id>"  # Get from AWS console
KEY_NAME="chatmrpt-key"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Prerequisites:${NC}"
echo "1. AWS CLI configured with appropriate credentials"
echo "2. Current staging instance ID: $STAGING_INSTANCE_ID"
echo "3. VPC ID: $VPC_ID"
echo "4. Subnets: $SUBNET_1, $SUBNET_2"
echo ""
read -p "Have you updated the configuration variables above? (y/n): " -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please update the configuration variables in this script first."
    exit 1
fi

echo ""
echo -e "${GREEN}Step 1: Creating snapshot of current staging instance${NC}"
echo "Finding volume ID..."
VOLUME_ID=$(aws ec2 describe-instances \
    --instance-ids $STAGING_INSTANCE_ID \
    --region $REGION \
    --query "Reservations[0].Instances[0].BlockDeviceMappings[0].Ebs.VolumeId" \
    --output text)

echo "Creating snapshot of volume $VOLUME_ID..."
SNAPSHOT_ID=$(aws ec2 create-snapshot \
    --volume-id $VOLUME_ID \
    --description "Staging before ALB migration - $(date)" \
    --region $REGION \
    --query "SnapshotId" \
    --output text)

echo -e "${GREEN}✓ Snapshot created: $SNAPSHOT_ID${NC}"

echo ""
echo -e "${GREEN}Step 2: Creating security groups${NC}"

# Create ALB security group
echo "Creating ALB security group..."
ALB_SG_ID=$(aws ec2 create-security-group \
    --group-name chatmrpt-staging-alb-sg \
    --description "Security group for ChatMRPT staging ALB" \
    --vpc-id $VPC_ID \
    --region $REGION \
    --query "GroupId" \
    --output text 2>/dev/null || echo "exists")

if [ "$ALB_SG_ID" = "exists" ]; then
    ALB_SG_ID=$(aws ec2 describe-security-groups \
        --filters "Name=group-name,Values=chatmrpt-staging-alb-sg" \
        --region $REGION \
        --query "SecurityGroups[0].GroupId" \
        --output text)
    echo "Using existing ALB security group: $ALB_SG_ID"
else
    # Add rules to ALB security group
    aws ec2 authorize-security-group-ingress \
        --group-id $ALB_SG_ID \
        --protocol tcp \
        --port 80 \
        --cidr 0.0.0.0/0 \
        --region $REGION

    echo -e "${GREEN}✓ ALB security group created: $ALB_SG_ID${NC}"
fi

# Create instance security group
echo "Creating instance security group..."
INSTANCE_SG_ID=$(aws ec2 create-security-group \
    --group-name chatmrpt-staging-instance-sg \
    --description "Security group for ChatMRPT staging instances" \
    --vpc-id $VPC_ID \
    --region $REGION \
    --query "GroupId" \
    --output text 2>/dev/null || echo "exists")

if [ "$INSTANCE_SG_ID" = "exists" ]; then
    INSTANCE_SG_ID=$(aws ec2 describe-security-groups \
        --filters "Name=group-name,Values=chatmrpt-staging-instance-sg" \
        --region $REGION \
        --query "SecurityGroups[0].GroupId" \
        --output text)
    echo "Using existing instance security group: $INSTANCE_SG_ID"
else
    # Allow traffic from ALB
    aws ec2 authorize-security-group-ingress \
        --group-id $INSTANCE_SG_ID \
        --protocol tcp \
        --port 8080 \
        --source-group $ALB_SG_ID \
        --region $REGION

    # Allow SSH (update with your IP)
    aws ec2 authorize-security-group-ingress \
        --group-id $INSTANCE_SG_ID \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0 \
        --region $REGION

    echo -e "${GREEN}✓ Instance security group created: $INSTANCE_SG_ID${NC}"
fi

echo ""
echo -e "${GREEN}Step 3: Creating AMI from current staging instance${NC}"
AMI_ID=$(aws ec2 create-image \
    --instance-id $STAGING_INSTANCE_ID \
    --name "chatmrpt-staging-base-$(date +%Y%m%d-%H%M%S)" \
    --description "ChatMRPT staging base image" \
    --region $REGION \
    --query "ImageId" \
    --output text)

echo "AMI creation initiated: $AMI_ID"
echo "Waiting for AMI to be available (this may take a few minutes)..."

aws ec2 wait image-available \
    --image-ids $AMI_ID \
    --region $REGION

echo -e "${GREEN}✓ AMI ready: $AMI_ID${NC}"

echo ""
echo -e "${GREEN}Step 4: Launching second staging instance${NC}"

# Get instance type of current staging
INSTANCE_TYPE=$(aws ec2 describe-instances \
    --instance-ids $STAGING_INSTANCE_ID \
    --region $REGION \
    --query "Reservations[0].Instances[0].InstanceType" \
    --output text)

echo "Launching second instance (type: $INSTANCE_TYPE)..."
INSTANCE_2_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $INSTANCE_SG_ID \
    --subnet-id $SUBNET_1 \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=chatmrpt-staging-2}]" \
    --region $REGION \
    --query "Instances[0].InstanceId" \
    --output text)

echo "Instance launched: $INSTANCE_2_ID"
echo "Waiting for instance to be running..."

aws ec2 wait instance-running \
    --instance-ids $INSTANCE_2_ID \
    --region $REGION

# Get private IP of new instance
INSTANCE_2_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_2_ID \
    --region $REGION \
    --query "Reservations[0].Instances[0].PrivateIpAddress" \
    --output text)

echo -e "${GREEN}✓ Second instance running: $INSTANCE_2_ID ($INSTANCE_2_IP)${NC}"

echo ""
echo -e "${GREEN}Step 5: Creating target group${NC}"
TG_ARN=$(aws elbv2 create-target-group \
    --name chatmrpt-staging-targets \
    --protocol HTTP \
    --port 8080 \
    --vpc-id $VPC_ID \
    --health-check-path /health \
    --health-check-interval-seconds 30 \
    --health-check-timeout-seconds 5 \
    --healthy-threshold-count 2 \
    --unhealthy-threshold-count 2 \
    --region $REGION \
    --query "TargetGroups[0].TargetGroupArn" \
    --output text 2>/dev/null || echo "exists")

if [ "$TG_ARN" = "exists" ]; then
    TG_ARN=$(aws elbv2 describe-target-groups \
        --names chatmrpt-staging-targets \
        --region $REGION \
        --query "TargetGroups[0].TargetGroupArn" \
        --output text)
    echo "Using existing target group: $TG_ARN"
else
    echo -e "${GREEN}✓ Target group created${NC}"
fi

echo ""
echo -e "${GREEN}Step 6: Registering instances to target group${NC}"

# Get private IP of first staging instance
INSTANCE_1_IP=$(aws ec2 describe-instances \
    --instance-ids $STAGING_INSTANCE_ID \
    --region $REGION \
    --query "Reservations[0].Instances[0].PrivateIpAddress" \
    --output text)

aws elbv2 register-targets \
    --target-group-arn $TG_ARN \
    --targets Id=$STAGING_INSTANCE_ID,Port=8080 Id=$INSTANCE_2_ID,Port=8080 \
    --region $REGION

echo -e "${GREEN}✓ Both instances registered${NC}"

echo ""
echo -e "${GREEN}Step 7: Creating Application Load Balancer${NC}"
ALB_ARN=$(aws elbv2 create-load-balancer \
    --name chatmrpt-staging-alb \
    --subnets $SUBNET_1 $SUBNET_2 \
    --security-groups $ALB_SG_ID \
    --region $REGION \
    --query "LoadBalancers[0].LoadBalancerArn" \
    --output text 2>/dev/null || echo "exists")

if [ "$ALB_ARN" = "exists" ]; then
    ALB_ARN=$(aws elbv2 describe-load-balancers \
        --names chatmrpt-staging-alb \
        --region $REGION \
        --query "LoadBalancers[0].LoadBalancerArn" \
        --output text)
    echo "Using existing ALB: $ALB_ARN"
else
    echo -e "${GREEN}✓ ALB created${NC}"
fi

# Get ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers \
    --load-balancer-arns $ALB_ARN \
    --region $REGION \
    --query "LoadBalancers[0].DNSName" \
    --output text)

echo ""
echo -e "${GREEN}Step 8: Creating listener${NC}"
aws elbv2 create-listener \
    --load-balancer-arn $ALB_ARN \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=forward,TargetGroupArn=$TG_ARN \
    --region $REGION \
    --output text >/dev/null 2>&1 || echo "Listener already exists"

echo -e "${GREEN}✓ Listener configured${NC}"

echo ""
echo -e "${GREEN}Step 9: Enabling sticky sessions${NC}"
aws elbv2 modify-target-group-attributes \
    --target-group-arn $TG_ARN \
    --attributes \
        Key=stickiness.enabled,Value=true \
        Key=stickiness.type,Value=lb_cookie \
        Key=stickiness.lb_cookie.duration_seconds,Value=86400 \
    --region $REGION \
    --output text >/dev/null

echo -e "${GREEN}✓ Sticky sessions enabled (24 hours)${NC}"

echo ""
echo -e "${GREEN}Step 10: Waiting for instances to be healthy${NC}"
echo "This may take a few minutes..."

# Wait for targets to be healthy
while true; do
    HEALTHY_COUNT=$(aws elbv2 describe-target-health \
        --target-group-arn $TG_ARN \
        --region $REGION \
        --query "length(TargetHealthDescriptions[?TargetHealth.State=='healthy'])" \
        --output text)
    
    if [ "$HEALTHY_COUNT" -eq "2" ]; then
        echo -e "${GREEN}✓ Both instances are healthy!${NC}"
        break
    else
        echo "Healthy instances: $HEALTHY_COUNT/2 - waiting..."
        sleep 10
    fi
done

echo ""
echo "=========================================="
echo -e "${GREEN}Staging Environment Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Configuration Summary:"
echo "----------------------"
echo "ALB DNS: http://$ALB_DNS"
echo "Instance 1: $STAGING_INSTANCE_ID ($INSTANCE_1_IP)"
echo "Instance 2: $INSTANCE_2_ID ($INSTANCE_2_IP)"
echo "Target Group: $TG_ARN"
echo "ALB Security Group: $ALB_SG_ID"
echo "Instance Security Group: $INSTANCE_SG_ID"
echo ""
echo "Next Steps:"
echo "-----------"
echo "1. Test the ALB endpoint: http://$ALB_DNS"
echo "2. Update staging instance security groups to use $INSTANCE_SG_ID"
echo "3. Update deployment scripts to deploy to both instances"
echo "4. Update CLAUDE.md with new staging architecture"
echo ""
echo "To verify setup:"
echo "curl http://$ALB_DNS/health"
echo ""
echo -e "${YELLOW}Note: Save this configuration information for your records.${NC}"