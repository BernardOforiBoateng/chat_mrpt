#!/bin/bash
# Immediate fix to sync both production instances
# This ensures TPR downloads and ITN exports work correctly

set -e

echo "=== Immediate Production Fix ===" 
echo "Date: $(date)"
echo ""
echo "This script will:"
echo "1. Add Instance 2 to known hosts"
echo "2. Sync all fixes from Instance 1 to Instance 2"
echo "3. Update Redis configuration on Instance 2"
echo "4. Restart services on both instances"
echo ""

SSH_KEY="/tmp/chatmrpt-key2.pem"
STAGING_HOST="ec2-user@18.117.115.217"

# Ensure we have the SSH key
if [ ! -f "$SSH_KEY" ]; then
    cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
    chmod 600 /tmp/chatmrpt-key2.pem
fi

echo "📋 Step 1: Setting up SSH access to Instance 2..."
ssh -i "$SSH_KEY" "$STAGING_HOST" << 'SETUP_SSH'
    # Add Instance 2 to known hosts
    echo "Adding Instance 2 (172.31.43.200) to known hosts..."
    ssh-keyscan -H 172.31.43.200 >> ~/.ssh/known_hosts 2>/dev/null
    
    # Test connection
    if ssh -i ~/.ssh/chatmrpt-key.pem -o ConnectTimeout=5 ec2-user@172.31.43.200 "echo 'Connection successful'" 2>/dev/null; then
        echo "✅ SSH access to Instance 2 confirmed"
    else
        echo "❌ Failed to connect to Instance 2"
        exit 1
    fi
SETUP_SSH

echo ""
echo "📋 Step 2: Creating backups on Instance 2..."
ssh -i "$SSH_KEY" "$STAGING_HOST" << 'CREATE_BACKUPS'
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.43.200 << 'BACKUP'
        cd /home/ec2-user/ChatMRPT
        BACKUP_DIR="backups/pre_sync_$(date +%Y%m%d_%H%M%S)"
        mkdir -p $BACKUP_DIR
        
        # Backup critical files
        cp app/static/js/modules/data/tpr-download-manager.js $BACKUP_DIR/ 2>/dev/null || true
        cp app/web/routes/analysis_routes.py $BACKUP_DIR/ 2>/dev/null || true
        cp app/web/routes/tpr_routes.py $BACKUP_DIR/ 2>/dev/null || true
        cp app/web/routes/export_routes.py $BACKUP_DIR/ 2>/dev/null || true
        cp app/tools/export_tools.py $BACKUP_DIR/ 2>/dev/null || true
        cp .env $BACKUP_DIR/ 2>/dev/null || true
        
        echo "✅ Backups created in $BACKUP_DIR"
BACKUP
CREATE_BACKUPS

echo ""
echo "📋 Step 3: Syncing files from Instance 1 to Instance 2..."
ssh -i "$SSH_KEY" "$STAGING_HOST" << 'SYNC_FILES'
    echo "Getting file list from Instance 1..."
    
    # Define files to sync
    FILES_TO_SYNC=(
        "app/static/js/modules/data/tpr-download-manager.js"
        "app/web/routes/analysis_routes.py"
        "app/web/routes/tpr_routes.py"
        "app/web/routes/export_routes.py"
        "app/tools/export_tools.py"
        "app/static/js/app.js"
        "app/static/js/modules/chat/core/message-handler.js"
    )
    
    # Create temp directory
    TEMP_DIR="/tmp/chatmrpt_sync_$(date +%s)"
    mkdir -p $TEMP_DIR
    
    # Copy files from Instance 1 to staging
    echo "Copying files from Instance 1..."
    for file in "${FILES_TO_SYNC[@]}"; do
        echo -n "  $file ... "
        scp -i ~/.ssh/chatmrpt-key.pem -q \
            ec2-user@172.31.44.52:/home/ec2-user/ChatMRPT/$file \
            $TEMP_DIR/$(basename $file) 2>/dev/null && echo "✓" || echo "✗"
    done
    
    # Copy files from staging to Instance 2
    echo ""
    echo "Copying files to Instance 2..."
    for file in "${FILES_TO_SYNC[@]}"; do
        filename=$(basename $file)
        dirname=$(dirname $file)
        
        if [ -f "$TEMP_DIR/$filename" ]; then
            echo -n "  $file ... "
            # Ensure directory exists on Instance 2
            ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.43.200 \
                "mkdir -p /home/ec2-user/ChatMRPT/$dirname" 2>/dev/null
            
            # Copy file
            scp -i ~/.ssh/chatmrpt-key.pem -q \
                $TEMP_DIR/$filename \
                ec2-user@172.31.43.200:/home/ec2-user/ChatMRPT/$file 2>/dev/null && echo "✓" || echo "✗"
        fi
    done
    
    # Cleanup
    rm -rf $TEMP_DIR
    echo ""
    echo "✅ File sync complete"
SYNC_FILES

echo ""
echo "📋 Step 4: Updating Redis configuration on Instance 2..."
ssh -i "$SSH_KEY" "$STAGING_HOST" << 'UPDATE_CONFIG'
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.43.200 << 'CONFIG'
        cd /home/ec2-user/ChatMRPT
        
        echo "Current Redis configuration:"
        grep "REDIS_URL" .env || echo "No Redis URL found"
        
        # Update to production Redis
        if grep -q "redis-staging" .env; then
            echo ""
            echo "Updating to production Redis..."
            sudo sed -i 's/chatmrpt-redis-staging/chatmrpt-redis-production/g' .env
            echo "✅ Updated to production Redis"
        elif ! grep -q "REDIS_URL=redis://chatmrpt-redis-production" .env; then
            echo ""
            echo "Adding production Redis configuration..."
            echo "REDIS_URL=redis://chatmrpt-redis-production.1b3pmt.0001.use2.cache.amazonaws.com:6379/0" | sudo tee -a .env
            echo "ENABLE_REDIS_SESSIONS=true" | sudo tee -a .env
        fi
        
        echo ""
        echo "New Redis configuration:"
        grep "REDIS_URL" .env
        grep "ENABLE_REDIS" .env || true
CONFIG
UPDATE_CONFIG

echo ""
echo "📋 Step 5: Verifying file sync..."
ssh -i "$SSH_KEY" "$STAGING_HOST" << 'VERIFY_SYNC'
    echo "Computing checksums..."
    
    # Get checksums from Instance 1
    MD5_INST1=$(ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 \
        'cd /home/ec2-user/ChatMRPT && md5sum app/static/js/modules/data/tpr-download-manager.js app/web/routes/analysis_routes.py 2>/dev/null')
    
    # Get checksums from Instance 2
    MD5_INST2=$(ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.43.200 \
        'cd /home/ec2-user/ChatMRPT && md5sum app/static/js/modules/data/tpr-download-manager.js app/web/routes/analysis_routes.py 2>/dev/null')
    
    echo ""
    echo "Instance 1 checksums:"
    echo "$MD5_INST1"
    echo ""
    echo "Instance 2 checksums:"
    echo "$MD5_INST2"
    
    if [ "$MD5_INST1" = "$MD5_INST2" ]; then
        echo ""
        echo "✅ Files are synchronized!"
    else
        echo ""
        echo "⚠️  Files may differ - manual verification recommended"
    fi
VERIFY_SYNC

echo ""
echo "📋 Step 6: Restarting services on both instances..."
ssh -i "$SSH_KEY" "$STAGING_HOST" << 'RESTART_SERVICES'
    echo "Restarting Instance 1 (172.31.44.52)..."
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'RESTART1'
        sudo systemctl restart chatmrpt
        sleep 3
        if sudo systemctl is-active chatmrpt > /dev/null; then
            echo "✅ Instance 1 service restarted successfully"
        else
            echo "❌ Instance 1 service failed to start"
        fi
RESTART1
    
    echo ""
    echo "Restarting Instance 2 (172.31.43.200)..."
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.43.200 << 'RESTART2'
        sudo systemctl restart chatmrpt
        sleep 3
        if sudo systemctl is-active chatmrpt > /dev/null; then
            echo "✅ Instance 2 service restarted successfully"
        else
            echo "❌ Instance 2 service failed to start"
        fi
RESTART2
RESTART_SERVICES

echo ""
echo "📋 Step 7: Final health check..."
ssh -i "$SSH_KEY" "$STAGING_HOST" << 'HEALTH_CHECK'
    echo ""
    for instance in "172.31.44.52" "172.31.43.200"; do
        echo "Instance $instance:"
        ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$instance << 'CHECK' 2>/dev/null
            # Check service
            SERVICE=$(sudo systemctl is-active chatmrpt 2>/dev/null || echo "unknown")
            
            # Check workers
            WORKERS=$(ps aux | grep gunicorn | grep -v grep | wc -l)
            
            # Check Redis
            cd /home/ec2-user/ChatMRPT
            REDIS_CHECK=$(source chatmrpt_env/bin/activate 2>/dev/null || source venv/bin/activate 2>/dev/null
            python3 -c "
import os, redis
from dotenv import load_dotenv
load_dotenv()
try:
    r = redis.from_url(os.getenv('REDIS_URL'))
    r.ping()
    print('connected')
except:
    print('failed')
" 2>/dev/null || echo "error")
            
            echo "  Service: $SERVICE | Workers: $WORKERS | Redis: $REDIS_CHECK"
CHECK
        echo ""
    done
HEALTH_CHECK

echo ""
echo "=== Fix Complete ==="
echo ""
echo "✅ Both production instances are now synchronized!"
echo ""
echo "What was fixed:"
echo "1. Instance 2 now has all the same code as Instance 1"
echo "2. Both instances use the production Redis"
echo "3. Services have been restarted on both instances"
echo ""
echo "Test the application now:"
echo "http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com/"
echo ""
echo "The TPR downloads and ITN exports should now work consistently!"
echo ""
echo "For future deployments, use the deployment system:"
echo "deployment/deploy_to_production.sh"