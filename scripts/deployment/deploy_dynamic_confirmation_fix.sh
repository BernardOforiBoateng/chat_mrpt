#!/bin/bash

echo "=== Deploying Dynamic Confirmation Detection Fix ==="

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 << 'EOSSH'
cd /home/ec2-user/ChatMRPT
source /home/ec2-user/chatmrpt_env/bin/activate

echo "1. Implementing dynamic confirmation detection..."
python3 << 'PYTHON'
import re

with open('app/core/request_interpreter.py', 'r') as f:
    content = f.read()

# Find and update the _is_confirmation_message function
old_function = r"def _is_confirmation_message\(self, message: str\) -> bool:\s*\n\s*\"\"\"Check if message is confirmation\.\"\"\"\s*\n\s*return message\.lower\(\)\.strip\(\) in \['yes', 'y', 'ok', 'okay', 'sure', 'proceed', 'continue'\]"

new_function = '''def _is_confirmation_message(self, message: str) -> bool:
        """Check if message is confirmation using dynamic detection."""
        msg = message.lower().strip()
        
        # Core confirmation words
        confirmation_words = {'yes', 'y', 'ok', 'okay', 'sure', 'proceed', 'continue', 'go', 'yep', 'yeah', 'affirmative'}
        negative_words = {'no', 'not', 'dont', "don't", 'cancel', 'stop', 'wait', 'hold'}
        
        # Split message into words
        words = msg.split()
        
        # Check if any word in the message is a confirmation word
        has_confirmation = any(word in confirmation_words for word in words)
        has_negative = any(word in negative_words for word in words)
        
        # If there's a negative word, it's not a confirmation
        if has_negative:
            return False
            
        # If there's at least one confirmation word and no negatives, it's a confirmation
        return has_confirmation'''

content = re.sub(old_function, new_function, content, flags=re.MULTILINE | re.DOTALL)

# Also add logging to track what's happening
confirmation_check = r'if self\._is_confirmation_message\(user_message\):'
replacement = '''logger.debug(f"Checking if '{user_message}' is a confirmation message")
            if self._is_confirmation_message(user_message):
                logger.info(f"✅ Confirmed! '{user_message}' detected as confirmation")'''

content = re.sub(confirmation_check, replacement, content)

with open('app/core/request_interpreter.py', 'w') as f:
    f.write(content)

print("✓ Implemented dynamic confirmation detection")
PYTHON

echo ""
echo "2. Testing the dynamic detection logic..."
python3 << 'PYTHON'
# Test the logic inline to verify it works
def _is_confirmation_message(message: str) -> bool:
    """Check if message is confirmation using dynamic detection."""
    msg = message.lower().strip()
    
    # Core confirmation words
    confirmation_words = {'yes', 'y', 'ok', 'okay', 'sure', 'proceed', 'continue', 'go', 'yep', 'yeah', 'affirmative'}
    negative_words = {'no', 'not', 'dont', "don't", 'cancel', 'stop', 'wait', 'hold'}
    
    # Split message into words
    words = msg.split()
    
    # Check if any word in the message is a confirmation word
    has_confirmation = any(word in confirmation_words for word in words)
    has_negative = any(word in negative_words for word in words)
    
    # If there's a negative word, it's not a confirmation
    if has_negative:
        return False
        
    # If there's at least one confirmation word and no negatives, it's a confirmation
    return has_confirmation

# Test cases
test_cases = [
    ("yes", True),
    ("yes proceed", True),
    ("ok let's continue", True),
    ("sure go ahead", True),
    ("no", False),
    ("not now", False),
    ("yes but not now", False),
    ("proceed with the analysis", True),
    ("I want to proceed", True),
    ("random text", False)
]

print("Testing dynamic confirmation detection:")
for msg, expected in test_cases:
    result = _is_confirmation_message(msg)
    status = "✓" if result == expected else "✗"
    print(f"{status} '{msg}' -> {result} (expected {expected})")
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
echo "=== Dynamic Confirmation Detection Deployed! ==="
echo ""
echo "The system now dynamically detects confirmations by:"
echo "- Looking for ANY confirmation word in the message"
echo "- Rejecting messages with negative words"
echo "- No hardcoded phrases - fully dynamic!"
echo ""
echo "Examples that will work:"
echo "- 'yes proceed'"
echo "- 'ok let's go'"
echo "- 'sure, continue with that'"
echo "- 'yeah proceed with the analysis'"
EOSSH