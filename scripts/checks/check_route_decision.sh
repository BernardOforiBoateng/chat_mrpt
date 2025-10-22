#!/bin/bash

echo "=== Checking How Routes Decide Which Agent to Use ==="

cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'EOF'

ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'CHECK'
cd /home/ec2-user/ChatMRPT

echo "1. Check analysis_routes.py chat_stream endpoint:"
grep -B5 -A15 "@analysis_bp.route.*/api/analysis/stream" app/web/routes/analysis_routes.py | head -30

echo ""
echo "2. Check if there's logic to detect data analysis mode:"
grep -n "session\[.data_analysis\|has_data_upload\|data_loaded" app/web/routes/analysis_routes.py | head -10

echo ""
echo "3. Check data_analysis_v3_routes chat endpoint:"
grep -B5 -A10 "@data_analysis_v3_bp.route.*/chat" app/web/routes/data_analysis_v3_routes.py | head -20

CHECK

EOF
