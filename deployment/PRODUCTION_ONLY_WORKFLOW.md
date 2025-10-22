# Production-Only Deployment Workflow

## Why This Change?
- **Cost Savings**: Running 2 staging instances costs ~$60/month
- **Efficiency**: Most testing can be done locally
- **Simplicity**: One environment to manage instead of two

## Safe Production Deployment Strategy

### The Setup
- **2 Production Instances** behind Application Load Balancer (ALB)
  - Instance 1: 172.31.44.52
  - Instance 2: 172.31.43.200
- **ALB URL**: http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com

### How It Works
1. **Rolling Updates**: Update one instance at a time
2. **Zero Downtime**: ALB routes traffic to healthy instance while other updates
3. **Rollback Ready**: If issues occur, only one instance is affected

## Deployment Commands

### Quick Deploy (Single File)
```bash
# Make script executable
chmod +x deployment/safe_production_deploy.sh

# Deploy a single file
./deployment/safe_production_deploy.sh app/core/agent.py

# Deploy multiple files
./deployment/safe_production_deploy.sh app/core/agent.py app/static/js/modules/chat/core/message-handler.js
```

### Manual Deployment (More Control)
```bash
# Step 1: Deploy to Instance 1 only
scp -i /tmp/chatmrpt-key2.pem <file> ec2-user@172.31.44.52:/home/ec2-user/ChatMRPT/
ssh -i /tmp/chatmrpt-key2.pem ec2-user@172.31.44.52 'sudo systemctl restart chatmrpt'

# Step 2: Test Instance 1 (ALB will route some traffic to it)
curl http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com/ping

# Step 3: If good, deploy to Instance 2
scp -i /tmp/chatmrpt-key2.pem <file> ec2-user@172.31.43.200:/home/ec2-user/ChatMRPT/
ssh -i /tmp/chatmrpt-key2.pem ec2-user@172.31.43.200 'sudo systemctl restart chatmrpt'
```

## Best Practices

### 1. **Test Locally First**
```bash
# Always test in local environment
source chatmrpt_venv_new/bin/activate
python run.py
# Test at http://localhost:5000
```

### 2. **Deploy During Low Traffic**
- Best times: 2-4 AM EST
- Check CloudWatch for traffic patterns

### 3. **Monitor After Deployment**
```bash
# Check logs on both instances
ssh -i /tmp/chatmrpt-key2.pem ec2-user@172.31.44.52 'sudo journalctl -u chatmrpt -f'
```

### 4. **Quick Rollback**
```bash
# If issues occur, quickly revert
ssh -i /tmp/chatmrpt-key2.pem ec2-user@172.31.44.52 'cd ChatMRPT && git checkout <file>'
ssh -i /tmp/chatmrpt-key2.pem ec2-user@172.31.44.52 'sudo systemctl restart chatmrpt'
```

## Staging Management

### Shutdown Staging (Save Money)
```bash
chmod +x deployment/shutdown_staging.sh
./deployment/shutdown_staging.sh
```

### Restart Staging (If Needed Later)
```bash
# Start instances
aws ec2 start-instances --instance-ids i-0994615951d0b9563 i-0f3b25b72f18a5037 --region us-east-2

# Wait 2-3 minutes for boot
# IPs will remain the same (Elastic IPs)
```

## Cost Analysis

### Current (With Staging)
- Production: 2 × t3.medium = ~$60/month
- Staging: 2 × t3.medium = ~$60/month
- **Total: ~$120/month**

### New (Production Only)
- Production: 2 × t3.medium = ~$60/month
- Staging: Stopped (only EBS storage ~$2/month)
- **Total: ~$62/month**

### Savings: ~$58/month (~48% reduction)

## Emergency Procedures

### If Both Production Instances Fail
1. **Restart staging immediately**:
   ```bash
   aws ec2 start-instances --instance-ids i-0994615951d0b9563 i-0f3b25b72f18a5037 --region us-east-2
   ```

2. **Point DNS to staging ALB** (temporary):
   - Staging ALB: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com

3. **Fix production** while staging serves traffic

### If Deployment Goes Wrong
1. **Immediate Rollback**:
   ```bash
   # On affected instance
   ssh -i /tmp/chatmrpt-key2.pem ec2-user@<instance-ip> '
     cd /home/ec2-user/ChatMRPT
     git stash
     git pull origin main
     sudo systemctl restart chatmrpt
   '
   ```

2. **Remove from ALB** (if critical):
   ```bash
   aws elbv2 deregister-targets \
     --target-group-arn <target-group-arn> \
     --targets Id=<instance-id>
   ```

## Monitoring

### Health Checks
- ALB Health: http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com/ping
- CloudWatch Dashboards: Check AWS Console
- Instance Logs: `sudo journalctl -u chatmrpt -f`

### Key Metrics to Watch
1. Response time
2. Error rate
3. CPU utilization
4. Memory usage

## Summary

✅ **Benefits**:
- 48% cost reduction
- Simpler management
- Same availability (2 instances)

⚠️ **Risks** (Mitigated):
- No staging buffer → Test locally first
- Direct production updates → Rolling updates minimize risk
- No staging for big changes → Can restart staging when needed

This workflow maintains high availability while significantly reducing costs!