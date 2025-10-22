#!/usr/bin/env python
"""Simple test to check TPR workflow facility->age flow."""

import os
import sys
import json
import tempfile
sys.path.insert(0, '.')

# Create test data
test_data = """State,LGA,Ward,facility_level,age_group,tests_conducted,positive_cases
Kano,Municipal,Ward1,Primary,Under5,100,20
Kano,Municipal,Ward1,Primary,5-14,150,25
Kano,Municipal,Ward1,Primary,15+,200,30
Kano,Municipal,Ward1,Secondary,Under5,80,15
Kano,Municipal,Ward2,Primary,Under5,120,18
Kano,Municipal,Ward2,Primary,5-14,90,12
"""

# Setup test session
session_id = "test_session_123"
session_dir = f"instance/uploads/{session_id}"
os.makedirs(session_dir, exist_ok=True)

# Write test data
data_file = os.path.join(session_dir, "test_data.csv")
with open(data_file, 'w') as f:
    f.write(test_data)

print(f"Created test data at {data_file}")

# Import after setup
from app.data_analysis_v3.core.state_manager import DataAnalysisStateManager
from app.data_analysis_v3.core.tpr_workflow_handler import TPRWorkflowHandler, ConversationStage
from app.data_analysis_v3.core.tpr_data_analyzer import TPRDataAnalyzer
from app.data_analysis_v3.core.encoding_handler import EncodingHandler

# Initialize
state_manager = DataAnalysisStateManager(session_id)
tpr_analyzer = TPRDataAnalyzer()
tpr_handler = TPRWorkflowHandler(session_id, state_manager, tpr_analyzer)

# Load data
data = EncodingHandler.read_csv_with_encoding(data_file)
tpr_handler.set_data(data)
print(f"Loaded {len(data)} rows")

# Start workflow
print("\n=== Starting TPR Workflow ===")
result = tpr_handler.start_workflow()
print(f"Stage after start: {result.get('stage')}")
print(f"Current stage: {tpr_handler.current_stage}")

# Should be at facility selection (single state auto-selected)
if result.get('stage') == 'facility_selection':
    print("\n=== Selecting Facility: 'primary' ===")
    
    # This should move to age selection
    result = tpr_handler.handle_workflow("primary")
    print(f"Result stage: {result.get('stage')}")
    print(f"Current stage: {tpr_handler.current_stage}")
    print(f"Stage should be 'age_selection': {result.get('stage') == 'age_selection'}")
    
    # Check the condition that would stop processing
    if result.get('stage') == 'age_selection' or result.get('require_input'):
        print("✅ Would return early - CORRECT")
    else:
        print("❌ Would NOT return early - BUG!")
    
    # Now simulate what happens if we send "primary" again
    print("\n=== Sending 'primary' AGAIN (simulating double-send) ===")
    saved_stage = state_manager.get_workflow_stage()
    print(f"Stage before second call: {saved_stage}")
    
    result2 = tpr_handler.handle_workflow("primary")
    print(f"Result stage after double-send: {result2.get('stage')}")
    print(f"Current stage after double-send: {tpr_handler.current_stage}")
    
    # What should happen: Since we're at TPR_AGE_GROUP, "primary" might be interpreted as an age group!
    if "calculate" in str(result2.get('message', '')).lower():
        print("❌ BUG CONFIRMED: Double-send caused it to jump to calculation!")
    elif result2.get('stage') == 'age_selection':
        print("✅ Still at age selection - handled correctly")
    else:
        print(f"🤔 Unexpected result: {result2.get('stage')}")

# Cleanup
import shutil
shutil.rmtree(session_dir)
print("\nTest complete.")