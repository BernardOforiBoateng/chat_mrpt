#!/usr/bin/env python
"""
Simplified Test Suite for TPR Progressive Disclosure
Focuses on key functionality without complex fixtures
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import pandas as pd
from pathlib import Path


def test_no_auto_visualizations():
    """Test that visualizations are not auto-displayed"""
    from app.data_analysis_v3.core.state_manager import DataAnalysisStateManager
    from app.data_analysis_v3.core.tpr_workflow_handler import TPRWorkflowHandler
    from app.data_analysis_v3.core.tpr_data_analyzer import TPRDataAnalyzer

    # Setup
    session_id = 'test_no_auto_viz'
    test_data = pd.DataFrame({
        'State': ['Kano'] * 10,
        'WardName': [f'Ward_{i}' for i in range(10)],
        'facility_level': ['primary'] * 5 + ['secondary'] * 3 + ['tertiary'] * 2,
        'Tests_Examined_u5_rdt': [100] * 10,
        'Tests_Positive_u5_rdt': [20] * 10
    })

    state_manager = DataAnalysisStateManager(session_id)
    tpr_analyzer = TPRDataAnalyzer()
    tpr_handler = TPRWorkflowHandler(session_id, state_manager, tpr_analyzer)
    tpr_handler.set_data(test_data)

    # Test
    result = tpr_handler.start_workflow()

    # Assertions
    assert result['success'] == True, "Workflow should start successfully"
    assert result.get('visualizations') is None, "Visualizations should NOT be auto-displayed"
    assert 'Welcome to TPR Analysis!' in result['message'], "Should have welcome message"

    # Cleanup
    state_manager.clear_state()
    print("✅ Test 1 PASSED: No auto-display of visualizations")
    return True


def test_visualizations_stored_in_state():
    """Test that visualizations are stored for later retrieval"""
    from app.data_analysis_v3.core.state_manager import DataAnalysisStateManager
    from app.data_analysis_v3.core.tpr_workflow_handler import TPRWorkflowHandler
    from app.data_analysis_v3.core.tpr_data_analyzer import TPRDataAnalyzer

    # Setup
    session_id = 'test_viz_storage'
    test_data = pd.DataFrame({
        'State': ['Kano'] * 10 + ['Lagos'] * 10,
        'WardName': [f'Ward_{i}' for i in range(20)],
        'facility_level': (['primary'] * 5 + ['secondary'] * 3 + ['tertiary'] * 2) * 2,
        'Tests_Examined_u5_rdt': [100] * 20,
        'Tests_Positive_u5_rdt': [20] * 20
    })

    state_manager = DataAnalysisStateManager(session_id)
    tpr_analyzer = TPRDataAnalyzer()
    tpr_handler = TPRWorkflowHandler(session_id, state_manager, tpr_analyzer)
    tpr_handler.set_data(test_data)

    # Start workflow and select state
    tpr_handler.start_workflow()
    result = tpr_handler.handle_state_selection("Kano")

    # Check no visualizations in response
    assert result.get('visualizations') is None, "Should not display facility visualizations"

    # Check visualizations are stored
    pending = state_manager.get_field('pending_visualizations')
    assert pending is not None, "Visualizations should be stored"
    assert 'facility_level' in pending, "Should have facility level visualizations"

    # Cleanup
    state_manager.clear_state()
    print("✅ Test 2 PASSED: Visualizations stored in state")
    return True


def test_retrieve_visualizations():
    """Test that stored visualizations can be retrieved"""
    from app.data_analysis_v3.core.state_manager import DataAnalysisStateManager
    from app.data_analysis_v3.core.tpr_workflow_handler import TPRWorkflowHandler
    from app.data_analysis_v3.core.tpr_data_analyzer import TPRDataAnalyzer

    # Setup
    session_id = 'test_viz_retrieval'
    test_data = pd.DataFrame({
        'State': ['Kano'] * 10,
        'WardName': [f'Ward_{i}' for i in range(10)],
        'facility_level': ['primary'] * 5 + ['secondary'] * 3 + ['tertiary'] * 2,
        'Tests_Examined_u5_rdt': [100] * 10,
        'Tests_Positive_u5_rdt': [20] * 10
    })

    state_manager = DataAnalysisStateManager(session_id)
    tpr_analyzer = TPRDataAnalyzer()
    tpr_handler = TPRWorkflowHandler(session_id, state_manager, tpr_analyzer)
    tpr_handler.set_data(test_data)

    # Progress through workflow (single state - auto-selected)
    tpr_handler.start_workflow()

    # Retrieve visualizations
    retrieved = tpr_handler.get_pending_visualizations()

    # Assertions
    assert retrieved is not None, "Should retrieve stored visualizations"
    assert len(retrieved) > 0, "Should have at least one visualization"

    # Cleanup
    state_manager.clear_state()
    print("✅ Test 3 PASSED: Visualizations can be retrieved")
    return True


def test_conversational_formatting():
    """Test that messages are conversational with hints"""
    from app.data_analysis_v3.core.formatters import MessageFormatter

    formatter = MessageFormatter('test_session')

    # Test facility selection formatting
    analysis = {
        'levels': {
            'primary': {'count': 100},
            'secondary': {'count': 50},
            'tertiary': {'count': 10}
        }
    }

    message = formatter.format_facility_selection("Kano", analysis)

    # Check conversational elements
    assert "Now let's determine" in message, "Should be conversational"
    assert "💡" in message, "Should have hint emoji"
    assert "I can show you" in message, "Should hint about data availability"

    print("✅ Test 4 PASSED: Conversational formatting works")
    return True


def test_workflow_progression():
    """Test that workflow progresses correctly without visualizations"""
    from app.data_analysis_v3.core.state_manager import DataAnalysisStateManager
    from app.data_analysis_v3.core.tpr_workflow_handler import TPRWorkflowHandler
    from app.data_analysis_v3.core.tpr_data_analyzer import TPRDataAnalyzer

    # Setup
    session_id = 'test_progression'
    test_data = pd.DataFrame({
        'State': ['Kano'] * 10,
        'WardName': [f'Ward_{i}' for i in range(10)],
        'facility_level': ['primary'] * 5 + ['secondary'] * 3 + ['tertiary'] * 2,
        'Tests_Examined_u5_rdt': [100] * 10,
        'Tests_Positive_u5_rdt': [20] * 10,
        'Tests_Examined_o5_rdt': [80] * 10,
        'Tests_Positive_o5_rdt': [10] * 10
    })

    state_manager = DataAnalysisStateManager(session_id)
    tpr_analyzer = TPRDataAnalyzer()
    tpr_handler = TPRWorkflowHandler(session_id, state_manager, tpr_analyzer)
    tpr_handler.set_data(test_data)

    # Progress through workflow
    result1 = tpr_handler.start_workflow()
    assert result1['stage'] == 'facility_selection', "Should start at facility (single state)"
    assert result1.get('visualizations') is None

    result2 = tpr_handler.handle_facility_selection("secondary")
    assert result2['stage'] == 'age_selection', "Should progress to age selection"
    assert result2.get('visualizations') is None

    result3 = tpr_handler.handle_age_group_selection("u5")
    assert result3['success'] == True, "Should complete TPR calculation"

    # Cleanup
    state_manager.clear_state()
    print("✅ Test 5 PASSED: Workflow progresses without auto-visualizations")
    return True


def test_introduction_message():
    """Test that workflow introduction is comprehensive"""
    from app.data_analysis_v3.core.state_manager import DataAnalysisStateManager
    from app.data_analysis_v3.core.tpr_workflow_handler import TPRWorkflowHandler
    from app.data_analysis_v3.core.tpr_data_analyzer import TPRDataAnalyzer

    # Setup with multiple states to see full introduction
    session_id = 'test_intro'
    test_data = pd.DataFrame({
        'State': ['Kano'] * 10 + ['Lagos'] * 10,
        'WardName': [f'Ward_{i}' for i in range(20)],
        'facility_level': (['primary'] * 5 + ['secondary'] * 5) * 2,
        'Tests_Examined_u5_rdt': [100] * 20,
        'Tests_Positive_u5_rdt': [20] * 20
    })

    state_manager = DataAnalysisStateManager(session_id)
    tpr_analyzer = TPRDataAnalyzer()
    tpr_handler = TPRWorkflowHandler(session_id, state_manager, tpr_analyzer)
    tpr_handler.set_data(test_data)

    # Start workflow
    result = tpr_handler.start_workflow()

    # Check introduction elements
    assert "Welcome to TPR Analysis!" in result['message']
    assert "3 simple steps" in result['message'] or "3 quick steps" in result['message']
    assert "🎯" in result['message']

    # Cleanup
    state_manager.clear_state()
    print("✅ Test 6 PASSED: Introduction message is comprehensive")
    return True


def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "="*70)
    print("TPR PROGRESSIVE DISCLOSURE - SIMPLIFIED TEST SUITE")
    print("="*70 + "\n")

    tests = [
        test_no_auto_visualizations,
        test_visualizations_stored_in_state,
        test_retrieve_visualizations,
        test_conversational_formatting,
        test_workflow_progression,
        test_introduction_message
    ]

    passed = 0
    failed = 0
    errors = []

    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            failed += 1
            error_msg = f"{test_func.__name__}: {str(e)}"
            errors.append(error_msg)
            print(f"❌ Test FAILED: {error_msg}")

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"✅ PASSED: {passed}/{len(tests)}")
    print(f"❌ FAILED: {failed}/{len(tests)}")

    if errors:
        print("\nFailed Tests Details:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n🎉 ALL TESTS PASSED! 🎉")

    return passed == len(tests)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
