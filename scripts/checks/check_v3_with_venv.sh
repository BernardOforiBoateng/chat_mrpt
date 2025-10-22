#!/bin/bash

echo "=== Checking V3 Registration with Virtual Environment ==="

cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'EOF'

ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'CHECK'
cd /home/ec2-user/ChatMRPT

echo "1. Activating venv and checking V3:"
source chatmrpt_venv_new/bin/activate 2>/dev/null || source venv/bin/activate 2>/dev/null

python3 -c "
from app import create_app
app = create_app()

print('=== Blueprint Registration Check ===')
if 'data_analysis_v3' in app.blueprints:
    print('✅ data_analysis_v3 blueprint IS registered!')
else:
    print('❌ data_analysis_v3 blueprint NOT registered')

print('\nAll registered blueprints:')
for bp_name in app.blueprints:
    print(f'  - {bp_name}')

print('\n=== Route Check ===')
print('Routes handling /api/data-analysis/upload:')
for rule in app.url_map.iter_rules():
    if 'data-analysis/upload' in rule.rule:
        print(f'  {rule.rule} -> {rule.endpoint}')
"

echo ""
echo "2. Check which agent handles the chat after upload:"
grep -n "class.*Agent" app/data_analysis_v3/core/agent.py | head -3

CHECK

EOF
