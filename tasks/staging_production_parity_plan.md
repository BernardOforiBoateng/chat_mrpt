# Staging-Production Parity Implementation Plan

## Goal
Make staging environment identical to production to eliminate deployment issues and ensure true testing before production deployment.

## Current State

### Production Architecture
- **Load Balancer**: ALB (chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com)
- **Instances**: 2 EC2 instances
  - Instance 1: i-06d3edfcc85a1f1c7 (172.31.44.52)
  - Instance 2: i-0183aaf795bf8f24e (172.31.43.200)
- **Redis**: ElastiCache (chatmrpt-redis-production)
- **Workers**: 6-7 Gunicorn workers per instance
- **Access**: Through ALB only

### Staging Architecture (Current)
- **Load Balancer**: None (direct access)
- **Instances**: 1 EC2 instance (18.117.115.217)
- **Redis**: ElastiCache (chatmrpt-redis-staging)
- **Workers**: 2-7 Gunicorn workers
- **Access**: Direct IP access

## Implementation Steps

### Phase 1: Prepare Current Staging Instance
1. **Take Snapshot**
   ```bash
   aws ec2 create-snapshot --region us-east-2 \
     --volume-id <staging-volume-id> \
     --description "Staging before ALB migration - $(date)"
   ```

2. **Update Security Groups**
   - Create new security group: `chatmrpt-staging-alb-sg`
   - Allow inbound HTTP/HTTPS from anywhere
   - Allow health checks from ALB

3. **Verify Redis Configuration**
   - Ensure staging uses: `chatmrpt-redis-staging`
   - Test Redis connectivity

### Phase 2: Create Second Staging Instance
1. **Create AMI from Current Staging**
   ```bash
   aws ec2 create-image --region us-east-2 \
     --instance-id <staging-instance-id> \
     --name "chatmrpt-staging-base-$(date +%Y%m%d)"
   ```

2. **Launch Second Instance**
   ```bash
   aws ec2 run-instances --region us-east-2 \
     --image-id <ami-id> \
     --instance-type t3.medium \
     --key-name chatmrpt-key \
     --security-group-ids <sg-id> \
     --subnet-id <subnet-id> \
     --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=chatmrpt-staging-2}]'
   ```

3. **Configure Second Instance**
   - Verify ChatMRPT service starts
   - Check Redis connectivity
   - Ensure same configuration as instance 1

### Phase 3: Set Up Application Load Balancer
1. **Create Target Group**
   ```bash
   aws elbv2 create-target-group \
     --name chatmrpt-staging-targets \
     --protocol HTTP \
     --port 8080 \
     --vpc-id <vpc-id> \
     --health-check-path /health \
     --health-check-interval-seconds 30 \
     --region us-east-2
   ```

2. **Register Both Instances**
   ```bash
   aws elbv2 register-targets \
     --target-group-arn <target-group-arn> \
     --targets Id=<instance-1-id>,Port=8080 Id=<instance-2-id>,Port=8080 \
     --region us-east-2
   ```

3. **Create Load Balancer**
   ```bash
   aws elbv2 create-load-balancer \
     --name chatmrpt-staging-alb \
     --subnets <subnet-1> <subnet-2> \
     --security-groups <alb-sg-id> \
     --region us-east-2
   ```

4. **Configure Listener**
   ```bash
   aws elbv2 create-listener \
     --load-balancer-arn <alb-arn> \
     --protocol HTTP \
     --port 80 \
     --default-actions Type=forward,TargetGroupArn=<target-group-arn> \
     --region us-east-2
   ```

5. **Enable Sticky Sessions**
   ```bash
   aws elbv2 modify-target-group-attributes \
     --target-group-arn <target-group-arn> \
     --attributes \
       Key=stickiness.enabled,Value=true \
       Key=stickiness.type,Value=lb_cookie \
       Key=stickiness.lb_cookie.duration_seconds,Value=86400 \
     --region us-east-2
   ```

### Phase 4: Update Configuration
1. **Update Instance Security Groups**
   - Remove public HTTP access from instances
   - Only allow traffic from ALB security group

2. **Update DNS/Access Points**
   - Point staging DNS to new ALB
   - Update documentation with new staging URL

3. **Update Deployment Scripts**
   - Modify to deploy to both staging instances
   - Use same pattern as production deployment

### Phase 5: Testing
1. **Health Checks**
   - Verify both instances healthy in target group
   - Test ALB endpoint responds

2. **Functionality Tests**
   - Upload data through ALB
   - Run analysis
   - Test session persistence
   - Verify Redis session sharing

3. **Load Distribution**
   - Monitor requests going to both instances
   - Verify sticky sessions working

### Phase 6: Update Documentation
1. **Update CLAUDE.md**
   - New staging architecture
   - Deployment procedures
   - Access instructions

2. **Update Deployment Scripts**
   ```bash
   deployment/
   ├── deploy_to_staging.sh      # New script for staging
   ├── deploy_to_production.sh   # Existing production script
   └── deploy_to_all.sh         # Deploy to both environments
   ```

## Configuration Details

### Instance Configuration
Both staging instances should have:
- Same OS and packages
- Identical ChatMRPT code
- Same Gunicorn configuration
- Shared Redis endpoint
- Identical environment variables

### ALB Configuration
- **Health Check**: `/health` endpoint
- **Sticky Sessions**: 24 hours
- **Idle Timeout**: 60 seconds
- **Cross-Zone Load Balancing**: Enabled

### Security Groups
1. **ALB Security Group** (chatmrpt-staging-alb-sg)
   - Inbound: 80/443 from 0.0.0.0/0
   - Outbound: 8080 to instance SG

2. **Instance Security Group** (chatmrpt-staging-instance-sg)
   - Inbound: 8080 from ALB SG
   - Inbound: 22 from specific IPs
   - Outbound: All traffic

## Benefits of This Setup

1. **True Testing Environment**
   - Identical architecture to production
   - Catch multi-instance issues before production
   - Test load balancing behavior

2. **Reliable Deployments**
   - Same deployment process for staging and production
   - No more "works in staging, fails in production"
   - Confidence in deployment process

3. **Better Development Workflow**
   - Test → Staging (multi-instance) → Production (multi-instance)
   - Rollback capability at each stage
   - Clear promotion path

## Cost Considerations

### Additional Monthly Costs (Estimated)
- 1 additional t3.medium instance: ~$30/month
- 1 ALB: ~$20/month
- Data transfer: ~$5/month
- **Total**: ~$55/month additional

### Cost Optimization Options
- Use t3.small instances for staging (save $15/month)
- Schedule staging instances (stop nights/weekends)
- Share ALB with other services if available

## Rollback Plan

If issues arise:
1. Route traffic back to single instance
2. Delete ALB and second instance
3. Restore direct IP access
4. Revert to original staging setup

## Success Criteria

1. ✅ Two staging instances running behind ALB
2. ✅ Sticky sessions working correctly
3. ✅ Redis sessions shared between instances
4. ✅ Deployment scripts work for both instances
5. ✅ Feature parity with production environment
6. ✅ All tests pass through ALB endpoint

## Timeline

- **Day 1**: Preparation and snapshots
- **Day 2**: Launch second instance and configure
- **Day 3**: Set up ALB and test
- **Day 4**: Update scripts and documentation
- **Day 5**: Final testing and validation

## Next Steps

1. Get approval for additional AWS resources
2. Schedule maintenance window
3. Create snapshots of current state
4. Begin implementation following this plan