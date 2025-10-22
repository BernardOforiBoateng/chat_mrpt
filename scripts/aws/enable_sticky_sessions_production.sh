#!/bin/bash

echo "======================================================"
echo "   ENABLING STICKY SESSIONS ON PRODUCTION ALB"
echo "======================================================"
echo ""
echo "This will fix the issue where numeric selections (1, 2, 3)"
echo "get routed to different instances and lose context."
echo ""

# Configuration
REGION="us-east-2"
STICKINESS_DURATION=3600  # 1 hour in seconds

# First, find the production ALB
echo "🔍 Finding Production ALB..."
ALB_ARN=$(aws elbv2 describe-load-balancers \
    --region $REGION \
    --query "LoadBalancers[?DNSName=='chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com'].LoadBalancerArn" \
    --output text)

if [ -z "$ALB_ARN" ] || [ "$ALB_ARN" == "None" ]; then
    echo "⚠️  Couldn't find ALB by DNS name, searching by name pattern..."
    ALB_ARN=$(aws elbv2 describe-load-balancers \
        --region $REGION \
        --query "LoadBalancers[?contains(LoadBalancerName, 'chatmrpt')].LoadBalancerArn" \
        --output text | head -1)
fi

if [ -z "$ALB_ARN" ] || [ "$ALB_ARN" == "None" ]; then
    echo "❌ Could not find production ALB"
    echo ""
    echo "Available ALBs in $REGION:"
    aws elbv2 describe-load-balancers --region $REGION \
        --query "LoadBalancers[*].[LoadBalancerName,DNSName]" \
        --output table
    exit 1
fi

ALB_NAME=$(echo $ALB_ARN | rev | cut -d'/' -f2 | rev)
echo "✅ Found ALB: $ALB_NAME"

# Get the target group(s) for this ALB
echo ""
echo "🔍 Finding Target Group(s)..."
TARGET_GROUP_ARNS=$(aws elbv2 describe-target-groups \
    --region $REGION \
    --load-balancer-arn $ALB_ARN \
    --query "TargetGroups[*].TargetGroupArn" \
    --output text)

if [ -z "$TARGET_GROUP_ARNS" ]; then
    echo "❌ No target groups found for this ALB"
    exit 1
fi

# Process each target group
for TG_ARN in $TARGET_GROUP_ARNS; do
    TG_NAME=$(echo $TG_ARN | rev | cut -d':' -f1 | rev)
    echo ""
    echo "📋 Processing Target Group: $TG_NAME"
    
    # Check current stickiness settings
    echo "  Checking current settings..."
    STICKINESS_ENABLED=$(aws elbv2 describe-target-group-attributes \
        --region $REGION \
        --target-group-arn $TG_ARN \
        --query "Attributes[?Key=='stickiness.enabled'].Value" \
        --output text)
    
    if [ "$STICKINESS_ENABLED" == "true" ]; then
        CURRENT_DURATION=$(aws elbv2 describe-target-group-attributes \
            --region $REGION \
            --target-group-arn $TG_ARN \
            --query "Attributes[?Key=='stickiness.lb_cookie.duration_seconds'].Value" \
            --output text)
        echo "  ⚠️  Stickiness already enabled (Duration: ${CURRENT_DURATION}s)"
        echo "  Updating duration to ${STICKINESS_DURATION}s..."
    else
        echo "  ❌ Stickiness currently DISABLED"
        echo "  Enabling sticky sessions..."
    fi
    
    # Enable/Update stickiness
    aws elbv2 modify-target-group-attributes \
        --region $REGION \
        --target-group-arn $TG_ARN \
        --attributes \
            Key=stickiness.enabled,Value=true \
            Key=stickiness.type,Value=lb_cookie \
            Key=stickiness.lb_cookie.duration_seconds,Value=$STICKINESS_DURATION \
        --output text > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo "  ✅ Sticky sessions configured successfully!"
    else
        echo "  ❌ Failed to configure sticky sessions"
    fi
done

echo ""
echo "🔍 Verifying configuration..."
echo ""
echo "Target Group Stickiness Settings:"
echo "---------------------------------"
for TG_ARN in $TARGET_GROUP_ARNS; do
    TG_NAME=$(echo $TG_ARN | rev | cut -d':' -f1 | rev)
    echo ""
    echo "Target Group: ${TG_NAME}"
    aws elbv2 describe-target-group-attributes \
        --region $REGION \
        --target-group-arn $TG_ARN \
        --query "Attributes[?contains(Key, 'stickiness')].[Key,Value]" \
        --output table
done

echo ""
echo "======================================================"
echo "   ✅ STICKY SESSIONS CONFIGURATION COMPLETE!"
echo "======================================================"
echo ""
echo "What this means for your users:"
echo "• When a user uploads a file and sees options (1, 2, 3)"
echo "• Their selection will go to THE SAME instance"
echo "• No more confusion about what '2' means!"
echo ""
echo "Technical Details:"
echo "• Cookie Name: AWSALB"
echo "• Duration: $STICKINESS_DURATION seconds (1 hour)"
echo "• Method: Load Balancer Cookie"
echo ""
echo "The fix is IMMEDIATE - no restart required!"
echo ""
echo "Test it now at:"
echo "http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"
echo ""