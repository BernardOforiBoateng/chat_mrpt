#!/bin/bash
set -e

echo "=========================================="
echo "ChatMRPT Production Deployment Script"
echo "Deploying all fixes from staging to production"
echo "=========================================="

# Production server IP
PRODUCTION_IP="3.137.158.17"

echo -e "\n1. Creating backup of production files..."
ssh -i ~/tmp/chatmrpt-key.pem ec2-user@$PRODUCTION_IP 'bash -s' << 'EOF'
set -e
cd /home/ec2-user/ChatMRPT
echo "Creating backups..."
cp app/core/unified_data_state.py app/core/unified_data_state.py.backup_$(date +%Y%m%d_%H%M%S)
cp app/core/analysis_state_handler.py app/core/analysis_state_handler.py.backup_$(date +%Y%m%d_%H%M%S)
cp app/core/request_interpreter.py app/core/request_interpreter.py.backup_$(date +%Y%m%d_%H%M%S)
cp gunicorn.conf.py gunicorn.conf.py.backup_$(date +%Y%m%d_%H%M%S)
echo "Backups created successfully"
EOF

echo -e "\n2. Copying fixed files from staging to production..."
# Get the fixed files from staging
echo "Retrieving fixed files from staging..."
scp -i ~/tmp/chatmrpt-key.pem ec2-user@18.117.115.217:/home/ec2-user/ChatMRPT/app/core/unified_data_state.py /tmp/unified_data_state_fixed.py
scp -i ~/tmp/chatmrpt-key.pem ec2-user@18.117.115.217:/home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py /tmp/analysis_state_handler_fixed.py
scp -i ~/tmp/chatmrpt-key.pem ec2-user@18.117.115.217:/home/ec2-user/ChatMRPT/app/core/request_interpreter.py /tmp/request_interpreter_fixed.py

# Copy to production
echo "Deploying fixed files to production..."
scp -i ~/tmp/chatmrpt-key.pem /tmp/unified_data_state_fixed.py ec2-user@$PRODUCTION_IP:/home/ec2-user/ChatMRPT/app/core/unified_data_state.py
scp -i ~/tmp/chatmrpt-key.pem /tmp/analysis_state_handler_fixed.py ec2-user@$PRODUCTION_IP:/home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py
scp -i ~/tmp/chatmrpt-key.pem /tmp/request_interpreter_fixed.py ec2-user@$PRODUCTION_IP:/home/ec2-user/ChatMRPT/app/core/request_interpreter.py

echo -e "\n3. Updating worker configuration on production..."
ssh -i ~/tmp/chatmrpt-key.pem ec2-user@$PRODUCTION_IP 'bash -s' << 'EOF'
set -e
cd /home/ec2-user/ChatMRPT

echo "Current worker configuration:"
grep "workers =" gunicorn.conf.py

echo -e "\nUpdating to 6 workers..."
sed -i 's/workers = [0-9]*/workers = 6/' gunicorn.conf.py

echo "New configuration:"
grep "workers =" gunicorn.conf.py

echo -e "\nChecking syntax of deployed files..."
python3 -m py_compile app/core/unified_data_state.py && echo "✅ unified_data_state.py OK"
python3 -m py_compile app/core/analysis_state_handler.py && echo "✅ analysis_state_handler.py OK"
python3 -m py_compile app/core/request_interpreter.py && echo "✅ request_interpreter.py OK"
EOF

echo -e "\n4. Checking production server resources..."
ssh -i ~/tmp/chatmrpt-key.pem ec2-user@$PRODUCTION_IP 'bash -s' << 'EOF'
echo "Server resources:"
echo "CPUs: $(nproc)"
free -h
echo -e "\nCurrent Gunicorn processes:"
ps aux | grep gunicorn | grep -v grep | wc -l
EOF

echo -e "\n5. Restarting production ChatMRPT with new configuration..."
ssh -i ~/tmp/chatmrpt-key.pem ec2-user@$PRODUCTION_IP 'bash -s' << 'EOF'
set -e
echo "Restarting ChatMRPT service..."
sudo systemctl restart chatmrpt
sleep 10

echo -e "\nVerifying new worker count:"
ps aux | grep gunicorn | grep -v grep | wc -l

echo -e "\nChecking service health:"
curl -s http://localhost:5000/ping && echo -e "\n✅ Production service is healthy!"

echo -e "\nChecking recent logs for errors:"
sudo journalctl -u chatmrpt -n 20 | grep -i error || echo "No errors in recent logs"
EOF

# Cleanup temp files
rm -f /tmp/unified_data_state_fixed.py /tmp/analysis_state_handler_fixed.py /tmp/request_interpreter_fixed.py

echo -e "\n=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo "Production server (3.137.158.17) now has:"
echo "- Multi-worker session state fixes"
echo "- ITN planning detection fix"
echo "- Session context file-based detection"
echo "- 6 workers for 50-60 concurrent users"
echo ""
echo "Staging server (18.117.115.217) remains unchanged"
echo "for future testing and improvements."
echo "=========================================="