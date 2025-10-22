#!/bin/bash

echo "=== Deploying TPR State Persistence Fix ==="

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 << 'EOSSH'
cd /home/ec2-user/ChatMRPT
source /home/ec2-user/chatmrpt_env/bin/activate

echo "1. Backing up tpr_state_manager.py..."
cp app/tpr_module/core/tpr_state_manager.py app/tpr_module/core/tpr_state_manager.py.backup_persistence_fix

echo "2. Applying TPR state persistence fix..."
python3 << 'PYTHON'
import re

# Fix tpr_state_manager.py
with open('app/tpr_module/core/tpr_state_manager.py', 'r') as f:
    content = f.read()

# Update the __init__ method to load from Flask session
content = re.sub(
    r'def __init__\(self, session_id: str = None\):\s*\n\s*"""\s*\n\s*Initialize state manager\.\s*\n\s*Args:\s*\n\s*session_id: Unique session identifier\s*\n\s*"""\s*\n\s*self\.session_id = session_id or self\._generate_session_id\(\)\s*\n\s*self\.state = ConversationState\(\s*session_id=self\.session_id,\s*start_time=datetime\.now\(\),\s*current_stage=\'initial\'\s*\)\s*\n\s*self\.state_history = \[\]',
    '''def __init__(self, session_id: str = None):
        """
        Initialize state manager.
        
        Args:
            session_id: Unique session identifier
        """
        self.session_id = session_id or self._generate_session_id()
        
        # Try to load existing state from Flask session
        try:
            from flask import session
            session_key = f'tpr_state_{self.session_id}'
            if session_key in session:
                saved_state = session[session_key]
                # Reconstruct state from saved data
                self.state = ConversationState(
                    session_id=saved_state.get('session_id', self.session_id),
                    start_time=datetime.fromisoformat(saved_state.get('start_time', datetime.now().isoformat())),
                    current_stage=saved_state.get('current_stage', 'initial')
                )
                # Restore other attributes
                for key, value in saved_state.items():
                    if hasattr(self.state, key) and key not in ['session_id', 'start_time', 'current_stage']:
                        setattr(self.state, key, value)
                logger.info(f"TPR State Manager: Loaded existing state for session {self.session_id}")
            else:
                # Create new state
                self.state = ConversationState(
                    session_id=self.session_id,
                    start_time=datetime.now(),
                    current_stage='initial'
                )
                logger.info(f"TPR State Manager: Created new state for session {self.session_id}")
        except Exception as e:
            logger.warning(f"TPR State Manager: Could not load from session: {e}, creating new state")
            self.state = ConversationState(
                session_id=self.session_id,
                start_time=datetime.now(),
                current_stage='initial'
            )
        
        self.state_history = []''',
    content
)

# Update the update_state method to save to Flask session
content = re.sub(
    r'# Handle dictionary update\s+if isinstance\(key_or_dict, dict\):\s+for key, val in key_or_dict\.items\(\):\s+if hasattr\(self\.state, key\):\s+setattr\(self\.state, key, val\)\s+else:\s+# Store in extra attrs\s+if not self\.state\._extra_attrs:\s+self\.state\._extra_attrs = {}\s+self\.state\._extra_attrs\[key\] = val\s+else:\s+# Handle single key-value update\s+if hasattr\(self\.state, key_or_dict\):\s+setattr\(self\.state, key_or_dict, value\)\s+else:\s+# Store in extra attrs\s+if not self\.state\._extra_attrs:\s+self\.state\._extra_attrs = {}\s+self\.state\._extra_attrs\[key_or_dict\] = value',
    '''# Handle dictionary update
        if isinstance(key_or_dict, dict):
            for key, val in key_or_dict.items():
                if hasattr(self.state, key):
                    setattr(self.state, key, val)
                else:
                    # Store in extra attrs
                    if not self.state._extra_attrs:
                        self.state._extra_attrs = {}
                    self.state._extra_attrs[key] = val
        else:
            # Handle single key-value update
            if hasattr(self.state, key_or_dict):
                setattr(self.state, key_or_dict, value)
            else:
                # Store in extra attrs
                if not self.state._extra_attrs:
                    self.state._extra_attrs = {}
                self.state._extra_attrs[key_or_dict] = value
        
        # Save to Flask session for persistence
        try:
            from flask import session
            session_key = f'tpr_state_{self.session_id}'
            session[session_key] = self.state.to_dict()
            session.modified = True
            logger.debug(f"TPR State Manager: Saved state to session for {self.session_id}")
        except Exception as e:
            logger.warning(f"TPR State Manager: Could not save to session: {e}")''',
    content
)

with open('app/tpr_module/core/tpr_state_manager.py', 'w') as f:
    f.write(content)

print("✅ TPR state persistence fix applied")
PYTHON

echo "3. Restarting application..."
sudo systemctl restart chatmrpt

echo "4. Waiting for application to start..."
sleep 10

echo "5. Testing application status..."
curl -s http://localhost:5000/health || echo "Application not responding"

echo "✅ TPR state persistence fix deployed successfully!"
echo ""
echo "The fix addresses the issue where TPR state was not persisting across requests."
echo "Now the TPR workflow router will be able to detect when TPR analysis is complete"
echo "and properly handle the transition to risk analysis."
echo ""
echo "Key changes:"
echo "- Added Flask session persistence to TPR state manager"
echo "- State now loads from session on initialization"
echo "- State is saved to session on every update"
echo "- Added debug logging to track state transitions"

EOSSH

echo "=== Deployment Complete ===" 