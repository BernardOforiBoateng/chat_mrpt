#!/bin/bash

echo "=== Deploying Permission Debug Fix ==="

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 << 'EOSSH'
cd /home/ec2-user/ChatMRPT
source /home/ec2-user/chatmrpt_env/bin/activate

echo "1. Backing up request_interpreter.py..."
cp app/core/request_interpreter.py app/core/request_interpreter.py.backup_permission_debug

echo "2. Adding extensive debugging to permission workflow..."
python3 << 'PYTHON'
with open('app/core/request_interpreter.py', 'r') as f:
    content = f.read()

# Find and update the permission workflow section
import re

# Add debug logging to process_message_streaming
old_streaming = r'special_result = self\._handle_special_workflows\(user_message, session_id, session_data\)\s*\n\s*if special_result:'
new_streaming = '''special_result = self._handle_special_workflows(user_message, session_id, session_data)
        logger.info(f"DEBUG: special_result = {special_result}")
        if special_result:'''

content = re.sub(old_streaming, new_streaming, content)

# Add debug logging to the permission response section
old_permission = r'if self\._is_confirmation_message\(user_message\):\s*\n\s*logger\.info\("✅ User confirmed with \'yes\' - showing data exploration options\.\.\."'
new_permission = '''if self._is_confirmation_message(user_message):
                logger.info("✅ User confirmed with 'yes' - showing data exploration options...")
                logger.info(f"DEBUG: user_message='{user_message}', is_confirmation={self._is_confirmation_message(user_message)}")'''

content = re.sub(old_permission, new_permission, content)

# Add debug logging before return
old_return = r'return \{\s*\'response\': response,\s*\'status\': \'success\',\s*\'tools_used\': \[\]\s*\}'
new_return = '''logger.info(f"DEBUG: Returning permission response, length={len(response)}")
                return {
                    'response': response,
                    'status': 'success',
                    'tools_used': []
                }'''

content = re.sub(old_return, new_return, content, flags=re.MULTILINE | re.DOTALL)

# Write the updated file
with open('app/core/request_interpreter.py', 'w') as f:
    f.write(content)

print("✓ Added debugging to request_interpreter.py")
PYTHON

echo ""
echo "3. Checking syntax..."
python3 -m py_compile app/core/request_interpreter.py && echo "✓ Syntax OK"

echo ""
echo "4. Restarting service..."
sudo systemctl restart chatmrpt

sleep 3

echo ""
echo "5. Service status:"
sudo systemctl status chatmrpt < /dev/null | head -10

echo ""
echo "6. Tailing logs for debugging..."
echo "Waiting for service to stabilize..."
sleep 2
echo ""
echo "Recent permission-related logs:"
sudo journalctl -u chatmrpt --since '30 seconds ago' | grep -E '(DEBUG:|Permission|special_result)' | tail -20

echo ""
echo "=== Deployment Complete! ==="
echo ""
echo "Debug logging added to track:"
echo "- special_result value from _handle_special_workflows"
echo "- Confirmation message detection"
echo "- Permission response return"
echo ""
echo "Please test again and check the logs for DEBUG messages"
EOSSH