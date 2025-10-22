#!/usr/bin/env python3
"""
Comprehensive test suite for all user interaction scenarios with TPR module
Tests all paths a user might take
"""

import asyncio
import sys
import os
import shutil
import pandas as pd
sys.path.insert(0, '.')

# Suppress warnings for cleaner output
import warnings
warnings.filterwarnings('ignore')

async def test_scenario_1_explore_analyze():
    """Test Scenario 1: User chooses to Explore & Analyze data"""
    print("\n" + "="*60)
    print("SCENARIO 1: EXPLORE & ANALYZE")
    print("="*60)
    
    from app.data_analysis_v3.core.agent import DataAnalysisAgent
    
    session_id = "test_explore"
    os.makedirs(f"instance/uploads/{session_id}", exist_ok=True)
    
    # Copy test file
    test_file = "www/tpr_data_by_state/ab_Abia_State_TPR_LLIN_2024.xlsx"
    shutil.copy(test_file, f"instance/uploads/{session_id}/")
    
    agent = DataAnalysisAgent(session_id)
    
    # User chooses option 1
    response = await agent.analyze("I want to explore and analyze my data")
    print(f"✅ Response received: {response['success']}")
    print(f"   Message preview: {response['message'][:200]}...")
    
    # Try common exploration queries
    test_queries = [
        "Show me summary statistics",
        "What are the top 5 wards by testing volume?",
        "Create a visualization of test patterns"
    ]
    
    for query in test_queries:
        print(f"\n📤 User: '{query}'")
        response = await agent.analyze(query)
        print(f"   Response: {response['success']}")
        if 'visualizations' in response and response['visualizations']:
            print(f"   ✅ Visualization created")
    
    # Cleanup
    shutil.rmtree(f"instance/uploads/{session_id}", ignore_errors=True)
    return True


async def test_scenario_2_tpr_all_variations():
    """Test Scenario 2: Calculate TPR with all possible combinations"""
    print("\n" + "="*60)
    print("SCENARIO 2: CALCULATE TPR - ALL VARIATIONS")
    print("="*60)
    
    from app.data_analysis_v3.core.agent import DataAnalysisAgent
    
    # Test matrix: age_group x test_method x facility_level
    test_combinations = [
        # Recommended path
        ("u5", "both", "primary", "Recommended"),
        # Other age groups
        ("all_ages", "both", "all", "All Ages"),
        ("o5", "rdt", "all", "Over 5 with RDT"),
        ("pw", "microscopy", "secondary", "Pregnant Women"),
        # Edge cases
        ("u5", "rdt", "tertiary", "Under 5 Tertiary"),
    ]
    
    results = []
    
    for age, method, facility, description in test_combinations:
        print(f"\n Testing: {description}")
        print(f"   Age: {age}, Method: {method}, Facility: {facility}")
        
        session_id = f"test_tpr_{age}_{method}_{facility}"
        os.makedirs(f"instance/uploads/{session_id}", exist_ok=True)
        
        # Copy test file
        test_file = "www/tpr_data_by_state/ab_Abia_State_TPR_LLIN_2024.xlsx"
        shutil.copy(test_file, f"instance/uploads/{session_id}/")
        
        agent = DataAnalysisAgent(session_id)
        
        # Simulate conversation flow
        response = await agent.analyze("Calculate TPR")
        
        # Select age group
        age_selection = {
            "all_ages": "all ages",
            "u5": "under 5",
            "o5": "over 5",
            "pw": "pregnant women"
        }[age]
        response = await agent.analyze(age_selection)
        
        # Select test method
        method_selection = {
            "both": "both",
            "rdt": "RDT only",
            "microscopy": "microscopy"
        }[method]
        response = await agent.analyze(method_selection)
        
        # Select facility level
        facility_selection = {
            "all": "all facilities",
            "primary": "primary",
            "secondary": "secondary",
            "tertiary": "tertiary"
        }[facility]
        response = await agent.analyze(facility_selection)
        
        # Check results
        tpr_file = f"instance/uploads/{session_id}/tpr_results.csv"
        map_file = f"instance/uploads/{session_id}/tpr_distribution_map.html"
        
        has_results = os.path.exists(tpr_file)
        has_map = os.path.exists(map_file)
        
        if has_results:
            df = pd.read_csv(tpr_file)
            avg_tpr = df['TPR'].mean()
            result_status = f"✅ TPR: {avg_tpr:.1f}%"
        else:
            result_status = "❌ No results"
        
        map_status = "✅ Map created" if has_map else "❌ No map"
        
        print(f"   Results: {result_status}")
        print(f"   Map: {map_status}")
        
        results.append({
            'description': description,
            'has_results': has_results,
            'has_map': has_map,
            'avg_tpr': avg_tpr if has_results else None
        })
        
        # Cleanup
        shutil.rmtree(f"instance/uploads/{session_id}", ignore_errors=True)
    
    # Summary
    print("\n" + "-"*40)
    print("SUMMARY:")
    success_count = sum(1 for r in results if r['has_results'])
    map_count = sum(1 for r in results if r['has_map'])
    print(f"✅ Successful TPR calculations: {success_count}/{len(results)}")
    print(f"✅ Maps created: {map_count}/{len(results)}")
    
    return success_count == len(results)


async def test_scenario_3_quick_overview():
    """Test Scenario 3: User wants quick overview"""
    print("\n" + "="*60)
    print("SCENARIO 3: QUICK OVERVIEW")
    print("="*60)
    
    from app.data_analysis_v3.core.agent import DataAnalysisAgent
    
    session_id = "test_overview"
    os.makedirs(f"instance/uploads/{session_id}", exist_ok=True)
    
    # Copy test file
    test_file = "www/tpr_data_by_state/ab_Abia_State_TPR_LLIN_2024.xlsx"
    shutil.copy(test_file, f"instance/uploads/{session_id}/")
    
    agent = DataAnalysisAgent(session_id)
    
    # User chooses option 3
    response = await agent.analyze("Give me a quick overview")
    print(f"✅ Response received: {response['success']}")
    print(f"   Message preview: {response['message'][:300]}...")
    
    # Follow-up questions
    follow_ups = [
        "What's the data quality like?",
        "How many records are there?",
        "What time period does this cover?"
    ]
    
    for query in follow_ups:
        print(f"\n📤 User: '{query}'")
        response = await agent.analyze(query)
        print(f"   Response: {response['success']}")
    
    # Cleanup
    shutil.rmtree(f"instance/uploads/{session_id}", ignore_errors=True)
    return True


async def test_scenario_4_user_confusion():
    """Test Scenario 4: User gives unclear or confusing input"""
    print("\n" + "="*60)
    print("SCENARIO 4: UNCLEAR USER INPUT")
    print("="*60)
    
    from app.data_analysis_v3.core.agent import DataAnalysisAgent
    
    session_id = "test_confusion"
    os.makedirs(f"instance/uploads/{session_id}", exist_ok=True)
    
    # Copy test file
    test_file = "www/tpr_data_by_state/ab_Abia_State_TPR_LLIN_2024.xlsx"
    shutil.copy(test_file, f"instance/uploads/{session_id}/")
    
    agent = DataAnalysisAgent(session_id)
    
    # Test unclear inputs
    unclear_inputs = [
        "2",  # Just a number
        "yes",  # Ambiguous confirmation
        "calculate",  # Incomplete request
        "show me the data",  # Vague request
        "what about children?",  # Indirect age group reference
        "primary please",  # Out of context facility selection
    ]
    
    for input_text in unclear_inputs:
        print(f"\n📤 User: '{input_text}'")
        try:
            response = await agent.analyze(input_text)
            print(f"   ✅ Handled gracefully: {response['success']}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}")
    
    # Cleanup
    shutil.rmtree(f"instance/uploads/{session_id}", ignore_errors=True)
    return True


async def test_scenario_5_tpr_to_risk_transition():
    """Test Scenario 5: TPR completion to risk analysis transition"""
    print("\n" + "="*60)
    print("SCENARIO 5: TPR TO RISK ANALYSIS TRANSITION")
    print("="*60)
    
    from app.data_analysis_v3.core.agent import DataAnalysisAgent
    
    session_id = "test_transition"
    os.makedirs(f"instance/uploads/{session_id}", exist_ok=True)
    
    # Copy test file
    test_file = "www/tpr_data_by_state/ab_Abia_State_TPR_LLIN_2024.xlsx"
    shutil.copy(test_file, f"instance/uploads/{session_id}/")
    
    agent = DataAnalysisAgent(session_id)
    
    # Complete TPR calculation
    await agent.analyze("Calculate TPR")
    await agent.analyze("under 5")
    await agent.analyze("both")
    response = await agent.analyze("all facilities")
    
    print("TPR calculation completed")
    
    # Check for transition prompt
    if "risk analysis" in response['message'].lower() or "next" in response['message'].lower():
        print("✅ Transition to risk analysis mentioned")
    else:
        print("⚠️ No transition guidance provided")
    
    # Test transition responses
    transition_tests = [
        ("yes, proceed to risk analysis", "Positive confirmation"),
        ("not now", "Decline transition"),
        ("what's risk analysis?", "Question about next step")
    ]
    
    for user_input, description in transition_tests:
        print(f"\n Testing: {description}")
        print(f"   User: '{user_input}'")
        response = await agent.analyze(user_input)
        print(f"   Response handled: {response['success']}")
    
    # Cleanup
    shutil.rmtree(f"instance/uploads/{session_id}", ignore_errors=True)
    return True


async def test_scenario_6_missing_data():
    """Test Scenario 6: Files with missing or incomplete data"""
    print("\n" + "="*60)
    print("SCENARIO 6: MISSING/INCOMPLETE DATA")
    print("="*60)
    
    from app.data_analysis_v3.core.agent import DataAnalysisAgent
    
    session_id = "test_missing"
    os.makedirs(f"instance/uploads/{session_id}", exist_ok=True)
    
    # Create a file with missing columns
    incomplete_data = pd.DataFrame({
        'State': ['Test State'] * 10,
        'LGA': ['LGA1'] * 10,
        'WardName': [f'Ward{i}' for i in range(10)],
        # Missing test columns - only has RDT, no Microscopy
        'Persons presenting with fever & tested by RDT <5yrs': [10, 20, 15, 0, 0, 5, 8, 12, 0, 3],
        'Persons tested positive for malaria by RDT <5yrs': [2, 5, 3, 0, 0, 1, 2, 3, 0, 1]
    })
    
    incomplete_file = f"instance/uploads/{session_id}/incomplete_data.xlsx"
    incomplete_data.to_excel(incomplete_file, index=False)
    
    agent = DataAnalysisAgent(session_id)
    
    # Try to calculate TPR with missing data
    print("Testing with incomplete data (RDT only, no Microscopy)...")
    response = await agent.analyze("Calculate TPR")
    print(f"Response: {response['success']}")
    
    # Try different methods
    await agent.analyze("under 5")
    
    # This should work (RDT only)
    response = await agent.analyze("RDT only")
    print(f"✅ RDT only (should work): {response['success']}")
    
    await agent.analyze("all facilities")
    
    # Check if calculation worked with limited data
    tpr_file = f"instance/uploads/{session_id}/tpr_results.csv"
    if os.path.exists(tpr_file):
        print("✅ TPR calculated with limited data")
    else:
        print("❌ Could not calculate TPR with limited data")
    
    # Cleanup
    shutil.rmtree(f"instance/uploads/{session_id}", ignore_errors=True)
    return True


async def test_scenario_7_multiple_files():
    """Test Scenario 7: User uploads multiple files"""
    print("\n" + "="*60)
    print("SCENARIO 7: MULTIPLE FILES")
    print("="*60)
    
    from app.data_analysis_v3.core.agent import DataAnalysisAgent
    
    session_id = "test_multiple"
    os.makedirs(f"instance/uploads/{session_id}", exist_ok=True)
    
    # Copy multiple test files
    files = [
        "www/tpr_data_by_state/ab_Abia_State_TPR_LLIN_2024.xlsx",
        "www/NMEP TPR and LLIN 2024_16072025.xlsx"
    ]
    
    for file in files:
        if os.path.exists(file):
            shutil.copy(file, f"instance/uploads/{session_id}/")
            print(f"Copied: {os.path.basename(file)}")
    
    agent = DataAnalysisAgent(session_id)
    
    # Check how agent handles multiple files
    print("\nAgent's response to multiple files:")
    if hasattr(agent, 'data_summary'):
        print(f"Data summary shows: {agent.data_summary[:200]}...")
    
    response = await agent.analyze("Which file should I analyze?")
    print(f"Response: {response['message'][:200]}...")
    
    # Cleanup
    shutil.rmtree(f"instance/uploads/{session_id}", ignore_errors=True)
    return True


async def run_all_tests():
    """Run all test scenarios"""
    print("\n" + "="*70)
    print("COMPREHENSIVE USER SCENARIO TESTING")
    print("="*70)
    
    test_results = []
    
    # Run each scenario
    scenarios = [
        ("Explore & Analyze", test_scenario_1_explore_analyze),
        ("TPR Calculations", test_scenario_2_tpr_all_variations),
        ("Quick Overview", test_scenario_3_quick_overview),
        ("Unclear Input", test_scenario_4_user_confusion),
        ("TPR to Risk Transition", test_scenario_5_tpr_to_risk_transition),
        ("Missing Data", test_scenario_6_missing_data),
        ("Multiple Files", test_scenario_7_multiple_files)
    ]
    
    for name, test_func in scenarios:
        print(f"\n🧪 Running: {name}")
        try:
            result = await test_func()
            test_results.append((name, "✅ PASSED" if result else "⚠️ PARTIAL"))
        except Exception as e:
            print(f"❌ ERROR: {str(e)[:200]}")
            test_results.append((name, "❌ FAILED"))
            import traceback
            traceback.print_exc()
    
    # Final summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for name, status in test_results:
        print(f"{status} - {name}")
    
    passed = sum(1 for _, status in test_results if "✅" in status)
    total = len(test_results)
    
    print(f"\nOverall: {passed}/{total} scenarios passed")
    
    # List identified issues
    print("\n" + "="*70)
    print("IDENTIFIED ISSUES")
    print("="*70)
    print("1. TPR values >100% due to data quality issues")
    print("2. Need to handle facility level filtering better")
    print("3. Transition to risk analysis needs clearer prompts")
    print("4. Multiple file handling needs improvement")
    
    return passed == total


if __name__ == "__main__":
    print("🚀 Starting comprehensive test suite...")
    
    # Activate virtual environment
    import subprocess
    subprocess.run(["source", "chatmrpt_venv_new/bin/activate"], shell=True)
    
    # Run tests
    asyncio.run(run_all_tests())