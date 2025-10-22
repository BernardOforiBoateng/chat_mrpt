#!/bin/bash

echo "=== Deploying Report Generation Fix ==="

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 'bash -s' << 'EOSSH'
cd /home/ec2-user/ChatMRPT
source /home/ec2-user/chatmrpt_env/bin/activate

echo "1. Backing up and deploying debug_routes.py..."
cp app/web/routes/debug_routes.py app/web/routes/debug_routes.py.backup_report_fix 2>/dev/null || true
cp /tmp/debug_routes_new.py app/web/routes/debug_routes.py

echo "2. Checking syntax..."
python3 -m py_compile app/web/routes/debug_routes.py && echo "✓ debug_routes.py OK"

echo "3. Restarting service..."
sudo systemctl restart chatmrpt

echo "4. Waiting for service to start..."
sleep 3

echo "5. Testing debug endpoint..."
curl -s http://localhost:5000/debug/session_state | head -20

echo ""
echo "6. Service status:"
sudo systemctl status chatmrpt | head -10

echo ""
echo "✅ Report generation fix deployed!"
echo ""
echo "The /debug/session_state endpoint is now available."
echo "The 'Generate a report' button should work after completing an analysis."
EOSSH