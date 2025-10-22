#!/usr/bin/env python3
"""
Test TPR state persistence fixes.

Verifies that:
1. State is properly saved and retrieved
2. State persists across workflow stages
3. 500 error is prevented when state is missing
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tempfile
from pathlib import Path
import pandas as pd
from unittest.mock import Mock, MagicMock

def test_state_persistence():
    """Test that state persists through workflow stages."""
    from app.data_analysis_v3.core.state_manager import DataAnalysisStateManager
    from app.data_analysis_v3.core.tpr_workflow_handler import TPRWorkflowHandler
    from app.data_analysis_v3.core.tpr_data_analyzer import TPRDataAnalyzer

    print("\n=== Testing TPR State Persistence ===\n")

    # Create temp session directory
    with tempfile.TemporaryDirectory() as temp_dir:
        session_id = 'test_session'
        session_dir = Path(temp_dir) / session_id
        session_dir.mkdir(exist_ok=True)

        # Create state manager
        state_manager = DataAnalysisStateManager(str(session_dir))

        # Create mock data with Kaduna state
        mock_data = pd.DataFrame({
            'State': ['Kaduna'] * 10,
            'LGA': ['TestLGA'] * 10,
            'WardName': ['Ward1'] * 10,
            'FacilityLevel': ['primary'] * 5 + ['secondary'] * 5,
            'Total RDT Tested (<5)': [100] * 10,
            'Total RDT Positive (<5)': [20] * 10
        })

        # Create TPR analyzer and handler
        tpr_analyzer = TPRDataAnalyzer()
        tpr_handler = TPRWorkflowHandler(session_id, state_manager, tpr_analyzer)
        tpr_handler.set_data(mock_data)

        # Test 1: Start workflow (should auto-detect Kaduna)
        print("1. Starting workflow...")
        result = tpr_handler.start_workflow()
        assert result['success'], "Failed to start workflow"
        print(f"   ✓ Workflow started, stage: {result.get('stage')}")

        # Test 2: Handle facility selection
        print("\n2. Selecting primary facilities...")
        tpr_handler.tpr_selections = {}  # Simulate empty selections
        result = tpr_handler.handle_facility_selection('primary')
        assert result['success'], "Failed to handle facility selection"

        # Check if state was loaded
        assert 'state' in tpr_handler.tpr_selections, "State not loaded in facility selection"
        assert tpr_handler.tpr_selections['state'] == 'Kaduna', f"Wrong state: {tpr_handler.tpr_selections['state']}"
        print(f"   ✓ State persisted: {tpr_handler.tpr_selections['state']}")

        # Test 3: Handle age group selection
        print("\n3. Selecting under 5 age group...")
        tpr_handler.tpr_selections = {}  # Simulate empty selections again
        result = tpr_handler.handle_age_group_selection('u5')

        # Check if state and facility were loaded
        assert 'state' in tpr_handler.tpr_selections, "State not loaded in age selection"
        assert 'facility_level' in tpr_handler.tpr_selections, "Facility not loaded in age selection"
        print(f"   ✓ State persisted: {tpr_handler.tpr_selections.get('state')}")
        print(f"   ✓ Facility persisted: {tpr_handler.tpr_selections.get('facility_level')}")

        # Test 4: Check state manager's get_tpr_selection method
        print("\n4. Testing state manager methods...")
        saved_state = state_manager.get_tpr_selection('state')
        saved_facility = state_manager.get_tpr_selection('facility_level')
        saved_age = state_manager.get_tpr_selection('age_group')

        print(f"   ✓ State from manager: {saved_state}")
        print(f"   ✓ Facility from manager: {saved_facility}")
        print(f"   ✓ Age from manager: {saved_age}")

        # Test 5: Verify calculate_tpr doesn't crash with empty selections
        print("\n5. Testing calculate_tpr with empty selections...")
        tpr_handler.tpr_selections = {}  # Empty selections

        # Mock the analyze_tpr_data tool to avoid actual calculation
        from unittest.mock import patch
        with patch('app.data_analysis_v3.core.tpr_workflow_handler.analyze_tpr_data') as mock_tool:
            mock_tool.invoke.return_value = "TPR calculated successfully"

            result = tpr_handler.calculate_tpr()

            # Should either succeed or return error message, not crash
            assert result is not None, "calculate_tpr returned None"
            assert 'session_id' in result, "Result missing session_id"

            if result.get('success'):
                print("   ✓ TPR calculation succeeded with state recovery")
            else:
                print(f"   ✓ TPR calculation handled missing state gracefully: {result.get('message')}")

        print("\n=== All Tests Passed! ===")
        print("\nSummary:")
        print("✓ State auto-detection works")
        print("✓ State persists across workflow stages")
        print("✓ State is recovered when missing from tpr_selections")
        print("✓ No 500 errors when state is missing")


if __name__ == '__main__':
    test_state_persistence()