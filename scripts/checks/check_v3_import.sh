#!/bin/bash

echo "=== Checking V3 Import and Registration ==="

cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'EOF'

ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'CHECK'
cd /home/ec2-user/ChatMRPT

echo "1. Test if V3 can be imported:"
python3 -c "
try:
    from app.web.routes.data_analysis_v3_routes import data_analysis_v3_bp
    print('✅ V3 import successful')
    print(f'V3 blueprint name: {data_analysis_v3_bp.name}')
except Exception as e:
    print(f'❌ V3 import failed: {e}')
"

echo ""
echo "2. Check app initialization for V3 registration:"
python3 -c "
from app import create_app
app = create_app()
if 'data_analysis_v3' in app.blueprints:
    print('✅ V3 blueprint IS registered!')
else:
    print('❌ V3 blueprint NOT registered')
    print('Registered blueprints:', list(app.blueprints.keys()))
"

echo ""
echo "3. Check if there's a route conflict:"
python3 -c "
from app import create_app
app = create_app()
for rule in app.url_map.iter_rules():
    if 'data-analysis/upload' in rule.rule:
        print(f'Route: {rule.rule} -> Endpoint: {rule.endpoint}')
"

CHECK

EOF
