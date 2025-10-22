#!/bin/bash

echo "=== Deploying Session Modified Fix ==="

# First copy the file to tmp
cp app/web/routes/analysis_routes.py /tmp/analysis_routes_fixed.py

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 'bash -s' << 'EOSSH'
cd /home/ec2-user/ChatMRPT

echo "1. Backing up current analysis_routes.py..."
cp app/web/routes/analysis_routes.py app/web/routes/analysis_routes.py.backup_session_fix

echo "2. Waiting for file transfer..."
EOSSH

echo "3. Transferring fixed file..."
scp -i /tmp/chatmrpt-key2.pem /tmp/analysis_routes_fixed.py ec2-user@3.137.158.17:/tmp/

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 'bash -s' << 'EOSSH'
cd /home/ec2-user/ChatMRPT

echo "4. Deploying fixed analysis_routes.py..."
cp /tmp/analysis_routes_fixed.py app/web/routes/analysis_routes.py

echo "5. Checking syntax..."
python3 -m py_compile app/web/routes/analysis_routes.py && echo "✓ analysis_routes.py OK"

echo "6. Restarting service..."
sudo systemctl restart chatmrpt

echo "7. Waiting for service to start..."
sleep 5

echo "8. Checking service status..."
sudo systemctl status chatmrpt | head -15

echo ""
echo "✅ Session Modified Fix deployed!"
echo ""
echo "What was fixed:"
echo "- Added session.modified = True after setting analysis_complete"
echo "- Added session.modified = True after pop operations"
echo "- This ensures Flask filesystem sessions are properly saved"
echo ""
echo "Report generation should now work correctly after analysis!"
EOSSH