# Auto Scaling Group Migration - READY TO COMPLETE

## Date: July 28, 2025

### Current Status: TWO INSTANCES SERVING TRAFFIC ✅

### What We've Achieved
- **ASG Instance**: i-06d3edfcc85a1f1c7 (healthy, serving traffic)
- **Manual Instance**: i-0183aaf795bf8f24e (healthy, serving traffic)
- **Load Balancing**: ALB distributing traffic between both instances

### Issues Encountered & Fixed
1. **Disk Space**: ASG instance had full disk from old AMI
   - Cleaned up logs to free 4.7GB
   - Note: Launch template says 40GB but instance has 20GB (will fix in next AMI)

2. **Port Registration**: ASG was registering on port 80 instead of 8080
   - Fixed by deregistering and re-registering on correct port

### Current Architecture
```
CloudFront → ALB → [Manual Instance + ASG Instance]
                    Both serving traffic successfully
```

### To Complete Migration

#### Option 1: Safe Migration (Recommended)
Keep both instances for 24 hours to ensure stability:
```bash
# Tomorrow, remove manual instance
aws elbv2 deregister-targets \
  --target-group-arn arn:aws:elasticloadbalancing:us-east-2:593543055880:targetgroup/chatmrpt-targets/80780274e6640a25 \
  --targets Id=i-0183aaf795bf8f24e

# Update ASG minimum to 1
aws autoscaling update-auto-scaling-group \
  --auto-scaling-group-name ChatMRPT-Production-ASG \
  --min-size 1
```

#### Option 2: Complete Now
Remove manual instance immediately:
```bash
# Remove manual instance from target group
aws elbv2 deregister-targets \
  --target-group-arn arn:aws:elasticloadbalancing:us-east-2:593543055880:targetgroup/chatmrpt-targets/80780274e6640a25 \
  --targets Id=i-0183aaf795bf8f24e

# Set ASG minimum to 1
aws autoscaling update-auto-scaling-group \
  --auto-scaling-group-name ChatMRPT-Production-ASG \
  --min-size 1

# Wait 5 minutes for deregistration
# Then terminate manual instance
aws ec2 terminate-instances --instance-ids i-0183aaf795bf8f24e
```

### Benefits Now Active
- ✅ **Load Distribution**: Traffic split between 2 instances
- ✅ **Redundancy**: If one fails, other continues serving
- ✅ **Auto-healing**: ASG will replace failed instances
- ✅ **Auto-scaling**: Will scale 1-3 instances based on CPU

### To Fix Later
1. Create new AMI with:
   - Cleaned disk
   - 40GB properly configured
   - Latest application code

2. Update launch template with new AMI

### Monitoring
- CloudWatch Dashboard: Shows metrics for both instances
- Email Alerts: Will notify if either instance has issues
- Target Group: Shows both instances as healthy

### Decision Required
Do you want to:
1. Keep both instances for 24 hours (safer)
2. Complete migration now (save $50/month)

Both instances are working perfectly, so either option is fine!