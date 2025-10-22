#!/bin/bash
# Deploy to a single instance

INSTANCE_IP=$1
DEPLOYMENT_ID=$2

if [ -z "$INSTANCE_IP" ] || [ -z "$DEPLOYMENT_ID" ]; then
    echo "Usage: $0 <instance_ip> <deployment_id>"
    exit 1
fi

LOG_FILE="deployment/logs/deploy_${INSTANCE_IP}_${DEPLOYMENT_ID}.log"

echo "=== Deploying to $INSTANCE_IP ===" | tee $LOG_FILE
echo "Deployment ID: $DEPLOYMENT_ID" | tee -a $LOG_FILE
echo "Start time: $(date)" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# 1. Create backup
echo "📋 Creating backup..." | tee -a $LOG_FILE
ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
    ec2-user@$INSTANCE_IP << 'BACKUP' 2>&1 | tee -a $LOG_FILE
cd /home/ec2-user/ChatMRPT
BACKUP_DIR="backups/deployment_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Backup critical files
cp app/static/js/modules/data/tpr-download-manager.js $BACKUP_DIR/
cp app/web/routes/analysis_routes.py $BACKUP_DIR/
cp app/web/routes/tpr_routes.py $BACKUP_DIR/
cp app/web/routes/export_routes.py $BACKUP_DIR/
cp .env $BACKUP_DIR/

echo "✅ Backup created at $BACKUP_DIR"
BACKUP

# 2. Pull latest changes from git (if using git)
echo "" | tee -a $LOG_FILE
echo "📋 Pulling latest changes..." | tee -a $LOG_FILE
ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
    ec2-user@$INSTANCE_IP << 'PULL' 2>&1 | tee -a $LOG_FILE
cd /home/ec2-user/ChatMRPT
# If using git:
# git pull origin main
# For now, we'll sync from staging
echo "Syncing from staging/primary instance..."
PULL

# 3. Copy files from staging or primary instance
# This section should be customized based on your deployment method
# For now, we'll copy from the primary instance (172.31.44.52)

echo "" | tee -a $LOG_FILE
echo "📋 Syncing application files..." | tee -a $LOG_FILE

# Get files from primary instance to staging first
PRIMARY_IP="172.31.44.52"
if [ "$INSTANCE_IP" != "$PRIMARY_IP" ]; then
    # Copy critical files
    for file in \
        "app/static/js/modules/data/tpr-download-manager.js" \
        "app/web/routes/analysis_routes.py" \
        "app/web/routes/tpr_routes.py" \
        "app/web/routes/export_routes.py"
    do
        echo "Copying $file..." | tee -a $LOG_FILE
        # Copy from primary to staging
        scp -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
            ec2-user@$PRIMARY_IP:/home/ec2-user/ChatMRPT/$file \
            /tmp/$(basename $file) 2>&1 | tee -a $LOG_FILE
        
        # Copy from staging to target
        scp -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
            /tmp/$(basename $file) \
            ec2-user@$INSTANCE_IP:/home/ec2-user/ChatMRPT/$file 2>&1 | tee -a $LOG_FILE
    done
fi

# 4. Update configuration
echo "" | tee -a $LOG_FILE
echo "📋 Updating configuration..." | tee -a $LOG_FILE
ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
    ec2-user@$INSTANCE_IP << 'CONFIG' 2>&1 | tee -a $LOG_FILE
cd /home/ec2-user/ChatMRPT

# Ensure Redis is pointing to production
if grep -q "redis://chatmrpt-redis-staging" .env; then
    echo "Updating Redis to production endpoint..."
    sudo sed -i 's|redis://chatmrpt-redis-staging|redis://chatmrpt-redis-production|g' .env
fi

# Verify Redis config
echo "Redis configuration:"
grep REDIS_URL .env
CONFIG

# 5. Install dependencies (if needed)
echo "" | tee -a $LOG_FILE
echo "📋 Checking dependencies..." | tee -a $LOG_FILE
ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
    ec2-user@$INSTANCE_IP << 'DEPS' 2>&1 | tee -a $LOG_FILE
cd /home/ec2-user/ChatMRPT
source chatmrpt_env/bin/activate 2>/dev/null || source venv/bin/activate 2>/dev/null

# Check if requirements have changed
# pip install -r requirements.txt --quiet
echo "Dependencies check complete"
DEPS

# 6. Run tests (if available)
echo "" | tee -a $LOG_FILE
echo "📋 Running tests..." | tee -a $LOG_FILE
# Add your test commands here

# 7. Restart service
echo "" | tee -a $LOG_FILE
echo "📋 Restarting service..." | tee -a $LOG_FILE
ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
    ec2-user@$INSTANCE_IP << 'RESTART' 2>&1 | tee -a $LOG_FILE
sudo systemctl stop chatmrpt
sleep 2
sudo systemctl start chatmrpt
sleep 5

# Check if service started successfully
if sudo systemctl is-active chatmrpt > /dev/null; then
    echo "✅ Service restarted successfully"
    sudo systemctl status chatmrpt | head -10
else
    echo "❌ Service failed to start!"
    sudo journalctl -u chatmrpt -n 50
    exit 1
fi
RESTART

# 8. Verify deployment
echo "" | tee -a $LOG_FILE
echo "📋 Verifying deployment..." | tee -a $LOG_FILE
./deployment/scripts/check_instance_health.sh $INSTANCE_IP 2>&1 | tee -a $LOG_FILE

echo "" | tee -a $LOG_FILE
echo "Deployment to $INSTANCE_IP completed at $(date)" | tee -a $LOG_FILE
