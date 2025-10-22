#!/usr/bin/env python
"""
Test the integrated TPR workflow with tool
"""

import sys
import os
import json
import pandas as pd
import numpy as np
sys.path.insert(0, '.')

from app.data_analysis_v3.core.agent import DataAnalysisAgent

# Create test data
def create_test_data():
    """Create test TPR data."""
    data = {
        'orgunitlevel2': ['Adamawa State'] * 50,
        'orgunitlevel3': [f'LGA_{i%5}' for i in range(50)],
        'orgunitlevel4': [f'Ward_{i}' for i in range(50)],
        'orgunitlevel5': [f'Facility_{i}' for i in range(50)],
        'Persons presenting with fever & tested by RDT <5yrs': np.random.randint(10, 100, 50),
        'Persons tested positive for malaria by RDT <5yrs': np.random.randint(5, 50, 50),
        'Persons presenting with fever and tested by Microscopy <5yrs': np.random.randint(5, 50, 50),
        'Persons tested positive for malaria by Microscopy <5yrs': np.random.randint(2, 25, 50),
    }
    return pd.DataFrame(data)

def test_integrated_workflow():
    """Test the integrated TPR workflow."""
    print("="*60)
    print("Testing Integrated TPR Workflow with Tool")
    print("="*60)
    
    # Create test session
    session_id = "test_integrated_tpr"
    session_dir = f"instance/uploads/{session_id}"
    os.makedirs(session_dir, exist_ok=True)
    
    # Save test data
    test_data = create_test_data()
    data_path = os.path.join(session_dir, "uploaded_data.csv")
    test_data.to_csv(data_path, index=False)
    print(f"\n✅ Test data saved to {data_path}")
    
    # Create agent
    agent = DataAnalysisAgent(session_id)
    agent.uploaded_data = test_data
    
    # Start TPR workflow
    print("\n1. Starting TPR workflow...")
    response = agent._start_tpr_workflow()
    print(f"   Stage: {response.get('stage')}")
    
    # Since we have single state, should skip to facility
    if response.get('stage') == 'facility_selection':
        print("   ✅ Single state detected, skipped to facility selection")
    
    # Select facility level
    print("\n2. Selecting facility level: all...")
    response = agent._handle_facility_selection("all")
    if response.get('stage') == 'age_selection':
        print("   ✅ Moved to age group selection")
    
    # Select age group
    print("\n3. Selecting age group: under 5...")
    response = agent._handle_age_group_selection("under 5")
    
    # Check the response
    print("\n4. Checking results...")
    message = response.get('message', '')
    
    # Print first part of message for debugging
    print(f"   Message preview: {message[:200]}...")
    
    # Check for key indicators
    if "TPR Calculation Complete" in message:
        print("   ✅ TPR calculation completed")
    else:
        print("   ❌ TPR calculation may have failed")
    
    if "Average TPR" in message:
        print("   ✅ Statistics displayed")
    
    if "Map Created" in message:
        print("   ✅ Map generation mentioned")
    
    if "Results Saved" in message:
        print("   ✅ Results saved")
    
    # Check if files were created
    print("\n5. Checking output files...")
    
    # Check for TPR results CSV
    results_file = os.path.join(session_dir, "tpr_results.csv")
    if os.path.exists(results_file):
        print(f"   ✅ TPR results saved: {results_file}")
        results_df = pd.read_csv(results_file)
        print(f"      - {len(results_df)} wards")
        print(f"      - Average TPR: {results_df['TPR'].mean():.1f}%")
    else:
        print("   ❌ TPR results file not found")
    
    # Check for map
    map_file = os.path.join(session_dir, "tpr_distribution_map.html")
    if os.path.exists(map_file):
        print(f"   ✅ TPR map created: {map_file}")
    else:
        print("   ⚠️ TPR map not found (might be OK if no shapefile)")
    
    print("\n" + "="*60)
    print("Integration test complete!")
    print("="*60)

if __name__ == "__main__":
    test_integrated_workflow()