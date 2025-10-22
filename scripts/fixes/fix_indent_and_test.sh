#!/bin/bash

echo "=== Fixing Indentation and Testing Permission System ==="

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 << 'EOSSH'
cd /home/ec2-user/ChatMRPT
source /home/ec2-user/chatmrpt_env/bin/activate

echo "1. Restoring clean backup..."
cp app/core/request_interpreter.py.backup_permission_debug app/core/request_interpreter.py

echo "2. Checking syntax of backup..."
python3 -m py_compile app/core/request_interpreter.py
if [ $? -eq 0 ]; then
    echo "✓ Backup file has valid syntax"
else
    echo "✗ Even backup has syntax errors, need different approach"
    # List available backups
    echo "Available backups:"
    ls -la app/core/request_interpreter.py.backup* | tail -5
fi

echo ""
echo "3. Looking for the permission logic..."
grep -n "should_ask_analysis_permission" app/core/request_interpreter.py | head -5
echo ""
grep -n "_is_confirmation_message" app/core/request_interpreter.py | head -5

echo ""
echo "4. Restarting with clean file..."
sudo systemctl restart chatmrpt

sleep 3

echo ""
echo "5. Testing current behavior..."
echo "Recent logs showing permission workflow:"
sudo journalctl -u chatmrpt --since '20 minutes ago' | grep -B5 -A15 "Permission flag found" | tail -40

echo ""
echo "6. Service status:"
sudo systemctl status chatmrpt | head -10
EOSSH