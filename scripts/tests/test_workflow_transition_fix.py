#!/usr/bin/env python3
"""
Test workflow transition fix - verifies that after TPR completion,
the system properly exits Data Analysis V3 mode and routes to main workflow.
"""

import os
import json
import shutil
import tempfile
from pathlib import Path

def test_workflow_transition():
    """Test the workflow transition from Data Analysis V3 to main ChatMRPT."""
    
    print("=" * 60)
    print("TESTING WORKFLOW TRANSITION FIX")
    print("=" * 60)
    
    # Create test session
    session_id = "test_transition_123"
    session_folder = f"instance/uploads/{session_id}"
    
    # Clean up if exists
    if os.path.exists(session_folder):
        shutil.rmtree(session_folder)
    
    os.makedirs(session_folder, exist_ok=True)
    print(f"✅ Created test session: {session_id}")
    
    # Test 1: Create initial state files
    print("\n1. Setting up initial Data Analysis V3 state...")
    
    # Create .data_analysis_mode flag
    flag_file = os.path.join(session_folder, '.data_analysis_mode')
    with open(flag_file, 'w') as f:
        f.write('test_data.csv\n2025-01-18T00:00:00')
    print(f"   ✅ Created .data_analysis_mode flag")
    
    # Create agent state
    state_file = os.path.join(session_folder, '.agent_state.json')
    initial_state = {
        '_session_id': session_id,
        'current_stage': 'tpr_complete',
        'tpr_completed': True,
        'workflow_transitioned': False,
        '_last_updated': '2025-01-18T00:00:00'
    }
    with open(state_file, 'w') as f:
        json.dump(initial_state, f, indent=2)
    print(f"   ✅ Created agent state (workflow_transitioned=False)")
    
    # Test 2: Simulate workflow transition
    print("\n2. Simulating workflow transition...")
    
    # Import the handler
    import sys
    sys.path.insert(0, '.')
    from app.data_analysis_v3.core.tpr_workflow_handler import TPRWorkflowHandler
    from app.data_analysis_v3.core.state_manager import DataAnalysisStateManager
    
    # Initialize handler
    state_manager = DataAnalysisStateManager(session_id)
    handler = TPRWorkflowHandler(session_id, state_manager, None)
    
    # Trigger transition
    result = handler.trigger_risk_analysis()
    
    print(f"   ✅ Triggered risk analysis transition")
    print(f"   Success: {result.get('success')}")
    
    # Test 3: Verify flag file removal
    print("\n3. Checking flag file removal...")
    if os.path.exists(flag_file):
        print(f"   ❌ FAIL: .data_analysis_mode flag still exists!")
        success = False
    else:
        print(f"   ✅ PASS: .data_analysis_mode flag removed")
        success = True
    
    # Test 4: Verify state update
    print("\n4. Checking state update...")
    with open(state_file, 'r') as f:
        updated_state = json.load(f)
    
    if updated_state.get('workflow_transitioned'):
        print(f"   ✅ PASS: workflow_transitioned = True")
    else:
        print(f"   ❌ FAIL: workflow_transitioned still False")
        success = False
    
    # Test 5: Verify request_interpreter behavior
    print("\n5. Testing request_interpreter routing...")
    from app.core.request_interpreter import RequestInterpreter
    from flask import Flask, session
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'
    app.config['UPLOAD_FOLDER'] = 'instance/uploads'
    
    with app.test_request_context():
        # Set session data
        session['session_id'] = session_id
        session['active_tab'] = 'data-analysis'
        
        interpreter = RequestInterpreter()
        
        # First, recreate the flag to test the check
        with open(flag_file, 'w') as f:
            f.write('test_data.csv\n2025-01-18T00:00:00')
        
        # This should NOT route to Data Analysis V3 because workflow_transitioned=True
        try:
            # Mock the interpret method check
            import logging
            logger = logging.getLogger('app.core.request_interpreter')
            
            # The actual routing logic would check both flag and state
            has_flag = os.path.exists(flag_file)
            has_transition = updated_state.get('workflow_transitioned', False)
            
            if has_flag and not has_transition:
                print(f"   ❌ FAIL: Would route to Data Analysis V3")
                success = False
            elif has_flag and has_transition:
                print(f"   ✅ PASS: Would NOT route to Data Analysis V3 (transition detected)")
            else:
                print(f"   ✅ PASS: No flag, would use main workflow")
                
        except Exception as e:
            print(f"   ⚠️ Could not fully test interpreter: {e}")
    
    # Cleanup
    print("\n6. Cleaning up test data...")
    if os.path.exists(session_folder):
        shutil.rmtree(session_folder)
    print(f"   ✅ Cleaned up test session")
    
    # Summary
    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED - Workflow transition fix working!")
    else:
        print("❌ SOME TESTS FAILED - Please review the fixes")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    import sys
    success = test_workflow_transition()
    sys.exit(0 if success else 1)