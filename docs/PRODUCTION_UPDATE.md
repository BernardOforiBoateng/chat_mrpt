# ChatMRPT Production Environment Update

## 🎯 Key Changes

### Production Environment Consolidation
- **NEW PRODUCTION**: The former "staging" environment is now the ONLY production
- **OLD PRODUCTION**: Should be STOPPED/DISABLED to prevent confusion

## 📍 Current Production Infrastructure

### Active Production Environment
- **Instance 1**: `i-0994615951d0b9563` (IP: 3.21.167.170)
- **Instance 2**: `i-0f3b25b72f18a5037` (IP: 18.220.103.20)
- **Primary URL (HTTPS)**: https://d225ar6c86586s.cloudfront.net
- **ALB URL (HTTP)**: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com
- **Redis**: `chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com:6379`

### Disabled Infrastructure (DO NOT USE)
- ~~Old Instance 1: `i-06d3edfcc85a1f1c7` (172.31.44.52)~~ **[TO BE STOPPED]**
- ~~Old Instance 2: `i-0183aaf795bf8f24e` (172.31.43.200)~~ **[TO BE STOPPED]**
- ~~Old ALB: http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com~~
- ~~Old Redis: chatmrpt-redis-production.1b3pmt.0001.use2.cache.amazonaws.com:6379~~

## 🚀 Deployment Process

### Simple Deployment Command
```bash
# Deploy specific files to production
./deploy_production.sh app/core/request_interpreter.py app/tools/complete_analysis_tools.py

# Deploy all tools
./deploy_production.sh app/tools/*.py

# Deploy multiple files
./deploy_production.sh app/web/routes/analysis_routes.py app/services/agent.py
```

### Manual Deployment (if needed)
```bash
# SSH to production instances
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170  # Instance 1
ssh -i /tmp/chatmrpt-key2.pem ec2-user@18.220.103.20  # Instance 2

# Deploy to both instances
for ip in 3.21.167.170 18.220.103.20; do
    scp -i /tmp/chatmrpt-key2.pem <files> ec2-user@$ip:/home/ec2-user/ChatMRPT/
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$ip 'sudo systemctl restart chatmrpt'
done
```

## 🛑 Disable Old Production

To prevent confusion and accidental deployments to the wrong environment:

```bash
# Run this to stop old production instances
./disable_old_production.sh
```

This will:
1. Stop instances `i-06d3edfcc85a1f1c7` and `i-0183aaf795bf8f24e`
2. Prevent accidental deployments to old infrastructure
3. Save costs by not running unused instances

## ✅ What's Been Fixed

### State Management Solution Deployed
- **WorkflowStateManager**: Centralized state management
- **No more false "analysis already completed" messages**
- **Clean workflow transitions**
- **Consistent behavior across workers**

### Infrastructure Simplified
- Single production environment (no staging/production confusion)
- Clear deployment process
- Updated documentation

## 📋 Action Items

1. **Disable old production instances**:
   ```bash
   ./disable_old_production.sh
   ```
   Or manually stop in AWS Console: EC2 → Instances → Stop instances

2. **Update any CI/CD pipelines** to point to new production IPs:
   - 3.21.167.170
   - 18.220.103.20

3. **Update monitoring/alerts** to remove old production instances

4. **Update DNS/CloudFront** if needed (currently working correctly)

5. **Remove old deployment scripts** that reference old production:
   ```bash
   rm deployment/deploy_to_staging.sh  # No longer needed
   rm deployment/deploy_to_old_production.sh  # If exists
   ```

## 🔍 Verification

### Check Production Health
```bash
# Check both instances are running
curl -I http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com/ping

# Check CloudFront
curl -I https://d225ar6c86586s.cloudfront.net/ping

# SSH and check logs
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 'sudo journalctl -u chatmrpt -n 50'
```

### Test State Management Fix
1. Go to https://d225ar6c86586s.cloudfront.net
2. Upload data via Data Analysis tab
3. Complete TPR analysis
4. Transition to main workflow
5. Request risk analysis - should NOT say "already completed"

## 📝 Notes

- The ALB still has "staging" in its name but it's actually production
- CloudFront correctly points to this ALB
- All user traffic goes through CloudFront (HTTPS)
- Both production instances must be deployed to maintain consistency

## 🆘 Troubleshooting

If deployment fails:
1. Check SSH key permissions: `chmod 600 /tmp/chatmrpt-key2.pem`
2. Verify instance IPs haven't changed in AWS Console
3. Check instance status: `aws ec2 describe-instances --region us-east-2`
4. Use AWS Systems Manager if direct SSH fails

---

**Last Updated**: August 27, 2025
**Updated By**: System Migration
**Status**: ✅ Production Active | ⚠️ Old Production To Be Disabled