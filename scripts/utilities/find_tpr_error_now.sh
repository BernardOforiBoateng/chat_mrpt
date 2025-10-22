#!/bin/bash

echo "=== Finding TPR Calculation Error Just Occurred ==="
echo ""

# Copy key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'EOF'

echo "Looking for the 500 error that just occurred..."

for INSTANCE_IP in 172.31.44.52 172.31.43.200; do
    echo ""
    echo "=== Instance: $INSTANCE_IP ==="
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$INSTANCE_IP << 'CHECK'
    
    echo "1. Last 5 minutes - Look for 'Under 5 Years' and errors:"
    sudo journalctl -u chatmrpt --since "5 minutes ago" | grep -B5 -A10 "Under 5\|Internal Server Error\|500\|Traceback\|Exception"
    
    echo ""
    echo "2. Check for session ID errors:"
    sudo journalctl -u chatmrpt --since "5 minutes ago" | grep -i "session_26e3e74d28e155a0\|session.*not found"
    
    echo ""
    echo "3. Check data_analysis_v3 processing:"
    sudo journalctl -u chatmrpt --since "5 minutes ago" | grep -B2 -A5 "data_analysis_v3.*chat\|DataAnalysisV3Agent\|handle_age_group"
    
CHECK
done

EOF