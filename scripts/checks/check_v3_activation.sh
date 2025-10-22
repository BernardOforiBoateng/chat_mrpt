#!/bin/bash

echo "=== Checking Why Data Analysis V3 Isn't Active ==="
echo ""

# Copy key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'EOF'

echo "Checking Production configuration..."
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'CHECK'
cd /home/ec2-user/ChatMRPT

echo "1. Check if data_analysis_v3 blueprint is registered:"
python3 -c "
from app import create_app
app = create_app()
print('Registered blueprints:')
for name in app.blueprints:
    print(f'  - {name}')
" 2>/dev/null | grep -E "blueprint|data_analysis"

echo ""
echo "2. Check frontend - which endpoint is being called for uploads?"
grep -n "data-analysis/upload" app/static/js/modules/upload/data-analysis-upload.js | head -5

echo ""
echo "3. Check the actual upload endpoint in data_analysis_v3_routes:"
grep -n "@data_analysis_v3_bp.route.*upload" app/web/routes/data_analysis_v3_routes.py | head -5

echo ""
echo "4. Check if frontend is using the correct chat endpoint:"
grep -n "api/analysis/stream\|api/data-analysis-v3" app/static/js/modules/utils/api-client.js | head -10

echo ""
echo "5. The issue - frontend is calling wrong endpoint!"
echo "Frontend calls: /api/data-analysis/upload"
echo "V3 expects: /api/data-analysis-v3/upload"
echo ""
echo "Checking current frontend configuration:"
grep "const.*UPLOAD_URL\|uploadUrl\|/upload" app/static/js/modules/upload/data-analysis-upload.js | head -5

CHECK

EOF
