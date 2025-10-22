#!/bin/bash

# Script to run from staging server to deploy to production ASG instance
# This script should be copied to staging and executed there

echo "=== Deploying from Staging to Production ASG ==="
echo "This script should be run from the staging server (18.117.115.217)"

# Production ASG instance (update if instance changes)
PROD_INSTANCE="i-06d3edfcc85a1f1c7"

# Create deployment package on staging
echo "1. Creating deployment package..."
cd /home/ec2-user/ChatMRPT
tar -czf /tmp/chatmrpt_fixes.tar.gz \
  app/core/unified_data_state.py \
  app/core/analysis_state_handler.py \
  app/core/request_interpreter.py \
  gunicorn.conf.py

echo "2. Package created at /tmp/chatmrpt_fixes.tar.gz"
echo ""
echo "Next steps to complete deployment:"
echo "=================================="
echo "1. Use AWS Console → EC2 → Instances"
echo "2. Find instance: $PROD_INSTANCE"
echo "3. Click 'Connect' → 'Session Manager'"
echo "4. Once connected, run these commands:"
echo ""
cat << 'EOF'
# On production instance:
cd /home/ec2-user/ChatMRPT

# Create backups
sudo cp app/core/unified_data_state.py app/core/unified_data_state.py.backup_$(date +%Y%m%d_%H%M%S)
sudo cp app/core/analysis_state_handler.py app/core/analysis_state_handler.py.backup_$(date +%Y%m%d_%H%M%S)
sudo cp app/core/request_interpreter.py app/core/request_interpreter.py.backup_$(date +%Y%m%d_%H%M%S)
sudo cp gunicorn.conf.py gunicorn.conf.py.backup_$(date +%Y%m%d_%H%M%S)

# Get the fixes from staging (if network allows)
scp ec2-user@18.117.115.217:/tmp/chatmrpt_fixes.tar.gz /tmp/
tar -xzf /tmp/chatmrpt_fixes.tar.gz -C /home/ec2-user/ChatMRPT/

# Or manually copy each file:
scp ec2-user@18.117.115.217:/home/ec2-user/ChatMRPT/app/core/unified_data_state.py app/core/
scp ec2-user@18.117.115.217:/home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py app/core/
scp ec2-user@18.117.115.217:/home/ec2-user/ChatMRPT/app/core/request_interpreter.py app/core/
scp ec2-user@18.117.115.217:/home/ec2-user/ChatMRPT/gunicorn.conf.py .

# Test syntax
python3 -m py_compile app/core/unified_data_state.py
python3 -m py_compile app/core/analysis_state_handler.py
python3 -m py_compile app/core/request_interpreter.py

# Restart service
sudo systemctl restart chatmrpt

# Verify
sleep 10
ps aux | grep gunicorn | grep -v grep | wc -l  # Should show 7
curl http://localhost:8080/ping
EOF

echo ""
echo "5. Test at: http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"