#!/bin/bash

echo "=== Tracing Request Flow for Option '2' ==="
echo ""

# Copy key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'EOF'

echo "Checking which route handles the upload and chat messages..."
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'TRACE'
cd /home/ec2-user/ChatMRPT

echo "1. Check analysis_routes.py - is it handling data analysis uploads?"
grep -n "data-analysis/upload\|/api/analysis/stream" app/web/routes/analysis_routes.py | head -10

echo ""
echo "2. Check data_analysis_v3_routes.py - is this active?"
ls -la app/web/routes/data_analysis_v3_routes.py 2>/dev/null && echo "File exists" || echo "File NOT found"

echo ""
echo "3. Check if request goes to regular analysis or data_analysis_v3:"
sudo journalctl -u chatmrpt --since "30 minutes ago" | grep -E "POST.*\/api\/" | grep -v "ping\|health" | tail -10

echo ""
echo "4. Check request_interpreter.py for route decision:"
grep -B2 -A5 "data_analysis_upload\|has_data_upload" app/core/request_interpreter.py | head -20

echo ""
echo "5. Most importantly - is data analysis v3 even being triggered?"
sudo journalctl -u chatmrpt --since "30 minutes ago" | grep -i "DataAnalysisV3Agent\|data_analysis_v3" | wc -l
echo "Number of data_analysis_v3 mentions in last 30 mins: ^"

echo ""
echo "6. What agent is actually handling the requests?"
sudo journalctl -u chatmrpt --since "30 minutes ago" | grep -i "agent\|ChatMRPTAgent" | tail -5

TRACE

EOF