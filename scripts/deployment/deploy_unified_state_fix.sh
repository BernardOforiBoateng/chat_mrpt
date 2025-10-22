#!/bin/bash
set -e

echo "Applying comprehensive state detection fix..."

# SSH to staging and apply fix
ssh -i ~/tmp/chatmrpt-key.pem ec2-user@18.117.115.217 'bash -s' << 'EOF'
set -e

echo "1. Creating backup of files..."
cd /home/ec2-user/ChatMRPT
cp app/core/unified_data_state.py app/core/unified_data_state.py.backup_state_fix
cp app/tools/complete_analysis_tools.py app/tools/complete_analysis_tools.py.backup_state_fix
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
            # Use absolute path if base_upload_folder is relative
            if not self.base_upload_folder.is_absolute():
                session_folder = Path("/home/ec2-user/ChatMRPT") / session_folder
                
            unified_files = [
                'unified_dataset.geoparquet',
                'unified_dataset.csv',
                'analysis_vulnerability_rankings.csv',
                'analysis_vulnerability_rankings_pca.csv'
            ]
            
            for filename in unified_files:
                filepath = session_folder / filename
                if filepath.exists():
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
        if not self.base_upload_folder.is_absolute():
            session_folder = Path("/home/ec2-user/ChatMRPT") / session_folder
            
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

echo "3. Updating complete_analysis_tools.py to save state..."
# Add state saving after analysis completes
sed -i '/✅ Unified dataset created successfully/a\        \n        # Save session state for multi-worker compatibility\n        try:\n            from ..core.session_state_manager import get_session_state_manager\n            state_manager = get_session_state_manager()\n            state_data = {\n                "analysis_complete": True,\n                "unified_dataset": "unified_dataset.geoparquet",\n                "analysis_timestamp": datetime.now().isoformat(),\n                "methods": ["composite", "pca"],\n                "ward_count": len(unified_df) if "unified_df" in locals() else None\n            }\n            state_manager.save_state(session_id, state_data)\n            logger.info(f"✅ Saved session state for multi-worker access")\n        except Exception as e:\n            logger.warning(f"Failed to save session state: {e}")' app/tools/complete_analysis_tools.py

# Add datetime import if needed
if ! grep -q "from datetime import datetime" app/tools/complete_analysis_tools.py; then
    sed -i '1a from datetime import datetime' app/tools/complete_analysis_tools.py
fi

echo "4. Updating ITN planning tool to use session state manager..."
# First, add the import
if ! grep -q "session_state_manager" app/tools/itn_planning_tools.py; then
    sed -i '/from pathlib import Path/a from ..core.session_state_manager import get_session_state_manager' app/tools/itn_planning_tools.py
fi

# Create a simple Python script to replace the method
cat > /tmp/fix_itn_check.py << 'PYFIX'
import re

with open('app/tools/itn_planning_tools.py', 'r') as f:
    content = f.read()

# Find and replace the entire _check_analysis_complete method
pattern = r'def _check_analysis_complete\(self, data_handler: DataHandler\) -> bool:.*?(?=\n    def|\nclass|\Z)'

replacement = '''def _check_analysis_complete(self, data_handler: DataHandler) -> bool:
        """Check if analysis has been completed using centralized state manager."""
        logger.info("🔍 Checking if analysis is complete...")
        
        session_id = getattr(data_handler, 'session_id', None)
        if not session_id:
            logger.warning("No session ID available")
            return False
        
        logger.info(f"Session ID: {session_id}")
        
        # Use centralized session state manager
        try:
            state_manager = get_session_state_manager()
            is_complete = state_manager.is_analysis_complete(session_id)
            
            if is_complete:
                logger.info("✅ Analysis is complete (verified by session state manager)")
            else:
                logger.info("❌ Analysis not complete")
            
            return is_complete
        except Exception as e:
            logger.error(f"Error checking analysis state: {e}")
            # Fallback to direct file check
            import os
            unified_path = f"/home/ec2-user/ChatMRPT/instance/uploads/{session_id}/unified_dataset.geoparquet"
            if os.path.exists(unified_path):
                logger.info("✅ Analysis complete (direct file check)")
                return True
            return False'''

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('app/tools/itn_planning_tools.py', 'w') as f:
    f.write(content)

print("Fixed ITN planning tool")
PYFIX

python3 /tmp/fix_itn_check.py

echo "5. Testing the state manager..."
cat > /tmp/test_state.py << 'PYTEST'
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

info = state_manager.get_analysis_info(test_session)
print(f"Files found: {len(info['files'])}")
for f in info['files']:
    print(f"  - {f['name']}")
PYTEST

python3 /tmp/test_state.py

echo "6. Restarting application..."
sudo systemctl restart chatmrpt
sleep 5

echo "7. Testing health..."
curl -s http://localhost:8080/ping && echo -e "\nApp is healthy!"

echo -e "\n✅ Unified state detection fix applied!"
echo "The system now uses:"
echo "1. SessionStateManager for centralized state tracking"
echo "2. File-based state that works across all workers"
echo "3. Automatic state detection from existing files"
echo "4. Consistent state checking across all tools"

# Cleanup
rm -f /tmp/fix_itn_check.py /tmp/test_state.py
EOF

echo "Fix deployment complete!"