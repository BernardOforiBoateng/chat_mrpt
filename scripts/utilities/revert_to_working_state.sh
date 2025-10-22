#!/bin/bash
set -e

echo "Reverting to working state (before session state manager changes)..."

# SSH to staging and revert changes
ssh -i ~/tmp/chatmrpt-key.pem ec2-user@18.117.115.217 'bash -s' << 'EOF'
set -e

cd /home/ec2-user/ChatMRPT

echo "1. Checking for backup files..."
ls -la app/core/*.backup* app/tools/*.backup* | head -20

echo -e "\n2. Reverting complete_analysis_tools.py..."
if [ -f "app/tools/complete_analysis_tools.py.backup_state_fix" ]; then
    cp app/tools/complete_analysis_tools.py.backup_state_fix app/tools/complete_analysis_tools.py
    echo "✅ Reverted complete_analysis_tools.py"
else
    echo "⚠️  No backup found for complete_analysis_tools.py"
fi

echo -e "\n3. Reverting itn_planning_tools.py..."
if [ -f "app/tools/itn_planning_tools.py.backup_state_fix" ]; then
    cp app/tools/itn_planning_tools.py.backup_state_fix app/tools/itn_planning_tools.py
    echo "✅ Reverted itn_planning_tools.py"
elif [ -f "app/tools/itn_planning_tools.py.backup" ]; then
    # Use the backup from the simple ITN fix
    cp app/tools/itn_planning_tools.py.backup app/tools/itn_planning_tools.py
    echo "✅ Reverted itn_planning_tools.py (from simple fix backup)"
else
    echo "⚠️  No backup found for itn_planning_tools.py"
fi

echo -e "\n4. Reverting unified_data_state.py..."
if [ -f "app/core/unified_data_state.py.backup_state_fix" ]; then
    cp app/core/unified_data_state.py.backup_state_fix app/core/unified_data_state.py
    echo "✅ Reverted unified_data_state.py"
else
    echo "⚠️  No backup found for unified_data_state.py"
fi

echo -e "\n5. Removing session_state_manager.py..."
if [ -f "app/core/session_state_manager.py" ]; then
    rm -f app/core/session_state_manager.py
    echo "✅ Removed session_state_manager.py"
fi

echo -e "\n6. Verifying syntax of reverted files..."
python3 -m py_compile app/tools/complete_analysis_tools.py && echo "✅ complete_analysis_tools.py syntax OK" || echo "❌ Syntax error in complete_analysis_tools.py"
python3 -m py_compile app/tools/itn_planning_tools.py && echo "✅ itn_planning_tools.py syntax OK" || echo "❌ Syntax error in itn_planning_tools.py"
python3 -m py_compile app/core/unified_data_state.py && echo "✅ unified_data_state.py syntax OK" || echo "❌ Syntax error in unified_data_state.py"

echo -e "\n7. Restarting application..."
sudo systemctl restart chatmrpt
sleep 5

echo -e "\n8. Testing health..."
curl -s http://localhost:8080/ping && echo -e "\nApp is healthy!"

echo -e "\n9. Checking recent logs for errors..."
sudo journalctl -u chatmrpt -n 20 | grep -E "(ERROR|error|Error)" || echo "No errors in recent logs"

echo -e "\n✅ Revert complete!"
echo "The system has been restored to the state before the session state manager changes."
echo "- Risk analysis and visualization tools should work again"
echo "- ITN planning will still have the issue detecting completed analysis"
echo "- But at least the core functionality is restored"
EOF

echo -e "\nRevert deployment complete!"