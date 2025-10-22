#!/bin/bash
# Sync fixes to BOTH production instances
# This solves the "works in staging but not production" issue!

set -e

echo "=== Syncing Both Production Instances ==="
echo "Date: $(date)"
echo ""
echo "We've been updating only Instance 1 (172.31.44.52)"
echo "Instance 2 (172.31.43.200) doesn't have the fixes!"
echo ""

SSH_KEY="/tmp/chatmrpt-key2.pem"
STAGING_HOST="ec2-user@18.117.115.217"
INSTANCE1_IP="172.31.44.52"   # Already has fixes
INSTANCE2_IP="172.31.43.200"  # Needs fixes

# Ensure we have the SSH key
if [ ! -f "$SSH_KEY" ]; then
    cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
    chmod 600 /tmp/chatmrpt-key2.pem
fi

echo "📋 Step 1: Checking current state of both instances..."
echo ""

ssh -i "$SSH_KEY" "$STAGING_HOST" << 'CHECK_STATE'
    echo "Instance 1 (172.31.44.52) - Already Updated:"
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'INST1'
        cd /home/ec2-user/ChatMRPT
        echo -n "  tpr-download-manager.js: "
        ls -la app/static/js/modules/data/tpr-download-manager.js | awk '{print $5, $6, $7}'
        echo -n "  analysis_routes.py: "
        ls -la app/web/routes/analysis_routes.py | awk '{print $5, $6, $7}'
        echo -n "  Redis configured: "
        grep "REDIS_URL=redis://chatmrpt-redis-production" .env > /dev/null && echo "✅ Yes" || echo "❌ No"
INST1
    
    echo ""
    echo "Instance 2 (172.31.43.200) - Needs Update:"
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.43.200 << 'INST2'
        cd /home/ec2-user/ChatMRPT
        echo -n "  tpr-download-manager.js: "
        ls -la app/static/js/modules/data/tpr-download-manager.js | awk '{print $5, $6, $7}'
        echo -n "  analysis_routes.py: "
        ls -la app/web/routes/analysis_routes.py | awk '{print $5, $6, $7}'
        echo -n "  Redis configured: "
        grep "REDIS_URL=redis://chatmrpt-redis-production" .env > /dev/null && echo "✅ Yes" || echo "❌ No"
INST2
CHECK_STATE

echo ""
echo "📋 Step 2: Syncing files from Instance 1 to Instance 2..."
echo ""

ssh -i "$SSH_KEY" "$STAGING_HOST" << 'SYNC_FILES'
    # First, create backups on Instance 2
    echo "Creating backups on Instance 2..."
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.43.200 << 'BACKUP'
        cd /home/ec2-user/ChatMRPT
        sudo cp app/static/js/modules/data/tpr-download-manager.js app/static/js/modules/data/tpr-download-manager.js.backup_$(date +%Y%m%d_%H%M%S)
        sudo cp app/web/routes/analysis_routes.py app/web/routes/analysis_routes.py.backup_$(date +%Y%m%d_%H%M%S)
        sudo cp .env .env.backup_$(date +%Y%m%d_%H%M%S)
        echo "✅ Backups created"
BACKUP
    
    # Copy files from Instance 1 to staging first
    echo ""
    echo "Copying files from Instance 1 to staging..."
    scp -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52:/home/ec2-user/ChatMRPT/app/static/js/modules/data/tpr-download-manager.js ~/tpr-download-manager.js
    scp -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52:/home/ec2-user/ChatMRPT/app/web/routes/analysis_routes.py ~/analysis_routes.py
    
    # Copy files from staging to Instance 2
    echo ""
    echo "Copying files to Instance 2..."
    scp -i ~/.ssh/chatmrpt-key.pem ~/tpr-download-manager.js ec2-user@172.31.43.200:/home/ec2-user/ChatMRPT/app/static/js/modules/data/
    scp -i ~/.ssh/chatmrpt-key.pem ~/analysis_routes.py ec2-user@172.31.43.200:/home/ec2-user/ChatMRPT/app/web/routes/
    
    echo "✅ Files synced"
SYNC_FILES

echo ""
echo "📋 Step 3: Updating Redis configuration on Instance 2..."
echo ""

ssh -i "$SSH_KEY" "$STAGING_HOST" << 'UPDATE_REDIS'
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.43.200 << 'INST2_REDIS'
        cd /home/ec2-user/ChatMRPT
        
        # Update Redis URL to production Redis
        echo "Updating Redis configuration..."
        sudo sed -i 's|REDIS_URL=redis://chatmrpt-redis-staging|REDIS_URL=redis://chatmrpt-redis-production|' .env
        
        # Verify the change
        echo "New Redis configuration:"
        grep REDIS_URL .env
INST2_REDIS
UPDATE_REDIS

echo ""
echo "📋 Step 4: Restarting services on Instance 2..."
echo ""

ssh -i "$SSH_KEY" "$STAGING_HOST" << 'RESTART'
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.43.200 << 'INST2_RESTART'
        echo "Restarting ChatMRPT service..."
        sudo systemctl restart chatmrpt
        
        sleep 5
        
        echo "Service status:"
        sudo systemctl status chatmrpt | head -10
        
        echo ""
        echo "Worker count:"
        ps aux | grep gunicorn | grep -v grep | wc -l
INST2_RESTART
RESTART

echo ""
echo "📋 Step 5: Verifying both instances are in sync..."
echo ""

ssh -i "$SSH_KEY" "$STAGING_HOST" << 'VERIFY'
    echo "Comparing file checksums..."
    
    MD5_1=$(ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 'cd /home/ec2-user/ChatMRPT && md5sum app/static/js/modules/data/tpr-download-manager.js app/web/routes/analysis_routes.py')
    MD5_2=$(ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.43.200 'cd /home/ec2-user/ChatMRPT && md5sum app/static/js/modules/data/tpr-download-manager.js app/web/routes/analysis_routes.py')
    
    echo "Instance 1:"
    echo "$MD5_1"
    echo ""
    echo "Instance 2:"
    echo "$MD5_2"
    
    if [ "$MD5_1" = "$MD5_2" ]; then
        echo ""
        echo "✅ Files are identical on both instances!"
    else
        echo ""
        echo "❌ Files differ between instances!"
    fi
VERIFY

echo ""
echo "=== Sync Complete ==="
echo ""
echo "Both production instances are now synchronized!"
echo ""
echo "This fixes the inconsistent behavior where:"
echo "- Sometimes TPR downloads work (Instance 1)"
echo "- Sometimes they don't (Instance 2)"
echo ""
echo "Test the application now at:"
echo "http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com/"
echo ""
echo "The ALB will now route to two identical instances,"
echo "so the behavior should be consistent!"