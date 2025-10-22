#!/bin/bash
set -e

echo "Applying simple marker file fix..."

# SSH to staging and apply fix
ssh -i ~/tmp/chatmrpt-key.pem ec2-user@18.117.115.217 'bash -s' << 'EOF'
set -e

cd /home/ec2-user/ChatMRPT

echo "1. First, let's add debug logging to ITN tool..."
# Add debug logging to see what session_id ITN tool receives
cat > /tmp/add_itn_debug.py << 'PYFIX'
import re

with open('app/tools/itn_planning_tools.py', 'r') as f:
    content = f.read()

# Find the calculate_itn_needs method and add logging at the very start
pattern = r'(def calculate_itn_needs.*?\n)(\s+)(""".*?"""\n)'
replacement = r'\1\2\3\2logger.info(f"🔍 ITN DEBUG: calculate_itn_needs called")\n\2session_id = getattr(data_handler, "session_id", None)\n\2logger.info(f"🔍 ITN DEBUG: Extracted session_id: {session_id}")\n'

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('app/tools/itn_planning_tools.py', 'w') as f:
    f.write(content)

print("Added debug logging to ITN tool")
PYFIX

python3 /tmp/add_itn_debug.py

echo "2. Now add marker file creation to complete_analysis_tools.py..."
# Find the line after unified dataset creation and add marker
sed -i '/✅ Unified dataset created successfully/a\        \n        # Write marker file for multi-worker state detection\n        try:\n            marker_file = os.path.join(session_folder, "analysis_complete.marker")\n            with open(marker_file, "w") as f:\n                f.write(f"Analysis completed at {datetime.now().isoformat()}")\n            logger.info(f"✅ Wrote analysis complete marker: {marker_file}")\n        except Exception as e:\n            logger.warning(f"Failed to write marker file: {e}")' app/tools/complete_analysis_tools.py

# Make sure datetime is imported
if ! grep -q "from datetime import datetime" app/tools/complete_analysis_tools.py; then
    sed -i '1a from datetime import datetime' app/tools/complete_analysis_tools.py
fi

echo "3. Update ITN tool to check for marker file..."
cat > /tmp/fix_itn_check.py << 'PYFIX'
import re

with open('app/tools/itn_planning_tools.py', 'r') as f:
    content = f.read()

# Replace the entire _check_analysis_complete method with a simpler version
new_method = '''def _check_analysis_complete(self, data_handler: DataHandler) -> bool:
        """Check if analysis has been completed - simplified marker file approach."""
        logger.info("🔍 Checking if analysis is complete...")
        
        # Get session_id from data_handler
        session_id = getattr(data_handler, 'session_id', None)
        logger.info(f"🔍 ITN CHECK: session_id = {session_id}")
        
        if not session_id:
            logger.warning("No session ID available")
            return False
        
        # Simple marker file check
        marker_path = f"/home/ec2-user/ChatMRPT/instance/uploads/{session_id}/analysis_complete.marker"
        logger.info(f"🔍 ITN CHECK: Checking for marker at {marker_path}")
        
        import os
        if os.path.exists(marker_path):
            logger.info(f"✅ Found analysis complete marker!")
            return True
        
        # Fallback: Check for unified dataset
        unified_path = f"/home/ec2-user/ChatMRPT/instance/uploads/{session_id}/unified_dataset.geoparquet"
        if os.path.exists(unified_path):
            logger.info(f"✅ Found unified dataset (fallback check)")
            return True
            
        logger.info("❌ Analysis not complete - no marker or unified dataset found")
        
        # List what files DO exist to help debug
        session_dir = f"/home/ec2-user/ChatMRPT/instance/uploads/{session_id}"
        if os.path.exists(session_dir):
            files = os.listdir(session_dir)
            logger.info(f"🔍 Files in session dir: {files[:10]}...")  # Show first 10 files
        
        return False'''

# Find and replace the method
pattern = r'def _check_analysis_complete\(self, data_handler: DataHandler\) -> bool:.*?(?=\n    def|\n\nclass|\Z)'
content = re.sub(pattern, new_method, content, flags=re.DOTALL)

with open('app/tools/itn_planning_tools.py', 'w') as f:
    f.write(content)

print("Updated ITN analysis check")
PYFIX

python3 /tmp/fix_itn_check.py

echo "4. Verify syntax..."
python3 -m py_compile app/tools/complete_analysis_tools.py && echo "✅ complete_analysis_tools.py OK"
python3 -m py_compile app/tools/itn_planning_tools.py && echo "✅ itn_planning_tools.py OK"

echo "5. Check if marker files exist for previous sessions..."
ls -la /home/ec2-user/ChatMRPT/instance/uploads/*/analysis_complete.marker 2>/dev/null || echo "No existing marker files"

echo "6. Let's also check what files exist in the test session..."
if [ -d "/home/ec2-user/ChatMRPT/instance/uploads/a3c57b5f-13de-448d-ad62-aaa90f528b55" ]; then
    echo "Files in test session:"
    ls -la /home/ec2-user/ChatMRPT/instance/uploads/a3c57b5f-13de-448d-ad62-aaa90f528b55/ | grep -E "(unified|analysis|marker)" | head -10
fi

echo "7. Restart application..."
sudo systemctl restart chatmrpt
sleep 5

echo "8. Test health..."
curl -s http://localhost:8080/ping && echo -e "\nApp is healthy!"

echo -e "\n✅ Simple marker file fix applied!"
echo "This fix:"
echo "1. Adds debug logging to see what session_id ITN tool receives"
echo "2. Creates a simple marker file when analysis completes"
echo "3. ITN tool checks for that marker file first"
echo "4. Falls back to checking for unified dataset"
echo "5. Logs what files exist to help debug"

# Cleanup
rm -f /tmp/add_itn_debug.py /tmp/fix_itn_check.py
EOF

echo "Fix deployment complete!"