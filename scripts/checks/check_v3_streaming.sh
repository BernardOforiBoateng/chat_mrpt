#!/bin/bash

echo "=== Checking V3 Streaming Support ==="
echo ""

# Copy key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'EOF'

ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'CHECK'
cd /home/ec2-user/ChatMRPT

echo "1. Check if V3 chat endpoint is async or sync:"
grep -B5 -A20 "@data_analysis_v3_bp.route('/api/v1/data-analysis/chat'" app/web/routes/data_analysis_v3_routes.py | head -30

echo ""
echo "2. Check if frontend is expecting streaming response:"
grep -B5 -A10 "hasDataAnalysis.*'/api/v1/data-analysis/chat'" app/static/js/modules/utils/api-client.js

echo ""
echo "3. The problem: Frontend expects STREAMING but V3 might not support it!"
echo ""
echo "4. Check if there's a streaming version of V3 endpoint:"
grep -n "stream\|Stream" app/web/routes/data_analysis_v3_routes.py | head -10

CHECK

EOF