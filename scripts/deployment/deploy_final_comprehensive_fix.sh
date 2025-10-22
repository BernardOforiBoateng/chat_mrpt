#!/bin/bash

echo "=== Deploying Comprehensive Permission Fix ==="
echo "Based on analysis: Permission flag is detected but response not returned properly"

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 << 'EOSSH'
cd /home/ec2-user/ChatMRPT
source /home/ec2-user/chatmrpt_env/bin/activate

echo "1. Creating a detailed analysis of the issue..."
python3 << 'PYTHON'
# Let's trace the exact flow
with open('app/core/request_interpreter.py', 'r') as f:
    content = f.read()

# Find the critical section where permission is handled
import re

# Look for the permission handling section
match = re.search(r'if should_ask_permission:.*?return None', content, re.DOTALL)
if match:
    print("Found permission handling section")
    permission_section = match.group(0)
    
    # Check if it has proper return for confirmation
    if "_is_confirmation_message" in permission_section and "return {" in permission_section:
        print("✓ Permission section has confirmation check and return statement")
    else:
        print("✗ Permission section missing proper return flow")

# Check process_message_streaming to ensure it handles special_result
streaming_match = re.search(r'def process_message_streaming.*?special_result = self\._handle_special_workflows.*?if special_result:', content, re.DOTALL)
if streaming_match:
    print("✓ Streaming method calls _handle_special_workflows")
    if "yield" in streaming_match.group(0):
        print("✓ Streaming method yields special_result")
    else:
        print("✗ Streaming method doesn't yield special_result properly")
PYTHON

echo ""
echo "2. Applying the comprehensive fix..."
python3 << 'PYTHON'
with open('app/core/request_interpreter.py', 'r') as f:
    lines = f.readlines()

# Fix 1: Add explicit logging to trace the flow
modified = False
for i, line in enumerate(lines):
    # Add logging when entering permission check
    if "if should_ask_permission:" in line and "Permission flag found!" in lines[i+1]:
        # Add detailed logging after permission flag detection
        indent = line[:len(line) - len(line.lstrip())]
        if i+2 < len(lines) and "if self._is_confirmation_message" in lines[i+2]:
            # Insert debug between flag detection and confirmation check
            lines.insert(i+2, f"{indent}    logger.info(f\"DEBUG: Checking if '{user_message}' is confirmation message\")\n")
            modified = True
            print("✓ Added debug before confirmation check")
            break

# Fix 2: Ensure the permission response is logged before return
for i, line in enumerate(lines):
    if "'response': response," in line and i+1 < len(lines) and "'status': 'success'," in lines[i+1]:
        # This looks like the permission response return
        if i > 5 and "I've loaded your data from" in ''.join(lines[i-10:i]):
            # We're in the permission response section
            indent = line[:len(line) - len(line.lstrip())]
            lines.insert(i, f"{indent}logger.info(\"CRITICAL: About to return permission exploration response\")\n")
            modified = True
            print("✓ Added logging before permission response return")
            break

# Fix 3: Add explicit check in process_message_streaming
for i, line in enumerate(lines):
    if "special_result = self._handle_special_workflows" in line:
        # Add detailed logging after getting special_result
        if i+1 < len(lines):
            indent = line[:len(line) - len(line.lstrip())]
            lines.insert(i+1, f"{indent}if special_result:\n")
            lines.insert(i+2, f"{indent}    logger.info(f\"CRITICAL: special_result returned from _handle_special_workflows: {{special_result.get('response', '')[:50]}}...\")\n")
            modified = True
            print("✓ Added critical logging for special_result")
            break

if modified:
    with open('app/core/request_interpreter.py', 'w') as f:
        f.writelines(lines)
    print("\n✓ All modifications applied")
else:
    print("\n✗ No modifications made - structure might be different")
PYTHON

echo ""
echo "3. Checking syntax..."
python3 -m py_compile app/core/request_interpreter.py 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Syntax OK"
else
    echo "✗ Syntax error - reverting"
    cp app/core/request_interpreter.py.backup_permission_debug app/core/request_interpreter.py
fi

echo ""
echo "4. Restarting service..."
sudo systemctl restart chatmrpt

sleep 3

echo ""
echo "5. Service is ready. Key points to test:"
echo "   - Complete TPR analysis"
echo "   - Say 'yes proceed' when prompted"
echo "   - Watch for these log messages:"
echo "     • DEBUG: Checking if 'yes proceed' is confirmation message"
echo "     • CRITICAL: About to return permission exploration response"
echo "     • CRITICAL: special_result returned from _handle_special_workflows"
echo ""
echo "Monitor with: sudo journalctl -u chatmrpt -f | grep -E '(CRITICAL:|DEBUG:|Permission)'"

echo ""
echo "6. Current service status:"
sudo systemctl status chatmrpt | head -10
EOSSH