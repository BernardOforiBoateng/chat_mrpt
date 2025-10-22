#!/bin/bash

echo "=== Fixing and Analyzing Permission Issue ==="

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 << 'EOSSH'
cd /home/ec2-user/ChatMRPT
source /home/ec2-user/chatmrpt_env/bin/activate

echo "1. Restoring from backup..."
cp app/core/request_interpreter.py.backup_permission_debug app/core/request_interpreter.py

echo "2. Checking if service works with backup..."
python3 -m py_compile app/core/request_interpreter.py && echo "✓ Syntax OK"

echo "3. Restarting service..."
sudo systemctl restart chatmrpt
sleep 3

echo "4. Now let's analyze the actual issue..."
echo ""
echo "=== ANALYZING PERMISSION WORKFLOW ==="

# Check the current logs when permission flag is found
echo "Recent permission-related logs:"
sudo journalctl -u chatmrpt --since '30 minutes ago' | grep -B2 -A10 'Permission flag found' | tail -30

echo ""
echo "=== CHECKING DATA FLOW ==="
echo "Looking for what happens after permission flag detection:"
sudo journalctl -u chatmrpt --since '30 minutes ago' | grep -A20 "yes proceed" | grep -E "(special_result|Permission|Tool call|streaming)" | tail -20

echo ""
echo "=== SERVICE STATUS ==="
sudo systemctl status chatmrpt | head -10
EOSSH