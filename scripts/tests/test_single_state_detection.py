#!/usr/bin/env python
"""
Test single state detection in TPR workflow
"""

import pandas as pd
import numpy as np
import sys
import os
sys.path.insert(0, '.')

from app.data_analysis_v3.core.tpr_data_analyzer import TPRDataAnalyzer
from app.data_analysis_v3.core.agent import DataAnalysisAgent

# Create test data with single state
def create_single_state_data():
    """Create test data with only one state."""
    data = {
        'State': ['Adamawa'] * 50,  # Only one state
        'HealthFacility': [f'Facility_{i}' for i in range(50)],
        'FacilityLevel': ['Primary'] * 30 + ['Secondary'] * 15 + ['Tertiary'] * 5,
        'Persons presenting with fever & tested by RDT <5yrs': np.random.randint(10, 100, 50),
        'Persons presenting with fever & tested positive by RDT <5yrs': np.random.randint(5, 50, 50),
    }
    return pd.DataFrame(data)

# Create test data with multiple states
def create_multi_state_data():
    """Create test data with multiple states."""
    data = {
        'State': ['Adamawa'] * 30 + ['Kwara'] * 30 + ['Osun'] * 30,
        'HealthFacility': [f'Facility_{i}' for i in range(90)],
        'FacilityLevel': ['Primary'] * 50 + ['Secondary'] * 30 + ['Tertiary'] * 10,
        'Persons presenting with fever & tested by RDT <5yrs': np.random.randint(10, 100, 90),
        'Persons presenting with fever & tested positive by RDT <5yrs': np.random.randint(5, 50, 90),
    }
    return pd.DataFrame(data)

def test_single_state():
    """Test single state detection."""
    print("="*60)
    print("Testing Single State Detection")
    print("="*60)
    
    # Create analyzer
    analyzer = TPRDataAnalyzer()
    
    # Test with single state data
    single_state_df = create_single_state_data()
    result = analyzer.analyze_states(single_state_df)
    
    print(f"\nSingle state data analysis:")
    print(f"Total states: {result['total_states']}")
    print(f"States found: {list(result['states'].keys())}")
    
    if result['total_states'] == 1:
        print("✅ Single state correctly detected!")
    else:
        print("❌ Single state not detected")
    
    # Test with multi-state data
    multi_state_df = create_multi_state_data()
    result = analyzer.analyze_states(multi_state_df)
    
    print(f"\nMulti-state data analysis:")
    print(f"Total states: {result['total_states']}")
    print(f"States found: {list(result['states'].keys())}")
    
    if result['total_states'] == 3:
        print("✅ Multiple states correctly detected!")
    else:
        print("❌ Multiple states not detected")

def test_agent_workflow():
    """Test agent workflow with single state."""
    print("\n" + "="*60)
    print("Testing Agent Workflow with Single State")
    print("="*60)
    
    # Create agent
    agent = DataAnalysisAgent("test_session")
    
    # Set single state data
    agent.uploaded_data = create_single_state_data()
    
    # Start TPR workflow
    response = agent._start_tpr_workflow()
    
    print(f"\nWorkflow stage: {response.get('stage')}")
    print(f"Message preview: {response['message'][:200]}...")
    
    if response.get('stage') == 'facility_selection':
        print("✅ Correctly skipped to facility selection!")
    else:
        print("❌ Did not skip state selection")
    
    # Check if state was auto-selected
    if agent.tpr_selections.get('state') == 'Adamawa':
        print("✅ State was auto-selected!")
    else:
        print("❌ State was not auto-selected")

if __name__ == "__main__":
    test_single_state()
    test_agent_workflow()