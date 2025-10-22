#!/bin/bash

echo "=== Deploying Permission Debug Fix v2 ==="

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 << 'EOSSH'
cd /home/ec2-user/ChatMRPT
source /home/ec2-user/chatmrpt_env/bin/activate

echo "1. Restoring from backup..."
cp app/core/request_interpreter.py.backup_permission_fix app/core/request_interpreter.py

echo "2. Adding targeted debugging..."
python3 << 'PYTHON'
with open('app/core/request_interpreter.py', 'r') as f:
    lines = f.readlines()

# Find the line with special_result assignment
for i, line in enumerate(lines):
    if 'special_result = self._handle_special_workflows' in line and 'try:' in lines[i-1]:
        # Insert debug logging after the assignment
        indent = ' ' * 12  # Match indentation
        lines.insert(i+1, f'{indent}logger.debug(f"DEBUG: special_result from _handle_special_workflows = {{special_result}}")\n')
        break

# Find the permission response section and add debug
for i, line in enumerate(lines):
    if 'DEBUG: Returning permission response' in line:
        # Already has debug logging
        break
    elif "return {" in line and "'response': response," in lines[i+1] and "'tools_used': []" in lines[i+3]:
        # Found the permission return, add debug before it
        indent = ' ' * 16
        lines.insert(i, f'{indent}logger.info(f"DEBUG: Returning permission response with {{len(response)}} chars")\n')
        break

# Write the updated file
with open('app/core/request_interpreter.py', 'w') as f:
    f.writelines(lines)

print("✓ Added debugging to request_interpreter.py")
PYTHON

echo ""
echo "3. Verifying the permission logic is intact..."
python3 << 'PYTHON'
with open('app/core/request_interpreter.py', 'r') as f:
    content = f.read()

# Check if permission logic exists
if 'should_ask_analysis_permission' in content and '_is_confirmation_message' in content:
    print("✓ Permission logic found")
    
    # Count occurrences
    permission_count = content.count('should_ask_analysis_permission')
    confirmation_count = content.count('_is_confirmation_message')
    print(f"  - Found {permission_count} references to should_ask_analysis_permission")
    print(f"  - Found {confirmation_count} references to _is_confirmation_message")
else:
    print("✗ Permission logic missing!")
PYTHON

echo ""
echo "4. Checking syntax..."
python3 -m py_compile app/core/request_interpreter.py && echo "✓ Syntax OK" || echo "✗ Syntax error"

echo ""
echo "5. Restarting service..."
sudo systemctl restart chatmrpt

sleep 3

echo ""
echo "6. Service status:"
sudo systemctl status chatmrpt < /dev/null | head -10

echo ""
echo "=== Deployment Complete! ==="
echo ""
echo "Test the flow again and look for DEBUG messages in the logs"
echo "Use: sudo journalctl -u chatmrpt -f | grep -E '(DEBUG:|permission|special_result)'"
EOSSH