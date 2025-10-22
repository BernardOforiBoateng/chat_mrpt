# ROOT CAUSE IDENTIFIED: ALB Sticky Sessions Not Enabled

## The Problem
- **Staging**: Works because users connect DIRECTLY to the single EC2 instance (http://18.117.115.217:8080)
- **Production**: Fails because ALB distributes requests across multiple workers WITHOUT session affinity
- **Result**: TPR upload sets session on Worker A, but verification request goes to Worker B which doesn't see the session

## Evidence
1. No AWSALB stickiness cookie present in responses
2. Session state not persisting between requests through ALB
3. Same code works on staging (direct access) but not production (ALB access)

## The Solution: Enable ALB Sticky Sessions

### Option 1: AWS Console (Recommended)
1. Go to AWS Console → EC2 → Target Groups
2. Find the target group: `chatmrpt-tg`
3. Go to "Attributes" tab
4. Edit attributes
5. Enable "Stickiness"
6. Set duration: 1 day (86400 seconds)
7. Cookie name: AWSALB (default)
8. Save changes

### Option 2: AWS CLI
```bash
# Get the target group ARN
TARGET_GROUP_ARN=$(aws elbv2 describe-target-groups --names chatmrpt-tg --query 'TargetGroups[0].TargetGroupArn' --output text)

# Enable stickiness
aws elbv2 modify-target-group-attributes \
    --target-group-arn $TARGET_GROUP_ARN \
    --attributes Key=stickiness.enabled,Value=true \
                 Key=stickiness.type,Value=lb_cookie \
                 Key=stickiness.lb_cookie.duration_seconds,Value=86400
```

## Why This Fixes Everything
1. With sticky sessions, once a user uploads TPR data to Worker A, ALL subsequent requests go to Worker A
2. Even though Redis is configured, it doesn't matter - the session stays on the same worker
3. This is why it worked with 1 worker (all requests go to the same worker) but broke with 6 workers

## After Enabling
Users will see:
- An additional cookie: `AWSALB=...` or `AWSALBTG=...`
- TPR uploads will work without page refresh
- Session state will persist properly

## No Code Changes Needed!
The race condition fix we applied earlier can stay, but the real issue was architectural, not code-based.