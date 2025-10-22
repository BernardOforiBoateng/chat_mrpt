#!/bin/bash

echo "=== Checking Why System Gets Stuck After Option 2 ==="
echo ""

# Copy key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'EOF'

echo "Checking both production instances for errors..."

for INSTANCE_IP in 172.31.44.52 172.31.43.200; do
    echo ""
    echo "=== Instance: $INSTANCE_IP ==="
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$INSTANCE_IP << 'CHECK'
    
    echo "1. Recent errors in last 5 minutes:"
    sudo journalctl -u chatmrpt --since "5 minutes ago" | grep -i "error\|exception\|traceback\|timeout" | tail -20
    
    echo ""
    echo "2. Check for V3 endpoint activity:"
    sudo journalctl -u chatmrpt --since "5 minutes ago" | grep -E "/api/v1/data-analysis/chat|DataAnalysisV3Agent|data_analysis_v3" | tail -10
    
    echo ""
    echo "3. Check for stuck requests or timeouts:"
    sudo journalctl -u chatmrpt --since "5 minutes ago" | grep -E "stuck|timeout|hanging|Option 2|option.*2" | tail -10
    
    echo ""
    echo "4. Last 10 lines of general logs:"
    sudo journalctl -u chatmrpt --since "2 minutes ago" | tail -10
    
CHECK
done

EOF