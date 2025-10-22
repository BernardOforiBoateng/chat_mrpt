#!/bin/bash

echo "🔍 Checking AWS staging logs for workflow transition issues..."
echo ""

# SSH into staging instance and check logs
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@3.21.167.170 << 'EOF'
echo "📋 Recent workflow transition logs:"
echo "=================================="

# Check for workflow_transitioned flag
sudo journalctl -u chatmrpt --since "1 hour ago" | grep -E "(workflow_transitioned|exit_data_analysis_mode|Data Analysis V3|TPR.*transition|active_tab)" | tail -50

echo ""
echo "📊 Checking session state files:"
echo "=================================="

# Find recent session folders
for session_dir in $(ls -td /home/ec2-user/ChatMRPT/instance/uploads/*/ 2>/dev/null | head -5); do
    session_id=$(basename $session_dir)
    state_file="$session_dir/.state.json"
    if [ -f "$state_file" ]; then
        echo "Session: $session_id"
        echo "State content:"
        cat "$state_file" | python3 -m json.tool | grep -E "(workflow_transitioned|tpr_completed|workflow_stage)" || echo "No relevant flags"
        echo "---"
    fi
done

echo ""
echo "🔍 Recent Data Analysis route hits:"
echo "===================================="
sudo journalctl -u chatmrpt --since "30 minutes ago" | grep -E "(/api/v1/data-analysis/chat|Data Analysis V3 chat request)" | tail -20

EOF