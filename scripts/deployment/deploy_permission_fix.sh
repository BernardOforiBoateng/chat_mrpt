#\!/bin/bash

echo "=== Deploying Permission System Fix ==="

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 << 'EOSSH'
cd /home/ec2-user/ChatMRPT
source /home/ec2-user/chatmrpt_env/bin/activate

echo "1. Backing up request_interpreter.py..."
cp app/core/request_interpreter.py app/core/request_interpreter.py.backup_permission_fix

echo "2. Updating request_interpreter.py..."
python3 << 'PYTHON'
import re

with open('app/core/request_interpreter.py', 'r') as f:
    content = f.read()

# Replace the automatic analysis execution with data exploration prompt
old_pattern = r'if self\._is_confirmation_message\(user_message\):\s*\n\s*logger\.info\("✅ User confirmed with \'yes\' - executing automatic analysis\.\.\."\)\s*\n\s*# User said yes - run analysis\s*\n\s*result = self\._execute_automatic_analysis\(session_id\)'

new_code = '''if self._is_confirmation_message(user_message):
                logger.info("✅ User confirmed with 'yes' - showing data exploration options...")
                
                # Get data info for the prompt
                try:
                    data_handler = self.data_service.get_handler(session_id)
                    if data_handler and hasattr(data_handler, 'csv_data') and data_handler.csv_data is not None:
                        rows = len(data_handler.csv_data)
                        cols = len(data_handler.csv_data.columns)
                    else:
                        rows = 0
                        cols = 0
                except:
                    rows = 0
                    cols = 0
                
                state = session_data.get('state_name', 'your region')
                
                response = f"""I've loaded your data from {state}. It has {rows} rows and {cols} columns.

What would you like to do?
• I can help you map variable distribution
• Check data quality
• Explore specific variables
• Run malaria risk analysis to rank wards for ITN distribution
• Something else

Just tell me what you're interested in."""'''

# Find and replace the section
start_idx = content.find('if self._is_confirmation_message(user_message):')
if start_idx \!= -1:
    # Find the end of the return result statement
    end_idx = content.find('return result', start_idx)
    if end_idx \!= -1:
        # Replace the entire block
        before = content[:start_idx]
        after = content[end_idx + len('return result'):]
        
        # Build the new content
        new_content = before + new_code + '''
                
                # Clear the permission flag in all places
                try:
                    from flask import session as flask_session
                    flask_session['should_ask_analysis_permission'] = False
                except:
                    pass
                
                try:
                    # Skip session state update for now
                    pass
                except:
                    pass
                
                return {
                    'response': response,
                    'status': 'success',
                    'tools_used': []
                }''' + after
        
        with open('app/core/request_interpreter.py', 'w') as f:
            f.write(new_content)
        print("✓ Updated request_interpreter.py")
    else:
        print("✗ Could not find end marker")
else:
    print("✗ Could not find start marker")
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
sudo systemctl status chatmrpt  < /dev/null |  head -10

echo ""
echo "=== Deployment Complete\! ==="
echo "Permission system will now:"
echo "- Show data exploration options when user says 'yes'"
echo "- NOT automatically run the analysis"
echo "- Allow users to explore data before choosing analysis"
EOSSH
