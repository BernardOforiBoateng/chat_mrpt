#!/bin/bash

echo "=== Checking Why Option '2' Selection Fails ==="
echo "The menu shows but selection isn't recognized"
echo ""

# Copy key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'EOF'

echo "=== Checking Production Instance 1 - Selection Handling ==="
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'CHECK'
cd /home/ec2-user/ChatMRPT

echo "1. Checking if data_analysis_v3 routes are active:"
grep -A5 "data_analysis_v3" app/web/routes/__init__.py

echo ""
echo "2. Checking agent.py for numeric input handling:"
grep -B2 -A2 'user_query.strip() == "2"' app/data_analysis_v3/core/agent.py 2>/dev/null || echo "Pattern not found in data_analysis_v3"

echo ""
echo "3. Checking state manager for workflow state:"
grep -A5 "workflow_state\|menu_context" app/data_analysis_v3/core/state_manager.py 2>/dev/null | head -20

echo ""
echo "4. Recent logs showing the actual flow:"
sudo journalctl -u chatmrpt --since "30 minutes ago" | grep -E "workflow_state|menu_context|user_query.*2|selection.*2" | tail -20

echo ""
echo "5. Checking Redis for session state:"
python3 << 'PYTEST'
import os
from dotenv import load_dotenv
load_dotenv()

# Check if menu state is being saved
print("Checking if state is persisted in Redis...")
print(f"Redis enabled: {os.getenv('REDIS_ENABLED', 'false')}")
print(f"Redis host: {os.getenv('REDIS_HOST', 'not set')}")
PYTEST

CHECK

EOF