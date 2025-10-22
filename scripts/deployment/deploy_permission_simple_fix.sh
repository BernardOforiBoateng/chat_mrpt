#!/bin/bash

echo "=== Deploying Simple Permission Fix ==="

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 << 'EOSSH'
cd /home/ec2-user/ChatMRPT
source /home/ec2-user/chatmrpt_env/bin/activate

echo "1. Checking for valid backup..."
if [ -f "app/core/request_interpreter.py.backup_permission_debug" ]; then
    echo "✓ Found backup file"
    cp app/core/request_interpreter.py.backup_permission_debug app/core/request_interpreter.py
    echo "✓ Restored from backup"
else
    echo "✗ No backup found, proceeding with current file"
fi

echo ""
echo "2. Making a simple, targeted fix..."
python3 << 'PYTHON'
# Read the file
with open('app/core/request_interpreter.py', 'r') as f:
    lines = f.readlines()

# Find the line that returns None after permission check fails
for i, line in enumerate(lines):
    if "# Continue with normal message processing" in line and i+1 < len(lines) and "return None" in lines[i+1]:
        # This is where we need to ensure the permission response is returned
        # Let's check a few lines back to see if we're in the right place
        if i > 10:
            # Look for the permission response construction
            found_response = False
            for j in range(i-20, i):
                if "I've loaded your data from" in lines[j]:
                    found_response = True
                    break
            
            if found_response:
                print(f"Found the permission block at line {i}")
                # The issue might be that we're not in the right scope
                # Let's trace back to ensure proper indentation

# Simple approach: Add a debug flag to trace execution
# Insert debug logging at key points
insertions = []

for i, line in enumerate(lines):
    # Add debug at start of _handle_special_workflows
    if "def _handle_special_workflows" in line and "user_message: str" in line:
        insertions.append((i+3, "        logger.debug('PERMISSION_DEBUG: Entering _handle_special_workflows')\n"))
    
    # Add debug when permission flag is found
    if "Permission flag found!" in line:
        insertions.append((i+1, "            logger.debug('PERMISSION_DEBUG: About to check confirmation message')\n"))
    
    # Add debug when returning permission response
    if "'response': response," in line and "'tools_used': []" in lines[i+2] and "}" in lines[i+3]:
        # This looks like the permission response return
        insertions.append((i, "                logger.info('PERMISSION_DEBUG: Returning permission exploration response!')\n"))

# Apply insertions in reverse order to maintain line numbers
for line_num, content in reversed(insertions):
    lines.insert(line_num, content)

# Write the file back
with open('app/core/request_interpreter.py', 'w') as f:
    f.writelines(lines)

print(f"✓ Added {len(insertions)} debug statements")
PYTHON

echo ""
echo "3. Checking syntax..."
python3 -m py_compile app/core/request_interpreter.py
if [ $? -eq 0 ]; then
    echo "✓ Syntax OK"
else
    echo "✗ Syntax error detected"
    echo "Showing the error:"
    python3 -m py_compile app/core/request_interpreter.py 2>&1
fi

echo ""
echo "4. Restarting service..."
sudo systemctl restart chatmrpt

sleep 3

echo ""
echo "5. Service status:"
sudo systemctl status chatmrpt < /dev/null | head -10

echo ""
echo "=== Testing the Debug Flow ==="
echo "To test:"
echo "1. Complete a TPR analysis"
echo "2. When prompted, say 'yes proceed'"
echo "3. Watch for PERMISSION_DEBUG messages in logs"
echo ""
echo "Monitor with: sudo journalctl -u chatmrpt -f | grep PERMISSION_DEBUG"
EOSSH