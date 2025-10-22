#!/bin/bash

echo "=== Checking Actual Message Flow ==="

cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'EOF'

echo "Checking on Staging first (where it works)..."
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@18.220.103.20 << 'STAGING'
echo "STAGING - Recent chat activity:"
sudo journalctl -u chatmrpt --since "2 hours ago" | grep -E "user_query.*2|option 2|TPR workflow" | tail -5
echo ""
echo "STAGING - Which agent handles requests:"
sudo journalctl -u chatmrpt --since "2 hours ago" | grep -i "DataAnalysisV3Agent\|DataAnalysisAgent" | tail -3
STAGING

echo ""
echo "Now checking Production..."
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'PROD'
echo "PRODUCTION - Recent chat activity:"
sudo journalctl -u chatmrpt --since "1 hour ago" | grep -E "user_query.*2|option 2|TPR workflow" | tail -5
echo ""
echo "PRODUCTION - Which agent handles requests:"
sudo journalctl -u chatmrpt --since "1 hour ago" | grep -i "DataAnalysisV3Agent\|DataAnalysisAgent\|ChatMRPTAgent" | tail -3
echo ""
echo "PRODUCTION - Check request_interpreter routing:"
sudo journalctl -u chatmrpt --since "1 hour ago" | grep -i "request_interpreter\|route_request" | tail -5
PROD

EOF
