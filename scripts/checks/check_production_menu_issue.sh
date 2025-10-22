#!/bin/bash

echo "=== Checking Production Menu Display Issue ==="
echo "Looking for why TPR menu options aren't shown after file upload"
echo ""

# Copy key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# Check both instances
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'EOF'

echo "=== Checking Instance 1 Logs ==="
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'INST1'
echo "Recent upload and analysis logs:"
sudo journalctl -u chatmrpt --since "30 minutes ago" | grep -E "adamawa_tpr|upload|TPR|menu|options|Quick TPR|Guided TPR|Complete Analysis" | tail -30

echo ""
echo "Checking for menu generation in agent logs:"
sudo journalctl -u chatmrpt --since "30 minutes ago" | grep -E "format_initial_menu|menu_options|analysis_options|workflow_type" | tail -20
INST1

echo ""
echo "=== Checking Instance 2 Logs ==="
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.43.200 << 'INST2'
echo "Recent upload and analysis logs:"
sudo journalctl -u chatmrpt --since "30 minutes ago" | grep -E "adamawa_tpr|upload|TPR|menu|options|Quick TPR|Guided TPR|Complete Analysis" | tail -30

echo ""
echo "Checking for menu generation in agent logs:"
sudo journalctl -u chatmrpt --since "30 minutes ago" | grep -E "format_initial_menu|menu_options|analysis_options|workflow_type" | tail -20
INST2

echo ""
echo "=== Checking for Data Analysis V3 route handling ==="
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'CHECK'
echo "Checking if data_analysis_v3 is being used:"
sudo journalctl -u chatmrpt --since "30 minutes ago" | grep -i "data_analysis" | tail -10

echo ""
echo "Checking for state manager activity:"
sudo journalctl -u chatmrpt --since "30 minutes ago" | grep -i "state_manager\|StateManager" | tail -10
CHECK

EOF