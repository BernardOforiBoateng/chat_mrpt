#!/bin/bash

echo "=== Checking TPR Calculation Error ==="
echo ""

# Copy key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'EOF'

echo "Looking for the 500 error when calculating TPR..."

for INSTANCE_IP in 172.31.44.52 172.31.43.200; do
    echo ""
    echo "=== Instance: $INSTANCE_IP ==="
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$INSTANCE_IP << 'CHECK'
    
    echo "1. Recent 500 errors with full traceback:"
    sudo journalctl -u chatmrpt --since "30 minutes ago" | grep -A20 "Internal Server Error\|500\|Traceback" | tail -30
    
    echo ""
    echo "2. Check data_analysis_v3 agent errors:"
    sudo journalctl -u chatmrpt --since "30 minutes ago" | grep -i "DataAnalysisV3Agent\|data_analysis_v3\|calculate_tpr\|age_group" | tail -20
    
    echo ""
    echo "3. Check if TPR calculation tool exists:"
    grep -n "calculate_tpr\|run_tpr" /home/ec2-user/ChatMRPT/app/data_analysis_v3/core/agent.py | head -5
    
CHECK
done

EOF