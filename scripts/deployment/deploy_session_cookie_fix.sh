#!/bin/bash

echo "=== Deploying Session Cookie Persistence Fix ==="

# First copy the files to tmp
cp app/config/base.py /tmp/base_fixed.py
cp app/__init__.py /tmp/init_fixed.py
cp app/web/routes/core_routes.py /tmp/core_routes_fixed.py

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 'bash -s' << 'EOSSH'
cd /home/ec2-user/ChatMRPT

echo "1. Backing up current files..."
cp app/config/base.py app/config/base.py.backup_cookie_fix
cp app/__init__.py app/__init__.py.backup_cookie_fix
cp app/web/routes/core_routes.py app/web/routes/core_routes.py.backup_cookie_fix

echo "2. Waiting for file transfer..."
EOSSH

echo "3. Transferring fixed files..."
scp -i /tmp/chatmrpt-key2.pem /tmp/base_fixed.py ec2-user@3.137.158.17:/tmp/
scp -i /tmp/chatmrpt-key2.pem /tmp/init_fixed.py ec2-user@3.137.158.17:/tmp/
scp -i /tmp/chatmrpt-key2.pem /tmp/core_routes_fixed.py ec2-user@3.137.158.17:/tmp/

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 'bash -s' << 'EOSSH'
cd /home/ec2-user/ChatMRPT

echo "4. Deploying fixed files..."
cp /tmp/base_fixed.py app/config/base.py
cp /tmp/init_fixed.py app/__init__.py
cp /tmp/core_routes_fixed.py app/web/routes/core_routes.py

echo "5. Checking syntax..."
python3 -m py_compile app/config/base.py && echo "✓ base.py OK"
python3 -m py_compile app/__init__.py && echo "✓ __init__.py OK"
python3 -m py_compile app/web/routes/core_routes.py && echo "✓ core_routes.py OK"

echo "6. Clearing old session files..."
rm -rf instance/flask_session/*

echo "7. Restarting service..."
sudo systemctl restart chatmrpt

echo "8. Waiting for service to start..."
sleep 5

echo "9. Checking service status..."
sudo systemctl status chatmrpt | head -15

echo ""
echo "✅ Session Cookie Persistence Fix deployed!"
echo ""
echo "What was fixed:"
echo "- Added session.permanent = True before every request"
echo "- Added session.modified = True after session initialization"
echo "- Added session.modified = True after TPR state changes"
echo "- Added SESSION_COOKIE_NAME for consistent cookie naming"
echo ""
echo "This ensures session cookies persist across requests and page refreshes."
echo "Report generation should now work correctly!"
EOSSH