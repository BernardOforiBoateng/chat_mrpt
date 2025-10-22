#!/bin/bash

echo "=== Debugging State Persistence Issue ==="
echo ""

# Copy key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'EOF'

echo "Checking Production - Why state is lost between menu display and selection"
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'DEBUG'
cd /home/ec2-user/ChatMRPT

echo "1. Check state_manager.py save_state method:"
grep -B5 -A10 "def save_state" app/data_analysis_v3/core/state_manager.py | head -30

echo ""
echo "2. Check if workflow_state is being saved after menu display:"
grep -B2 -A5 "workflow_state.*initial_menu\|save_state.*workflow" app/data_analysis_v3/core/agent.py | head -20

echo ""
echo "3. Check actual session folder for state files:"
ls -la instance/uploads/*/state.json 2>/dev/null | tail -5 || echo "No state files found"

echo ""
echo "4. Check if data_analysis_v3 is handling the upload response:"
sudo journalctl -u chatmrpt --since "30 minutes ago" | grep -i "data_analysis_v3\|DataAnalysisV3Agent" | tail -10

echo ""
echo "5. Check the actual route being hit:"
sudo journalctl -u chatmrpt --since "30 minutes ago" | grep "POST /api/" | tail -10

DEBUG

EOF