"""
Test Suite for TPR Progressive Disclosure Implementation
Tests that visualizations are stored but not auto-displayed
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import pandas as pd
import json
from pathlib import Path
from app.data_analysis_v3.core.state_manager import DataAnalysisStateManager, ConversationStage
from app.data_analysis_v3.core.tpr_workflow_handler import TPRWorkflowHandler
from app.data_analysis_v3.core.tpr_data_analyzer import TPRDataAnalyzer
from app.data_analysis_v3.core.agent import DataAnalysisAgent
from app.data_analysis_v3.core.formatters import MessageFormatter


class TestTPRProgressiveDisclosure:
    """Test suite for TPR workflow progressive disclosure features"""

    @pytest.fixture
    def setup_test_environment(self):
        """Set up test environment with data and handlers"""
        # Create test session
        session_id = 'test_tpr_progressive'

        # Create test data with multiple states for complete testing
        test_data = pd.DataFrame({
            'State': ['Kano'] * 20 + ['Lagos'] * 15,
            'WardName': [f'Ward_{i}' for i in range(35)],
            'facility_level': (['primary'] * 10 + ['secondary'] * 7 + ['tertiary'] * 3) +
                            (['primary'] * 8 + ['secondary'] * 5 + ['tertiary'] * 2),
            'Tests_Examined_u5_rdt': [100 + i*10 for i in range(35)],
            'Tests_Positive_u5_rdt': [20 + i*2 for i in range(35)],
            'Tests_Examined_o5_rdt': [80 + i*8 for i in range(35)],
            'Tests_Positive_o5_rdt': [10 + i for i in range(35)],
            'Tests_Examined_pw_rdt': [50 + i*5 for i in range(35)],
            'Tests_Positive_pw_rdt': [8 + i for i in range(35)]
        })

        # Initialize components
        state_manager = DataAnalysisStateManager(session_id)
        tpr_analyzer = TPRDataAnalyzer()
        tpr_handler = TPRWorkflowHandler(session_id, state_manager, tpr_analyzer)
        tpr_handler.set_data(test_data)

        # Create session directory for visualizations
        session_dir = Path(f"instance/uploads/{session_id}")
        session_dir.mkdir(parents=True, exist_ok=True)

        yield {
            'session_id': session_id,
            'test_data': test_data,
            'state_manager': state_manager,
            'tpr_handler': tpr_handler,
            'tpr_analyzer': tpr_analyzer
        }

        # Cleanup
        state_manager.clear_state()

    def test_workflow_start_no_auto_visualizations(self, setup_test_environment):
        """Test that starting workflow doesn't auto-display visualizations"""
        env = setup_test_environment
        tpr_handler = env['tpr_handler']
        state_manager = env['state_manager']

        # Start workflow
        result = tpr_handler.start_workflow()

        # Assertions
        assert result['success'] == True
        assert result.get('visualizations') is None, "Visualizations should not be auto-displayed"
        assert 'Welcome to TPR Analysis!' in result['message']
        assert '3 simple steps' in result['message']

        # Check that workflow is marked as active
        assert state_manager.is_tpr_workflow_active() == True

        print("✅ Test 1: Workflow starts without auto-displaying visualizations")

    def test_visualizations_stored_in_state(self, setup_test_environment):
        """Test that visualizations are generated and stored but not displayed"""
        env = setup_test_environment
        tpr_handler = env['tpr_handler']
        state_manager = env['state_manager']

        # Start workflow (will show state selection)
        tpr_handler.start_workflow()

        # Select a state
        result = tpr_handler.handle_state_selection("Kano")

        # Check response has no visualizations
        assert result.get('visualizations') is None, "Facility visualizations should not be auto-displayed"

        # Check visualizations are stored in state
        pending = state_manager.get_field('pending_visualizations')
        assert pending is not None, "Visualizations should be stored in state"
        assert 'facility_level' in pending, "Facility visualizations should be stored"
        assert len(pending['facility_level']) > 0, "Should have stored visualization data"

        print("✅ Test 2: Visualizations are stored in state but not displayed")

    def test_retrieve_visualizations_on_demand(self, setup_test_environment):
        """Test that visualizations can be retrieved when requested"""
        env = setup_test_environment
        tpr_handler = env['tpr_handler']
        state_manager = env['state_manager']

        # Start workflow and select state
        tpr_handler.start_workflow()
        tpr_handler.handle_state_selection("Kano")

        # Retrieve pending visualizations
        retrieved = tpr_handler.get_pending_visualizations()

        assert retrieved is not None, "Should be able to retrieve stored visualizations"
        assert len(retrieved) > 0, "Should have visualizations to retrieve"
        assert all('type' in viz for viz in retrieved), "Each visualization should have a type"

        print("✅ Test 3: Visualizations can be retrieved on demand")

    def test_conversational_messages_with_hints(self, setup_test_environment):
        """Test that messages are conversational with hints about data"""
        env = setup_test_environment
        formatter = MessageFormatter(env['session_id'])

        # Test facility selection message
        facility_analysis = {
            'levels': {
                'primary': {'count': 100, 'name': 'Primary'},
                'secondary': {'count': 50, 'name': 'Secondary'},
                'tertiary': {'count': 10, 'name': 'Tertiary'}
            }
        }

        message = formatter.format_facility_selection("Kano", facility_analysis)

        # Check for conversational elements
        assert "Now let's determine" in message
        assert "💡" in message, "Should have hint emoji"
        assert "I can show you" in message, "Should hint about data availability"
        assert "primary" in message.lower(), "Should show options"

        print("✅ Test 4: Messages are conversational with hints")

    def test_agent_handles_visualization_requests(self, setup_test_environment):
        """Test that agent detects and handles requests for visualizations"""
        env = setup_test_environment
        session_id = env['session_id']

        # Save test data to session directory
        data_path = f"instance/uploads/{session_id}/test_data.csv"
        env['test_data'].to_csv(data_path, index=False)

        # Initialize agent
        agent = DataAnalysisAgent(session_id)

        # Mark TPR workflow as active and set stage
        env['state_manager'].mark_tpr_workflow_active()
        env['state_manager'].update_workflow_stage(ConversationStage.TPR_FACILITY_LEVEL)

        # Store some test visualizations
        test_viz = [{
            'type': 'iframe',
            'url': '/test/viz.html',
            'title': 'Test Visualization'
        }]
        env['state_manager'].update_state({
            'pending_visualizations': {
                'facility_level': test_viz,
                'stage': 'facility_selection'
            }
        })

        # Test that "show me the data" returns visualizations
        response = agent.analyze("show me the data")

        # Should return visualizations
        assert response.get('visualizations') is not None, "Should show visualizations when requested"
        assert "facility data" in response['message'].lower(), "Should explain what's being shown"

        print("✅ Test 5: Agent handles visualization requests correctly")

    def test_keyword_selections_still_work(self, setup_test_environment):
        """Test that direct keyword selections work without showing visualizations"""
        env = setup_test_environment
        tpr_handler = env['tpr_handler']

        # Start workflow
        tpr_handler.start_workflow()

        # Select state
        tpr_handler.handle_state_selection("Kano")

        # Select facility with keyword
        result = tpr_handler.handle_facility_selection("secondary")

        assert result['success'] == True
        assert result.get('visualizations') is None, "No visualizations on keyword selection"
        assert result['stage'] == 'age_selection', "Should progress to age selection"

        # Select age group with number
        result = tpr_handler.handle_age_group_selection("1")  # u5

        assert result['success'] == True
        # Note: Final TPR calculation will show the result map

        print("✅ Test 6: Keyword selections work without showing visualizations")

    def test_single_state_auto_selection(self, setup_test_environment):
        """Test workflow with single state (auto-selection)"""
        env = setup_test_environment

        # Create single-state data
        single_state_data = pd.DataFrame({
            'State': ['Kano'] * 10,
            'WardName': [f'Ward_{i}' for i in range(10)],
            'facility_level': ['primary'] * 5 + ['secondary'] * 3 + ['tertiary'] * 2,
            'Tests_Examined_u5_rdt': [100] * 10,
            'Tests_Positive_u5_rdt': [20] * 10
        })

        # Initialize new handler with single-state data
        tpr_handler = TPRWorkflowHandler(
            env['session_id'] + '_single',
            env['state_manager'],
            env['tpr_analyzer']
        )
        tpr_handler.set_data(single_state_data)

        # Start workflow
        result = tpr_handler.start_workflow()

        # Should skip state selection and go to facility
        assert 'Auto-selected: Kano' in result['message']
        assert result['stage'] == 'facility_selection'
        assert result.get('visualizations') is None

        print("✅ Test 7: Single state auto-selection works correctly")

    def test_workflow_introduction_message(self, setup_test_environment):
        """Test that workflow introduction is comprehensive and friendly"""
        env = setup_test_environment
        tpr_handler = env['tpr_handler']

        result = tpr_handler.start_workflow()

        # Check introduction elements
        assert "Welcome to TPR Analysis!" in result['message']
        assert "🎯" in result['message'], "Should have emoji"
        assert "3 simple steps" in result['message'] or "3 quick steps" in result['message']
        assert "Test Positivity Rates" in result['message']
        assert "Let's begin" in result['message'] or "Let's start" in result['message']

        print("✅ Test 8: Workflow introduction is comprehensive and friendly")

    def test_navigation_commands(self, setup_test_environment):
        """Test navigation commands (back, status, exit)"""
        env = setup_test_environment
        tpr_handler = env['tpr_handler']

        # Start and progress through workflow
        tpr_handler.start_workflow()
        tpr_handler.handle_state_selection("Kano")
        tpr_handler.handle_facility_selection("primary")

        # Test 'back' command
        result = tpr_handler.handle_navigation('back')
        assert result['success'] == True
        assert "back to facility selection" in result['message'].lower()

        # Test 'status' command
        result = tpr_handler.handle_navigation('status')
        assert result['success'] == True
        assert "TPR workflow status" in result['message']

        print("✅ Test 9: Navigation commands work correctly")

    def test_no_visualization_leak_between_stages(self, setup_test_environment):
        """Test that visualizations don't leak between workflow stages"""
        env = setup_test_environment
        tpr_handler = env['tpr_handler']
        state_manager = env['state_manager']

        # Start workflow
        tpr_handler.start_workflow()

        # Select state (stores facility visualizations)
        tpr_handler.handle_state_selection("Kano")

        # Check facility viz stored
        pending = state_manager.get_field('pending_visualizations')
        assert 'facility_level' in pending

        # Select facility (should update to age visualizations)
        tpr_handler.handle_facility_selection("secondary")

        # Check age viz replaced facility viz
        pending = state_manager.get_field('pending_visualizations')
        assert 'age_group' in pending, "Should have age visualizations"
        assert pending.get('stage') == 'age_selection', "Stage should be updated"

        print("✅ Test 10: Visualizations don't leak between stages")


def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "="*60)
    print("TPR PROGRESSIVE DISCLOSURE TEST SUITE")
    print("="*60 + "\n")

    # Create test instance
    test_suite = TestTPRProgressiveDisclosure()

    # Setup environment
    import pytest

    # Create a mock fixture
    class MockEnv:
        def __init__(self):
            self.session_id = 'test_session'
            self.test_data = pd.DataFrame({
                'State': ['Kano'] * 20 + ['Lagos'] * 15,
                'WardName': [f'Ward_{i}' for i in range(35)],
                'facility_level': (['primary'] * 10 + ['secondary'] * 7 + ['tertiary'] * 3) +
                                (['primary'] * 8 + ['secondary'] * 5 + ['tertiary'] * 2),
                'Tests_Examined_u5_rdt': [100 + i*10 for i in range(35)],
                'Tests_Positive_u5_rdt': [20 + i*2 for i in range(35)],
                'Tests_Examined_o5_rdt': [80 + i*8 for i in range(35)],
                'Tests_Positive_o5_rdt': [10 + i for i in range(35)],
                'Tests_Examined_pw_rdt': [50 + i*5 for i in range(35)],
                'Tests_Positive_pw_rdt': [8 + i for i in range(35)]
            })

            # Initialize components
            self.state_manager = DataAnalysisStateManager(self.session_id)
            self.tpr_analyzer = TPRDataAnalyzer()
            self.tpr_handler = TPRWorkflowHandler(self.session_id, self.state_manager, self.tpr_analyzer)
            self.tpr_handler.set_data(self.test_data)

            # Create session directory
            session_dir = Path(f"instance/uploads/{self.session_id}")
            session_dir.mkdir(parents=True, exist_ok=True)

    # Run tests
    passed = 0
    failed = 0
    errors = []

    test_methods = [
        'test_workflow_start_no_auto_visualizations',
        'test_visualizations_stored_in_state',
        'test_retrieve_visualizations_on_demand',
        'test_conversational_messages_with_hints',
        'test_agent_handles_visualization_requests',
        'test_keyword_selections_still_work',
        'test_single_state_auto_selection',
        'test_workflow_introduction_message',
        'test_navigation_commands',
        'test_no_visualization_leak_between_stages'
    ]

    for test_name in test_methods:
        try:
            env_dict = {
                'session_id': 'test_session',
                'test_data': MockEnv().test_data,
                'state_manager': MockEnv().state_manager,
                'tpr_handler': MockEnv().tpr_handler,
                'tpr_analyzer': MockEnv().tpr_analyzer
            }
            test_method = getattr(test_suite, test_name)
            test_method(env_dict)
            passed += 1
        except Exception as e:
            failed += 1
            errors.append(f"{test_name}: {str(e)}")
            print(f"❌ {test_name} failed: {str(e)}")

    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    print(f"✅ Passed: {passed}/{len(test_methods)}")
    print(f"❌ Failed: {failed}/{len(test_methods)}")

    if errors:
        print("\nFailed Tests:")
        for error in errors:
            print(f"  - {error}")

    return passed == len(test_methods)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)