#!/bin/bash

echo "=== Checking Frontend Chat Endpoint Usage ==="

cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'EOF'

ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'CHECK'
cd /home/ec2-user/ChatMRPT

echo "1. Check api-client.js - which endpoint is used for streaming:"
grep -n "sendMessageStreaming\|/api/analysis/stream" app/static/js/modules/utils/api-client.js | head -10

echo ""
echo "2. Check message-handler.js - does it know about data analysis mode?"
grep -n "dataAnalysis\|data-analysis\|/api/v1/data-analysis" app/static/js/modules/chat/core/message-handler.js | head -5

echo ""
echo "3. Check if there's any logic to switch endpoints based on mode:"
grep -n "isDataAnalysis\|dataAnalysisMode\|chatEndpoint" app/static/js/modules/chat/core/message-handler.js | head -5

echo ""
echo "4. THE PROBLEM: Frontend always uses /api/analysis/stream"
echo "   It should use /api/v1/data-analysis/chat after data analysis upload!"

CHECK

EOF
