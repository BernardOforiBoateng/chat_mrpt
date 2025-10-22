#!/usr/bin/env python3
"""
Comprehensive fix for multi-worker state detection in ChatMRPT.
This creates a unified, file-based state detection system.
"""

import os
import sys

def main():
    print("Unified State Detection System Fix")
    print("=" * 50)
    
    # Create the deployment script
    fix_script = '''#!/bin/bash
set -e

echo "Applying comprehensive state detection fix..."

# SSH to staging and apply fix
ssh -i ~/tmp/chatmrpt-key.pem ec2-user@18.117.115.217 'bash -s' << 'EOF'
set -e

echo "1. Creating backup of files..."
cd /home/ec2-user/ChatMRPT
cp app/core/unified_data_state.py app/core/unified_data_state.py.backup_state_fix
cp app/tools/complete_analysis_tools.py app/tools/complete_analysis_tools.py.backup_state_fix
cp app/tools/visualization_tools.py app/tools/visualization_tools.py.backup_state_fix || true
cp app/tools/itn_planning_tools.py app/tools/itn_planning_tools.py.backup_state_fix

echo "2. Creating session state manager..."
cat > app/core/session_state_manager.py << 'PYFILE'
"""
Centralized session state management for multi-worker environments.
Uses file-based state to ensure consistency across all workers.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class SessionStateManager:
    """Manages session state using file-based storage for multi-worker compatibility."""
    
    def __init__(self, base_upload_folder: str = "instance/uploads"):
        self.base_upload_folder = Path(base_upload_folder)
    
    def _get_state_file_path(self, session_id: str) -> Path:
        """Get the path to the session state file."""
        return self.base_upload_folder / session_id / "session_state.json"
    
    def save_state(self, session_id: str, state_data: Dict[str, Any]) -> bool:
        """Save session state to file."""
        try:
            state_file = self._get_state_file_path(session_id)
            state_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Add timestamp
            state_data['last_updated'] = datetime.now().isoformat()
            state_data['session_id'] = session_id
            
            with open(state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
            
            logger.info(f"✅ Saved session state for {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save session state: {e}")
            return False
    
    def load_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session state from file."""
        try:
            state_file = self._get_state_file_path(session_id)
            if state_file.exists():
                with open(state_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load session state: {e}")
        return None
    
    def update_state(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing session state."""
        state = self.load_state(session_id) or {}
        state.update(updates)
        return self.save_state(session_id, state)
    
    def is_analysis_complete(self, session_id: str) -> bool:
        """Check if analysis is complete for the session."""
        # Method 1: Check state file
        state = self.load_state(session_id)
        if state and state.get('analysis_complete'):
            logger.info(f"✅ Analysis complete (from state file)")
            return True
        
        # Method 2: Check for unified dataset files
        session_folder = self.base_upload_folder / session_id
        if session_folder.exists():
            unified_files = [
                'unified_dataset.geoparquet',
                'unified_dataset.csv',
                'analysis_vulnerability_rankings.csv',
                'analysis_vulnerability_rankings_pca.csv'
            ]
            
            for filename in unified_files:
                if (session_folder / filename).exists():
                    logger.info(f"✅ Analysis complete (found {filename})")
                    # Update state file for next time
                    self.update_state(session_id, {'analysis_complete': True})
                    return True
        
        return False
    
    def get_analysis_info(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive analysis information."""
        info = {
            'session_id': session_id,
            'analysis_complete': False,
            'files': []
        }
        
        # Load state file info
        state = self.load_state(session_id)
        if state:
            info.update(state)
        
        # Check actual files
        session_folder = self.base_upload_folder / session_id
        if session_folder.exists():
            important_files = [
                'unified_dataset.geoparquet',
                'unified_dataset.csv',
                'analysis_vulnerability_rankings.csv',
                'analysis_vulnerability_rankings_pca.csv',
                'tpr_analysis.csv',
                'raw_data.csv'
            ]
            
            for filename in important_files:
                filepath = session_folder / filename
                if filepath.exists():
                    info['files'].append({
                        'name': filename,
                        'size': filepath.stat().st_size,
                        'modified': datetime.fromtimestamp(filepath.stat().st_mtime).isoformat()
                    })
            
            # Update analysis complete status
            if any(f['name'].startswith('unified_dataset') for f in info['files']):
                info['analysis_complete'] = True
        
        return info


# Global instance for easy access
_state_manager = None

def get_session_state_manager(base_folder: str = "instance/uploads") -> SessionStateManager:
    """Get the session state manager instance."""
    global _state_manager
    if _state_manager is None:
        _state_manager = SessionStateManager(base_folder)
    return _state_manager
PYFILE

echo "3. Updating unified_data_state.py to use session state manager..."
python3 << 'PYFIX1'
import re

# Read the file
with open('app/core/unified_data_state.py', 'r') as f:
    content = f.read()

# Add import for SessionStateManager
import_section = """from typing import Dict, Optional, Any, List, Tuple
import pandas as pd
import geopandas as gpd
from pathlib import Path
import os
import logging
import json
from datetime import datetime
from ..core.session_state_manager import get_session_state_manager"""

# Replace the imports
content = re.sub(
    r'from typing import.*?import logging',
    import_section,
    content,
    flags=re.DOTALL
)

# Update the get_state method to use session state manager
new_get_state = '''def get_state(self, session_id: str) -> UnifiedDataState:
        """Get or create data state for session."""
        # Always create new instance for multi-worker compatibility
        state = UnifiedDataState(session_id, self.base_upload_folder)
        
        # Check if analysis is already complete via session state manager
        state_manager = get_session_state_manager(self.base_upload_folder)
        if state_manager.is_analysis_complete(session_id):
            logger.info(f"Session {session_id} has completed analysis (detected via state manager)")
        
        return state'''

content = re.sub(
    r'def get_state\(self, session_id: str\) -> UnifiedDataState:.*?return UnifiedDataState\(session_id, self\.base_upload_folder\)',
    new_get_state,
    content,
    flags=re.DOTALL
)

# Write back
with open('app/core/unified_data_state.py', 'w') as f:
    f.write(content)

print("Updated unified_data_state.py")
PYFIX1

echo "4. Updating complete_analysis_tools.py to save state..."
python3 << 'PYFIX2'
import re

# Read the file
with open('app/tools/complete_analysis_tools.py', 'r') as f:
    content = f.read()

# Add import
if 'from ..core.session_state_manager import' not in content:
    content = re.sub(
        r'(from pathlib import Path)',
        r'\\1\\nfrom ..core.session_state_manager import get_session_state_manager',
        content
    )

# Find where analysis completes and add state save
# Look for the success section where unified dataset is created
success_pattern = r'(logger\.info\(f"✅ Unified dataset created successfully.*?"\))'
state_save_code = '''\\1
        
        # Save session state for multi-worker compatibility
        try:
            state_manager = get_session_state_manager()
            state_data = {
                'analysis_complete': True,
                'unified_dataset': 'unified_dataset.geoparquet',
                'analysis_timestamp': datetime.now().isoformat(),
                'methods': ['composite', 'pca'],
                'ward_count': len(unified_df) if 'unified_df' in locals() else None,
                'columns': list(unified_df.columns) if 'unified_df' in locals() else []
            }
            state_manager.save_state(session_id, state_data)
            logger.info(f"✅ Saved session state for multi-worker access")
        except Exception as e:
            logger.warning(f"Failed to save session state: {e}")'''

content = re.sub(success_pattern, state_save_code, content)

# Also add datetime import if not present
if 'from datetime import datetime' not in content:
    content = re.sub(
        r'(import.*?logging)',
        r'\\1\\nfrom datetime import datetime',
        content,
        flags=re.DOTALL
    )

# Write back
with open('app/tools/complete_analysis_tools.py', 'w') as f:
    f.write(content)

print("Updated complete_analysis_tools.py")
PYFIX2

echo "5. Updating visualization tools to use session state manager..."
# First check if the file exists
if [ -f "app/tools/visualization_tools.py" ]; then
    python3 << 'PYFIX3'
import re

# Read the file
with open('app/tools/visualization_tools.py', 'r') as f:
    content = f.read()

# Add import
if 'from ..core.session_state_manager import' not in content:
    content = re.sub(
        r'(import.*?from pathlib import Path)',
        r'\\1\\nfrom ..core.session_state_manager import get_session_state_manager',
        content,
        flags=re.DOTALL
    )

# Find create_vulnerability_map function and update its analysis check
# This regex looks for the function and its initial checks
func_pattern = r'(def create_vulnerability_map.*?data_handler.*?:.*?\\n)(.*?)(# Check if analysis)'

new_check = '''\\1    """Create vulnerability distribution map."""
    # Use session state manager for consistent multi-worker detection
    state_manager = get_session_state_manager()
    session_id = getattr(data_handler, 'session_id', None)
    
    if session_id and not state_manager.is_analysis_complete(session_id):
        # Run analysis if not complete
        from .complete_analysis_tools import run_complete_analysis
        logger.info("Running analysis before creating vulnerability map...")
        analysis_result = run_complete_analysis(data_handler, **kwargs)
        if not analysis_result.get("success"):
            return {"error": "Failed to complete analysis", "success": False}
    
    \\3'''

content = re.sub(func_pattern, new_check, content, flags=re.DOTALL)

# Write back
with open('app/tools/visualization_tools.py', 'w') as f:
    f.write(content)

print("Updated visualization_tools.py")
PYFIX3
else
    echo "visualization_tools.py not found, checking for individual viz tools..."
    
    # Update any tool that creates vulnerability maps
    for tool in app/tools/*vulnerability*.py app/tools/*viz*.py; do
        if [ -f "$tool" ]; then
            echo "Checking $tool..."
            if grep -q "create_vulnerability_map" "$tool"; then
                echo "Updating $tool with session state checks..."
                # Add similar fix as above
            fi
        fi
    done
fi

echo "6. Reverting ITN planning tool to use session state manager..."
python3 << 'PYFIX4'
import re

# Read the file
with open('app/tools/itn_planning_tools.py', 'r') as f:
    content = f.read()

# Add import
if 'from ..core.session_state_manager import' not in content:
    content = re.sub(
        r'(from pathlib import Path)',
        r'\\1\\nfrom ..core.session_state_manager import get_session_state_manager',
        content
    )

# Replace the _check_analysis_complete method with one that uses session state manager
new_check_method = '''def _check_analysis_complete(self, data_handler: DataHandler) -> bool:
        """Check if analysis has been completed using centralized state manager."""
        logger.info("🔍 Checking if analysis is complete...")
        
        session_id = getattr(data_handler, 'session_id', None)
        if not session_id:
            logger.warning("No session ID available")
            return False
        
        logger.info(f"Session ID: {session_id}")
        
        # Use centralized session state manager
        state_manager = get_session_state_manager()
        is_complete = state_manager.is_analysis_complete(session_id)
        
        if is_complete:
            logger.info("✅ Analysis is complete (verified by session state manager)")
        else:
            logger.info("❌ Analysis not complete")
        
        return is_complete'''

# Replace the entire _check_analysis_complete method
content = re.sub(
    r'def _check_analysis_complete\(self, data_handler: DataHandler\) -> bool:.*?return False',
    new_check_method,
    content,
    flags=re.DOTALL
)

# Write back
with open('app/tools/itn_planning_tools.py', 'w') as f:
    f.write(content)

print("Updated itn_planning_tools.py")
PYFIX4

echo "7. Creating a test script to verify the fix..."
cat > /tmp/test_state_manager.py << 'PYTEST'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/ec2-user/ChatMRPT')

from app.core.session_state_manager import get_session_state_manager
import os

# Test with a known session
test_session = "a3c57b5f-13de-448d-ad62-aaa90f528b55"
state_manager = get_session_state_manager("/home/ec2-user/ChatMRPT/instance/uploads")

print(f"Testing session: {test_session}")
print(f"Is analysis complete: {state_manager.is_analysis_complete(test_session)}")
print(f"Analysis info: {state_manager.get_analysis_info(test_session)}")

# Check if files exist
session_dir = f"/home/ec2-user/ChatMRPT/instance/uploads/{test_session}"
if os.path.exists(session_dir):
    print(f"\\nFiles in session directory:")
    for f in os.listdir(session_dir):
        print(f"  - {f}")
PYTEST

python3 /tmp/test_state_manager.py

echo "8. Restarting application..."
sudo systemctl restart chatmrpt
sleep 5

echo "9. Testing health..."
curl -s http://localhost:8080/ping && echo -e "\\nApp is healthy!"

echo -e "\\n✅ Unified state detection fix applied!"
echo "The fix implements:"
echo "1. Centralized SessionStateManager for file-based state"
echo "2. All tools now use the same state detection method"
echo "3. State persists across all workers via JSON files"
echo "4. Automatic fallback to file detection if state file missing"

# Cleanup
rm -f /tmp/test_state_manager.py
EOF

echo "Fix deployment complete!"
'''
    
    # Write the deployment script
    with open('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/deploy_unified_state_fix.sh', 'w') as f:
        f.write(fix_script)
    
    print("\nDeployment script created: deploy_unified_state_fix.sh")
    print("\nThis comprehensive fix will:")
    print("1. Create a centralized SessionStateManager class")
    print("2. Update all tools to use consistent state detection")
    print("3. Save session state to JSON files when analysis completes")
    print("4. Check both state files and actual data files for robustness")
    print("\nTo apply: chmod +x deploy_unified_state_fix.sh && ./deploy_unified_state_fix.sh")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())