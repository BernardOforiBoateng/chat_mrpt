#!/bin/bash

echo "=== Deploying Single Worker Fix for Session Persistence ==="

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 'bash -s' << 'EOSSH'
cd /home/ec2-user/ChatMRPT

echo "1. Backing up current gunicorn config..."
cp gunicorn.conf.py gunicorn.conf.py.backup_multiworker

echo "2. Updating to single worker configuration..."
# Update the workers line to use single worker
sed -i 's/workers = int(os.environ.get.*$/workers = 1  # Single worker for session persistence/' gunicorn.conf.py

echo "3. Showing the change..."
grep -n "workers =" gunicorn.conf.py

echo "4. Restarting ChatMRPT service..."
sudo systemctl restart chatmrpt

echo "5. Waiting for service to start..."
sleep 5

echo "6. Checking service status..."
sudo systemctl status chatmrpt | head -15

echo ""
echo "7. Verifying worker count..."
ps aux | grep gunicorn | grep -v grep | wc -l

echo ""
echo "✅ Single worker configuration deployed!"
echo ""
echo "Benefits:"
echo "- Session persistence will work correctly"
echo "- Report generation after analysis will function properly"
echo "- Suitable for up to 10 concurrent users"
echo ""
echo "To scale up later, we can implement Redis for session sharing."
EOSSH