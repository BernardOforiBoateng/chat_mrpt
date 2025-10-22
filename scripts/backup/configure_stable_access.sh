#!/bin/bash

# Script to configure stable access to ChatMRPT while making changes
# This will route all traffic to Instance 2 (stable) while Instance 1 is used for testing

echo "=== Configuring Stable Access for ChatMRPT ==="
echo ""
echo "This script will:"
echo "1. Remove Instance 1 from the load balancer (for testing changes)"
echo "2. Keep Instance 2 as the stable production instance"
echo "3. All users will access the stable version through CloudFront"
echo ""

# Configuration
TARGET_GROUP_ARN="arn:aws:elasticloadbalancing:us-east-2:992382473315:targetgroup/chatmrpt-staging-tg/b3c7f8e9e1f5c4d7"
INSTANCE_1_ID="i-0994615951d0b9563"  # Instance for testing (will be removed from LB)
INSTANCE_2_ID="i-0f3b25b72f18a5037"  # Stable instance (will serve all traffic)

echo "Current Configuration:"
echo "  Instance 1 (Testing): $INSTANCE_1_ID (IP: 3.21.167.170)"
echo "  Instance 2 (Stable):  $INSTANCE_2_ID (IP: 18.220.103.20)"
echo ""

# Step 1: Check current target health
echo "Step 1: Checking current load balancer targets..."
aws elbv2 describe-target-health \
    --target-group-arn $TARGET_GROUP_ARN \
    --query 'TargetHealthDescriptions[*].[Target.Id,TargetHealth.State]' \
    --output table

echo ""
echo "Step 2: Removing Instance 1 from load balancer..."
aws elbv2 deregister-targets \
    --target-group-arn $TARGET_GROUP_ARN \
    --targets Id=$INSTANCE_1_ID

echo "Waiting for deregistration to complete..."
sleep 30

# Step 3: Verify configuration
echo ""
echo "Step 3: Verifying new configuration..."
aws elbv2 describe-target-health \
    --target-group-arn $TARGET_GROUP_ARN \
    --query 'TargetHealthDescriptions[*].[Target.Id,TargetHealth.State]' \
    --output table

echo ""
echo "=== Configuration Complete ==="
echo ""
echo "STABLE ACCESS URL (for users):"
echo "  https://d225ar6c86586s.cloudfront.net"
echo ""
echo "This URL will ONLY route to Instance 2 (stable version)"
echo ""
echo "TESTING ACCESS (for development):"
echo "  Instance 1: ssh -i aws_files/chatmrpt-key.pem ec2-user@3.21.167.170"
echo "  Direct access: http://3.21.167.170:8000 (if port 8000 is open)"
echo ""
echo "TO RESTORE BOTH INSTANCES (after testing is complete):"
echo "  aws elbv2 register-targets --target-group-arn $TARGET_GROUP_ARN --targets Id=$INSTANCE_1_ID"
echo ""