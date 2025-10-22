#!/usr/bin/env python
"""
Test the TPR tool directly
"""

import sys
import os
import json
sys.path.insert(0, '.')

from app.data_analysis_v3.tools.tpr_analysis_tool import analyze_tpr_data

# Test the tool directly
session_id = "test_integrated_tpr"
graph_state = {
    'session_id': session_id,
    'data_loaded': True,
    'data_file': f"instance/uploads/{session_id}/uploaded_data.csv"
}

options = {
    'age_group': 'u5',
    'facility_level': 'all',
    'test_method': 'both'
}

print("Testing TPR tool directly...")
print(f"Session: {session_id}")
print(f"Options: {options}")

# Call the tool
result = analyze_tpr_data.invoke({
    'thought': "Testing TPR calculation",
    'action': "calculate_tpr",
    'options': json.dumps(options),
    'graph_state': graph_state
})

print("\n" + "="*60)
print("TOOL RESULT:")
print("="*60)
print(result[:1000] if len(result) > 1000 else result)

# Check for files
session_folder = f"instance/uploads/{session_id}"
print("\n" + "="*60)
print("FILES CREATED:")
print("="*60)

for file in os.listdir(session_folder):
    file_path = os.path.join(session_folder, file)
    size = os.path.getsize(file_path)
    print(f"  {file}: {size} bytes")