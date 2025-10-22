#!/bin/bash

echo "=== Checking if Requests are Reaching Server ==="
echo ""

# Copy key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'EOF'

echo "Checking recent activity on both instances..."

for INSTANCE_IP in 172.31.44.52 172.31.43.200; do
    echo ""
    echo "=== Instance: $INSTANCE_IP ==="
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$INSTANCE_IP << 'CHECK'
    
    echo "1. ANY activity in last 10 minutes:"
    sudo journalctl -u chatmrpt --since "10 minutes ago" | tail -20
    
    echo ""
    echo "2. Check if service is actually running:"
    sudo systemctl status chatmrpt | head -15
    
    echo ""
    echo "3. Check access logs for recent requests:"
    sudo journalctl -u chatmrpt --since "10 minutes ago" | grep -E "POST|GET|/api/" | tail -10
    
    echo ""
    echo "4. Check if data_analysis_v3_routes.py has the chat endpoint:"
    grep -n "@data_analysis_v3_bp.route('/api/v1/data-analysis/chat'" /home/ec2-user/ChatMRPT/app/web/routes/data_analysis_v3_routes.py
    
CHECK
done

EOF