#!/bin/bash

# =====================================================
# ChatMRPT Staging Environment Full Backup Script
# =====================================================
# Purpose: Create complete backup before staging-to-production transition
# Date: August 27, 2025
# =====================================================

set -e  # Exit on any error

# Configuration
BACKUP_DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_PREFIX="chatmrpt-staging-backup"
KEY_PATH="/tmp/chatmrpt-key2.pem"
STAGING_IP1="3.21.167.170"
STAGING_IP2="18.220.103.20"
AWS_REGION="us-east-2"
LOCAL_BACKUP_DIR="./backups/staging_${BACKUP_DATE}"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "======================================================"
echo "   CHATMRPT STAGING ENVIRONMENT BACKUP"
echo "   Backup Date: ${BACKUP_DATE}"
echo "======================================================"
echo ""

# Ensure SSH key is available
if [ ! -f "$KEY_PATH" ]; then
    cp aws_files/chatmrpt-key.pem $KEY_PATH
    chmod 600 $KEY_PATH
fi

# Create local backup directory
mkdir -p ${LOCAL_BACKUP_DIR}/{configs,data,scripts,aws}

echo "📁 Local backup directory: ${LOCAL_BACKUP_DIR}"
echo ""

# =====================================================
# STEP 1: AWS AMI SNAPSHOTS
# =====================================================
echo -e "${YELLOW}[1/7] Creating AMI Snapshots${NC}"
echo "==========================================="

# Create AMI backups via AWS CLI on staging server
ssh -i $KEY_PATH ec2-user@$STAGING_IP1 << EOF 2>/dev/null
    export AWS_DEFAULT_REGION=$AWS_REGION
    
    echo "Creating AMI for Instance 1 (i-0994615951d0b9563)..."
    aws ec2 create-image \
        --instance-id i-0994615951d0b9563 \
        --name "${BACKUP_PREFIX}-instance1-${BACKUP_DATE}" \
        --description "Staging Instance 1 backup before production transition" \
        --no-reboot \
        --output json > /tmp/ami1_result.json 2>&1
    
    if [ \$? -eq 0 ]; then
        AMI_ID=\$(cat /tmp/ami1_result.json | jq -r '.ImageId')
        echo "✅ AMI created: \$AMI_ID"
        echo "\$AMI_ID" > /tmp/ami1_id.txt
    else
        echo "❌ Failed to create AMI for Instance 1"
        cat /tmp/ami1_result.json
    fi
    
    echo ""
    echo "Creating AMI for Instance 2 (i-0f3b25b72f18a5037)..."
    aws ec2 create-image \
        --instance-id i-0f3b25b72f18a5037 \
        --name "${BACKUP_PREFIX}-instance2-${BACKUP_DATE}" \
        --description "Staging Instance 2 backup before production transition" \
        --no-reboot \
        --output json > /tmp/ami2_result.json 2>&1
    
    if [ \$? -eq 0 ]; then
        AMI_ID=\$(cat /tmp/ami2_result.json | jq -r '.ImageId')
        echo "✅ AMI created: \$AMI_ID"
        echo "\$AMI_ID" > /tmp/ami2_id.txt
    else
        echo "❌ Failed to create AMI for Instance 2"
        cat /tmp/ami2_result.json
    fi
    
    # Tag AMIs for easy identification
    if [ -f /tmp/ami1_id.txt ]; then
        AMI1=\$(cat /tmp/ami1_id.txt)
        aws ec2 create-tags --resources \$AMI1 --tags Key=BackupDate,Value=${BACKUP_DATE} Key=Purpose,Value=staging-to-prod-transition
    fi
    
    if [ -f /tmp/ami2_id.txt ]; then
        AMI2=\$(cat /tmp/ami2_id.txt)
        aws ec2 create-tags --resources \$AMI2 --tags Key=BackupDate,Value=${BACKUP_DATE} Key=Purpose,Value=staging-to-prod-transition
    fi
EOF

echo ""

# =====================================================
# STEP 2: APPLICATION DATA BACKUP
# =====================================================
echo -e "${YELLOW}[2/7] Backing up Application Data${NC}"
echo "==========================================="

# Backup Instance 1 data
echo "Backing up Instance 1 application files..."
ssh -i $KEY_PATH ec2-user@$STAGING_IP1 << 'EOF' 2>/dev/null
    cd /home/ec2-user/ChatMRPT
    
    # Create tarball of application (excluding large/unnecessary files)
    tar --exclude='chatmrpt_env' \
        --exclude='instance/uploads' \
        --exclude='*.pyc' \
        --exclude='__pycache__' \
        --exclude='.git' \
        --exclude='node_modules' \
        -czf /tmp/chatmrpt_app_backup.tar.gz .
    
    echo "✅ Application backup created: /tmp/chatmrpt_app_backup.tar.gz"
    
    # Backup .env file separately (contains secrets)
    if [ -f .env ]; then
        cp .env /tmp/env_backup_instance1.txt
        echo "✅ Environment file backed up"
    fi
    
    # Backup instance uploads if they exist
    if [ -d instance/uploads ]; then
        echo "Backing up user uploads..."
        tar -czf /tmp/uploads_backup.tar.gz instance/uploads/
        echo "✅ User uploads backed up"
    fi
EOF

# Copy backups to local machine
echo "Downloading backups to local machine..."
scp -i $KEY_PATH ec2-user@$STAGING_IP1:/tmp/chatmrpt_app_backup.tar.gz ${LOCAL_BACKUP_DIR}/data/ 2>/dev/null
scp -i $KEY_PATH ec2-user@$STAGING_IP1:/tmp/env_backup_instance1.txt ${LOCAL_BACKUP_DIR}/configs/ 2>/dev/null
scp -i $KEY_PATH ec2-user@$STAGING_IP1:/tmp/uploads_backup.tar.gz ${LOCAL_BACKUP_DIR}/data/ 2>/dev/null || echo "No uploads to backup"

echo ""

# =====================================================
# STEP 3: REDIS BACKUP
# =====================================================
echo -e "${YELLOW}[3/7] Creating Redis Backup${NC}"
echo "==========================================="

ssh -i $KEY_PATH ec2-user@$STAGING_IP1 << 'EOF' 2>/dev/null
    export AWS_DEFAULT_REGION=us-east-2
    
    # Create Redis snapshot
    echo "Creating ElastiCache Redis snapshot..."
    SNAPSHOT_NAME="chatmrpt-redis-staging-backup-$(date +%Y%m%d-%H%M%S)"
    
    aws elasticache create-snapshot \
        --cache-cluster-id chatmrpt-redis-staging \
        --snapshot-name "$SNAPSHOT_NAME" \
        --output json > /tmp/redis_snapshot.json 2>&1
    
    if [ $? -eq 0 ]; then
        echo "✅ Redis snapshot initiated: $SNAPSHOT_NAME"
        cat /tmp/redis_snapshot.json | jq -r '.Snapshot.SnapshotName'
    else
        echo "❌ Failed to create Redis snapshot"
        cat /tmp/redis_snapshot.json
    fi
EOF

echo ""

# =====================================================
# STEP 4: SECURITY GROUP & NETWORK CONFIG EXPORT
# =====================================================
echo -e "${YELLOW}[4/7] Exporting Security Groups & Network Config${NC}"
echo "==========================================="

ssh -i $KEY_PATH ec2-user@$STAGING_IP1 << 'EOF' > ${LOCAL_BACKUP_DIR}/aws/security_groups.json 2>/dev/null
    export AWS_DEFAULT_REGION=us-east-2
    
    # Export security group configurations
    echo "Exporting security group configurations..."
    aws ec2 describe-security-groups \
        --group-ids sg-0b21586985a0bbfbe sg-0a003f4d6500485b9 sg-08a1e242828bcb189 \
        --output json
EOF

ssh -i $KEY_PATH ec2-user@$STAGING_IP1 << 'EOF' > ${LOCAL_BACKUP_DIR}/aws/load_balancer.json 2>/dev/null
    export AWS_DEFAULT_REGION=us-east-2
    
    # Export ALB configuration
    echo "Exporting ALB configuration..." >&2
    aws elbv2 describe-load-balancers --names chatmrpt-staging-alb --output json
EOF

ssh -i $KEY_PATH ec2-user@$STAGING_IP1 << 'EOF' > ${LOCAL_BACKUP_DIR}/aws/target_groups.json 2>/dev/null
    export AWS_DEFAULT_REGION=us-east-2
    
    # Export target group configuration
    echo "Exporting target group configuration..." >&2
    aws elbv2 describe-target-groups --names chatmrpt-staging-targets --output json
EOF

echo "✅ AWS configurations exported"
echo ""

# =====================================================
# STEP 5: DATABASE SCHEMA & SCRIPTS BACKUP
# =====================================================
echo -e "${YELLOW}[5/7] Backing up Database Schema & Scripts${NC}"
echo "==========================================="

# Backup database if SQLite is used
ssh -i $KEY_PATH ec2-user@$STAGING_IP1 << 'EOF' 2>/dev/null
    cd /home/ec2-user/ChatMRPT
    
    # Backup SQLite databases if they exist
    if [ -d instance ]; then
        for db in instance/*.db; do
            if [ -f "$db" ]; then
                filename=$(basename "$db")
                cp "$db" "/tmp/${filename}.backup"
                echo "✅ Backed up database: $filename"
            fi
        done
    fi
    
    # Backup migration scripts
    if [ -d migrations ]; then
        tar -czf /tmp/migrations_backup.tar.gz migrations/
        echo "✅ Migration scripts backed up"
    fi
EOF

# Download database backups
scp -i $KEY_PATH "ec2-user@$STAGING_IP1:/tmp/*.db.backup" ${LOCAL_BACKUP_DIR}/data/ 2>/dev/null || echo "No SQLite databases to backup"
scp -i $KEY_PATH ec2-user@$STAGING_IP1:/tmp/migrations_backup.tar.gz ${LOCAL_BACKUP_DIR}/scripts/ 2>/dev/null || echo "No migrations to backup"

echo ""

# =====================================================
# STEP 6: CREATE BACKUP MANIFEST
# =====================================================
echo -e "${YELLOW}[6/7] Creating Backup Manifest${NC}"
echo "==========================================="

cat > ${LOCAL_BACKUP_DIR}/BACKUP_MANIFEST.txt << EOF
================================================
ChatMRPT STAGING BACKUP MANIFEST
================================================
Backup Date: ${BACKUP_DATE}
Environment: Staging
Purpose: Pre-transition to production backup

AMI SNAPSHOTS:
--------------
Instance 1 (i-0994615951d0b9563): ${BACKUP_PREFIX}-instance1-${BACKUP_DATE}
Instance 2 (i-0f3b25b72f18a5037): ${BACKUP_PREFIX}-instance2-${BACKUP_DATE}

REDIS SNAPSHOT:
---------------
Cluster: chatmrpt-redis-staging
Snapshot: chatmrpt-redis-staging-backup-*

APPLICATION FILES:
------------------
- chatmrpt_app_backup.tar.gz (application code)
- env_backup_instance1.txt (environment variables)
- uploads_backup.tar.gz (user uploaded files)

AWS CONFIGURATIONS:
-------------------
- security_groups.json (security group rules)
- load_balancer.json (ALB configuration)
- target_groups.json (target group settings)

DATABASE BACKUPS:
-----------------
- *.db.backup (SQLite databases)
- migrations_backup.tar.gz (migration scripts)

RESTORE INSTRUCTIONS:
---------------------
1. Launch new instances from AMI snapshots
2. Restore Redis from snapshot
3. Apply security group configurations
4. Restore application files and environment
5. Restore databases if needed
6. Update DNS/Load balancer targets

================================================
EOF

echo "✅ Backup manifest created"
echo ""

# =====================================================
# STEP 7: VERIFY BACKUP
# =====================================================
echo -e "${YELLOW}[7/7] Verifying Backup${NC}"
echo "==========================================="

echo "Backup contents:"
echo "----------------"
ls -la ${LOCAL_BACKUP_DIR}/
echo ""
ls -la ${LOCAL_BACKUP_DIR}/configs/ 2>/dev/null || echo "No configs"
ls -la ${LOCAL_BACKUP_DIR}/data/ 2>/dev/null || echo "No data"
ls -la ${LOCAL_BACKUP_DIR}/aws/ 2>/dev/null || echo "No AWS exports"

# Calculate backup size
BACKUP_SIZE=$(du -sh ${LOCAL_BACKUP_DIR} | cut -f1)
echo ""
echo "Total backup size: ${BACKUP_SIZE}"

# Create compressed archive of entire backup
echo ""
echo "Creating final compressed archive..."
tar -czf "${BACKUP_PREFIX}-${BACKUP_DATE}.tar.gz" -C . "backups/staging_${BACKUP_DATE}"
echo "✅ Complete backup archive: ${BACKUP_PREFIX}-${BACKUP_DATE}.tar.gz"

echo ""
echo -e "${GREEN}======================================================"
echo "   BACKUP COMPLETE!"
echo "======================================================"
echo ""
echo "📦 Backup Location: ${LOCAL_BACKUP_DIR}"
echo "📦 Archive: ${BACKUP_PREFIX}-${BACKUP_DATE}.tar.gz"
echo ""
echo "AMI Snapshots are being created in AWS (may take 5-10 minutes)"
echo "Redis snapshot is being created in ElastiCache"
echo ""
echo "IMPORTANT: Store the backup archive in a safe location!"
echo "         Consider uploading to S3 for additional redundancy"
echo -e "======================================================${NC}"