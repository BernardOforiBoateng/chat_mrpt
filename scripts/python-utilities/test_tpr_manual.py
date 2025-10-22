#!/usr/bin/env python3
"""
Manual test for TPR transition.
Simulates the exact flow needed to complete TPR and trigger transition.
"""

import os
import sys
import time
from pathlib import Path

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_tpr_transition_manually():
    """Manually test the TPR transition by calling the agent directly."""
    
    # Create a test session
    session_id = f"test_session_{int(time.time())}"
    session_folder = Path(f"instance/uploads/{session_id}")
    session_folder.mkdir(parents=True, exist_ok=True)
    
    print(f"🧪 Testing TPR Transition Manually")
    print(f"Session ID: {session_id}")
    print("=" * 50)
    
    # Step 1: Create the waiting flag (simulating TPR completion)
    print("\n1️⃣ Simulating TPR completion...")
    waiting_flag = session_folder / '.tpr_waiting_confirmation'
    waiting_flag.touch()
    print(f"✅ Created waiting flag: {waiting_flag}")
    
    # Step 2: Create sample data files
    raw_data = session_folder / 'raw_data.csv'
    raw_data.write_text("Ward,TPR,Total_Tested\nWard1,25.0,100\nWard2,30.0,150")
    print(f"✅ Created raw_data.csv")
    
    # Step 3: Test the agent's response to "yes"
    print("\n2️⃣ Testing agent response to 'yes'...")
    
    from app.data_analysis_v3.core.agent import DataAnalysisAgent
    agent = DataAnalysisAgent(session_id)
    
    # Call the transition check directly
    result = agent._check_tpr_transition("yes")
    
    if result:
        print("\n📊 Agent Response:")
        print(f"  - Success: {result.get('success', False)}")
        print(f"  - Trigger Analysis: {result.get('trigger_analysis', False)}")
        print(f"  - Exit Data Analysis Mode: {result.get('exit_data_analysis_mode', False)}")
        print(f"  - Redirect Message: {result.get('redirect_message', 'None')}")
        
        # Check if all flags are present
        if (result.get('success') and 
            result.get('trigger_analysis') and 
            result.get('exit_data_analysis_mode') and 
            result.get('redirect_message')):
            print("\n✅ SUCCESS: All transition flags are properly set!")
            
            # Check if waiting flag was removed
            if not waiting_flag.exists():
                print("✅ Waiting flag was correctly removed")
            else:
                print("⚠️ Waiting flag still exists (should be removed)")
                
        else:
            print("\n❌ FAILURE: Some flags are missing")
            if not result.get('exit_data_analysis_mode'):
                print("  - Missing exit_data_analysis_mode")
            if not result.get('redirect_message'):
                print("  - Missing redirect_message")
    else:
        print("❌ Agent returned None (transition not handled)")
    
    # Cleanup
    print("\n3️⃣ Cleaning up test session...")
    import shutil
    if session_folder.exists():
        shutil.rmtree(session_folder)
        print("✅ Test session cleaned up")

if __name__ == "__main__":
    try:
        test_tpr_transition_manually()
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()