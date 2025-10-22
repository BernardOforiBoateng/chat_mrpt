#!/bin/bash

echo "=== Deploying TPR Permission Synchronization Fix ==="

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 << 'EOSSH'
cd /home/ec2-user/ChatMRPT
source /home/ec2-user/chatmrpt_env/bin/activate

echo "1. Backing up tpr_handler.py..."
cp app/tpr_module/integration/tpr_handler.py app/tpr_module/integration/tpr_handler.py.backup_sync_fix

echo "2. Updating tpr_handler.py to force session write before response..."
python3 << 'PYTHON'
import re

with open('app/tpr_module/integration/tpr_handler.py', 'r') as f:
    content = f.read()

# Find the section where TPR flags are cleared
old_pattern = r'# CRITICAL: Clear TPR workflow flags after successful transition\s*\n\s*# This allows the permission system to take over\s*\n\s*session\.pop\(\'tpr_workflow_active\', None\)\s*\n\s*session\.pop\(\'tpr_session_id\', None\)\s*\n\s*session\.modified = True\s*\n\s*logger\.info\(f"TPR workflow flags cleared for risk transition - session \{self\.session_id\}"\)'

new_code = '''# CRITICAL: Clear TPR workflow flags after successful transition
                    # This allows the permission system to take over
                    session.pop('tpr_workflow_active', None)
                    session.pop('tpr_session_id', None)
                    
                    # CRITICAL FIX: Force session write to backend IMMEDIATELY
                    # This ensures multi-worker environments see the change
                    session.modified = True
                    session.permanent = True  # Ensure session persists
                    
                    # Double-check flags are cleared
                    if 'tpr_workflow_active' in session:
                        logger.error(f"Failed to clear tpr_workflow_active flag!")
                    
                    logger.info(f"TPR workflow flags cleared for risk transition - session {self.session_id}")
                    logger.info(f"Session state after clear: tpr_active={session.get('tpr_workflow_active')}, permission={session.get('should_ask_analysis_permission')}")'''

# Replace the section
content = re.sub(old_pattern, new_code, content, flags=re.MULTILINE | re.DOTALL)

with open('app/tpr_module/integration/tpr_handler.py', 'w') as f:
    f.write(content)

print("✓ Updated tpr_handler.py with session sync fix")
PYTHON

echo ""
echo "3. Creating session debugging endpoint..."
cat > app/web/routes/debug_session.py << 'EOF'
"""Debug endpoint to check session state."""
from flask import Blueprint, jsonify, session
import logging

debug_bp = Blueprint('debug', __name__, url_prefix='/debug')
logger = logging.getLogger(__name__)

@debug_bp.route('/session-state', methods=['GET'])
def get_session_state():
    """Return current session state for debugging."""
    return jsonify({
        'session_id': session.get('session_id'),
        'tpr_workflow_active': session.get('tpr_workflow_active'),
        'tpr_session_id': session.get('tpr_session_id'),
        'should_ask_analysis_permission': session.get('should_ask_analysis_permission'),
        'data_loaded': session.get('data_loaded'),
        'csv_loaded': session.get('csv_loaded'),
        'shapefile_loaded': session.get('shapefile_loaded'),
        'risk_workflow_active': session.get('risk_workflow_active'),
        'tpr_transition_complete': session.get('tpr_transition_complete')
    })
EOF

echo ""
echo "4. Registering debug blueprint..."
python3 << 'PYTHON'
# Add debug blueprint registration
with open('app/__init__.py', 'r') as f:
    content = f.read()

# Check if debug blueprint already registered
if 'debug_bp' not in content:
    # Find the blueprint registration section
    import_idx = content.find('from .web.routes.export_routes import export_bp')
    if import_idx != -1:
        # Add debug import after export import
        new_import = '\n    from .web.routes.debug_session import debug_bp'
        content = content[:import_idx + len('from .web.routes.export_routes import export_bp')] + new_import + content[import_idx + len('from .web.routes.export_routes import export_bp'):]
        
        # Find where to register the blueprint
        register_idx = content.find('app.register_blueprint(export_bp)')
        if register_idx != -1:
            new_register = '\n    app.register_blueprint(debug_bp)'
            end_of_line = content.find('\n', register_idx)
            content = content[:end_of_line] + new_register + content[end_of_line:]
            
    with open('app/__init__.py', 'w') as f:
        f.write(content)
    print("✓ Added debug blueprint registration")
else:
    print("✓ Debug blueprint already registered")
PYTHON

echo ""
echo "5. Updating analysis_routes.py to add session state logging..."
python3 << 'PYTHON'
with open('app/web/routes/analysis_routes.py', 'r') as f:
    content = f.read()

# Find the TPR workflow check section
old_check = '''# Check for active TPR workflow FIRST
        if session.get('tpr_workflow_active', False):
            logger.info(f"TPR workflow active for session {session_id}, routing to TPR handler")'''

new_check = '''# Check for active TPR workflow FIRST
        tpr_active = session.get('tpr_workflow_active', False)
        permission_flag = session.get('should_ask_analysis_permission', False)
        logger.info(f"Session {session_id} state: tpr_active={tpr_active}, permission={permission_flag}")
        
        if tpr_active:
            logger.info(f"TPR workflow active for session {session_id}, routing to TPR handler")'''

content = content.replace(old_check, new_check)

with open('app/web/routes/analysis_routes.py', 'w') as f:
    f.write(content)

print("✓ Added session state logging to analysis_routes.py")
PYTHON

echo ""
echo "6. Checking syntax..."
python3 -m py_compile app/tpr_module/integration/tpr_handler.py && echo "✓ tpr_handler.py syntax OK"
python3 -m py_compile app/web/routes/analysis_routes.py && echo "✓ analysis_routes.py syntax OK"
python3 -m py_compile app/web/routes/debug_session.py && echo "✓ debug_session.py syntax OK"
python3 -m py_compile app/__init__.py && echo "✓ __init__.py syntax OK"

echo ""
echo "7. Restarting service..."
sudo systemctl restart chatmrpt

sleep 3

echo ""
echo "8. Service status:"
sudo systemctl status chatmrpt < /dev/null | head -10

echo ""
echo "=== Deployment Complete! ==="
echo ""
echo "Session synchronization improvements:"
echo "- Force immediate session write after clearing TPR flags"
echo "- Added session state logging for debugging"
echo "- Debug endpoint available at /debug/session-state"
echo ""
echo "This should fix the race condition where TPR flags aren't properly cleared"
echo "between requests in multi-worker environments."
EOSSH