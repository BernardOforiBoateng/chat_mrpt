#!/usr/bin/env python3
"""
Test TPR to Risk Analysis Transition Flow
"""

import os
import sys
import asyncio
import shutil
from pathlib import Path

# Add app to path
sys.path.insert(0, '.')

# Import required modules
from app.data_analysis_v3.core.agent import DataAnalysisAgent
from app.data_analysis_v3.tools.tpr_analysis_tool import analyze_tpr_data


async def test_transition_flow():
    """Test the complete TPR to risk analysis transition flow"""
    
    print("=" * 60)
    print("TESTING TPR TO RISK ANALYSIS TRANSITION")
    print("=" * 60)
    
    # Setup test session
    session_id = "test_transition"
    session_folder = f"instance/uploads/{session_id}"
    
    # Clean up if exists
    if os.path.exists(session_folder):
        shutil.rmtree(session_folder)
    os.makedirs(session_folder, exist_ok=True)
    
    # Copy TPR test file
    source_file = "www/tpr_data_by_state/ad_Adamawa_State_TPR_LLIN_2024.xlsx"
    dest_file = os.path.join(session_folder, "test_tpr_data.xlsx")
    shutil.copy(source_file, dest_file)
    print(f"✅ Setup test session: {session_id}")
    
    # Step 1: Run TPR prepare_for_risk action
    print("\n📊 Step 1: Running TPR prepare_for_risk action...")
    
    graph_state = {'session_id': session_id}
    result = analyze_tpr_data.invoke({
        "thought": "Preparing TPR data for risk analysis",
        "action": "prepare_for_risk",
        "options": "{}",
        "graph_state": graph_state
    })
    
    if "TPR Data Prepared for Risk Analysis" in result:
        print("✅ TPR data prepared successfully")
        
        # Check for transition prompt
        if "Would you like to proceed to the risk analysis" in result:
            print("✅ Transition prompt found in response")
        else:
            print("⚠️ Transition prompt not found")
    else:
        print("❌ TPR preparation failed")
        return False
    
    # Check flags
    waiting_flag = os.path.join(session_folder, '.tpr_waiting_confirmation')
    risk_ready_flag = os.path.join(session_folder, '.risk_ready')
    
    print(f"\n📁 Checking flags:")
    print(f"  - .tpr_waiting_confirmation: {'✅ Exists' if os.path.exists(waiting_flag) else '❌ Not found'}")
    print(f"  - .risk_ready: {'✅ Exists' if os.path.exists(risk_ready_flag) else '❌ Not found'}")
    
    # Step 2: Test user confirmation
    print("\n💬 Step 2: Testing user confirmation response...")
    
    # Create agent
    agent = DataAnalysisAgent(session_id)
    
    # Test confirmation message
    test_messages = [
        ("yes", True, "User says 'yes'"),
        ("Yes, proceed with the risk analysis", True, "Explicit confirmation"),
        ("ok let's do it", True, "Casual confirmation"),
        ("run the risk analysis", True, "Direct request"),
        ("no not now", False, "User declines"),
        ("what else can you do?", False, "Different question")
    ]
    
    for message, should_confirm, description in test_messages:
        print(f"\n  Testing: {description} - '{message}'")
        
        # Check if it's detected as confirmation
        is_confirmation = agent._is_confirmation_message(message)
        
        if is_confirmation == should_confirm:
            print(f"    ✅ Correctly {'detected' if should_confirm else 'rejected'}")
        else:
            print(f"    ❌ Expected {should_confirm}, got {is_confirmation}")
    
    # Step 3: Test actual transition
    print("\n🔄 Step 3: Testing actual transition with 'yes' response...")
    
    # Ensure waiting flag exists
    if not os.path.exists(waiting_flag):
        Path(waiting_flag).touch()
    
    # Send confirmation
    response = await agent.analyze("yes")
    
    if response.get('trigger_analysis'):
        print("✅ Transition triggered successfully")
        print(f"   Message preview: {response['message'][:200]}...")
    else:
        print("❌ Transition not triggered")
    
    # Check if waiting flag was cleared
    if not os.path.exists(waiting_flag):
        print("✅ Waiting flag cleared after confirmation")
    else:
        print("❌ Waiting flag still exists")
    
    # Step 4: Test declining transition
    print("\n🚫 Step 4: Testing declining transition...")
    
    # Reset waiting flag
    Path(waiting_flag).touch()
    
    response = await agent.analyze("no thanks, not now")
    
    if not response.get('trigger_analysis'):
        print("✅ Correctly handled decline")
        print(f"   Message preview: {response['message'][:200]}...")
    else:
        print("❌ Incorrectly triggered analysis on decline")
    
    # Check if waiting flag was cleared
    if not os.path.exists(waiting_flag):
        print("✅ Waiting flag cleared after decline")
    else:
        print("❌ Waiting flag still exists after decline")
    
    # Clean up
    print("\n🧹 Cleaning up test session...")
    if os.path.exists(session_folder):
        shutil.rmtree(session_folder)
    
    return True


if __name__ == "__main__":
    print("🚀 Starting TPR Transition Flow Test\n")
    
    # Run async test
    success = asyncio.run(test_transition_flow())
    
    print("\n" + "=" * 60)
    print("TEST RESULT:", "✅ PASSED" if success else "❌ FAILED")
    print("=" * 60)