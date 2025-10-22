#!/bin/bash
set -e

echo "Applying risk analysis multi-worker fix to staging..."

# SSH and apply fixes
ssh -i ~/tmp/chatmrpt-key.pem ec2-user@3.137.158.17 'bash -s' << 'EOF'
set -e

echo "Creating backups..."
cp /home/ec2-user/ChatMRPT/app/core/unified_data_state.py /home/ec2-user/ChatMRPT/app/core/unified_data_state.py.backup
cp /home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py /home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py.backup

echo "Applying fix to unified_data_state.py..."
# Comment out the _states cache line
sed -i 's/self\._states: Dict\[str, UnifiedDataState\] = {}/# Removed for multi-worker: self._states: Dict[str, UnifiedDataState] = {}/' /home/ec2-user/ChatMRPT/app/core/unified_data_state.py

# Fix get_state method to always create new instance
sed -i '/def get_state(self, session_id: str) -> UnifiedDataState:/,/return self\._states\[session_id\]/{
    s/"""Get or create data state for session."""/"""Get or create data state for session."""\n        # Always create new instance for multi-worker compatibility\n        return UnifiedDataState(session_id, self.base_upload_folder)/
    /if session_id not in self\._states:/d
    /self\._states\[session_id\] = UnifiedDataState(/d
    /session_id,/d
    /self\.base_upload_folder/d
    /)/d
    /return self\._states\[session_id\]/d
}' /home/ec2-user/ChatMRPT/app/core/unified_data_state.py

# Fix clear_state method
sed -i '/def clear_state(self, session_id: str):/,/del self\._states\[session_id\]/{
    s/"""Clear state for a session."""/"""Clear state for a session."""\n        # No longer needed since we don'\''t cache\n        pass/
    /if session_id in self\._states:/d
    /del self\._states\[session_id\]/d
}' /home/ec2-user/ChatMRPT/app/core/unified_data_state.py

echo "Applying fix to analysis_state_handler.py..."
# Remove global singleton
sed -i 's/^_analysis_state_handler = None/# Removed for multi-worker: _analysis_state_handler = None/' /home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py

# Fix get_analysis_state_handler to always create new instance
sed -i '/def get_analysis_state_handler() -> AnalysisStateHandler:/,/return _analysis_state_handler/{
    s/"""Get the global analysis state handler instance."""/"""Get analysis state handler instance."""/
    s/global _analysis_state_handler/# Always create new instance for multi-worker compatibility/
    s/if _analysis_state_handler is None:/handler = AnalysisStateHandler()/
    s/_analysis_state_handler = AnalysisStateHandler()/_register_default_hooks(handler)/
    /# Register default hooks/d
    s/_register_default_hooks(_analysis_state_handler)/return handler/
    /return _analysis_state_handler/d
}' /home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py

echo "Restarting application..."
sudo systemctl restart chatmrpt

echo "Waiting for app to start..."
sleep 5

# Test app is healthy
curl -s http://localhost:8080/ping || echo "App health check failed"

echo -e "\n\nRisk analysis multi-worker fix applied!"

# Show the changes
echo -e "\n\nChanges made:"
echo "1. unified_data_state.py - removed _states cache, get_state() always creates new instance"
echo "2. analysis_state_handler.py - removed global singleton, always creates new handler"
EOF

echo "Fix deployed to staging!"