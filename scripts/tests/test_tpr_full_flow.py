#!/usr/bin/env python3
"""
Test the COMPLETE TPR flow including actual calculation
"""

import asyncio
import sys
import os
sys.path.insert(0, '.')

async def test_full_tpr_flow():
    """Test the complete TPR conversation and calculation flow."""
    
    from app.data_analysis_v3.core.agent_redesigned import DataAnalysisAgent
    
    print("="*60)
    print("TESTING COMPLETE TPR FLOW WITH CALCULATION")
    print("="*60)
    
    # Create test session
    session_id = "test_tpr_complete"
    
    # Create test directory and copy TPR file
    os.makedirs(f"instance/uploads/{session_id}", exist_ok=True)
    import shutil
    test_file = "www/tpr_data_by_state/ab_Abia_State_TPR_LLIN_2024.xlsx"
    if os.path.exists(test_file):
        shutil.copy(test_file, f"instance/uploads/{session_id}/")
        print("✅ Test file copied (Abia State TPR data)")
    else:
        print(f"❌ Test file not found at {test_file}")
        return
    
    # Initialize agent
    agent = DataAnalysisAgent(session_id)
    
    # Simulate complete conversation
    print("\n" + "="*60)
    print("SIMULATING USER CONVERSATION")
    print("="*60)
    
    # Step 1: User uploads and asks what's in the data
    print("\n📤 User: 'What's in my data?'")
    response = await agent.analyze("What's in my data?")
    print(f"🤖 Agent: {response['message'][:400]}...")
    
    # Verify we see options
    if "What would you like to do?" in response['message']:
        print("✅ Shows user choices!")
    else:
        print("❌ Missing user choices")
    
    # Step 2: User chooses to calculate TPR
    print("\n📤 User: 'I want to calculate TPR'")
    response = await agent.analyze("I want to calculate TPR")
    print(f"🤖 Agent: {response['message'][:300]}...")
    
    # Verify TPR flow started
    if "age group" in response['message'].lower():
        print("✅ TPR flow started - asking for age group")
    else:
        print("❌ TPR flow not started properly")
    
    # Step 3: User selects age group
    print("\n📤 User: 'Under 5 years'")
    response = await agent.analyze("Under 5 years")
    print(f"🤖 Agent: {response['message'][:300]}...")
    
    # Verify moved to test method
    if "test method" in response['message'].lower():
        print("✅ Moved to test method selection")
    else:
        print("❌ Did not progress to test method")
    
    # Step 4: User selects test method
    print("\n📤 User: 'RDT only'")
    response = await agent.analyze("RDT only")
    print(f"🤖 Agent: {response['message'][:300]}...")
    
    # Verify moved to facility level
    if "facilities" in response['message'].lower():
        print("✅ Moved to facility level selection")
    else:
        print("❌ Did not progress to facility level")
    
    # Step 5: User selects facility level - THIS TRIGGERS CALCULATION
    print("\n📤 User: 'All facilities'")
    response = await agent.analyze("All facilities")
    print(f"🤖 Agent Response:")
    print("-" * 40)
    print(response['message'])
    print("-" * 40)
    
    # Verify calculation happened
    if "TPR Calculation Complete" in response['message']:
        print("\n✅ TPR CALCULATION PERFORMED!")
        
        # Check for key results
        if "Average TPR:" in response['message']:
            print("✅ Shows average TPR")
        if "Highest TPR:" in response['message']:
            print("✅ Shows highest TPR")
        if "Top 5 Highest TPR Wards:" in response['message']:
            print("✅ Shows top wards")
        if "tpr_results.csv" in response['message']:
            print("✅ Results saved to file")
    else:
        print("\n❌ TPR calculation did not complete")
    
    # Check if results file was created
    results_file = f"instance/uploads/{session_id}/tpr_results.csv"
    if os.path.exists(results_file):
        print(f"\n✅ Results file created: {results_file}")
        
        # Load and check the results
        import pandas as pd
        results_df = pd.read_csv(results_file)
        print(f"   - Contains {len(results_df)} ward results")
        print(f"   - Columns: {list(results_df.columns)[:5]}")
        
        if 'TPR' in results_df.columns:
            avg_tpr = results_df['TPR'].mean() * 100
            print(f"   - Average TPR: {avg_tpr:.1f}%")
    else:
        print(f"\n❌ Results file not created")
    
    # Step 6: Test continuing conversation
    print("\n📤 User: 'What next?'")
    response = await agent.analyze("What next?")
    print(f"🤖 Agent: {response['message'][:200]}...")
    
    # Verify we can continue
    if "prepare for risk analysis" in response['message'].lower() or "What would you like to do?" in response['message']:
        print("✅ Can continue with next steps")
    else:
        print("⚠️ Next steps not clear")
    
    # Clean up
    shutil.rmtree(f"instance/uploads/{session_id}", ignore_errors=True)
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    
    return True

if __name__ == "__main__":
    print("🧪 Testing Complete TPR Flow with Calculation")
    
    try:
        # Activate virtual environment first if needed
        import subprocess
        result = subprocess.run(
            ["source", "chatmrpt_venv_new/bin/activate"], 
            shell=True, 
            capture_output=True
        )
        
        asyncio.run(test_full_tpr_flow())
        print("\n✅ Full TPR flow test completed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()