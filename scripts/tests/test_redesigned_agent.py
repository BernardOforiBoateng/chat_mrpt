#!/usr/bin/env python3
"""
Test the redesigned user-choice driven agent
"""

import asyncio
import sys
import os
sys.path.insert(0, '.')

async def test_redesigned_agent():
    """Test the redesigned agent with user choices."""
    
    from app.data_analysis_v3.core.agent_redesigned import DataAnalysisAgent, UserIntent
    
    # Create test session
    session_id = "test_redesign"
    
    # Create test directory and copy TPR file
    os.makedirs(f"instance/uploads/{session_id}", exist_ok=True)
    import shutil
    test_file = "www/tpr_data_by_state/ab_Abia_State_TPR_LLIN_2024.xlsx"
    if os.path.exists(test_file):
        shutil.copy(test_file, f"instance/uploads/{session_id}/")
        print("✅ Test file copied")
    else:
        print(f"⚠️ Test file not found at {test_file}")
    
    # Initialize agent
    agent = DataAnalysisAgent(session_id)
    
    print("="*60)
    print("TESTING REDESIGNED AGENT")
    print("="*60)
    
    # Test 1: Check initial data summary
    print("\n1. Initial Data Summary:")
    print("-" * 40)
    if agent.data_summary:
        print(agent.data_summary[:800])
        
        # Check key elements
        if "What would you like to do?" in agent.data_summary:
            print("\n✅ Shows user choices!")
        else:
            print("\n❌ Missing user choices")
            
        if "224 wards" in agent.data_summary:
            print("✅ Shows correct ward count!")
        else:
            print("❌ Wrong ward count")
    else:
        print("❌ No data summary generated")
    
    # Test 2: Intent Detection
    print("\n\n2. Testing Intent Detection:")
    print("-" * 40)
    
    test_phrases = [
        ("calculate TPR", UserIntent.TPR_CALCULATION),
        ("test positivity rate", UserIntent.TPR_CALCULATION),
        ("2", UserIntent.TPR_CALCULATION),
        ("explore the data", UserIntent.DATA_EXPLORATION),
        ("show patterns", UserIntent.DATA_EXPLORATION),
        ("1", UserIntent.DATA_EXPLORATION),
        ("quick overview", UserIntent.QUICK_OVERVIEW),
        ("3", UserIntent.QUICK_OVERVIEW),
        ("hello", UserIntent.UNCLEAR)
    ]
    
    for phrase, expected in test_phrases:
        detected = agent._detect_user_intent(phrase)
        icon = "✅" if detected == expected else "❌"
        print(f"{icon} '{phrase}' -> {detected.value} (expected: {expected.value})")
    
    # Test 3: TPR Flow
    print("\n\n3. Testing TPR Flow:")
    print("-" * 40)
    
    # Start TPR flow
    response = agent._start_tpr_flow()
    print("Starting TPR flow:")
    print(response[:200] + "...")
    
    # Select age group
    response = agent._handle_tpr_age_selection("under 5")
    if "Under 5 years" in response and "test method" in response:
        print("\n✅ Age selection works, moved to test method")
    else:
        print("\n❌ Age selection failed")
    
    # Select test method
    response = agent._handle_tpr_test_selection("RDT")
    if "RDT only" in response and "facilities" in response:
        print("✅ Test method selection works, moved to facilities")
    else:
        print("❌ Test method selection failed")
    
    # Select facilities
    response = agent._handle_tpr_facility_selection("all")
    if "All facilities" in response and "complete" in response:
        print("✅ Facility selection works, ready to calculate")
    else:
        print("❌ Facility selection failed")
    
    # Check selections stored
    print(f"\nTPR Selections: {agent.tpr_selections}")
    if agent.tpr_selections == {'age_group': 'under_5', 'test_method': 'rdt', 'facility_level': 'all'}:
        print("✅ All selections stored correctly!")
    else:
        print("❌ Selections not stored correctly")
    
    # Test 4: Full conversation flow
    print("\n\n4. Testing Full Conversation:")
    print("-" * 40)
    
    # Reset agent
    agent.reset()
    
    # Simulate user asking "What's in my data?"
    response = await agent.analyze("What's in my data?")
    print(f"User: 'What's in my data?'")
    print(f"Agent: {response['message'][:300]}...")
    
    if "What would you like to do?" in response['message']:
        print("\n✅ Shows options on first query!")
    
    # User chooses TPR
    response = await agent.analyze("I want to calculate TPR")
    print(f"\nUser: 'I want to calculate TPR'")
    print(f"Agent: {response['message'][:200]}...")
    
    if "age group" in response['message'].lower():
        print("✅ Started TPR flow!")
    
    # Clean up
    shutil.rmtree(f"instance/uploads/{session_id}", ignore_errors=True)
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    
    return True

if __name__ == "__main__":
    print("🧪 Testing Redesigned Agent")
    
    try:
        asyncio.run(test_redesigned_agent())
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()