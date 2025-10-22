# ChatMRPT Disaster Recovery Runbook

## Quick Reference
- **Production IPs**: Check AWS Console (IPs change on restart)
- **Staging**: 18.117.115.217
- **CloudFront**: https://d225ar6c86586s.cloudfront.net
- **ALB**: http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com
- **S3 Backups**: chatmrpt-backups-20250728
- **Golden AMI**: ami-02c0a366899ceb8d2

## Emergency Contacts
- **Primary**: urbanmalaria@gmail.com (gets all alerts)
- **AWS Support**: Via AWS Console
- **SSH Key**: chatmrpt-key.pem

---

## SCENARIO 1: Website is Down

### Symptoms
- CloudFront shows 504 Gateway Timeout
- ALB not responding
- Users report site unavailable

### Quick Checks
1. **Check ALB Health**:
   ```bash
   aws elbv2 describe-target-health \
     --target-group-arn arn:aws:elasticloadbalancing:us-east-2:593543055880:targetgroup/chatmrpt-targets/80780274e6640a25
   ```

2. **Check EC2 Instances**:
   - Go to EC2 Console
   - Check instance status
   - Look for stopped or terminated instances

### Resolution Steps

#### If Instance Crashed:
1. **ASG will auto-recover** (wait 5 minutes)
2. If not, manually set ASG capacity:
   ```bash
   aws autoscaling set-desired-capacity \
     --auto-scaling-group-name ChatMRPT-Production-ASG \
     --desired-capacity 2
   ```

#### If Service Stopped:
1. SSH to instance:
   ```bash
   ssh -i chatmrpt-key.pem ec2-user@<INSTANCE-IP>
   ```
2. Check service:
   ```bash
   sudo systemctl status chatmrpt
   sudo systemctl restart chatmrpt
   ```

---

## SCENARIO 2: Database Corruption

### Symptoms
- Application errors
- Data not saving
- Strange behavior

### Recovery Steps
1. **Stop application** (prevent further corruption):
   ```bash
   sudo systemctl stop chatmrpt
   ```

2. **Restore from backup**:
   ```bash
   # List available backups
   aws s3 ls s3://chatmrpt-backups-20250728/production/
   
   # Download latest backup
   aws s3 cp s3://chatmrpt-backups-20250728/production/chatmrpt-backup-YYYYMMDD.tar.gz .
   
   # Extract database
   tar -xzf chatmrpt-backup-*.tar.gz
   
   # Replace corrupted database
   sudo cp chatmrpt.db /home/ec2-user/ChatMRPT/instance/
   ```

3. **Restart service**:
   ```bash
   sudo systemctl start chatmrpt
   ```

---

## SCENARIO 3: Disk Full

### Symptoms
- Email alert: "Low disk space"
- Application errors
- Can't upload files

### Quick Fix
```bash
# Clean logs
sudo journalctl --vacuum-size=50M
sudo rm -rf /home/ec2-user/ChatMRPT/instance/*.log

# Clean old backups
rm -rf /home/ec2-user/backups/*

# Check space
df -h
```

### Permanent Fix
- Increase disk size in AWS Console
- Or clean up old data

---

## SCENARIO 4: High Memory/CPU Alert

### Symptoms
- Email alert from CloudWatch
- Site slow or unresponsive

### Resolution
1. **Check what's consuming resources**:
   ```bash
   top
   ps aux | sort -k3 -r | head -20  # CPU
   ps aux | sort -k4 -r | head -20  # Memory
   ```

2. **If normal traffic** → ASG will auto-scale
3. **If attack/bug** → Restart service:
   ```bash
   sudo systemctl restart chatmrpt
   ```

---

## SCENARIO 5: Complete Disaster Recovery

### When to Use
- Multiple instances failed
- Region-wide AWS issue
- Major corruption

### Steps
1. **Launch new instance from AMI**:
   ```bash
   aws ec2 run-instances \
     --image-id ami-02c0a366899ceb8d2 \
     --instance-type t3.medium \
     --key-name chatmrpt-key \
     --security-group-ids sg-0b21586985a0bbfbe \
     --iam-instance-profile Name=ChatMRPT-EC2-Role
   ```

2. **Restore latest backup**:
   - Follow database restoration steps above

3. **Register with ALB**:
   ```bash
   aws elbv2 register-targets \
     --target-group-arn arn:aws:elasticloadbalancing:us-east-2:593543055880:targetgroup/chatmrpt-targets/80780274e6640a25 \
     --targets Id=<NEW-INSTANCE-ID>,Port=8080
   ```

---

## SCENARIO 6: SSL/HTTPS Issues

### Symptoms
- Browser shows "Not Secure"
- HTTPS not working

### Resolution
- CloudFront handles HTTPS automatically
- Direct users to: https://d225ar6c86586s.cloudfront.net
- ALB is HTTP only (by design)

---

## Preventive Measures

### Daily Checks
1. Visit CloudWatch Dashboard
2. Check email for alerts
3. Verify backups completed

### Weekly Tasks
1. Review CloudWatch logs for errors
2. Check disk usage trends
3. Update this runbook with new issues

### Monthly Tasks
1. Test backup restoration
2. Review AWS costs
3. Update AMI with latest code

---

## Common Commands Reference

### Service Management
```bash
sudo systemctl status chatmrpt
sudo systemctl restart chatmrpt
sudo journalctl -u chatmrpt -n 100
```

### AWS CLI
```bash
# List instances
aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,State.Name,PublicIpAddress]' --output table

# Check ALB
aws elbv2 describe-target-health --target-group-arn <ARN>

# Set ASG capacity
aws autoscaling set-desired-capacity --auto-scaling-group-name ChatMRPT-Production-ASG --desired-capacity 2
```

### Disk Management
```bash
df -h
du -sh /home/ec2-user/ChatMRPT/*
sudo journalctl --vacuum-size=50M
```

---

## Recovery Time Objectives

- **From AMI**: 10 minutes
- **From S3 backup**: 15 minutes
- **ASG auto-recovery**: 5 minutes
- **Service restart**: 1 minute

---

## Remember
1. **Don't panic** - We have multiple recovery options
2. **Check email** - CloudWatch sends alerts
3. **ASG auto-heals** - Often fixes itself
4. **Backups exist** - Daily in S3
5. **Documentation** - Everything is in /tasks/project_notes/