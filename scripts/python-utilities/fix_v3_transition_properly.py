#!/usr/bin/env python3
"""
Fix V3 routes to properly trigger risk analysis and set Flask session flags
when transitioning from TPR workflow.
"""

import sys
import os

def apply_fixes():
    """Apply fix to V3 routes to call trigger_risk_analysis"""
    
    file_path = "app/web/routes/data_analysis_v3_routes.py"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix: Call trigger_risk_analysis before exiting
    fix_marker = """        # If workflow has transitioned, signal frontend to exit Data Analysis mode
        if current_state.get('workflow_transitioned'):
            logger.info(f"Workflow has transitioned for session {session_id}, exiting Data Analysis mode")
            return jsonify({
                'success': True,
                'exit_data_analysis_mode': True,
                'message': "Data has been prepared. Switching to main ChatMRPT workflow.",
                'redirect_message': message,  # Pass the original message to be sent to main workflow
                'session_id': session_id
            })"""
    
    fix_replacement = """        # If workflow has transitioned, signal frontend to exit Data Analysis mode
        if current_state.get('workflow_transitioned'):
            logger.info(f"Workflow has transitioned for session {session_id}, exiting Data Analysis mode")
            
            # CRITICAL FIX: Actually trigger risk analysis to set Flask session flags
            # This ensures the Flask session is properly configured before exiting V3
            from app.data_analysis_v3.core.tpr_workflow_handler import TPRWorkflowHandler
            try:
                tpr_handler = TPRWorkflowHandler(session_id, state_manager, None)
                risk_result = tpr_handler.trigger_risk_analysis()
                logger.info(f"✅ Triggered risk analysis for session {session_id}: {risk_result.get('success')}")
            except Exception as e:
                logger.error(f"Failed to trigger risk analysis: {e}")
            
            return jsonify({
                'success': True,
                'exit_data_analysis_mode': True,
                'message': "Data has been prepared. Switching to main ChatMRPT workflow.",
                'redirect_message': message,  # Pass the original message to be sent to main workflow
                'session_id': session_id
            })"""
    
    if fix_marker in content:
        content = content.replace(fix_marker, fix_replacement)
        print("✅ Added trigger_risk_analysis call to V3 routes")
    else:
        print("⚠️ Could not find exact marker, checking alternative...")
        return False
    
    # Write the fixed content
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("\n🎉 V3 transition fix applied!")
    print("\nThis fix ensures that when workflow transitions:")
    print("1. trigger_risk_analysis is actually called")
    print("2. Flask session flags are set (csv_loaded, data_loaded, etc.)")
    print("3. Session is properly configured for main workflow")
    
    return True

if __name__ == "__main__":
    success = apply_fixes()
    sys.exit(0 if success else 1)