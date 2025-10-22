#!/bin/bash
set -e

echo "Applying simple ITN analysis detection fix..."

# Apply the fix directly
ssh -i ~/tmp/chatmrpt-key.pem ec2-user@18.117.115.217 'bash -s' << 'EOF'
set -e

echo "1. Backing up itn_planning_tools.py..."
cp /home/ec2-user/ChatMRPT/app/tools/itn_planning_tools.py /home/ec2-user/ChatMRPT/app/tools/itn_planning_tools.py.backup

echo "2. Applying simple fix..."

# Simple sed fix to use absolute path
sed -i 's|Path("instance/uploads")|Path("/home/ec2-user/ChatMRPT/instance/uploads")|g' /home/ec2-user/ChatMRPT/app/tools/itn_planning_tools.py

echo "3. Adding early return for unified dataset check..."
# Add a check right after the session_id is obtained
python3 << 'PYFIX'
import re

with open('/home/ec2-user/ChatMRPT/app/tools/itn_planning_tools.py', 'r') as f:
    content = f.read()

# Find where session_id is logged and add our check right after
pattern = r'(logger\.info\(f"Session ID: {session_id}"\))'
replacement = '''\\1
        
        # CRITICAL: Direct unified dataset check (works across workers)
        if session_id:
            import os
            unified_path = f"/home/ec2-user/ChatMRPT/instance/uploads/{session_id}/unified_dataset.geoparquet"
            if os.path.exists(unified_path):
                logger.info(f"✅ DIRECT CHECK: Found unified dataset - analysis is complete!")
                return True
            unified_csv = f"/home/ec2-user/ChatMRPT/instance/uploads/{session_id}/unified_dataset.csv"
            if os.path.exists(unified_csv):
                logger.info(f"✅ DIRECT CHECK: Found unified CSV - analysis is complete!")
                return True'''

content = re.sub(pattern, replacement, content)

with open('/home/ec2-user/ChatMRPT/app/tools/itn_planning_tools.py', 'w') as f:
    f.write(content)

print("Added direct unified dataset check")
PYFIX

echo "4. Verifying changes..."
echo "Checking for absolute path..."
grep "/home/ec2-user/ChatMRPT/instance/uploads" /home/ec2-user/ChatMRPT/app/tools/itn_planning_tools.py | head -2

echo -e "\nChecking for direct check..."
grep -A2 "CRITICAL: Direct unified dataset check" /home/ec2-user/ChatMRPT/app/tools/itn_planning_tools.py

echo -e "\n5. Restarting application..."
sudo systemctl restart chatmrpt
sleep 5

echo "6. Testing health..."
curl -s http://localhost:8080/ping && echo -e "\nApp is healthy!"

echo -e "\n✅ Simple ITN fix applied!"
echo "The fix adds a direct check for unified dataset files at the very beginning of analysis detection."
EOF

echo "Fix complete!"