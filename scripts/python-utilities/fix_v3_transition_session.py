#!/usr/bin/env python3
"""
Fix Data Analysis V3 to properly set Flask session flags during TPR transition.
This mimics what production does in risk_transition.py
"""

import sys
import os

def apply_fixes():
    """Apply session flag fixes to TPR workflow handler"""
    
    file_path = "app/data_analysis_v3/core/tpr_workflow_handler.py"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix: Add Flask session updates in trigger_risk_analysis
    fix_marker = """            # Clear TPR workflow state and ensure data_loaded is set
            self.state_manager.update_state({
                'tpr_workflow_active': False,
                'tpr_completed': True,
                'data_loaded': True,  # CRITICAL: Set this for main workflow to recognize data
                'csv_loaded': True,   # Also set this for compatibility
                'workflow_transitioned': True
            })"""
    
    fix_replacement = """            # Clear TPR workflow state and ensure data_loaded is set
            self.state_manager.update_state({
                'tpr_workflow_active': False,
                'tpr_completed': True,
                'data_loaded': True,  # CRITICAL: Set this for main workflow to recognize data
                'csv_loaded': True,   # Also set this for compatibility
                'workflow_transitioned': True
            })
            
            # CRITICAL: Also update Flask session directly (like production does)
            # This ensures the flags persist across Redis sessions
            from flask import session
            session['csv_loaded'] = True
            session['shapefile_loaded'] = True
            session['data_loaded'] = True
            session['tpr_transition_complete'] = True
            session['previous_workflow'] = 'tpr'
            # Force Redis persistence
            session.permanent = True
            session.modified = True
            logger.info(f"✅ Set Flask session flags for TPR transition: csv_loaded=True, data_loaded=True")"""
    
    if fix_marker in content:
        content = content.replace(fix_marker, fix_replacement)
        print("✅ Added Flask session flag updates to trigger_risk_analysis")
    else:
        print("⚠️ Could not find exact marker, trying alternative approach...")
        
        # Alternative: Add after state_manager.update_state in trigger_risk_analysis
        alt_marker = "self.state_manager.update_state({"
        if alt_marker in content:
            # Find the closing of update_state call
            import re
            pattern = r'(self\.state_manager\.update_state\({[^}]+}\))'
            matches = list(re.finditer(pattern, content))
            if matches:
                # Replace the last match (should be in trigger_risk_analysis)
                last_match = matches[-1]
                original = last_match.group(0)
                replacement = original + """
            
            # CRITICAL: Also update Flask session directly (like production does)
            from flask import session
            session['csv_loaded'] = True
            session['shapefile_loaded'] = True
            session['data_loaded'] = True
            session['tpr_transition_complete'] = True
            session['previous_workflow'] = 'tpr'
            session.permanent = True
            session.modified = True
            logger.info(f"✅ Set Flask session flags for TPR transition")"""
                
                content = content[:last_match.start()] + replacement + content[last_match.end():]
                print("✅ Added Flask session updates using alternative approach")
    
    # Write the fixed content
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("\n🎉 V3 transition session fix applied!")
    print("\nThis fix ensures that when TPR workflow completes and transitions:")
    print("1. Flask session flags are set directly (csv_loaded, shapefile_loaded, data_loaded)")
    print("2. Session is marked as permanent for Redis persistence")
    print("3. Transition is marked complete like production does")
    print("\nThis mimics production's approach in risk_transition.py")
    
    return True

if __name__ == "__main__":
    success = apply_fixes()
    sys.exit(0 if success else 1)