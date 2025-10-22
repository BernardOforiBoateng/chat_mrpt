#!/usr/bin/env python3
"""
Apply risk analysis multi-worker fixes to staging server.
Clean version with proper string handling.
"""

import subprocess
import sys
import os

def run_ssh_command(command):
    """Run command on staging server via SSH."""
    ssh_cmd = [
        'ssh', '-i', os.path.expanduser('~/tmp/chatmrpt-key.pem'),
        'ec2-user@3.137.158.17',
        command
    ]
    result = subprocess.run(ssh_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    print(result.stdout)
    return True

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
    
    # Step 2: Apply fixes using sed
    print("\n2. Fixing unified_data_state.py...")
    
    # First, comment out the _states line
    fix1_cmd = """sed -i 's/self._states: Dict\[str, UnifiedDataState\] = {}/# Removed for multi-worker: &/' /home/ec2-user/ChatMRPT/app/core/unified_data_state.py"""
    run_ssh_command(fix1_cmd)
    
    # Create a patch file for get_state method
    patch_cmd = """cat > /tmp/get_state_patch.txt << 'EOF'
    def get_state(self, session_id: str) -> UnifiedDataState:
        """Get or create data state for session."""
        # Always create new instance for multi-worker compatibility
        return UnifiedDataState(session_id, self.base_upload_folder)
EOF"""
    run_ssh_command(patch_cmd)
    
    # Apply the get_state fix using Python
    fix_get_state = """python3 -c "
import re

with open('/home/ec2-user/ChatMRPT/app/core/unified_data_state.py', 'r') as f:
    content = f.read()

# Find and replace get_state method
pattern = r'def get_state\\(self, session_id: str\\) -> UnifiedDataState:.*?return self\\._states\\[session_id\\]'
replacement = '''def get_state(self, session_id: str) -> UnifiedDataState:
        \\\"\\\"\\\"Get or create data state for session.\\\"\\\"\\\"
        # Always create new instance for multi-worker compatibility
        return UnifiedDataState(session_id, self.base_upload_folder)'''

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Fix clear_state method
pattern2 = r'def clear_state\\(self, session_id: str\\):.*?del self\\._states\\[session_id\\]'
replacement2 = '''def clear_state(self, session_id: str):
        \\\"\\\"\\\"Clear state for a session.\\\"\\\"\\\"
        # No longer needed since we don\'t cache
        pass'''

content = re.sub(pattern2, replacement2, content, flags=re.DOTALL)

with open('/home/ec2-user/ChatMRPT/app/core/unified_data_state.py', 'w') as f:
    f.write(content)

print('Fixed unified_data_state.py')
"
"""
    run_ssh_command(fix_get_state)
    
    # Step 3: Fix analysis_state_handler.py
    print("\n3. Fixing analysis_state_handler.py...")
    
    # Comment out global singleton
    fix2_cmd = """sed -i 's/^_analysis_state_handler = None/# Removed for multi-worker: &/' /home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py"""
    run_ssh_command(fix2_cmd)
    
    # Fix get_analysis_state_handler using Python
    fix_handler = """python3 -c "
import re

with open('/home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py', 'r') as f:
    content = f.read()

# Find and replace get_analysis_state_handler function
pattern = r'def get_analysis_state_handler\\(\\) -> AnalysisStateHandler:.*?return _analysis_state_handler'
replacement = '''def get_analysis_state_handler() -> AnalysisStateHandler:
    \\\"\\\"\\\"Get analysis state handler instance.\\\"\\\"\\\"
    # Always create new instance for multi-worker compatibility
    handler = AnalysisStateHandler()
    _register_default_hooks(handler)
    return handler'''

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('/home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py', 'w') as f:
    f.write(content)

print('Fixed analysis_state_handler.py')
"
"""
    run_ssh_command(fix_handler)
    
    # Step 4: Verify the changes
    print("\n4. Verifying changes...")
    verify_cmd = """
    echo "=== unified_data_state.py - _states line ===" && \
    grep -n "# Removed for multi-worker" /home/ec2-user/ChatMRPT/app/core/unified_data_state.py && \
    echo -e "\\n=== get_state method ===" && \
    grep -A 4 "def get_state" /home/ec2-user/ChatMRPT/app/core/unified_data_state.py | head -6 && \
    echo -e "\\n=== analysis_state_handler.py - singleton ===" && \
    grep -n "# Removed for multi-worker" /home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py && \
    echo -e "\\n=== get_analysis_state_handler function ===" && \
    grep -A 6 "def get_analysis_state_handler" /home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py | head -8
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
    print("\n6. Cleaning up...")
    cleanup_cmd = "rm -f /tmp/get_state_patch.txt"
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