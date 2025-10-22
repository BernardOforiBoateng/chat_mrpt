#!/bin/bash

echo "=== Copying Working Files from Staging to Production ==="
echo "Staging works perfectly - copying everything to production"
echo ""

# Copy key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# Files to copy
FILES_TO_COPY="
app/web/routes/data_analysis_v3_routes.py
app/web/routes/analysis_routes.py
app/data_analysis_v3/core/agent.py
app/data_analysis_v3/core/state_manager.py
app/static/js/modules/utils/api-client.js
app/static/js/modules/upload/data-analysis-upload.js
app/static/js/modules/chat/core/message-handler.js
"

echo "Copying files from staging to production..."
echo ""

# First, copy files from staging to local
ssh -i /tmp/chatmrpt-key2.pem ec2-user@18.220.103.20 << 'EOF'
cd /home/ec2-user/ChatMRPT
tar czf /tmp/staging_files.tar.gz \
  app/web/routes/data_analysis_v3_routes.py \
  app/web/routes/analysis_routes.py \
  app/data_analysis_v3/core/agent.py \
  app/data_analysis_v3/core/state_manager.py \
  app/static/js/modules/utils/api-client.js \
  app/static/js/modules/upload/data-analysis-upload.js \
  app/static/js/modules/chat/core/message-handler.js
EOF

# Copy tar file to local
scp -i /tmp/chatmrpt-key2.pem ec2-user@18.220.103.20:/tmp/staging_files.tar.gz /tmp/

# Now copy to both production instances via staging proxy
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'EOF'

# Copy tar file to staging first
scp -i ~/.ssh/chatmrpt-key.pem ec2-user@18.220.103.20:/tmp/staging_files.tar.gz /tmp/

# Copy to both production instances
for PROD_IP in 172.31.44.52 172.31.43.200; do
    echo "Deploying to production instance: $PROD_IP"
    
    # Copy tar file to production instance
    scp -i ~/.ssh/chatmrpt-key.pem /tmp/staging_files.tar.gz ec2-user@$PROD_IP:/tmp/
    
    # Extract and restart on production instance
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP << 'PROD'
    cd /home/ec2-user/ChatMRPT
    
    # Backup current files
    echo "Backing up current files..."
    tar czf /tmp/prod_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
      app/web/routes/data_analysis_v3_routes.py \
      app/web/routes/analysis_routes.py \
      app/data_analysis_v3/core/agent.py \
      app/data_analysis_v3/core/state_manager.py \
      app/static/js/modules/utils/api-client.js \
      app/static/js/modules/upload/data-analysis-upload.js \
      app/static/js/modules/chat/core/message-handler.js 2>/dev/null
    
    # Extract staging files
    echo "Extracting staging files..."
    tar xzf /tmp/staging_files.tar.gz
    
    # Restart service
    echo "Restarting service..."
    sudo systemctl restart chatmrpt
    
    # Check status
    sleep 3
    echo "Service status:"
    sudo systemctl is-active chatmrpt
    
    echo "✅ Instance $PROD_IP updated with staging files"
    echo "-----------------------------------"
PROD
done

echo ""
echo "=== COMPLETE ==="
echo "Both production instances now have the exact same files as staging!"
echo "The system should work exactly like staging now."

EOF