#!/usr/bin/env python3
"""
Simple test for key user scenarios
"""

import asyncio
import sys
import os
import shutil
sys.path.insert(0, '.')

async def test_user_choice_1_explore():
    """Test User Choice 1: Explore & Analyze"""
    print("\n" + "="*60)
    print("SCENARIO: User Choice 1: Explore & Analyze")
    print("="*60)
    
    from app.data_analysis_v3.core.agent import DataAnalysisAgent
    
    session_id = "test_explore"
    os.makedirs(f"instance/uploads/{session_id}", exist_ok=True)
    shutil.copy("www/tpr_data_by_state/ab_Abia_State_TPR_LLIN_2024.xlsx", 
                f"instance/uploads/{session_id}/")
    
    agent = DataAnalysisAgent(session_id)
    
    print("📤 User: 'I want to explore my data'")
    response = await agent.analyze("I want to explore my data")
    print(f"Success: {response['success']}")
    
    if response['success']:
        print("✅ User Choice 1: Explore & Analyze - PASSED")
    else:
        print("❌ User Choice 1: Explore & Analyze - FAILED")
        print(f"Error: {response.get('error', 'Unknown')}")
    
    shutil.rmtree(f"instance/uploads/{session_id}", ignore_errors=True)
    return response['success']


async def test_user_choice_2_tpr_recommended():
    """Test User Choice 2: TPR with Recommendations"""
    print("\n" + "="*60)
    print("SCENARIO: User Choice 2: TPR with Recommendations")
    print("="*60)
    print("Testing recommended pathway: Under 5, Primary facilities, Both methods")
    
    from app.data_analysis_v3.core.agent import DataAnalysisAgent
    
    session_id = "test_tpr_rec"
    os.makedirs(f"instance/uploads/{session_id}", exist_ok=True)
    shutil.copy("www/tpr_data_by_state/ab_Abia_State_TPR_LLIN_2024.xlsx", 
                f"instance/uploads/{session_id}/")
    
    agent = DataAnalysisAgent(session_id)
    
    # Sequence of interactions
    interactions = [
        ("Calculate TPR", "User selects TPR calculation"),
        ("Under 5", "User selects Under 5 age group"),
        ("Primary", "User selects Primary facilities"),
        ("Both", "User selects both test methods")
    ]
    
    success = True
    for user_input, description in interactions:
        print(f"📤 User: '{user_input}'")
        response = await agent.analyze(user_input)
        if not response['success']:
            print(f"❌ Failed at: {description}")
            print(f"   Error: {response.get('error', 'Unknown')}")
            success = False
            break
    
    # Check if TPR was calculated
    tpr_file = f"instance/uploads/{session_id}/tpr_results.csv"
    map_file = f"instance/uploads/{session_id}/tpr_distribution_map.html"
    
    if os.path.exists(tpr_file):
        print("✅ TPR results file created")
        import pandas as pd
        df = pd.read_csv(tpr_file)
        print(f"   {len(df)} wards calculated")
    else:
        print("❌ No TPR results file")
        success = False
    
    if os.path.exists(map_file):
        print("✅ TPR map created")
    else:
        print("⚠️ TPR map not created")
    
    if success:
        print("✅ User Choice 2: TPR with Recommendations - PASSED")
    else:
        print("❌ User Choice 2: TPR with Recommendations - FAILED")
    
    shutil.rmtree(f"instance/uploads/{session_id}", ignore_errors=True)
    return success


async def test_user_choice_2_tpr_all_ages():
    """Test User Choice 2: TPR with All Ages"""
    print("\n" + "="*60)
    print("SCENARIO: User Choice 2: TPR with All Ages")
    print("="*60)
    print("Testing: All ages, All facilities, Both methods")
    
    from app.data_analysis_v3.core.agent import DataAnalysisAgent
    
    session_id = "test_tpr_all"
    os.makedirs(f"instance/uploads/{session_id}", exist_ok=True)
    shutil.copy("www/tpr_data_by_state/ab_Abia_State_TPR_LLIN_2024.xlsx", 
                f"instance/uploads/{session_id}/")
    
    agent = DataAnalysisAgent(session_id)
    
    # Direct calculation with all ages
    response = await agent.analyze("Calculate TPR for all ages")
    
    if response['success']:
        print("✅ User Choice 2: TPR with All Ages - PASSED")
    else:
        print("❌ User Choice 2: TPR with All Ages - FAILED")
        print(f"Error: {response.get('error', response.get('message', 'Unknown'))}")
    
    shutil.rmtree(f"instance/uploads/{session_id}", ignore_errors=True)
    return response['success']


async def test_user_choice_3_quick_overview():
    """Test User Choice 3: Quick Overview"""
    print("\n" + "="*60)
    print("SCENARIO: User Choice 3: Quick Overview")
    print("="*60)
    
    from app.data_analysis_v3.core.agent import DataAnalysisAgent
    
    session_id = "test_overview"
    os.makedirs(f"instance/uploads/{session_id}", exist_ok=True)
    shutil.copy("www/tpr_data_by_state/ab_Abia_State_TPR_LLIN_2024.xlsx", 
                f"instance/uploads/{session_id}/")
    
    agent = DataAnalysisAgent(session_id)
    
    print("📤 User: 'Give me a quick overview'")
    response = await agent.analyze("Give me a quick overview")
    
    if response['success']:
        print("✅ User Choice 3: Quick Overview - PASSED")
        print(f"   Preview: {response['message'][:200]}...")
    else:
        print("❌ User Choice 3: Quick Overview - FAILED")
    
    shutil.rmtree(f"instance/uploads/{session_id}", ignore_errors=True)
    return response['success']


async def test_ambiguous_requests():
    """Test handling of ambiguous user requests"""
    print("\n" + "="*60)
    print("SCENARIO: Ambiguous User Requests")
    print("="*60)
    
    from app.data_analysis_v3.core.agent import DataAnalysisAgent
    
    session_id = "test_ambiguous"
    os.makedirs(f"instance/uploads/{session_id}", exist_ok=True)
    shutil.copy("www/tpr_data_by_state/ab_Abia_State_TPR_LLIN_2024.xlsx", 
                f"instance/uploads/{session_id}/")
    
    agent = DataAnalysisAgent(session_id)
    
    ambiguous_inputs = [
        "help",
        "what can you do",
        "2",  # Just a number
        "yes",
        "show me the data"
    ]
    
    all_handled = True
    for user_input in ambiguous_inputs:
        print(f"📤 Testing: '{user_input}'")
        response = await agent.analyze(user_input)
        if response['success']:
            print(f"  ✅ Handled")
        else:
            print(f"  ❌ Error: {response.get('error', 'Unknown')}")
            all_handled = False
    
    if all_handled:
        print("✅ Ambiguous User Requests - PASSED")
    else:
        print("❌ Ambiguous User Requests - FAILED")
    
    shutil.rmtree(f"instance/uploads/{session_id}", ignore_errors=True)
    return all_handled


async def test_tpr_variations():
    """Test different TPR calculation variations"""
    print("\n" + "="*60)
    print("SCENARIO: TPR Calculation Variations")
    print("="*60)
    
    from app.core.tpr_utils import calculate_ward_tpr
    import pandas as pd
    
    # Load test data
    df = pd.read_excel("www/tpr_data_by_state/ab_Abia_State_TPR_LLIN_2024.xlsx")
    
    variations = [
        ("u5", "rdt", "all"),
        ("u5", "microscopy", "all"),
        ("o5", "both", "all"),
        ("pw", "both", "all")
    ]
    
    all_passed = True
    for age, method, facility in variations:
        print(f"Testing: age={age}, method={method}, facility={facility}")
        try:
            result = calculate_ward_tpr(df, age_group=age, test_method=method, facility_level=facility)
            if isinstance(result, pd.DataFrame) and len(result) > 1:
                print(f"  ✅ Got {len(result)} results")
            else:
                print(f"  ❌ Insufficient results")
                all_passed = False
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:100]}")
            all_passed = False
    
    if all_passed:
        print("✅ TPR Calculation Variations - PASSED")
    else:
        print("❌ TPR Calculation Variations - FAILED")
    
    return all_passed


async def test_error_handling():
    """Test error handling for various edge cases"""
    print("\n" + "="*60)
    print("SCENARIO: Error Handling")
    print("="*60)
    
    from app.data_analysis_v3.core.agent import DataAnalysisAgent
    import pandas as pd  # Fix missing import
    
    # Test with no data
    print("Testing with no data uploaded...")
    session_id = "test_nodata"
    os.makedirs(f"instance/uploads/{session_id}", exist_ok=True)
    
    agent = DataAnalysisAgent(session_id)
    response = await agent.analyze("Calculate TPR")
    
    if "no data" in response['message'].lower() or "upload" in response['message'].lower():
        print("  ✅ Handled no data gracefully")
        no_data_ok = True
    else:
        print("  ❌ Did not handle no data properly")
        no_data_ok = False
    
    shutil.rmtree(f"instance/uploads/{session_id}", ignore_errors=True)
    
    # Test with non-TPR data
    print("Testing with non-TPR data...")
    session_id = "test_nontpr"
    os.makedirs(f"instance/uploads/{session_id}", exist_ok=True)
    
    # Create non-TPR data
    non_tpr = pd.DataFrame({
        'Name': ['A', 'B', 'C'],
        'Value': [1, 2, 3]
    })
    non_tpr.to_csv(f"instance/uploads/{session_id}/data.csv", index=False)
    
    agent = DataAnalysisAgent(session_id)
    response = await agent.analyze("Calculate TPR")
    
    if "tpr" not in response['message'].lower() or response['success']:
        print("  ✅ Handled non-TPR data gracefully")
        non_tpr_ok = True
    else:
        print("  ❌ Did not handle non-TPR data properly")
        non_tpr_ok = False
    
    shutil.rmtree(f"instance/uploads/{session_id}", ignore_errors=True)
    
    if no_data_ok and non_tpr_ok:
        print("✅ Error Handling - PASSED")
        return True
    else:
        print("❌ Error Handling - FAILED")
        return False


async def test_multi_state():
    """Test handling of multi-state NMEP data"""
    print("\n" + "="*60)
    print("SCENARIO: Multi-State Data")
    print("="*60)
    
    if not os.path.exists("www/NMEP TPR and LLIN 2024_16072025.xlsx"):
        print("⚠️ Multi-state test file not found, skipping")
        return True
    
    from app.data_analysis_v3.core.agent import DataAnalysisAgent
    
    session_id = "test_multi"
    os.makedirs(f"instance/uploads/{session_id}", exist_ok=True)
    
    print("Testing with multi-state NMEP file...")
    shutil.copy("www/NMEP TPR and LLIN 2024_16072025.xlsx", 
                f"instance/uploads/{session_id}/")
    
    agent = DataAnalysisAgent(session_id)
    response = await agent.analyze("Show me what states are in this data")
    
    if response['success']:
        print("✅ Multi-State Data - PASSED")
    else:
        print("❌ Multi-State Data - FAILED")
    
    shutil.rmtree(f"instance/uploads/{session_id}", ignore_errors=True)
    return response['success']


async def main():
    """Run all test scenarios"""
    print("="*60)
    print("COMPREHENSIVE TPR USER SCENARIO TESTING")
    print("="*60)
    
    tests = [
        ("User Choice 1: Explore & Analyze", test_user_choice_1_explore),
        ("User Choice 2: TPR with Recommendations", test_user_choice_2_tpr_recommended),
        ("User Choice 2: TPR with All Ages", test_user_choice_2_tpr_all_ages),
        ("User Choice 3: Quick Overview", test_user_choice_3_quick_overview),
        ("Ambiguous User Requests", test_ambiguous_requests),
        ("TPR Calculation Variations", test_tpr_variations),
        ("Error Handling", test_error_handling),
        ("Multi-State Data", test_multi_state)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = await test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"❌ {name} - EXCEPTION: {str(e)[:200]}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = 0
    failed = 0
    for name, success in results:
        if success:
            print(f"✅ PASS: {name}")
            passed += 1
        else:
            print(f"❌ FAIL: {name}")
            failed += 1
    
    print(f"\nTotal: {passed}/{len(results)} passed")
    
    if failed > 0:
        print(f"\n⚠️  {failed} tests failed")
    else:
        print("\n🎉 All tests passed!")


if __name__ == "__main__":
    # Run with proper virtual environment
    import subprocess
    subprocess.run(["source", "chatmrpt_venv_new/bin/activate"], shell=True)
    
    # Run tests
    asyncio.run(main())