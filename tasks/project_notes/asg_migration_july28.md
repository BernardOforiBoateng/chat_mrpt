# Auto Scaling Group Migration

## Date: July 28, 2025

### Migration Status: IN PROGRESS

### What We're Doing
Migrating from a single manual EC2 instance to an Auto Scaling Group for:
- Automatic failover if instance fails
- Automatic scaling based on CPU usage
- Zero-downtime deployments
- Better reliability

### Current State
- **Manual Instance**: i-0183aaf795bf8f24e (healthy, port 8080)
- **ASG Instance**: i-06d3edfcc85a1f1c7 (launched, registering on port 8080)

### Migration Steps

#### 1. Launch ASG Instance ✅
```bash
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name ChatMRPT-Production-ASG \
  --desired-capacity 1
```

#### 2. Fix Port Registration ✅
- ASG was registering on port 80 instead of 8080
- Deregistered and re-registered on correct port

#### 3. Wait for Health Check ⏳
- Target group needs 2 successful health checks (60 seconds)
- Instance must show as "healthy" before proceeding

#### 4. Test Both Instances Working
- Verify traffic is distributed between both instances
- Check application functionality

#### 5. Remove Manual Instance
```bash
# After confirming ASG instance works
aws elbv2 deregister-targets \
  --target-group-arn arn:aws:elasticloadbalancing:us-east-2:593543055880:targetgroup/chatmrpt-targets/80780274e6640a25 \
  --targets Id=i-0183aaf795bf8f24e
```

#### 6. Update ASG Minimum
```bash
# Ensure ASG always has at least 1 instance
aws autoscaling update-auto-scaling-group \
  --auto-scaling-group-name ChatMRPT-Production-ASG \
  --min-size 1
```

#### 7. Terminate Manual Instance
- Only after confirming everything works
- Can keep as backup for a few days if preferred

### Benefits After Migration
- **Auto-healing**: If instance fails, ASG launches replacement
- **Auto-scaling**: Scales 1-3 instances based on CPU
- **Rolling updates**: Deploy new versions without downtime
- **Cost optimization**: Scale down during low usage

### Rollback Plan
If issues occur:
1. Keep manual instance in target group
2. Set ASG desired capacity to 0
3. Continue using manual instance
4. Investigate and fix issues

### Notes
- Launch template includes IAM instance profile
- 40GB disk configured
- CloudWatch agent pre-installed
- All instances register on port 8080