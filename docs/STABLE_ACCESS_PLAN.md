# Stable Access Plan for ChatMRPT

## The Solution: Instance Isolation

While you make major changes, we'll use this strategy:

### Instance Roles:
- **Instance 2 (18.220.103.20)**: STABLE - Serves all user traffic
- **Instance 1 (3.21.167.170)**: TESTING - For development and changes

## Stable Link for Users

**Users can continue accessing ChatMRPT at:**
```
https://d225ar6c86586s.cloudfront.net
```

This link will remain stable and functional throughout your changes.

## How It Works

1. **Remove Instance 1 from Load Balancer**
   - All traffic routes to stable Instance 2
   - Users experience no disruption

2. **Make Changes on Instance 1**
   - Test all changes on Instance 1
   - Instance 1 is isolated from production traffic

3. **After Testing is Complete**
   - Deploy tested changes to Instance 2
   - Re-add Instance 1 to load balancer

## Quick Commands

### To Enable Stable Access (run this now):
```bash
chmod +x configure_stable_access.sh
./configure_stable_access.sh
```

### To Make Changes (on Instance 1 only):
```bash
# SSH to Instance 1 (testing)
ssh -i aws_files/chatmrpt-key.pem ec2-user@3.21.167.170

# Make your changes, test them
# Users won't be affected since they're using Instance 2
```

### To Restore Normal Operation (after changes are tested):
```bash
# Deploy tested changes to Instance 2
ssh -i aws_files/chatmrpt-key.pem ec2-user@18.220.103.20
# ... deploy the tested changes ...

# Re-add Instance 1 to load balancer
aws elbv2 register-targets \
    --target-group-arn arn:aws:elasticloadbalancing:us-east-2:992382473315:targetgroup/chatmrpt-staging-tg/b3c7f8e9e1f5c4d7 \
    --targets Id=i-0994615951d0b9563
```

## Important Notes

- **DO NOT modify Instance 2** until changes are tested on Instance 1
- **Users will continue using** https://d225ar6c86586s.cloudfront.net without interruption
- **Test thoroughly on Instance 1** before deploying to Instance 2
- **CloudFront cache** may need invalidation after major changes

## Summary

✅ **Stable link for users**: https://d225ar6c86586s.cloudfront.net
✅ **No downtime** during your development
✅ **Safe testing** on Instance 1 without affecting users
✅ **Easy rollback** if needed (Instance 2 remains unchanged)