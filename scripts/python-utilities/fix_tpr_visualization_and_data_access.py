#!/usr/bin/env python3
"""
Fix TPR Visualization Display and Data Access After Transition

Issues:
1. TPR map visualization not showing in chat despite being created
2. Main workflow not accessing data after V3 transition

Root Causes:
1. Visualizations array not being properly forwarded to frontend
2. data_loaded flag not set in session after V3 transition
"""

import os
import sys

def fix_visualization_display():
    """Fix TPR visualization display in chat"""
    
    # The backend IS returning visualizations correctly
    # The issue is in the frontend handling
    
    print("Fix 1: Ensure visualizations are displayed")
    print("- Backend returns: visualizations: [{type: 'iframe', url: '/serve_viz_file/...'}]")
    print("- Frontend should handle this in visualization-manager.js")
    

def fix_data_access():
    """Fix data access in main workflow after transition"""
    
    print("\nFix 2: Ensure data_loaded flag is set after transition")
    
    # File: app/data_analysis_v3/core/tpr_workflow_handler.py
    # In trigger_risk_analysis method, add:
    fix_tpr_handler = '''
    # Line 371 - Update state to include data_loaded flag
    self.state_manager.update_state({
        'tpr_workflow_active': False,
        'tpr_completed': True,
        'data_loaded': True,  # ADD THIS LINE
        'workflow_transitioned': True
    })
    '''
    
    # File: app/core/request_interpreter.py
    # In _get_session_context method, fix the check:
    fix_context_check = '''
    # Line 1660 - Fix the data loaded check
    # OLD:
    data_loaded = (session_data.get('data_loaded', False) or session_data.get('csv_loaded', False)) and has_actual_data
    
    # NEW - Also check if we have data in self.session_data:
    data_loaded = (
        (session_data.get('data_loaded', False) or 
         session_data.get('csv_loaded', False) or
         session_id in self.session_data) and  # ADD THIS CHECK
        has_actual_data
    )
    '''
    
    print("Fixes needed:")
    print("1. Add data_loaded flag in tpr_workflow_handler.py")
    print("2. Check self.session_data in request_interpreter.py")
    

def fix_data_context():
    """Ensure data context is available for tool selection"""
    
    print("\nFix 3: Pass data context to LLM for proper responses")
    
    fix_context = '''
    # In request_interpreter.py process_message_streaming method
    # When data is loaded, pass it to the system prompt
    
    # Line 152 - Build system prompt with data context
    system_prompt = self._build_system_prompt(session_context, session_id)
    
    # The _build_system_prompt should include:
    if session_id in self.session_data:
        data_info = self.session_data[session_id]
        system_prompt += f"""
        Current Data Context:
        - Loaded data with {data_info['shape'][0]} rows and {data_info['shape'][1]} columns
        - Columns: {', '.join(data_info['columns'][:10])}...
        """
    '''
    
    print("System prompt should include actual data context")


if __name__ == "__main__":
    print("=" * 60)
    print("TPR VISUALIZATION AND DATA ACCESS FIXES")
    print("=" * 60)
    
    fix_visualization_display()
    fix_data_access()
    fix_data_context()
    
    print("\n" + "=" * 60)
    print("IMPLEMENTATION PLAN")
    print("=" * 60)
    print("""
1. Fix tpr_workflow_handler.py:
   - Add 'data_loaded': True to state update (line 371)

2. Fix request_interpreter.py:
   - Update _get_session_context to check self.session_data (line 1660)
   - Ensure _build_system_prompt includes data context

3. Fix frontend visualization handling:
   - Check if visualization-manager.js is processing V3 visualizations
   - Ensure iframe URLs are correctly served

4. Deploy all fixes to staging
""")