#!/bin/bash
# Discover all production instances behind the ALB

set -e

echo "=== Discovering Production Instances ==="

# Get ALB ARN
ALB_ARN=$(aws elbv2 describe-load-balancers --region us-east-2 \
    --query "LoadBalancers[?contains(DNSName, 'chatmrpt-alb')].LoadBalancerArn" \
    --output text)

if [ -z "$ALB_ARN" ]; then
    echo "❌ Could not find ChatMRPT ALB"
    exit 1
fi

# Get target group
TARGET_GROUP_ARN=$(aws elbv2 describe-target-groups --region us-east-2 \
    --load-balancer-arn "$ALB_ARN" \
    --query "TargetGroups[0].TargetGroupArn" \
    --output text)

# Get all healthy instances
INSTANCE_IDS=$(aws elbv2 describe-target-health --region us-east-2 \
    --target-group-arn "$TARGET_GROUP_ARN" \
    --query "TargetHealthDescriptions[?TargetHealth.State=='healthy'].Target.Id" \
    --output text)

# Get private IPs for instances
INSTANCE_IPS=""
for instance_id in $INSTANCE_IDS; do
    IP=$(aws ec2 describe-instances --region us-east-2 \
        --instance-ids "$instance_id" \
        --query "Reservations[0].Instances[0].PrivateIpAddress" \
        --output text)
    INSTANCE_IPS="$INSTANCE_IPS $IP"
done

echo "Found instances: $INSTANCE_IPS"
echo "$INSTANCE_IPS" > deployment/configs/production_instances.txt
