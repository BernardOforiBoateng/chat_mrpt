#\!/bin/bash

echo "=== Deploying TPR to Risk Analysis Transition Fix ==="

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 << 'EOSSH'
cd /home/ec2-user/ChatMRPT
source /home/ec2-user/chatmrpt_env/bin/activate

echo "1. Backing up tpr_handler.py..."
cp app/tpr_module/integration/tpr_handler.py app/tpr_module/integration/tpr_handler.py.backup_transition

echo "2. Updating tpr_handler.py..."
python3 << 'PYTHON'
import re

with open('app/tpr_module/integration/tpr_handler.py', 'r') as f:
    content = f.read()

# Update the transition success block to clear TPR flags
content = re.sub(
    r"if transition_result\['status'\] == 'success':\s*\n\s*logger\.info\(f\"Successfully prepared TPR data for risk analysis - session \{self\.session_id\}\"\)",
    """if transition_result['status'] == 'success':
                    logger.info(f"Successfully prepared TPR data for risk analysis - session {self.session_id}")
                    
                    # CRITICAL: Clear TPR workflow flags after successful transition
                    # This allows the permission system to take over
                    session.pop('tpr_workflow_active', None)
                    session.pop('tpr_session_id', None)
                    session.modified = True
                    logger.info(f"TPR workflow flags cleared for risk transition - session {self.session_id}")""",
    content
)

# Update completion messages to include transition prompt
completion_prompt = "\\n\\n**Next Step:** I've finished the TPR analysis. Would you like to proceed to the risk analysis to rank wards and plan for ITN distribution?"

# Update the detailed completion message
content = re.sub(
    r"(- All four files are ready for download)\n\"\"\"",
    f"\\1\\n\\n---{completion_prompt}\\n\"\"\"",
    content
)

# Update the simple completion message
content = re.sub(
    r"(integration with your existing workflows\.)\n\"\"\"",
    f"\\1{completion_prompt}\\n\"\"\"",
    content
)

# Update the _run_tpr_analysis to not clear flags immediately
content = re.sub(
    r"# Clear TPR session flag\s*\n\s*session\.pop\('tpr_workflow_active', None\)\s*\n\s*session\.pop\('tpr_session_id', None\)\s*\n\s*# CRITICAL: Force session update.*\n\s*session\.modified = True\s*\n\s*logger\.info\(.*?\)",
    """# NOTE: TPR flags will be cleared after successful risk transition
            # For now, just mark as completed but keep flags for transition
            logger.info(f"TPR workflow completed for session {self.session_id} - ready for risk transition")""",
    content,
    flags=re.DOTALL
)

with open('app/tpr_module/integration/tpr_handler.py', 'w') as f:
    f.write(content)

print("✓ Updated tpr_handler.py")
PYTHON

echo ""
echo "3. Restarting service..."
sudo systemctl restart chatmrpt

sleep 3

echo ""
echo "4. Service status:"
sudo systemctl status chatmrpt  < /dev/null |  head -15

echo ""
echo "=== Deployment Complete! ==="
echo "Changes:"
echo "- TPR workflow flags cleared after successful risk transition"
echo "- Added transition prompt in completion messages"
echo "- Permission system can now take over after TPR completes"
EOSSH
