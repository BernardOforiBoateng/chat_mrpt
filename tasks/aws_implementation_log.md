# AWS Implementation Log

## Date: July 28, 2025

### Initial State
- **Production Instance**: 3.137.158.17 (t3.medium)
- **AMI Created**: ami-02c0a366899ceb8d2 (ChatMRPT-Production-20250728-1334)
- **Working State**: Flask-Session 0.5.0, Werkzeug 2.3.7, TPR uploads working

### Infrastructure Created

#### 1. IAM Role ✅
- **Role Name**: ChatMRPT-EC2-Role
- **Attached to**: Both production and staging instances
- **Permissions**: EC2, S3, CloudWatch, Systems Manager

#### 2. S3 Bucket ✅
- **Bucket Name**: chatmrpt-backups-20250728
- **Features**:
  - Versioning enabled
  - Lifecycle policy (30 days to IA, 90 days delete old versions)
- **Purpose**: Centralized backup storage

#### 3. Staging Instance ✅
- **Instance ID**: i-0994615951d0b9563
- **Public IP**: 18.117.115.217
- **URL**: http://18.117.115.217:8080
- **Created from**: AMI ami-02c0a366899ceb8d2
- **Disk**: Expanded from 20GB to 40GB
- **Tags**:
  - Name: ChatMRPT-Staging
  - Environment: staging
  - Purpose: Testing-Infrastructure-Improvements

#### 4. CloudWatch Monitoring ✅
- **Agent Version**: 1.300057.1b1167
- **Metrics Collected**:
  - CPU usage
  - Memory usage
  - Disk usage
- **Logs Collected**:
  - /home/ec2-user/ChatMRPT/gunicorn-error.log
  - Log group: /aws/ec2/chatmrpt/staging

#### 5. Automated Backups ✅
- **Script Location**: /home/ec2-user/backup-chatmrpt.sh
- **Schedule**: Daily at 2 AM via cron
- **Backup Includes**:
  - SQLite database
  - Application code (excluding logs and uploads)
- **S3 Location**: s3://chatmrpt-backups-20250728/staging/
- **Local Retention**: 7 days

### Configuration Files

#### CloudWatch Agent Config (/tmp/cwagent-config.json)
```json
{
    "metrics": {
        "namespace": "ChatMRPT/Staging",
        "metrics_collected": {
            "cpu": {
                "measurement": [{"name": "cpu_usage_idle", "rename": "CPU_IDLE", "unit": "Percent"}],
                "totalcpu": false
            },
            "disk": {
                "measurement": [{"name": "used_percent", "rename": "DISK_USED", "unit": "Percent"}],
                "resources": ["*"]
            },
            "mem": {
                "measurement": [{"name": "mem_used_percent", "rename": "MEM_USED", "unit": "Percent"}]
            }
        }
    },
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/home/ec2-user/ChatMRPT/gunicorn-error.log",
                        "log_group_name": "/aws/ec2/chatmrpt/staging",
                        "log_stream_name": "{instance_id}/gunicorn-error"
                    }
                ]
            }
        }
    }
}
```

#### Backup Script (/home/ec2-user/backup-chatmrpt.sh)
```bash
#!/bin/bash
BACKUP_DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="/home/ec2-user/backups"
S3_BUCKET="chatmrpt-backups-20250728"
INSTANCE_TYPE="staging"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
sqlite3 /home/ec2-user/ChatMRPT/instance/interactions.db \
  ".backup $BACKUP_DIR/interactions-$BACKUP_DATE.db"

# Backup code (excluding large files)
tar -czf $BACKUP_DIR/code-$BACKUP_DATE.tar.gz \
  --exclude='*.log' \
  --exclude='instance/uploads' \
  --exclude='__pycache__' \
  --exclude='chatmrpt_env' \
  -C /home/ec2-user ChatMRPT

# Upload to S3
aws s3 sync $BACKUP_DIR s3://$S3_BUCKET/$INSTANCE_TYPE/ \
  --exclude "*" \
  --include "*.db" \
  --include "*.tar.gz"

# Clean up old local backups (keep 7 days)
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completed: $BACKUP_DATE"
```

### AWS Resources Summary

| Resource | Production | Staging |
|----------|------------|---------|
| EC2 Instance | i-0183aaf795bf8f24e | i-0994615951d0b9563 |
| Public IP | 3.137.158.17 | 18.117.115.217 |
| Instance Type | t3.medium | t3.medium |
| Disk Size | 20GB | 40GB |
| IAM Role | ChatMRPT-EC2-Role | ChatMRPT-EC2-Role |
| Monitoring | Basic | CloudWatch Agent |
| Backups | Manual | Automated to S3 |

### Cost Analysis
- **Monthly Costs**:
  - Production EC2: ~$50
  - Staging EC2: ~$50
  - S3 Storage: ~$5
  - CloudWatch: ~$10
  - **Total**: ~$115/month (14% of $833 budget)

### Commands for Recovery

#### To Access Instances
```bash
# Production
ssh -i chatmrpt-key.pem ec2-user@3.137.158.17

# Staging
ssh -i chatmrpt-key.pem ec2-user@18.117.115.217
```

#### To Create New AMI
```bash
aws ec2 create-image \
  --instance-id [INSTANCE-ID] \
  --name "ChatMRPT-[PURPOSE]-$(date +%Y%m%d)" \
  --description "[Description]" \
  --no-reboot
```

#### To Restore from AMI
```bash
aws ec2 run-instances \
  --image-id ami-02c0a366899ceb8d2 \
  --instance-type t3.medium \
  --key-name chatmrpt-key \
  --security-group-ids sg-0b21586985a0bbfbe \
  --subnet-id subnet-0713ee8d5af26578a
```

### Next Steps Planned
1. Create RDS PostgreSQL database (staging)
2. Migrate SQLite to PostgreSQL
3. Test performance and functionality
4. Create production RDS instance
5. Implement auto-scaling