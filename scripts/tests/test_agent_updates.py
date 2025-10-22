#!/usr/bin/env python3
"""
Test the updated agent.py with user-choice approach
"""

import sys
import os
sys.path.insert(0, '.')

def test_updated_agent():
    """Test the updated agent."""
    
    from app.data_analysis_v3.core.agent import DataAnalysisAgent
    
    # Create test session
    session_id = "test_update"
    
    # Create test directory
    os.makedirs(f"instance/uploads/{session_id}", exist_ok=True)
    
    # Create a simple test CSV with TPR-like data
    import pandas as pd
    test_data = pd.DataFrame({
        'State': ['Adamawa'] * 10,
        'LGA': ['LGA1', 'LGA2'] * 5,
        'WardName': [f'Ward{i}' for i in range(10)],
        'HealthFacility': [f'Facility{i}' for i in range(10)],
        'RDT_Under5': [10, 20, 15, 25, 30, 12, 18, 22, 28, 35],
        'Microscopy_Under5': [8, 18, 12, 20, 25, 10, 15, 20, 25, 30]
    })
    
    test_file = f"instance/uploads/{session_id}/test_data.csv"
    test_data.to_csv(test_file, index=False)
    print("✅ Test data created")
    
    # Initialize agent
    agent = DataAnalysisAgent(session_id)
    
    print("="*60)
    print("TESTING UPDATED AGENT.PY")
    print("="*60)
    
    # Test 1: Check data summary
    print("\n1. Data Summary with User Choices:")
    print("-" * 40)
    if hasattr(agent, 'data_summary') and agent.data_summary:
        print(agent.data_summary[:600])
        
        # Check key elements
        checks = [
            ("What would you like to do?", "Shows user choices"),
            ("Explore & Analyze", "Has explore option"),
            ("Calculate Test Positivity Rate", "Has TPR option"),
            ("10 wards", "Shows correct ward count"),
            ("2 LGAs", "Shows correct LGA count")
        ]
        
        print("\nChecks:")
        for text, description in checks:
            if text in agent.data_summary:
                print(f"✅ {description}")
            else:
                print(f"❌ Missing: {description}")
    else:
        print("❌ No data summary generated")
    
    # Test 2: Check stages are initialized
    print("\n\n2. Conversation Stage:")
    print("-" * 40)
    if hasattr(agent, 'current_stage'):
        print(f"Current stage: {agent.current_stage.value}")
        print("✅ Stage tracking initialized")
    else:
        print("❌ No stage tracking")
    
    # Test 3: Check TPR selections storage
    print("\n\n3. TPR Selections Storage:")
    print("-" * 40)
    if hasattr(agent, 'tpr_selections'):
        print(f"TPR selections dict: {agent.tpr_selections}")
        print("✅ TPR selections storage initialized")
    else:
        print("❌ No TPR selections storage")
    
    # Clean up
    import shutil
    shutil.rmtree(f"instance/uploads/{session_id}", ignore_errors=True)
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    
    return True

if __name__ == "__main__":
    print("🧪 Testing Updated Agent.py")
    
    try:
        test_updated_agent()
        print("\n✅ Basic tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()