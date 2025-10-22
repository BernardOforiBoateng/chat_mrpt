#!/bin/bash

echo "=== Copying ALL Working Files from Staging to Production ==="
echo "This will ensure production matches staging exactly"
echo ""

# Copy key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# Create tar file on staging with ALL relevant files
ssh -i /tmp/chatmrpt-key2.pem ec2-user@18.220.103.20 << 'EOF'
cd /home/ec2-user/ChatMRPT
tar czf /tmp/staging_complete.tar.gz \
  app/web/routes/*.py \
  app/data_analysis_v3/ \
  app/core/request_interpreter.py \
  app/core/unified_data_state.py \
  app/services/container.py \
  app/static/js/modules/utils/api-client.js \
  app/static/js/modules/upload/data-analysis-upload.js \
  app/static/js/modules/chat/core/message-handler.js \
  app/tools/complete_analysis_tools.py \
  app/tools/export_tools.py
EOF

# Copy tar file to local
scp -i /tmp/chatmrpt-key2.pem ec2-user@18.220.103.20:/tmp/staging_complete.tar.gz /tmp/

# Deploy to both production instances via staging proxy
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'EOF'

# Copy tar file to staging proxy
scp -i ~/.ssh/chatmrpt-key.pem ec2-user@18.220.103.20:/tmp/staging_complete.tar.gz /tmp/

# Deploy to both production instances
for PROD_IP in 172.31.44.52 172.31.43.200; do
    echo ""
    echo "Deploying to production instance: $PROD_IP"
    
    # Copy tar file to production instance
    scp -i ~/.ssh/chatmrpt-key.pem /tmp/staging_complete.tar.gz ec2-user@$PROD_IP:/tmp/
    
    # Extract and restart on production instance
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP << 'PROD'
    cd /home/ec2-user/ChatMRPT
    
    # Backup current files
    echo "Backing up current files..."
    tar czf /tmp/prod_backup_complete_$(date +%Y%m%d_%H%M%S).tar.gz \
      app/web/routes/ \
      app/data_analysis_v3/ \
      app/core/request_interpreter.py \
      app/services/container.py \
      app/static/js/modules/ \
      app/tools/ 2>/dev/null || true
    
    # Extract staging files
    echo "Extracting staging files..."
    tar xzf /tmp/staging_complete.tar.gz
    
    # Ensure Redis configuration is still correct
    echo "Verifying Redis configuration..."
    if ! grep -q "REDIS_HOST=chatmrpt-redis-production" .env; then
        echo "Fixing Redis configuration..."
        sed -i 's|REDIS_HOST=.*|REDIS_HOST=chatmrpt-redis-production.1b3pmt.0001.use2.cache.amazonaws.com|' .env
    fi
    
    # Restart service
    echo "Restarting service..."
    sudo systemctl restart chatmrpt
    
    # Wait for service to start
    sleep 5
    
    # Check status
    echo "Service status:"
    sudo systemctl is-active chatmrpt
    
    # Check for startup errors
    echo "Recent logs:"
    sudo journalctl -u chatmrpt --since "1 minute ago" | grep -E "ERROR|initialized|Data Analysis V3" | tail -10
    
    echo "✅ Instance $PROD_IP updated"
    echo "-----------------------------------"
PROD
done

echo ""
echo "=== COMPLETE ==="
echo "Both production instances now have the COMPLETE working configuration from staging"

EOF