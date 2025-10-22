#!/usr/bin/env python3
"""
Risk Analysis Multi-Worker Fix
Run this script directly on the ChatMRPT server to fix the multi-worker issues.
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
    print("Risk Analysis Multi-Worker Fix Deployment")
    print("=" * 50)
    
    # Step 1: Create backups
    print("\n1. Creating backups...")
    backup_cmd = """
    cp /home/ec2-user/ChatMRPT/app/core/unified_data_state.py /home/ec2-user/ChatMRPT/app/core/unified_data_state.py.backup && \
    cp /home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py /home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py.backup && \
    echo "Backups created successfully"
    """
    if not run_ssh_command(backup_cmd):
        print("Failed to create backups")
        return 1
    
    # Step 2: Fix unified_data_state.py
    print("\n2. Fixing unified_data_state.py...")
    
    # Create the fix script on the server
    fix_unified_script = """cat > /tmp/fix_unified_data_state.py << 'EOF'
import re

# Read the file
with open('/home/ec2-user/ChatMRPT/app/core/unified_data_state.py', 'r') as f:
    content = f.read()

# Fix 1: Comment out the _states cache
content = re.sub(
    r'(\s+)(self\._states: Dict\[str, UnifiedDataState\] = \{\})',
    r'\\1# Removed for multi-worker: \\2',
    content
)

# Fix 2: Rewrite get_state method
old_get_state = r'''def get_state\(self, session_id: str\) -> UnifiedDataState:
        """Get or create data state for session\."""
        if session_id not in self\._states:
            self\._states\[session_id\] = UnifiedDataState\(
                session_id, 
                self\.base_upload_folder
            \)
        return self\._states\[session_id\]'''

new_get_state = '''def get_state(self, session_id: str) -> UnifiedDataState:
        """Get or create data state for session."""
        # Always create new instance for multi-worker compatibility
        return UnifiedDataState(session_id, self.base_upload_folder)'''

content = re.sub(old_get_state, new_get_state, content, flags=re.DOTALL)

# Fix 3: Rewrite clear_state method  
old_clear_state = r'''def clear_state\(self, session_id: str\):
        """Clear state for a session\."""
        if session_id in self\._states:
            del self\._states\[session_id\]'''

new_clear_state = '''def clear_state(self, session_id: str):
        """Clear state for a session."""
        # No longer needed since we don't cache
        pass'''

content = re.sub(old_clear_state, new_clear_state, content, flags=re.DOTALL)

# Write back
with open('/home/ec2-user/ChatMRPT/app/core/unified_data_state.py', 'w') as f:
    f.write(content)

print("Fixed unified_data_state.py")
EOF
python3 /tmp/fix_unified_data_state.py
"""
    if not run_ssh_command(fix_unified_script):
        print("Failed to fix unified_data_state.py")
        return 1
    
    # Step 3: Fix analysis_state_handler.py
    print("\n3. Fixing analysis_state_handler.py...")
    
    fix_handler_script = """cat > /tmp/fix_analysis_state_handler.py << 'EOF'
import re

# Read the file
with open('/home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py', 'r') as f:
    content = f.read()

# Fix 1: Comment out global singleton
content = re.sub(
    r'^(_analysis_state_handler = None)',
    r'# Removed for multi-worker: \\1',
    content,
    flags=re.MULTILINE
)

# Fix 2: Rewrite get_analysis_state_handler function
old_function = r'''def get_analysis_state_handler\(\) -> AnalysisStateHandler:
    """Get the global analysis state handler instance\."""
    global _analysis_state_handler
    if _analysis_state_handler is None:
        _analysis_state_handler = AnalysisStateHandler\(\)
        
        # Register default hooks
        _register_default_hooks\(_analysis_state_handler\)
        
    return _analysis_state_handler'''

new_function = '''def get_analysis_state_handler() -> AnalysisStateHandler:
    """Get analysis state handler instance."""
    # Always create new instance for multi-worker compatibility
    handler = AnalysisStateHandler()
    _register_default_hooks(handler)
    return handler'''

content = re.sub(old_function, new_function, content, flags=re.DOTALL)

# Write back
with open('/home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py', 'w') as f:
    f.write(content)

print("Fixed analysis_state_handler.py")
EOF
python3 /tmp/fix_analysis_state_handler.py
"""
    if not run_ssh_command(fix_handler_script):
        print("Failed to fix analysis_state_handler.py")
        return 1
    
    # Step 4: Verify the changes
    print("\n4. Verifying changes...")
    verify_cmd = """
    echo "=== Checking unified_data_state.py ===" && \
    grep -n "_states:" /home/ec2-user/ChatMRPT/app/core/unified_data_state.py | head -5 && \
    echo -e "\\n=== Checking get_state method ===" && \
    grep -A 5 "def get_state" /home/ec2-user/ChatMRPT/app/core/unified_data_state.py && \
    echo -e "\\n=== Checking analysis_state_handler.py ===" && \
    grep -n "_analysis_state_handler =" /home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py | head -5 && \
    echo -e "\\n=== Checking get_analysis_state_handler ===" && \
    grep -A 5 "def get_analysis_state_handler" /home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py
    """
    run_ssh_command(verify_cmd)
    
    # Step 5: Restart the application
    print("\n5. Restarting application...")
    restart_cmd = """
    sudo systemctl restart chatmrpt && \
    echo "Application restarted" && \
    sleep 5 && \
    curl -s http://localhost:8080/ping && \
    echo -e "\\n\\nApplication is healthy!"
    """
    if not run_ssh_command(restart_cmd):
        print("Warning: Application restart might have issues")
    
    # Cleanup
    print("\n6. Cleaning up temporary files...")
    cleanup_cmd = "rm -f /tmp/fix_unified_data_state.py /tmp/fix_analysis_state_handler.py"
    run_ssh_command(cleanup_cmd)
    
    print("\n" + "=" * 50)
    print("Risk analysis multi-worker fix deployed successfully!")
    print("\nChanges made:")
    print("1. unified_data_state.py - Removed _states cache, get_state() always creates new instance")
    print("2. analysis_state_handler.py - Removed global singleton, always creates new handler")
    print("\nPlease test the complete workflow now.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())