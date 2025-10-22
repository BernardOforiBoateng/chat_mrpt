#!/bin/bash

echo "🔍 Verifying Workflow Fix v2 Deployment on Staging"
echo "=================================================="
echo ""

# Check the first staging instance
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@3.21.167.170 << 'EOF'
echo "📋 Checking key code changes:"
echo ""

echo "1. Backend - data_analysis_v3_routes.py:"
grep -n "exit_data_analysis_mode" /home/ec2-user/ChatMRPT/app/web/routes/data_analysis_v3_routes.py | head -5

echo ""
echo "2. Frontend - api-client.js:"
grep -n "data_analysis_exited" /home/ec2-user/ChatMRPT/app/static/js/modules/utils/api-client.js | head -5

echo ""
echo "3. State Manager - get_state method:"
grep -n "def get_state" /home/ec2-user/ChatMRPT/app/data_analysis_v3/core/state_manager.py

echo ""
echo "📊 Recent Data Analysis V3 exits (last hour):"
sudo journalctl -u chatmrpt --since "1 hour ago" | grep -E "(exit_data_analysis_mode|workflow_transitioned)" | tail -5

echo ""
echo "✅ Service Status:"
sudo systemctl is-active chatmrpt
EOF

echo ""
echo "✅ Verification complete!"