# Stable Working Link Configuration
Created: 2024-09-23

## Approach: Instance Isolation Strategy

### Configuration Plan
We'll maintain Instance 2 as the **STABLE PRODUCTION** instance while using Instance 1 for testing changes.

## Instance Roles

### Instance 1 (3.21.167.170) - TESTING
- Will receive all new changes
- Used for testing and validation
- Can be accessed for testing

### Instance 2 (18.220.103.20) - STABLE
- **FROZEN at current working state**
- Contains all TPR fixes that are working
- Will NOT receive any new changes until tested

## Access Methods

### 1. Through Load Balancer (Mixed Traffic)
Since the ALB distributes traffic between both instances, users might randomly hit either the stable or testing instance.
- URL: https://d225ar6c86586s.cloudfront.net
- Behavior: 50/50 chance of hitting stable vs testing instance

### 2. Direct Instance Access (Requires Security Group Update)
To access the stable instance directly:
```bash
# Need to open port 8000 in security group
# Then access at: http://18.220.103.20:8000
```

### 3. Temporary Workaround - Remove Instance 1 from Target Group
We can temporarily remove Instance 1 from the ALB target group so ALL traffic goes to the stable Instance 2:

```bash
# AWS CLI command to deregister Instance 1 from target group
aws elbv2 deregister-targets \
  --target-group-arn [TARGET_GROUP_ARN] \
  --targets Id=i-0994615951d0b9563

# To re-register after testing:
aws elbv2 register-targets \
  --target-group-arn [TARGET_GROUP_ARN] \
  --targets Id=i-0994615951d0b9563
```

## Recommended Approach

### For Immediate Stable Access:
1. **Temporarily remove Instance 1 from the load balancer**
2. All traffic through CloudFront will go to stable Instance 2
3. Test changes on Instance 1 via SSH or direct connection
4. Once changes are validated, update Instance 2 and re-add Instance 1

### Commands to Implement:

#### Step 1: Remove Instance 1 from Load Balancer
This ensures https://d225ar6c86586s.cloudfront.net only hits the stable instance

#### Step 2: Test on Instance 1
Deploy and test all changes on Instance 1 without affecting production

#### Step 3: Once Validated
- Update Instance 2 with tested changes
- Re-add Instance 1 to load balancer

## Important Notes

1. **Current State of Instance 2**:
   - Has all TPR state name fixes
   - Hardcoded fixes for Ebonyi, Kebbi, Plateau, Nasarawa
   - Stable and working

2. **Backup Available**:
   - Instance 2 backup: `/home/ec2-user/ChatMRPT_code_only_backup_20250923_161113.tar.gz`
   - Can restore if needed

3. **Do NOT Deploy to Instance 2**:
   - Keep Instance 2 frozen
   - Only deploy new changes to Instance 1 for testing

## Quick Reference

**Stable Link** (after removing Instance 1 from LB):
- https://d225ar6c86586s.cloudfront.net

**Instance to Update**:
- Instance 1 (3.21.167.170) ONLY

**Instance to Keep Stable**:
- Instance 2 (18.220.103.20) DO NOT MODIFY