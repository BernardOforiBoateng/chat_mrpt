#!/usr/bin/env python3
"""
Test the COMPLETE TPR flow including map visualization
"""

import asyncio
import sys
import os
sys.path.insert(0, '.')

async def test_complete_tpr_workflow():
    """Test the complete TPR workflow with map visualization."""
    
    from app.data_analysis_v3.core.agent import DataAnalysisAgent
    
    print("="*60)
    print("TESTING COMPLETE TPR WORKFLOW WITH MAP VISUALIZATION")
    print("="*60)
    
    # Create test session
    session_id = "test_tpr_map"
    
    # Create test directory and copy TPR file
    os.makedirs(f"instance/uploads/{session_id}", exist_ok=True)
    import shutil
    
    # Use a real TPR file
    test_files = [
        "www/tpr_data_by_state/ab_Abia_State_TPR_LLIN_2024.xlsx",
        "www/NMEP TPR and LLIN 2024_16072025.xlsx"
    ]
    
    test_file = None
    for file in test_files:
        if os.path.exists(file):
            test_file = file
            break
    
    if test_file:
        shutil.copy(test_file, f"instance/uploads/{session_id}/")
        print(f"✅ Test file copied: {os.path.basename(test_file)}")
    else:
        print("❌ No test file found")
        return
    
    # Initialize agent
    agent = DataAnalysisAgent(session_id)
    
    print("\n" + "="*60)
    print("STEP 1: INITIAL UPLOAD - USER CHOICE APPROACH")
    print("="*60)
    
    # Check initial data summary
    if hasattr(agent, 'data_summary') and agent.data_summary:
        print("\n📊 Initial Data Summary:")
        print("-" * 40)
        print(agent.data_summary[:500])
        
        # Verify user choices are shown
        if "What would you like to do?" in agent.data_summary:
            print("\n✅ User choices presented!")
        else:
            print("\n❌ User choices not shown")
    
    print("\n" + "="*60)
    print("STEP 2: SIMULATE TPR CALCULATION FLOW")
    print("="*60)
    
    # User chooses TPR calculation
    print("\n📤 User: 'Calculate TPR'")
    response = await agent.analyze("Calculate TPR")
    print(f"🤖 Agent: {response['message'][:300]}...")
    
    # Check stage progression
    if hasattr(agent, 'current_stage'):
        print(f"   Stage: {agent.current_stage.value}")
    
    # Select age group
    print("\n📤 User: 'All ages'")
    response = await agent.analyze("All ages")
    print(f"🤖 Agent: {response['message'][:300]}...")
    
    # Select test method
    print("\n📤 User: 'Both'")
    response = await agent.analyze("Both")
    print(f"🤖 Agent: {response['message'][:300]}...")
    
    # Select facility level - triggers calculation
    print("\n📤 User: 'All facilities'")
    response = await agent.analyze("All facilities")
    
    print("\n" + "="*60)
    print("STEP 3: CHECK TPR CALCULATION RESULTS")
    print("="*60)
    print(response['message'])
    
    # Check if TPR was calculated
    results_file = f"instance/uploads/{session_id}/tpr_results.csv"
    if os.path.exists(results_file):
        print("\n✅ TPR results file created")
        
        import pandas as pd
        results_df = pd.read_csv(results_file)
        print(f"   - {len(results_df)} wards analyzed")
        print(f"   - Average TPR: {results_df['TPR'].mean():.1f}%")
    else:
        print("\n❌ TPR results file not created")
    
    # Check if map was created
    map_file = f"instance/uploads/{session_id}/tpr_distribution_map.html"
    if os.path.exists(map_file):
        print("\n✅ TPR MAP VISUALIZATION CREATED!")
        print(f"   - Map file: {map_file}")
        
        # Check map file size
        size = os.path.getsize(map_file)
        print(f"   - Map size: {size:,} bytes")
        
        # Check if map contains expected elements
        with open(map_file, 'r') as f:
            content = f.read()
            if 'choropleth' in content.lower():
                print("   - ✅ Contains choropleth map")
            if 'TPR Distribution' in content:
                print("   - ✅ Has TPR Distribution title")
            if 'plotly' in content:
                print("   - ✅ Uses Plotly visualization")
    else:
        print("\n❌ TPR map not created")
    
    print("\n" + "="*60)
    print("STEP 4: TEST DATA EXPLORATION OPTION")
    print("="*60)
    
    # Reset agent for fresh conversation
    agent.reset()
    agent.current_stage = agent.ConversationStage.INITIAL
    
    print("\n📤 User: 'I want to explore my data'")
    response = await agent.analyze("I want to explore my data")
    print(f"🤖 Agent: {response['message'][:400]}...")
    
    # Verify agent doesn't force TPR
    if "age group" not in response['message'].lower():
        print("✅ Not forcing TPR flow - respects user choice")
    else:
        print("❌ Still asking TPR questions when user wants exploration")
    
    # Clean up
    shutil.rmtree(f"instance/uploads/{session_id}", ignore_errors=True)
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    
    return True

if __name__ == "__main__":
    print("🧪 Testing Complete TPR Workflow with Map Visualization")
    
    # Activate virtual environment
    import subprocess
    result = subprocess.run(
        ["source", "chatmrpt_venv_new/bin/activate"], 
        shell=True, 
        capture_output=True
    )
    
    try:
        asyncio.run(test_complete_tpr_workflow())
        print("\n✅ Complete workflow test finished!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()