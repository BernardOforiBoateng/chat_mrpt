#!/usr/bin/env python
"""Test TPR workflow to diagnose the issue."""

import os
import sys
import json
import shutil
sys.path.insert(0, '.')

from app.data_analysis_v3.core.state_manager import DataAnalysisStateManager
from app.data_analysis_v3.core.tpr_workflow_handler import TPRWorkflowHandler, ConversationStage
from app.data_analysis_v3.core.tpr_data_analyzer import TPRDataAnalyzer
from app.data_analysis_v3.core.encoding_handler import EncodingHandler

# Test session
session_id = "test_tpr_session"
session_dir = f"instance/uploads/{session_id}"

# Clean up and create test directory
if os.path.exists(session_dir):
    shutil.rmtree(session_dir)
os.makedirs(session_dir, exist_ok=True)

# Copy test data
test_data_path = "app/sample_data/sample_malaria_data.csv"
if os.path.exists(test_data_path):
    shutil.copy(test_data_path, os.path.join(session_dir, "test_data.csv"))
else:
    print("Warning: No test data found")

# Initialize components
state_manager = DataAnalysisStateManager(session_id)
tpr_analyzer = TPRDataAnalyzer()
tpr_handler = TPRWorkflowHandler(session_id, state_manager, tpr_analyzer)

# Load data
data_file = os.path.join(session_dir, "test_data.csv")
if os.path.exists(data_file):
    data = EncodingHandler.read_csv_with_encoding(data_file)
    tpr_handler.set_data(data)
    print(f"Loaded {len(data)} rows of data")
else:
    print("ERROR: No data file found")
    sys.exit(1)

# Start TPR workflow
print("\n=== Starting TPR Workflow ===")
result = tpr_handler.start_workflow()
print(f"Start result: success={result.get('success')}, stage={result.get('stage')}")
print(f"Current stage after start: {tpr_handler.current_stage}")

# If single state, we go directly to facility selection
if result.get('stage') == 'facility_selection':
    print("\n=== Selecting Facility: 'primary' ===")
    
    # Save current stage to state file
    state_manager.update_workflow_stage(ConversationStage.TPR_FACILITY_LEVEL)
    
    # Simulate selecting primary facility
    result = tpr_handler.handle_workflow("primary")
    print(f"Facility result: success={result.get('success')}, stage={result.get('stage')}")
    print(f"Current stage after facility: {tpr_handler.current_stage}")
    print(f"Response message preview: {result.get('message', '')[:200]}")
    
    # Check if stage was properly updated
    saved_stage = state_manager.get_workflow_stage()
    print(f"Stage saved in state manager: {saved_stage}")
    
    # Check the early return condition
    if result.get('stage') == 'age_selection' or result.get('require_input'):
        print("\n✅ CORRECT: Would return early for age selection")
    else:
        print("\n❌ ERROR: Would NOT return early - this is the bug!")
        
    # Now simulate what happens if another worker picks this up
    print("\n=== Simulating New Worker ===")
    
    # Create new handler (simulating different worker)
    new_handler = TPRWorkflowHandler(session_id, state_manager, tpr_analyzer)
    
    # Restore state
    current_stage = state_manager.get_workflow_stage()
    new_handler.current_stage = current_stage
    print(f"New worker restored stage: {current_stage}")
    
    # Restore selections
    state = state_manager.get_state()
    if 'tpr_selections' in state:
        new_handler.tpr_selections = state['tpr_selections']
        print(f"New worker restored selections: {new_handler.tpr_selections}")
    
    # Load data for new worker
    new_handler.set_data(data)
    
    # Try processing the same "primary" message again
    print("\n=== New Worker Processing 'primary' ===")
    result2 = new_handler.handle_workflow("primary")
    print(f"New worker result: success={result2.get('success')}, stage={result2.get('stage')}")
    print(f"New worker stage after: {new_handler.current_stage}")
    
else:
    print("Multiple states detected, would need state selection first")

# Clean up
if os.path.exists(session_dir):
    shutil.rmtree(session_dir)
print("\nTest complete.")