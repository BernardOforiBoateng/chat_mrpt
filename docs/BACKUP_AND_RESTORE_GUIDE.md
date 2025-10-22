# 📦 ChatMRPT Backup and Restore Guide

**Created**: August 27, 2025  
**Purpose**: Complete backup documentation for staging-to-production transition

---

## 🎯 Quick Start

### Run Complete Backup
```bash
# 1. Fix line endings and make executable
sed -i 's/\r$//' backup_staging_environment.sh github_backup_staging.sh
chmod +x backup_staging_environment.sh github_backup_staging.sh

# 2. Run AWS infrastructure backup
./backup_staging_environment.sh

# 3. Run GitHub repository backup
./github_backup_staging.sh
```

---

## 📋 Backup Components

### 1. AWS Infrastructure Backups

| Component | Backup Method | Location | Restore Time |
|-----------|--------------|----------|--------------|
| **EC2 Instances** | AMI Snapshots | AWS EC2 Console | 5-10 minutes |
| **Application Code** | Tar archives | `backups/staging_*/data/` | 5 minutes |
| **Environment Variables** | Text files | `backups/staging_*/configs/` | 1 minute |
| **User Uploads** | Tar archives | `backups/staging_*/data/` | 5-10 minutes |
| **Redis Data** | ElastiCache Snapshot | AWS ElastiCache Console | 10-15 minutes |
| **Security Groups** | JSON exports | `backups/staging_*/aws/` | 5 minutes |
| **Load Balancer Config** | JSON exports | `backups/staging_*/aws/` | 5 minutes |

### 2. GitHub Repository Backups

| Component | Backup Method | Location | Restore Time |
|-----------|--------------|----------|--------------|
| **Source Code** | Git branch | `backup/staging-to-prod-*` | 1 minute |
| **Version Tag** | Git tag | `staging-backup-*` | 1 minute |
| **Local Archive** | Tar.gz | `backups/github_*/` | 2 minutes |

---

## 🔄 Restore Procedures

### Emergency Full Restore (Complete Rollback)

#### Step 1: Launch EC2 Instances from AMI
```bash
# Via AWS Console or CLI
aws ec2 run-instances \
    --image-id ami-XXXXXXXXX \
    --instance-type t3.large \
    --key-name chatmrpt-key \
    --security-group-ids sg-0b21586985a0bbfbe \
    --subnet-id subnet-XXXXXXXXX
```

#### Step 2: Restore Redis from Snapshot
```bash
# Via AWS Console or CLI
aws elasticache create-cache-cluster \
    --cache-cluster-id chatmrpt-redis-staging-restored \
    --snapshot-name chatmrpt-redis-staging-backup-XXXXXXXX
```

#### Step 3: Update Load Balancer Targets
```bash
# Register new instances with target group
aws elbv2 register-targets \
    --target-group-arn arn:aws:elasticache:us-east-2:XXXX \
    --targets Id=i-NEWINSTANCE1 Id=i-NEWINSTANCE2
```

#### Step 4: Restore Application Code
```bash
# On new instances
scp -i chatmrpt-key.pem backups/staging_*/data/chatmrpt_app_backup.tar.gz ec2-user@NEW_IP:/tmp/
ssh -i chatmrpt-key.pem ec2-user@NEW_IP
cd /home/ec2-user
tar -xzf /tmp/chatmrpt_app_backup.tar.gz -C ChatMRPT/
```

#### Step 5: Restore Environment Variables
```bash
# Copy .env file back
scp -i chatmrpt-key.pem backups/staging_*/configs/env_backup_instance1.txt ec2-user@NEW_IP:/home/ec2-user/ChatMRPT/.env
```

#### Step 6: Start Services
```bash
# On each instance
sudo systemctl restart chatmrpt
```

---

### Partial Restore Options

#### Restore Only Code (GitHub)
```bash
# Checkout backup tag
git fetch --all --tags
git checkout staging-backup-YYYYMMDD_HHMMSS

# Or create new branch from backup
git checkout -b restore-from-backup staging-backup-YYYYMMDD_HHMMSS
```

#### Restore Only Configuration
```bash
# Copy environment file
scp backups/staging_*/configs/env_backup_instance1.txt user@server:/path/.env

# Apply security group configuration
aws ec2 authorize-security-group-ingress --cli-input-json file://backups/staging_*/aws/security_groups.json
```

#### Restore Only Data
```bash
# Restore user uploads
tar -xzf backups/staging_*/data/uploads_backup.tar.gz -C /home/ec2-user/ChatMRPT/
```

---

## 📍 Backup Locations

### Local Backups
```
ChatMRPT/
├── backups/
│   ├── staging_YYYYMMDD_HHMMSS/
│   │   ├── configs/          # Environment variables, settings
│   │   ├── data/             # Application data, uploads
│   │   ├── aws/              # AWS configurations
│   │   ├── scripts/          # Database migrations
│   │   └── BACKUP_MANIFEST.txt
│   └── github_YYYYMMDD_HHMMSS/
│       ├── chatmrpt-repo-*.tar.gz
│       └── repo_info.txt
```

### AWS Backups
- **AMI Snapshots**: EC2 Console > Images > AMIs
  - Filter by tag: `Purpose=staging-to-prod-transition`
  - Name pattern: `chatmrpt-staging-backup-*`

- **Redis Snapshots**: ElastiCache Console > Backups
  - Name pattern: `chatmrpt-redis-staging-backup-*`

### GitHub Backups
- **Branches**: `backup/staging-to-prod-*`
- **Tags**: `staging-backup-*`

---

## ⏱️ Restore Time Estimates

| Scenario | Time Required | Data Loss |
|----------|--------------|-----------|
| **Full restore from AMI** | 15-20 minutes | None |
| **Code rollback only** | 2-3 minutes | None |
| **Redis restore** | 10-15 minutes | Since last snapshot |
| **Manual rebuild** | 1-2 hours | Depends on backups |

---

## 🔐 Backup Security

### Sensitive Data Locations
- **Environment Variables**: `backups/*/configs/env_backup_*.txt`
  - Contains API keys, database passwords
  - **DO NOT** commit to Git
  - Store encrypted or in secure location

- **Database Backups**: `backups/*/data/*.db.backup`
  - May contain user data
  - Encrypt before long-term storage

### Recommended Storage
1. **AWS S3** with encryption and versioning
2. **External encrypted drive**
3. **Secure cloud storage** (separate from AWS)

---

## 📝 Backup Checklist

### Before Transition
- [ ] Run `backup_staging_environment.sh`
- [ ] Run `github_backup_staging.sh`
- [ ] Verify AMI creation in AWS Console
- [ ] Verify Redis snapshot in ElastiCache Console
- [носик backups to S3
- [ ] Document AMI IDs and snapshot names
- [ ] Test restore procedure on dev environment

### After Successful Transition
- [ ] Keep backups for 30 days minimum
- [ ] Archive to S3 Glacier for long-term storage
- [ ] Document successful transition date
- [ ] Clean up old backups after 90 days

---

## 🚨 Emergency Contacts

### If Restore Needed
1. Check this guide first
2. Locate most recent backup in `backups/` directory
3. Follow restore procedures above
4. If issues persist:
   - Check AWS Console for AMI/snapshot status
   - Verify security groups and network settings
   - Review application logs after restore

### Critical Files to Preserve
- `.env` files (environment variables)
- `instance/uploads/` (user data)
- `instance/*.db` (databases)
- SSL certificates (if any)

---

## 🔧 Automation Scripts

### Upload to S3
```bash
# Create S3 bucket if not exists
aws s3 mb s3://chatmrpt-backups-$(date +%Y)

# Upload backup with encryption
aws s3 cp chatmrpt-staging-backup-*.tar.gz \
    s3://chatmrpt-backups-$(date +%Y)/ \
    --storage-class STANDARD_IA \
    --server-side-encryption AES256
```

### Schedule Regular Backups
```bash
# Add to crontab for weekly backups
0 2 * * 0 /home/ubuntu/ChatMRPT/backup_staging_environment.sh
```

---

## ✅ Verification Commands

### Verify AWS Backups
```bash
# List AMI snapshots
aws ec2 describe-images --owners self --filters "Name=name,Values=chatmrpt-staging-backup-*"

# List Redis snapshots
aws elasticache describe-snapshots --snapshot-name chatmrpt-redis-staging-backup-*
```

### Verify GitHub Backups
```bash
# List backup branches
git branch -a | grep backup/staging-to-prod

# List backup tags
git tag -l "staging-backup-*"
```

---

## 📚 Additional Notes

- **Backup Retention**: Keep for minimum 30 days, archive after 90 days
- **Test Restores**: Test restore procedure quarterly
- **Documentation**: Update this guide after each major change
- **Monitoring**: Set up CloudWatch alarms for backup failures

---

**Last Updated**: August 27, 2025  
**Next Review**: After transition completion