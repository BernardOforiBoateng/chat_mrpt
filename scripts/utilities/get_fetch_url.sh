#!/bin/bash

echo "=== Getting Fetch URL ==="

cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'EOF'

ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'CHECK'
cd /home/ec2-user/ChatMRPT

echo "Finding fetch call in sendMessageStreaming:"
grep -A5 "fetch.*stream\|fetch.*'/api" app/static/js/modules/utils/api-client.js | head -10

echo ""
echo "Line number where fetch is called:"
grep -n "fetch.*'/api/analysis/stream'" app/static/js/modules/utils/api-client.js

CHECK

EOF
