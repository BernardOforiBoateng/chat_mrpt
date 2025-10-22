#!/usr/bin/env python3
"""
Risk Analysis Multi-Worker Fix
Run this script directly on the ChatMRPT server to fix the multi-worker issues.

Usage:
1. Copy this script to the server: 
   scp risk_analysis_fix_server.py ec2-user@3.137.158.17:/home/ec2-user/
2. SSH to the server and run:
   python3 risk_analysis_fix_server.py
"""

import re
import shutil
import os
import sys

def backup_file(filepath):
    """Create a backup of the file."""
    backup_path = filepath + '.backup'
    shutil.copy2(filepath, backup_path)
    print(f"Backed up {filepath} to {backup_path}")

def fix_unified_data_state():
    """Fix the unified_data_state.py file."""
    filepath = '/home/ec2-user/ChatMRPT/app/core/unified_data_state.py'
    
    print("\nFixing unified_data_state.py...")
    
    # Read the file
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Fix 1: Comment out the _states cache
    content = re.sub(
        r'(\s+)(self\._states: Dict\[str, UnifiedDataState\] = \{\})',
        r'\1# Removed for multi-worker: \2',
        content
    )
    
    # Fix 2: Rewrite get_state method
    old_get_state = r'def get_state\(self, session_id: str\) -> UnifiedDataState:\s*\n\s*"""Get or create data state for session\."""\s*\n\s*if session_id not in self\._states:\s*\n\s*self\._states\[session_id\] = UnifiedDataState\(\s*\n\s*session_id,\s*\n\s*self\.base_upload_folder\s*\n\s*\)\s*\n\s*return self\._states\[session_id\]'
    
    new_get_state = '''def get_state(self, session_id: str) -> UnifiedDataState:
        """Get or create data state for session."""
        # Always create new instance for multi-worker compatibility
        return UnifiedDataState(session_id, self.base_upload_folder)'''
    
    content = re.sub(old_get_state, new_get_state, content, flags=re.DOTALL)
    
    # Fix 3: Rewrite clear_state method
    old_clear_state = r'def clear_state\(self, session_id: str\):\s*\n\s*"""Clear state for a session\."""\s*\n\s*if session_id in self\._states:\s*\n\s*del self\._states\[session_id\]'
    
    new_clear_state = '''def clear_state(self, session_id: str):
        """Clear state for a session."""
        # No longer needed since we don't cache
        pass'''
    
    content = re.sub(old_clear_state, new_clear_state, content, flags=re.DOTALL)
    
    # Write back
    with open(filepath, 'w') as f:
        f.write(content)
    
    print("✓ Fixed unified_data_state.py")

def fix_analysis_state_handler():
    """Fix the analysis_state_handler.py file."""
    filepath = '/home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py'
    
    print("\nFixing analysis_state_handler.py...")
    
    # Read the file
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Fix 1: Comment out global singleton
    content = re.sub(
        r'^(_analysis_state_handler = None)',
        r'# Removed for multi-worker: \1',
        content,
        flags=re.MULTILINE
    )
    
    # Fix 2: Rewrite get_analysis_state_handler function
    old_function = r'def get_analysis_state_handler\(\) -> AnalysisStateHandler:\s*\n\s*"""Get the global analysis state handler instance\."""\s*\n\s*global _analysis_state_handler\s*\n\s*if _analysis_state_handler is None:\s*\n\s*_analysis_state_handler = AnalysisStateHandler\(\)\s*\n\s*\n\s*# Register default hooks\s*\n\s*_register_default_hooks\(_analysis_state_handler\)\s*\n\s*\n\s*return _analysis_state_handler'
    
    new_function = '''def get_analysis_state_handler() -> AnalysisStateHandler:
    """Get analysis state handler instance."""
    # Always create new instance for multi-worker compatibility
    handler = AnalysisStateHandler()
    _register_default_hooks(handler)
    return handler'''
    
    content = re.sub(old_function, new_function, content, flags=re.DOTALL)
    
    # Write back
    with open(filepath, 'w') as f:
        f.write(content)
    
    print("✓ Fixed analysis_state_handler.py")

def verify_changes():
    """Verify the changes were applied correctly."""
    print("\nVerifying changes...")
    
    # Check unified_data_state.py
    with open('/home/ec2-user/ChatMRPT/app/core/unified_data_state.py', 'r') as f:
        content = f.read()
        if '# Removed for multi-worker:' in content and 'Always create new instance for multi-worker' in content:
            print("✓ unified_data_state.py changes verified")
        else:
            print("✗ unified_data_state.py changes may not be complete")
    
    # Check analysis_state_handler.py
    with open('/home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py', 'r') as f:
        content = f.read()
        if '# Removed for multi-worker:' in content and 'Always create new instance for multi-worker' in content:
            print("✓ analysis_state_handler.py changes verified")
        else:
            print("✗ analysis_state_handler.py changes may not be complete")

def main():
    print("Risk Analysis Multi-Worker Fix")
    print("=" * 50)
    
    # Check if we're on the server
    if not os.path.exists('/home/ec2-user/ChatMRPT'):
        print("ERROR: This script must be run on the ChatMRPT server!")
        print("Copy this script to the server and run it there.")
        print("\nInstructions:")
        print("1. scp risk_analysis_fix_server.py ec2-user@3.137.158.17:/home/ec2-user/")
        print("2. ssh ec2-user@3.137.158.17")
        print("3. python3 risk_analysis_fix_server.py")
        return 1
    
    try:
        # Backup files
        print("\n1. Creating backups...")
        backup_file('/home/ec2-user/ChatMRPT/app/core/unified_data_state.py')
        backup_file('/home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py')
        
        # Apply fixes
        print("\n2. Applying fixes...")
        fix_unified_data_state()
        fix_analysis_state_handler()
        
        # Verify
        print("\n3. Verification...")
        verify_changes()
        
        print("\n" + "=" * 50)
        print("✓ Risk analysis multi-worker fix complete!")
        print("\nNext steps:")
        print("1. Restart the application: sudo systemctl restart chatmrpt")
        print("2. Test the complete workflow (TPR → Risk Analysis → Bed Net Planning)")
        print("\nChanges made:")
        print("- unified_data_state.py: Removed _states cache, get_state() always creates new instance")
        print("- analysis_state_handler.py: Removed global singleton, always creates new handler")
        
        return 0
        
    except Exception as e:
        print(f"\nERROR: {e}")
        print("The fix failed. Check the error and try again.")
        return 1

if __name__ == "__main__":
    sys.exit(main())