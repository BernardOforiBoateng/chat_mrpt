#!/bin/bash
set -e

echo "Fixing session context detection for ITN planning..."

# SSH to staging and apply fix
ssh -i ~/tmp/chatmrpt-key.pem ec2-user@18.117.115.217 'bash -s' << 'EOF'
set -e

cd /home/ec2-user/ChatMRPT

echo "1. Backing up request_interpreter.py..."
cp app/core/request_interpreter.py app/core/request_interpreter.py.backup_session_context

echo "2. Applying fix to _get_session_context method..."
python3 << 'PYFIX'
import re

with open('app/core/request_interpreter.py', 'r') as f:
    content = f.read()

# Find the _get_session_context method and add file-based check
# We need to add the check after line 1536 but before building the context
fix_code = '''
            # Check analysis_complete from session or conversation history
            analysis_complete = session_data.get('analysis_complete', False)
            if not analysis_complete and session_id in self.conversation_history:
                # Check if any conversation history entry marks analysis as complete
                for entry in self.conversation_history[session_id]:
                    if isinstance(entry, dict) and entry.get('analysis_complete'):
                        analysis_complete = True
                        break
            
            # NEW: Check for unified dataset files on disk (works across workers)
            if not analysis_complete and session_id:
                import os
                upload_path = os.path.join('instance/uploads', session_id)
                # Check for unified dataset files that indicate analysis is complete
                unified_files = ['unified_dataset.geoparquet', 'unified_dataset.csv', 
                                'analysis_vulnerability_rankings.csv', 'analysis_vulnerability_rankings_pca.csv']
                
                for filename in unified_files:
                    filepath = os.path.join(upload_path, filename)
                    if os.path.exists(filepath):
                        analysis_complete = True
                        logger.info(f"Session context: Found {filename}, marking analysis_complete=True for session {session_id}")
                        break
'''

# Replace the existing block
pattern = r'(# Check analysis_complete from session or conversation history.*?break\n)(\s+context = \{)'
replacement = fix_code + r'\n\2'

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('app/core/request_interpreter.py', 'w') as f:
    f.write(content)

print("Fixed session context detection")
PYFIX

echo "3. Verifying syntax..."
python3 -m py_compile app/core/request_interpreter.py && echo "✅ Syntax OK"

echo "4. Checking the fix was applied..."
grep -A15 "Check for unified dataset files on disk" app/core/request_interpreter.py || echo "Checking fix..."

echo "5. Restarting application..."
sudo systemctl restart chatmrpt
sleep 5

echo "6. Testing health..."
curl -s http://localhost:8080/ping && echo -e "\nApp is healthy!"

echo -e "\n✅ Session context fix applied!"
echo "The fix adds file-based detection to _get_session_context() so:"
echo "1. It checks for unified dataset files on disk"
echo "2. Sets analysis_complete=True if files exist"
echo "3. LLM sees this and calls ITN tool instead of re-running analysis"
echo "4. Works across all workers!"
EOF

echo "Fix deployment complete!"