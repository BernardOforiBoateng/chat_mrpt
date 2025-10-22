#!/usr/bin/env python3
"""
Simple marker file approach for multi-worker state detection.
When analysis completes, write a marker file.
When ITN tool runs, check for the marker file.
"""

import os
import sys

def main():
    print("Simple Marker File Fix for Multi-Worker State Detection")
    print("=" * 60)
    
    # Create the deployment script
    fix_script = '''#!/bin/bash
set -e

echo "Applying simple marker file fix..."

# SSH to staging and apply fix
ssh -i ~/tmp/chatmrpt-key.pem ec2-user@18.117.115.217 'bash -s' << 'EOF'
set -e

cd /home/ec2-user/ChatMRPT

echo "1. First, let's check what happens in ITN tool when called..."
# Add debug logging to see what session_id ITN tool receives
cat > /tmp/add_itn_debug.py << 'PYFIX'
import re

with open('app/tools/itn_planning_tools.py', 'r') as f:
    content = f.read()

# Find the calculate_itn_needs method and add logging at the very start
pattern = r'(def calculate_itn_needs.*?\\n)(\\s+)(\\"\\"\\".*?\\"\\"\\"\\n)'
replacement = r'\\1\\2\\3\\2logger.info(f"🔍 ITN DEBUG: calculate_itn_needs called")\\n\\2logger.info(f"🔍 ITN DEBUG: data_handler type: {type(data_handler)}")\\n\\2logger.info(f"🔍 ITN DEBUG: data_handler.__dict__: {data_handler.__dict__ if hasattr(data_handler, \\'__dict__\\') else \\'No dict\\'}")\\n\\2session_id = getattr(data_handler, \\'session_id\\', None)\\n\\2logger.info(f"🔍 ITN DEBUG: Extracted session_id: {session_id}")\\n'

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('app/tools/itn_planning_tools.py', 'w') as f:
    f.write(content)

print("Added debug logging to ITN tool")
PYFIX

python3 /tmp/add_itn_debug.py

echo "2. Now add marker file creation to complete_analysis_tools.py..."
# Add marker file creation when analysis completes
cat > /tmp/add_marker.py << 'PYFIX'
import re

with open('app/tools/complete_analysis_tools.py', 'r') as f:
    content = f.read()

# Find where unified dataset is created successfully
marker_code = '''
        # Write marker file for multi-worker state detection
        try:
            marker_file = os.path.join(session_folder, 'analysis_complete.marker')
            with open(marker_file, 'w') as f:
                f.write(f"Analysis completed at {datetime.now().isoformat()}")
            logger.info(f"✅ Wrote analysis complete marker: {marker_file}")
        except Exception as e:
            logger.warning(f"Failed to write marker file: {e}")
'''

# Insert after "Unified dataset created successfully"
pattern = r'(logger\\.info\\(f"✅ Unified dataset created successfully.*?"\\))'
replacement = f'\\1{marker_code}'

content = re.sub(pattern, replacement, content)

# Make sure datetime is imported
if 'from datetime import datetime' not in content:
    content = 'from datetime import datetime\\n' + content

with open('app/tools/complete_analysis_tools.py', 'w') as f:
    f.write(content)

print("Added marker file creation")
PYFIX

python3 /tmp/add_marker.py

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
        return False'''

# Find and replace the method
pattern = r'def _check_analysis_complete\\(self, data_handler: DataHandler\\) -> bool:.*?(?=\\n    def|\\n\\nclass|\\Z)'
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

echo "6. Restart application..."
sudo systemctl restart chatmrpt
sleep 5

echo "7. Test health..."
curl -s http://localhost:8080/ping && echo -e "\\nApp is healthy!"

echo -e "\\n✅ Simple marker file fix applied!"
echo "This fix:"
echo "1. Adds debug logging to see what session_id ITN tool receives"
echo "2. Creates a simple marker file when analysis completes"
echo "3. ITN tool just checks for that marker file"
echo "4. No complex state management, just a simple file check"

# Cleanup
rm -f /tmp/add_itn_debug.py /tmp/add_marker.py /tmp/fix_itn_check.py
EOF

echo "Fix deployment complete!"
'''
    
    # Write the deployment script
    with open('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/deploy_simple_marker_fix.sh', 'w') as f:
        f.write(fix_script)
    
    print("\nDeployment script created: deploy_simple_marker_fix.sh")
    print("\nThis simple fix:")
    print("1. Adds debug logging to understand what's happening")
    print("2. Creates a marker file when analysis completes")
    print("3. ITN tool checks for the marker file")
    print("4. No complex state management!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())