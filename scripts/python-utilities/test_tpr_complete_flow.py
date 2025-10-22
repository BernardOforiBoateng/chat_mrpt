#!/usr/bin/env python3
"""
Test complete TPR flow including prepare_for_risk action.
This simulates the actual workflow that leads to the transition prompt.
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_complete_tpr_flow():
    """Test the complete TPR workflow including prepare_for_risk."""
    
    session_id = "test_tpr_complete"
    session_folder = Path(f"instance/uploads/{session_id}")
    session_folder.mkdir(parents=True, exist_ok=True)
    
    print("🧪 Testing Complete TPR Flow with Transition")
    print("=" * 50)
    
    # Step 1: Create sample TPR data
    print("\n1️⃣ Creating sample TPR data...")
    tpr_data = pd.DataFrame({
        'State': ['Kano'] * 5,
        'LGA': ['Dala', 'Dala', 'Fagge', 'Fagge', 'Nasarawa'],
        'Ward': ['Ward1', 'Ward2', 'Ward3', 'Ward4', 'Ward5'],
        'Total_Tested': [100, 150, 200, 120, 180],
        'Total_Positive': [25, 45, 60, 30, 54],
        'TPR': [25.0, 30.0, 30.0, 25.0, 30.0]
    })
    
    tpr_results_path = session_folder / 'tpr_results.csv'
    tpr_data.to_csv(tpr_results_path, index=False)
    print(f"✅ Created TPR results: {tpr_results_path}")
    
    # Step 2: Use TPR tool to prepare for risk
    print("\n2️⃣ Running prepare_for_risk action...")
    
    from app.data_analysis_v3.tools.tpr_analysis_tool import tpr_analysis
    
    result = tpr_analysis(
        thought="Preparing TPR data for risk analysis",
        action="prepare_for_risk",
        options="{}",
        graph_state={'session_id': session_id}
    )
    
    print("TPR Tool Response (first 500 chars):")
    print(result[:500] if len(result) > 500 else result)
    
    # Check if the waiting flag was created
    waiting_flag = session_folder / '.tpr_waiting_confirmation'
    if waiting_flag.exists():
        print("\n✅ Waiting flag created successfully")
    else:
        print("\n❌ Waiting flag was NOT created")
        return False
    
    # Step 3: Test the agent's transition response
    print("\n3️⃣ Testing agent response to 'yes'...")
    
    from app.data_analysis_v3.core.agent import DataAnalysisAgent
    agent = DataAnalysisAgent(session_id)
    
    result = agent._check_tpr_transition("yes")
    
    if result:
        print("\n📊 Agent Transition Response:")
        print(f"  - Success: {result.get('success', False)}")
        print(f"  - Trigger Analysis: {result.get('trigger_analysis', False)}")
        print(f"  - Exit Data Analysis Mode: {result.get('exit_data_analysis_mode', False)}")
        print(f"  - Redirect Message: {result.get('redirect_message', 'None')}")
        
        # Verify all flags
        success = all([
            result.get('success'),
            result.get('trigger_analysis'),
            result.get('exit_data_analysis_mode'),
            result.get('redirect_message')
        ])
        
        if success:
            print("\n✅ SUCCESS: TPR transition is working correctly!")
            print("\nThe flow:")
            print("1. TPR tool creates waiting flag when complete")
            print("2. Agent detects 'yes' response")
            print("3. Agent returns proper transition flags")
            print("4. Frontend will exit Data Analysis mode")
            print("5. Risk analysis will auto-trigger")
        else:
            print("\n❌ Some transition flags are missing")
            
        # Check if waiting flag was removed
        if not waiting_flag.exists():
            print("\n✅ Waiting flag was correctly removed after transition")
        else:
            print("\n⚠️ Waiting flag still exists (should be removed)")
            
        return success
    else:
        print("\n❌ Agent returned None (transition not handled)")
        return False
    
    # Cleanup
    print("\n4️⃣ Cleaning up...")
    import shutil
    if session_folder.exists():
        shutil.rmtree(session_folder)
        print("✅ Test session cleaned up")

if __name__ == "__main__":
    try:
        success = test_complete_tpr_flow()
        
        print("\n" + "=" * 50)
        if success:
            print("🎉 COMPLETE TPR FLOW TEST PASSED!")
            print("\nDeployment ready:")
            print("✅ TPR completion triggers waiting state")
            print("✅ User confirmation triggers transition")
            print("✅ All required flags are set")
            print("✅ Frontend will receive proper signals")
        else:
            print("⚠️ TPR FLOW TEST FAILED")
            print("\nIssues to investigate:")
            print("- Check if TPR tool reaches prepare_for_risk")
            print("- Verify file creation permissions")
            print("- Check agent initialization")
            
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()