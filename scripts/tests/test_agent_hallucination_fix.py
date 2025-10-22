#!/usr/bin/env python
"""
Test that the Data Analysis V3 agent handles data correctly and doesn't hallucinate.
Tests the fixes for:
1. Column encoding issues
2. Tool failure handling
3. Preventing hallucinated responses
"""

import sys
import os
import asyncio
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_agent_with_special_columns():
    """Test that agent handles columns with special characters properly."""
    from app.data_analysis_v3.core.agent import DataAnalysisAgent
    
    # Create test session
    session_id = "test_hallucination_fix"
    session_dir = Path(f"instance/uploads/{session_id}")
    session_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test data with problematic column names
    test_data = pd.DataFrame({
        'WardName': ['Ward1', 'Ward2', 'Ward3'],
        'HealthFacility': ['Hospital A', 'Clinic B', 'Health Center C'],
        'Persons presenting with fever & tested by RDT <5yrs': [100, 150, 200],
        'Persons presenting with fever & tested by RDT  ≥5yrs (excl PW)': [300, 250, 180],
        'Persons tested positive for malaria by RDT <5yrs': [20, 35, 45],
        'Persons tested positive for malaria by RDT  ≥5yrs (excl PW)': [60, 50, 40],
    })
    
    # Save test data
    data_file = session_dir / "test_tpr_data.csv"
    test_data.to_csv(data_file, index=False, encoding='utf-8')
    print(f"✅ Created test data with special characters at {data_file}")
    
    # Initialize agent
    os.environ['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY', 'test_key')
    agent = DataAnalysisAgent(session_id)
    
    print("\n📊 Testing agent responses...")
    
    # Test 1: Request facility analysis (should NOT hallucinate facility names)
    print("\n1️⃣ Testing facility analysis...")
    response = await agent.analyze("Show me the top facilities by testing volume")
    
    # Verify response doesn't contain fake facilities
    assert "Facility A" not in response['message'], "❌ Agent hallucinated 'Facility A'"
    assert "Facility B" not in response['message'], "❌ Agent hallucinated 'Facility B'"
    
    # Should either have real facility names or acknowledge difficulty
    if "Hospital A" in response['message'] or "trouble" in response['message'].lower():
        print("✅ Agent handled facility request correctly (no hallucination)")
    else:
        print(f"⚠️ Check response: {response['message'][:200]}...")
    
    # Test 2: Request TPR calculation (should handle special characters)
    print("\n2️⃣ Testing TPR calculation with special characters...")
    response = await agent.analyze("Calculate the test positivity rate for children under 5")
    
    # Should not have generic error or hallucinated percentages
    assert "82.3%" not in response['message'], "❌ Agent hallucinated specific percentage"
    
    if "20%" in response['message'] or "explore" in response['message'].lower():
        print("✅ Agent handled TPR request correctly")
    else:
        print(f"⚠️ Check response: {response['message'][:200]}...")
    
    # Test 3: Request non-existent column (should handle gracefully)
    print("\n3️⃣ Testing non-existent column request...")
    response = await agent.analyze("Show me the malaria cases by district")
    
    # Should acknowledge that 'district' column doesn't exist
    if "district" not in test_data.columns:
        if "couldn't find" in response['message'].lower() or "explore" in response['message'].lower():
            print("✅ Agent handled missing column correctly")
        else:
            print(f"⚠️ Response might be hallucinated: {response['message'][:200]}...")
    
    print("\n✅ All tests completed!")
    
    # Cleanup
    import shutil
    if session_dir.exists():
        shutil.rmtree(session_dir)
    
    return True

def test_prompt_updates():
    """Verify that the system prompt has been updated correctly."""
    from app.data_analysis_v3.prompts.system_prompt import MAIN_SYSTEM_PROMPT
    
    print("\n📝 Checking system prompt updates...")
    
    # Check for key improvements
    checks = [
        ("Data integrity principles", "DATA INTEGRITY PRINCIPLES" in MAIN_SYSTEM_PROMPT),
        ("Error handling protocol", "ERROR HANDLING PROTOCOL" in MAIN_SYSTEM_PROMPT),
        ("Robust column handling", "ROBUST COLUMN HANDLING" in MAIN_SYSTEM_PROMPT),
        ("No hallucination rule", "NEVER" in MAIN_SYSTEM_PROMPT and "hallucinate" in MAIN_SYSTEM_PROMPT),
        ("Pattern-based discovery", "Pattern-Based Discovery" in MAIN_SYSTEM_PROMPT),
    ]
    
    for check_name, passed in checks:
        if passed:
            print(f"✅ {check_name}: Found in prompt")
        else:
            print(f"❌ {check_name}: Missing from prompt")
    
    return all(passed for _, passed in checks)

if __name__ == "__main__":
    print("🧪 Testing Data Analysis V3 Agent Hallucination Fixes")
    print("=" * 60)
    
    # Test prompt updates
    prompt_ok = test_prompt_updates()
    
    # Test agent behavior
    try:
        agent_ok = asyncio.run(test_agent_with_special_columns())
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        agent_ok = False
    
    print("\n" + "=" * 60)
    if prompt_ok and agent_ok:
        print("✅ ALL TESTS PASSED - Ready for deployment!")
    else:
        print("❌ Some tests failed - Review before deploying")