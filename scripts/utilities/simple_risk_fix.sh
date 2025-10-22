#!/bin/bash
# Simple risk analysis multi-worker fix

echo "Applying risk analysis multi-worker fix..."

# SSH and apply fixes directly
ssh -i ~/tmp/chatmrpt-key.pem ec2-user@3.137.158.17 'bash -s' << 'ENDSSH'
set -e

echo "1. Creating backups..."
cp /home/ec2-user/ChatMRPT/app/core/unified_data_state.py /home/ec2-user/ChatMRPT/app/core/unified_data_state.py.backup
cp /home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py /home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py.backup

echo "2. Fixing unified_data_state.py..."
# Comment out _states cache
sed -i '248s/self._states: Dict\[str, UnifiedDataState\] = {}/# Removed for multi-worker: self._states: Dict[str, UnifiedDataState] = {}/' /home/ec2-user/ChatMRPT/app/core/unified_data_state.py

# Fix get_state method - create temp file with new method
cat > /tmp/new_get_state.txt << 'EOF'
    def get_state(self, session_id: str) -> UnifiedDataState:
        """Get or create data state for session."""
        # Always create new instance for multi-worker compatibility
        return UnifiedDataState(session_id, self.base_upload_folder)
EOF

# Replace the method manually
python3 << 'PYEOF'
import re

with open('/home/ec2-user/ChatMRPT/app/core/unified_data_state.py', 'r') as f:
    content = f.read()

# Find and replace get_state method
old_pattern = r'def get_state\(self, session_id: str\) -> UnifiedDataState:[\s\S]*?return self\._states\[session_id\]'
new_method = '''def get_state(self, session_id: str) -> UnifiedDataState:
        """Get or create data state for session."""
        # Always create new instance for multi-worker compatibility
        return UnifiedDataState(session_id, self.base_upload_folder)'''

content = re.sub(old_pattern, new_method, content)

# Also fix clear_state
old_clear = r'def clear_state\(self, session_id: str\):[\s\S]*?del self\._states\[session_id\]'
new_clear = '''def clear_state(self, session_id: str):
        """Clear state for a session."""
        # No longer needed since we don't cache
        pass'''

content = re.sub(old_clear, new_clear, content)

with open('/home/ec2-user/ChatMRPT/app/core/unified_data_state.py', 'w') as f:
    f.write(content)

print("Fixed unified_data_state.py")
PYEOF

echo "3. Fixing analysis_state_handler.py..."
# Comment out global singleton
sed -i '147s/_analysis_state_handler = None/# Removed for multi-worker: _analysis_state_handler = None/' /home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py

# Fix get_analysis_state_handler method
python3 << 'PYEOF'
import re

with open('/home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py', 'r') as f:
    content = f.read()

# Find and replace get_analysis_state_handler
old_pattern = r'def get_analysis_state_handler\(\) -> AnalysisStateHandler:[\s\S]*?return _analysis_state_handler'
new_method = '''def get_analysis_state_handler() -> AnalysisStateHandler:
    """Get analysis state handler instance."""
    # Always create new instance for multi-worker compatibility
    handler = AnalysisStateHandler()
    _register_default_hooks(handler)
    return handler'''

content = re.sub(old_pattern, new_method, content)

with open('/home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py', 'w') as f:
    f.write(content)

print("Fixed analysis_state_handler.py")
PYEOF

echo "4. Verifying changes..."
echo "=== unified_data_state.py changes ==="
grep -n "# Removed for multi-worker" /home/ec2-user/ChatMRPT/app/core/unified_data_state.py || echo "Not found in unified_data_state.py"
echo ""
grep -A 4 "def get_state" /home/ec2-user/ChatMRPT/app/core/unified_data_state.py | head -6

echo -e "\n=== analysis_state_handler.py changes ==="
grep -n "# Removed for multi-worker" /home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py || echo "Not found in analysis_state_handler.py"
echo ""
grep -A 6 "def get_analysis_state_handler" /home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py | head -8

echo -e "\n5. Restarting application..."
sudo systemctl restart chatmrpt
sleep 5

echo "6. Testing health..."
curl -s http://localhost:8080/ping && echo -e "\nApp is healthy!" || echo -e "\nApp health check failed!"

echo -e "\nDone! Risk analysis multi-worker fix applied."
ENDSSH

echo "Fix deployment complete!"