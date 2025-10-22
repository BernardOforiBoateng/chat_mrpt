#!/bin/bash

# Configure ALB Sticky Sessions for ChatMRPT
echo "=========================================="
echo "Configuring ALB Sticky Sessions"
echo "=========================================="

# Get target group ARN for staging
ssh -i /tmp/chatmrpt-key3.pem -o StrictHostKeyChecking=no ec2-user@3.21.167.170 << 'EOF'

# Get instance metadata
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" 2>/dev/null)
INSTANCE_ID=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id 2>/dev/null)
REGION=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/region 2>/dev/null)

echo "Instance: $INSTANCE_ID"
echo "Region: $REGION"

# Find target group
echo -e "\nFinding target group..."
TARGET_GROUP_ARN=$(aws elbv2 describe-target-health \
    --region $REGION \
    --query "TargetHealthDescriptions[?Target.Id=='$INSTANCE_ID'].TargetGroupArn" \
    --output text 2>/dev/null | head -1)

if [ -z "$TARGET_GROUP_ARN" ]; then
    # Try alternate method
    echo "Searching for target groups..."
    aws elbv2 describe-target-groups --region $REGION \
        --query "TargetGroups[?contains(TargetGroupName, 'staging')].TargetGroupArn" \
        --output text
    
    # Get first staging target group
    TARGET_GROUP_ARN=$(aws elbv2 describe-target-groups --region $REGION \
        --query "TargetGroups[?contains(TargetGroupName, 'staging')].TargetGroupArn" \
        --output text | head -1)
fi

if [ -n "$TARGET_GROUP_ARN" ]; then
    echo "Target Group ARN: $TARGET_GROUP_ARN"
    
    # Enable stickiness
    echo -e "\nEnabling sticky sessions..."
    aws elbv2 modify-target-group-attributes \
        --region $REGION \
        --target-group-arn $TARGET_GROUP_ARN \
        --attributes \
            Key=stickiness.enabled,Value=true \
            Key=stickiness.type,Value=app_cookie \
            Key=stickiness.app_cookie.cookie_name,Value=CHATMRPT_SESSION \
            Key=stickiness.app_cookie.duration_seconds,Value=3600
    
    if [ $? -eq 0 ]; then
        echo "✅ Sticky sessions enabled!"
        
        # Verify configuration
        echo -e "\nCurrent stickiness configuration:"
        aws elbv2 describe-target-group-attributes \
            --region $REGION \
            --target-group-arn $TARGET_GROUP_ARN \
            --query "Attributes[?starts_with(Key, 'stickiness')]" \
            --output table
    else
        echo "❌ Failed to enable sticky sessions"
    fi
else
    echo "❌ Could not find target group ARN"
fi

EOF

echo ""
echo "=========================================="
echo "Configuration Complete!"
echo "=========================================="