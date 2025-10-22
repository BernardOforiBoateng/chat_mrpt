#!/bin/bash

echo "=== Finding the Actual Chat Endpoint ==="

cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'EOF'

ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'CHECK'
cd /home/ec2-user/ChatMRPT

echo "Finding the streaming endpoint in api-client.js:"
grep -A10 "sendMessageStreaming" app/static/js/modules/utils/api-client.js | grep -E "fetch|url|endpoint" | head -5

echo ""
echo "Checking if there's a session flag set after data analysis upload:"
grep -n "sessionStorage\|localStorage\|dataAnalysisMode" app/static/js/modules/upload/data-analysis-upload.js | head -10

CHECK

EOF
