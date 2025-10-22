#!/bin/bash

echo "=== Deploying Final Permission Fix ==="

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 << 'EOSSH'
cd /home/ec2-user/ChatMRPT
source /home/ec2-user/chatmrpt_env/bin/activate

echo "1. Creating a precise fix for the permission workflow..."
python3 << 'PYTHON'
import re

with open('app/core/request_interpreter.py', 'r') as f:
    content = f.read()

# Add logging to trace the permission workflow
# First, find where we check for permission flag and add debug logging
permission_check = r'if should_ask_permission:\s*\n\s*logger\.info\(f"🎯 Permission flag found! User message: \'{user_message}\'"'
replacement = '''if should_ask_permission:
            logger.info(f"🎯 Permission flag found! User message: '{user_message}'")
            logger.info(f"DEBUG: About to check if confirmation message")'''

content = re.sub(permission_check, replacement, content)

# Add debug logging after _is_confirmation_message check
confirmation_check = r'if self\._is_confirmation_message\(user_message\):\s*\n\s*logger\.info\("✅ User confirmed with \'yes\' - showing data exploration options\.\.\."'
replacement2 = '''if self._is_confirmation_message(user_message):
                logger.info("✅ User confirmed with 'yes' - showing data exploration options...")
                logger.info(f"DEBUG: Inside confirmation block, about to generate response")'''

content = re.sub(confirmation_check, replacement2, content)

# Most importantly, ensure we LOG and RETURN the response
# Find the return statement in the permission block
return_pattern = r'return \{\s*\'response\': response,\s*\'status\': \'success\',\s*\'tools_used\': \[\]\s*\}'
return_replacement = '''logger.info(f"DEBUG: RETURNING permission response (length={len(response)})")
                logger.info(f"DEBUG: Response preview: {response[:100]}...")
                return {
                    'response': response,
                    'status': 'success',
                    'tools_used': []
                }'''

content = re.sub(return_pattern, return_replacement, content, flags=re.MULTILINE | re.DOTALL)

# Add logging at the start of process_message_streaming to trace flow
streaming_start = r'def process_message_streaming\(self, user_message: str, session_id: str, session_data: Dict\[str, Any\] = None\):\s*\n\s*"""Streaming version for better UX\."""'
streaming_replacement = '''def process_message_streaming(self, user_message: str, session_id: str, session_data: Dict[str, Any] = None):
        """Streaming version for better UX."""
        logger.info(f"DEBUG: process_message_streaming called with message: '{user_message[:50]}...'")'''

content = re.sub(streaming_start, streaming_replacement, content)

# Add logging after special_result check
special_check = r'special_result = self\._handle_special_workflows\(user_message, session_id, session_data\)\s*\n\s*if special_result:'
special_replacement = '''special_result = self._handle_special_workflows(user_message, session_id, session_data)
            logger.info(f"DEBUG: special_result from _handle_special_workflows: {special_result is not None}")
            if special_result:
                logger.info(f"DEBUG: Yielding special_result response: {special_result.get('response', '')[:100]}...")'''

content = re.sub(special_check, special_replacement, content)

with open('app/core/request_interpreter.py', 'w') as f:
    f.write(content)

print("✓ Added comprehensive debugging to permission workflow")
PYTHON

echo ""
echo "2. Verifying the changes..."
python3 << 'PYTHON'
with open('app/core/request_interpreter.py', 'r') as f:
    content = f.read()

debug_count = content.count('DEBUG:')
print(f"✓ Added {debug_count} debug statements")

# Check key components are present
checks = [
    ('Permission detection', '🎯 Permission flag found!'),
    ('Confirmation check', '✅ User confirmed with'),
    ('Response return', 'RETURNING permission response'),
    ('Special workflow', 'special_result from _handle_special_workflows')
]

for name, pattern in checks:
    if pattern in content:
        print(f"✓ {name}: Found")
    else:
        print(f"✗ {name}: Missing!")
PYTHON

echo ""
echo "3. Checking syntax..."
python3 -m py_compile app/core/request_interpreter.py && echo "✓ Syntax OK" || echo "✗ Syntax error"

echo ""
echo "4. Restarting service..."
sudo systemctl restart chatmrpt

sleep 3

echo ""
echo "5. Service status:"
sudo systemctl status chatmrpt < /dev/null | head -10

echo ""
echo "=== Deployment Complete! ==="
echo ""
echo "Enhanced debugging will show:"
echo "1. When permission flag is detected"
echo "2. When confirmation message is recognized"
echo "3. When permission response is returned"
echo "4. Whether special_result is properly passed back"
echo ""
echo "Monitor logs with: sudo journalctl -u chatmrpt -f | grep -E 'DEBUG:|Permission|special_result'"
EOSSH