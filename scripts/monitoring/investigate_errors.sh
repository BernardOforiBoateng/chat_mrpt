#!/bin/bash

echo "=== Investigating Production Errors ==="
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
    
    echo "1. Check for 'is_data_analysis' parameter error:"
    sudo journalctl -u chatmrpt --since "30 minutes ago" | grep -i "is_data_analysis\|unexpected keyword" | tail -5
    
    echo ""
    echo "2. Check for 500 errors and TPR calculation issues:"
    sudo journalctl -u chatmrpt --since "30 minutes ago" | grep -E "500|Internal Server Error|Traceback|Exception|TPR|Under 5" | tail -20
    
    echo ""
    echo "3. Check request_interpreter.py signature:"
    grep -n "def process_message_streaming" /home/ec2-user/ChatMRPT/app/core/request_interpreter.py | head -2
    
    echo ""
    echo "4. Check analysis_routes.py where it calls request_interpreter:"
    grep -B2 -A5 "request_interpreter.process_message_streaming" /home/ec2-user/ChatMRPT/app/web/routes/analysis_routes.py | head -15
    
CHECK
done

EOF