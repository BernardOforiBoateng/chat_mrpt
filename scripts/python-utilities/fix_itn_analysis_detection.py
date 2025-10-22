#!/usr/bin/env python3
"""
Fix ITN planning tool's analysis detection in multi-worker environment.

The issue: ITN planning tool can't detect completed analysis because:
1. Flask session['analysis_complete'] isn't available across workers
2. The file-based detection isn't working properly
"""

import os
import sys

def main():
    print("ITN Analysis Detection Fix")
    print("=" * 50)
    
    # Create the fix script
    fix_script = '''#!/bin/bash
set -e

echo "Applying ITN analysis detection fix..."

# SSH to staging and apply fix
ssh -i ~/tmp/chatmrpt-key.pem ec2-user@18.117.115.217 'bash -s' << 'EOF'
set -e

echo "1. Backing up itn_planning_tools.py..."
cp /home/ec2-user/ChatMRPT/app/tools/itn_planning_tools.py /home/ec2-user/ChatMRPT/app/tools/itn_planning_tools.py.backup

echo "2. Fixing the _check_analysis_complete method..."

# Create a Python script to fix the issue
cat > /tmp/fix_itn_detection.py << 'PYFIX'
import re

# Read the file
with open('/home/ec2-user/ChatMRPT/app/tools/itn_planning_tools.py', 'r') as f:
    content = f.read()

# Find the _check_analysis_complete method and make it more robust
# We'll modify the path construction in Method 3 to use absolute path
old_pattern = r'session_folder = Path\\("instance/uploads"\\) / session_id'
new_pattern = 'session_folder = Path("/home/ec2-user/ChatMRPT/instance/uploads") / session_id'

content = re.sub(old_pattern, new_pattern, content)

# Also add logging to help debug
old_check = r'if session_folder\\.exists\\(\\):'
new_check = 'if session_folder.exists():\\n                    logger.info(f"✅ Session folder exists: {session_folder}")'

content = re.sub(old_check, new_check, content)

# Write back
with open('/home/ec2-user/ChatMRPT/app/tools/itn_planning_tools.py', 'w') as f:
    f.write(content)

print("Fixed ITN analysis detection")
PYFIX

python3 /tmp/fix_itn_detection.py

echo "3. Adding additional fix to ensure unified data state is checked properly..."

# Add a more direct check at the beginning of _check_analysis_complete
python3 << 'PYFIX2'
import re

with open('/home/ec2-user/ChatMRPT/app/tools/itn_planning_tools.py', 'r') as f:
    content = f.read()

# Find the beginning of _check_analysis_complete method
method_pattern = r'(def _check_analysis_complete\\(self, data_handler: DataHandler\\) -> bool:\\s*\\n\\s*"""Check if analysis has been completed"""\\s*\\n\\s*logger\\.info\\("🔍 Checking if analysis is complete\\.\\.\\."\\))'

# Add a direct file check at the very beginning
new_method_start = '''\\1
        
        # CRITICAL FIX: Direct file check first (most reliable for multi-worker)
        try:
            session_id = getattr(data_handler, 'session_id', None)
            if session_id:
                import os
                unified_file = f"/home/ec2-user/ChatMRPT/instance/uploads/{session_id}/unified_dataset.geoparquet"
                if os.path.exists(unified_file):
                    logger.info(f"✅ DIRECT CHECK: Found unified dataset at {unified_file}")
                    return True
        except Exception as e:
            logger.debug(f"Direct file check error: {e}")'''

content = re.sub(method_pattern, new_method_start, content)

with open('/home/ec2-user/ChatMRPT/app/tools/itn_planning_tools.py', 'w') as f:
    f.write(content)

print("Added direct file check")
PYFIX2

echo "4. Verifying the changes..."
grep -A5 "CRITICAL FIX: Direct file check" /home/ec2-user/ChatMRPT/app/tools/itn_planning_tools.py || echo "Direct check not found"
grep "Path(\"/home/ec2-user/ChatMRPT" /home/ec2-user/ChatMRPT/app/tools/itn_planning_tools.py || echo "Absolute path not found"

echo "5. Restarting application..."
sudo systemctl restart chatmrpt
sleep 5

echo "6. Testing health..."
curl -s http://localhost:8080/ping && echo -e "\\nApp is healthy!"

echo -e "\\n✅ ITN analysis detection fix applied!"
echo "The fix ensures ITN planning tool can detect completed analysis by:"
echo "1. Using absolute paths for file checks"
echo "2. Adding direct unified dataset file check at the beginning"
echo "3. Improving logging for debugging"

# Cleanup
rm -f /tmp/fix_itn_detection.py
EOF

echo "Fix deployment complete!"
'''
    
    # Write the deployment script
    with open('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/deploy_itn_fix.sh', 'w') as f:
        f.write(fix_script)
    
    print("\nDeployment script created: deploy_itn_fix.sh")
    print("\nTo apply the fix:")
    print("1. chmod +x deploy_itn_fix.sh")
    print("2. ./deploy_itn_fix.sh")
    print("\nThis fix will:")
    print("- Use absolute paths for file detection")
    print("- Add direct unified dataset check at the beginning") 
    print("- Improve logging to help debug issues")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())