#!/bin/bash
# Check and fix ALB sticky session configuration
# This is why staging works but production doesn't!

set -e

echo "=== ALB Session Affinity Investigation ==="
echo "Date: $(date)"
echo ""
echo "CRITICAL FINDING: Staging has no ALB, Production has ALB"
echo "This explains why session-based features work in staging but not production!"
echo ""

SSH_KEY="/tmp/chatmrpt-key2.pem"
STAGING_HOST="ec2-user@18.117.115.217"

# Ensure we have the SSH key
if [ ! -f "$SSH_KEY" ]; then
    cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
    chmod 600 /tmp/chatmrpt-key2.pem
fi

echo "📋 Step 1: Checking ALB Configuration..."
echo ""

ssh -i "$SSH_KEY" "$STAGING_HOST" << 'CHECK_ALB'
    # Get ALB and target group info
    echo "Finding ALB and Target Group..."
    
    # Find the ALB
    ALB_ARN=$(aws elbv2 describe-load-balancers --region us-east-2 \
        --query "LoadBalancers[?contains(DNSName, 'chatmrpt-alb')].LoadBalancerArn" \
        --output text)
    
    if [ -z "$ALB_ARN" ]; then
        echo "❌ Could not find ChatMRPT ALB"
        exit 1
    fi
    
    echo "✅ Found ALB: $ALB_ARN"
    
    # Get target group
    TARGET_GROUP_ARN=$(aws elbv2 describe-target-groups --region us-east-2 \
        --load-balancer-arn "$ALB_ARN" \
        --query "TargetGroups[0].TargetGroupArn" \
        --output text)
    
    echo "✅ Found Target Group: $TARGET_GROUP_ARN"
    echo ""
    
    # Check stickiness configuration
    echo "📋 Current Stickiness Configuration:"
    aws elbv2 describe-target-group-attributes --region us-east-2 \
        --target-group-arn "$TARGET_GROUP_ARN" \
        --query "Attributes[?Key=='stickiness.enabled' || Key=='stickiness.type' || Key=='stickiness.lb_cookie.duration_seconds']" \
        --output table
    
    echo ""
    
    # Check if stickiness is enabled
    STICKINESS_ENABLED=$(aws elbv2 describe-target-group-attributes --region us-east-2 \
        --target-group-arn "$TARGET_GROUP_ARN" \
        --query "Attributes[?Key=='stickiness.enabled'].Value" \
        --output text)
    
    if [ "$STICKINESS_ENABLED" == "true" ]; then
        echo "✅ Sticky sessions are ENABLED"
        
        # Get duration
        DURATION=$(aws elbv2 describe-target-group-attributes --region us-east-2 \
            --target-group-arn "$TARGET_GROUP_ARN" \
            --query "Attributes[?Key=='stickiness.lb_cookie.duration_seconds'].Value" \
            --output text)
        
        echo "   Duration: $DURATION seconds"
        
        if [ "$DURATION" -lt "3600" ]; then
            echo "⚠️  Duration is less than 1 hour. This might be too short!"
        fi
    else
        echo "❌ Sticky sessions are DISABLED!"
        echo "   This is causing the session synchronization issues!"
    fi
    
    echo ""
    echo "📋 Step 2: Fix Recommendation"
    echo ""
    
    if [ "$STICKINESS_ENABLED" != "true" ]; then
        echo "To enable sticky sessions, run:"
        echo ""
        echo "aws elbv2 modify-target-group-attributes \\"
        echo "    --region us-east-2 \\"
        echo "    --target-group-arn $TARGET_GROUP_ARN \\"
        echo "    --attributes \\"
        echo "        Key=stickiness.enabled,Value=true \\"
        echo "        Key=stickiness.type,Value=lb_cookie \\"
        echo "        Key=stickiness.lb_cookie.duration_seconds,Value=86400"
        echo ""
        echo "This will enable 24-hour sticky sessions."
    else
        echo "Sticky sessions are already enabled."
        echo ""
        echo "Other potential issues:"
        echo "1. Cookie duration might be too short"
        echo "2. Browser blocking third-party cookies"
        echo "3. ALB health checks causing instance changes"
    fi
    
    # Check target health
    echo ""
    echo "📋 Step 3: Checking Target Health..."
    aws elbv2 describe-target-health --region us-east-2 \
        --target-group-arn "$TARGET_GROUP_ARN" \
        --output table
CHECK_ALB

echo ""
echo "=== Summary ==="
echo ""
echo "The key difference between staging and production:"
echo "- STAGING: Direct access to instance (no load balancer)"
echo "- PRODUCTION: Behind Application Load Balancer (ALB)"
echo ""
echo "Without sticky sessions on the ALB:"
echo "1. User's requests go to different workers randomly"
echo "2. Session state updates on Worker A aren't seen by Worker B"
echo "3. Redis helps, but there's still a timing window"
echo ""
echo "This perfectly explains why:"
echo "- TPR download links don't appear (different worker handles the download check)"
echo "- ITN export seems incomplete (different worker handles the export)"
echo "- Everything works after refresh (might hit the same worker)"
echo ""
echo "Next steps:"
echo "1. Enable sticky sessions on the ALB (if not already enabled)"
echo "2. Set appropriate cookie duration (24 hours recommended)"
echo "3. Test to confirm the fix works"