#!/usr/bin/env python3
"""
Fix risk analysis state persistence for multi-worker environments

Similar to the TPR fix, we need to remove global singletons and in-memory caching
that doesn't work across workers. The unified data state manager should always
check the filesystem for the latest state.
"""

import sys
import os

# Fix for unified_data_state.py
unified_data_state_fix = '''
# In UnifiedDataStateManager class, remove the in-memory cache:

class UnifiedDataStateManager:
    """
    Manager for UnifiedDataState instances across sessions.
    
    FIXED FOR MULTI-WORKER: Always creates fresh instances that check filesystem.
    """
    
    def __init__(self, base_upload_folder: str = "instance/uploads"):
        self.base_upload_folder = base_upload_folder
        # REMOVE: self._states: Dict[str, UnifiedDataState] = {}
    
    def get_state(self, session_id: str) -> UnifiedDataState:
        """Get or create data state for session."""
        # ALWAYS create new instance - it will check filesystem
        return UnifiedDataState(session_id, self.base_upload_folder)
    
    def clear_state(self, session_id: str):
        """Clear state for a session."""
        # No longer needed since we don't cache
        pass
'''

# Fix for analysis_state_handler.py  
analysis_state_handler_fix = '''
# Remove global singleton pattern:

def get_analysis_state_handler() -> AnalysisStateHandler:
    """Get analysis state handler instance."""
    # ALWAYS create new instance for multi-worker compatibility
    handler = AnalysisStateHandler()
    _register_default_hooks(handler)
    return handler
'''

print("Risk Analysis Multi-Worker Fix")
print("=" * 50)
print("\nProblem: Two global singletons with in-memory state don't work across workers:")
print("1. _data_state_manager caches UnifiedDataState instances in memory")
print("2. _analysis_state_handler is a global singleton")
print()
print("Solution:")
print("1. Remove caching from UnifiedDataStateManager - always create fresh instances")
print("2. Remove singleton pattern from get_analysis_state_handler()")
print()
print("Files to modify:")
print("1. app/core/unified_data_state.py")
print("   - Remove self._states dictionary from UnifiedDataStateManager")
print("   - Make get_state() always return new UnifiedDataState instance")
print()
print("2. app/core/analysis_state_handler.py")  
print("   - Remove global _analysis_state_handler variable")
print("   - Make get_analysis_state_handler() always create new instance")
print()
print("This ensures each worker always checks the filesystem for the latest state.")

# Create deployment script
deploy_script = '''#!/bin/bash
set -e

echo "Deploying risk analysis multi-worker fix..."

# SSH to staging
ssh -i aws_files/chatmrpt-key.pem ec2-user@3.137.158.17 << 'EOF'
cd /home/ec2-user/ChatMRPT

echo "Creating backup..."
cp app/core/unified_data_state.py app/core/unified_data_state.py.backup
cp app/core/analysis_state_handler.py app/core/analysis_state_handler.py.backup

echo "Applying fixes..."

# Fix 1: unified_data_state.py
cat > fix_unified_data_state.py << 'PYFIX'
import re

# Read the file
with open('app/core/unified_data_state.py', 'r') as f:
    content = f.read()

# Remove the _states cache from __init__
content = re.sub(
    r'(self\.base_upload_folder = base_upload_folder)\s*\n\s*self\._states: Dict\[str, UnifiedDataState\] = \{\}',
    r'\\1\\n        # Removed _states cache for multi-worker compatibility',
    content
)

# Fix get_state to always create new instance
content = re.sub(
    r'def get_state\(self, session_id: str\) -> UnifiedDataState:\s*\n\s*"""Get or create data state for session\."""\s*\n\s*if session_id not in self\._states:\s*\n\s*self\._states\[session_id\] = UnifiedDataState\(\s*\n\s*session_id,\s*\n\s*self\.base_upload_folder\s*\n\s*\)\s*\n\s*return self\._states\[session_id\]',
    'def get_state(self, session_id: str) -> UnifiedDataState:\\n        """Get or create data state for session."""\\n        # Always create new instance for multi-worker compatibility\\n        return UnifiedDataState(session_id, self.base_upload_folder)',
    content,
    flags=re.DOTALL
)

# Fix clear_state
content = re.sub(
    r'def clear_state\(self, session_id: str\):\s*\n\s*"""Clear state for a session\."""\s*\n\s*if session_id in self\._states:\s*\n\s*del self\._states\[session_id\]',
    'def clear_state(self, session_id: str):\\n        """Clear state for a session."""\\n        # No longer needed since we don\\'t cache\\n        pass',
    content,
    flags=re.DOTALL
)

# Write back
with open('app/core/unified_data_state.py', 'w') as f:
    f.write(content)

print("Fixed unified_data_state.py")
PYFIX

python3 fix_unified_data_state.py

# Fix 2: analysis_state_handler.py
cat > fix_analysis_state_handler.py << 'PYFIX'
import re

# Read the file
with open('app/core/analysis_state_handler.py', 'r') as f:
    content = f.read()

# Remove global singleton
content = re.sub(
    r'# Global instance\s*\n_analysis_state_handler = None\s*\n\s*\n',
    '# Removed global instance for multi-worker compatibility\\n\\n',
    content
)

# Fix get_analysis_state_handler
content = re.sub(
    r'def get_analysis_state_handler\(\) -> AnalysisStateHandler:\s*\n\s*"""Get the global analysis state handler instance\."""\s*\n\s*global _analysis_state_handler\s*\n\s*if _analysis_state_handler is None:\s*\n\s*_analysis_state_handler = AnalysisStateHandler\(\)\s*\n\s*\n\s*# Register default hooks\s*\n\s*_register_default_hooks\(_analysis_state_handler\)\s*\n\s*\n\s*return _analysis_state_handler',
    'def get_analysis_state_handler() -> AnalysisStateHandler:\\n    """Get analysis state handler instance."""\\n    # Always create new instance for multi-worker compatibility\\n    handler = AnalysisStateHandler()\\n    _register_default_hooks(handler)\\n    return handler',
    content,
    flags=re.DOTALL
)

# Write back
with open('app/core/analysis_state_handler.py', 'w') as f:
    f.write(content)

print("Fixed analysis_state_handler.py")
PYFIX

python3 fix_analysis_state_handler.py

# Clean up
rm fix_unified_data_state.py fix_analysis_state_handler.py

echo "Restarting application..."
sudo systemctl restart chatmrpt

echo "Waiting for app to start..."
sleep 5

# Test app is healthy
curl -s http://localhost:8080/ping

echo -e "\\n\\nRisk analysis multi-worker fix deployed!"
EOF
'''

with open('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/deploy_risk_analysis_fix.sh', 'w') as f:
    f.write(deploy_script)

print("\nDeployment script created: deploy_risk_analysis_fix.sh")
print("Run: chmod +x deploy_risk_analysis_fix.sh && ./deploy_risk_analysis_fix.sh")