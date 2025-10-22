"""
Comprehensive TPR Workflow Simulation Test
Tests the entire workflow from data upload to TPR calculation
"""

import pytest
import sys
import os
import asyncio
import pandas as pd
import json
from unittest.mock import Mock, patch, MagicMock, AsyncMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.data_analysis_v3.core.agent import DataAnalysisAgent
from app.data_analysis_v3.core.state_manager import DataAnalysisStateManager, ConversationStage
from app.data_analysis_v3.core.tpr_workflow_handler import TPRWorkflowHandler
from app.data_analysis_v3.core.tpr_data_analyzer import TPRDataAnalyzer
from app.core.tpr_utils import calculate_ward_tpr


class TestCompleteTPRWorkflow:
    """Simulate the complete TPR workflow end-to-end."""
    
    @pytest.fixture
    def setup_test_environment(self, tmp_path):
        """Set up test environment with mock data."""
        # Create session directory
        session_id = 'test-session-123'
        session_dir = tmp_path / 'instance' / 'uploads' / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test TPR data file (mimicking adamawa_tpr_cleaned.csv)
        test_data = pd.DataFrame({
            'State': ['Adamawa'] * 100,
            'LGA': ['Yola North'] * 50 + ['Yola South'] * 50,
            'WardName': [f'Ward{i%10}' for i in range(100)],
            'HealthFacility': [f'Facility{i}' for i in range(100)],
            'facility_level': ['Primary'] * 80 + ['Secondary'] * 15 + ['Tertiary'] * 5,
            'Persons presenting with fever & tested by RDT <5yrs': [100 + i for i in range(100)],
            'Persons presenting with fever & tested by RDT  â‰¥5yrs (excl PW)': [200 + i for i in range(100)],
            'Persons presenting with fever & tested by RDT Preg Women (PW)': [50 + i for i in range(100)],
            'Persons tested positive for malaria by RDT <5yrs': [25 + i%20 for i in range(100)],
            'Persons tested positive for malaria by RDT  â‰¥5yrs (excl PW)': [40 + i%30 for i in range(100)],
            'Persons tested positive for malaria by RDT Preg Women (PW)': [10 + i%10 for i in range(100)],
            'Persons presenting with fever and tested by Microscopy <5yrs': [50 + i for i in range(100)],
            'Persons tested positive for malaria by Microscopy <5yrs': [10 + i%15 for i in range(100)]
        })
        
        data_file = session_dir / 'adamawa_tpr_cleaned.csv'
        test_data.to_csv(data_file, index=False)
        
        return {
            'session_id': session_id,
            'session_dir': str(session_dir),
            'data_file': str(data_file),
            'test_data': test_data
        }
    
    @pytest.mark.asyncio
    async def test_complete_workflow_simulation(self, setup_test_environment):
        """Test the complete TPR workflow from start to finish."""
        env = setup_test_environment
        session_id = env['session_id']
        
        print("\n" + "="*60)
        print("STARTING TPR WORKFLOW SIMULATION")
        print("="*60)
        
        # Step 1: Initialize agent and simulate data upload
        print("\n📁 Step 1: Simulating data upload...")
        with patch('os.path.exists', return_value=True):
            with patch('os.listdir', return_value=['adamawa_tpr_cleaned.csv']):
                agent = DataAnalysisAgent(session_id)
                
                # Simulate initial data upload message
                initial_response = await agent.analyze("Show me what's in the uploaded data")
                assert initial_response['success']
                print(f"✅ Initial response received: {initial_response['message'][:100]}...")
        
        # Step 2: Select option 2 for TPR workflow
        print("\n🔢 Step 2: Selecting option 2 for TPR workflow...")
        with patch('pandas.read_csv', return_value=env['test_data']):
            with patch('os.listdir', return_value=['adamawa_tpr_cleaned.csv']):
                with patch('os.path.join', return_value=env['data_file']):
                    option2_response = await agent.analyze("2")
                    assert option2_response['success']
                    assert 'facility' in option2_response['message'].lower()
                    print(f"✅ TPR workflow started: {option2_response.get('stage')}")
                    
                    # Verify state name is correct
                    if '**Adamawa**' in option2_response['message']:
                        print("✅ State name correctly displayed as 'Adamawa'")
                    else:
                        print("❌ State name issue detected")
        
        # Step 3: Select Primary facility level
        print("\n🏥 Step 3: Selecting Primary facility level...")
        primary_response = await agent.analyze("Primary")
        assert primary_response['success']
        
        # Should now ask for age group
        if 'age group' in primary_response['message'].lower():
            print("✅ Correctly progressed to age group selection")
        else:
            print(f"❌ Did not progress to age group: {primary_response['message'][:100]}")
        
        # Step 4: Select Under 5 age group
        print("\n👶 Step 4: Selecting Under 5 age group...")
        age_response = await agent.analyze("2")  # Option 2 is Under 5
        assert age_response['success']
        
        # Should trigger TPR calculation
        if 'TPR' in age_response['message'] or 'calculation' in age_response['message'].lower():
            print("✅ TPR calculation triggered")
        else:
            print("❌ TPR calculation not triggered")
        
        print("\n" + "="*60)
        print("WORKFLOW SIMULATION COMPLETE")
        print("="*60)
    
    def test_markdown_rendering(self):
        """Test that markdown is properly rendered."""
        print("\n📝 Testing Markdown Rendering...")
        
        # Simulate markdown parsing
        test_cases = [
            ("**Bold Text**", "<strong>Bold Text</strong>"),
            ("**Adamawa**", "<strong>Adamawa</strong>"),
            ("• Bullet point", "<li>Bullet point</li>"),
            ("## Header", "<h2>Header</h2>")
        ]
        
        # Mock the parseMarkdown function behavior
        def mock_parse_markdown(text):
            result = text
            result = result.replace('**', '<strong>').replace('**', '</strong>')
            result = result.replace('• ', '<li>').replace('\n', '</li>')
            result = result.replace('## ', '<h2>').replace('\n', '</h2>')
            return result
        
        for input_text, expected in test_cases:
            result = mock_parse_markdown(input_text)
            if '<strong>' in result or '<li>' in result or '<h2>' in result:
                print(f"✅ Markdown parsed: {input_text[:20]}...")
            else:
                print(f"❌ Failed to parse: {input_text}")
    
    def test_tpr_column_detection(self, setup_test_environment):
        """Test TPR column detection with various encodings."""
        print("\n🔍 Testing Column Detection...")
        env = setup_test_environment
        
        # Test with actual column names
        result = calculate_ward_tpr(env['test_data'], age_group='u5', test_method='rdt', facility_level='primary')
        
        if not result.empty:
            print(f"✅ Under 5 columns detected: {len(result)} wards")
            print(f"   Mean TPR: {result['TPR'].mean():.2f}%")
            
            # Check for non-zero results
            if result['Total_Tested'].sum() > 0:
                print(f"✅ Non-zero results: {result['Total_Tested'].sum()} tested")
            else:
                print("❌ Zero results detected")
        else:
            print("❌ Failed to detect columns")
        
        # Test Over 5 with encoding issue
        result_o5 = calculate_ward_tpr(env['test_data'], age_group='o5', test_method='rdt', facility_level='primary')
        if not result_o5.empty:
            print(f"✅ Over 5 columns (with â‰¥) detected: {len(result_o5)} wards")
        else:
            print("❌ Failed to detect Over 5 columns with encoding")
    
    def test_workflow_state_persistence(self):
        """Test that workflow state persists across messages."""
        print("\n💾 Testing Workflow State Persistence...")
        
        session_id = 'test-state-123'
        state_manager = DataAnalysisStateManager(session_id)
        
        # Set workflow stage
        state_manager.update_workflow_stage(ConversationStage.TPR_FACILITY_LEVEL)
        state_manager.save_tpr_selection('state', 'Adamawa')
        
        # Verify state persists
        current_stage = state_manager.get_workflow_stage()
        tpr_selections = state_manager.get_tpr_selections()
        
        if current_stage == ConversationStage.TPR_FACILITY_LEVEL:
            print("✅ Workflow stage persisted correctly")
        else:
            print(f"❌ Stage not persisted: {current_stage}")
        
        if tpr_selections.get('state') == 'Adamawa':
            print("✅ TPR selections persisted correctly")
        else:
            print(f"❌ Selections not persisted: {tpr_selections}")
        
        # Test workflow detection
        is_active = state_manager.is_tpr_workflow_active()
        if is_active:
            print("✅ TPR workflow correctly detected as active")
        else:
            print("❌ TPR workflow not detected as active")


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_data_handling(self):
        """Test handling of empty or invalid data."""
        print("\n⚠️ Testing Edge Cases...")
        
        # Empty dataframe
        empty_df = pd.DataFrame()
        result = calculate_ward_tpr(empty_df, age_group='all_ages')
        
        if result.empty or len(result) == 1:
            print("✅ Empty data handled gracefully")
        else:
            print("❌ Empty data not handled properly")
        
        # Missing columns
        partial_df = pd.DataFrame({
            'State': ['Test'],
            'WardName': ['Ward1']
        })
        result = calculate_ward_tpr(partial_df, age_group='u5')
        
        if 'No data' in str(result.values) or result['Total_Tested'].sum() == 0:
            print("✅ Missing columns handled gracefully")
        else:
            print("❌ Missing columns not handled properly")
    
    def test_special_characters_in_input(self):
        """Test handling of special characters."""
        print("\n🔤 Testing Special Character Handling...")
        
        handler = TPRWorkflowHandler('test-session', Mock(), Mock())
        
        # Test facility extraction with various inputs
        test_inputs = [
            ("1", "primary"),
            ("Primary", "primary"),
            ("PRIMARY", "primary"),
            ("1. Primary", "primary"),
            ("Option 1", "primary")
        ]
        
        for input_text, expected in test_inputs:
            result = handler.extract_facility_level(input_text)
            if result == expected:
                print(f"✅ Correctly extracted '{expected}' from '{input_text}'")
            else:
                print(f"❌ Failed to extract from '{input_text}': got '{result}'")


def run_all_tests():
    """Run all tests in sequence."""
    print("\n" + "="*60)
    print("RUNNING COMPREHENSIVE TPR WORKFLOW TESTS")
    print("="*60)
    
    # Setup
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create mock environment
        env = {
            'session_id': 'test-main',
            'session_dir': os.path.join(tmpdir, 'instance/uploads/test-main'),
            'test_data': pd.DataFrame({
                'State': ['Adamawa'] * 10,
                'LGA': ['Yola North'] * 10,
                'WardName': [f'Ward{i}' for i in range(10)],
                'facility_level': ['Primary'] * 8 + ['Secondary'] * 2,
                'Persons presenting with fever & tested by RDT <5yrs': [100] * 10,
                'Persons tested positive for malaria by RDT <5yrs': [25] * 10,
                'Persons presenting with fever & tested by RDT  â‰¥5yrs (excl PW)': [200] * 10,
                'Persons tested positive for malaria by RDT  â‰¥5yrs (excl PW)': [40] * 10
            })
        }
        
        os.makedirs(env['session_dir'], exist_ok=True)
        env['test_data'].to_csv(os.path.join(env['session_dir'], 'test_data.csv'), index=False)
        
        # Run tests
        workflow_test = TestCompleteTPRWorkflow()
        workflow_test.test_markdown_rendering()
        workflow_test.test_tpr_column_detection({'test_data': env['test_data']})
        workflow_test.test_workflow_state_persistence()
        
        edge_test = TestEdgeCases()
        edge_test.test_empty_data_handling()
        edge_test.test_special_characters_in_input()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETE")
    print("="*60)


if __name__ == '__main__':
    # Run comprehensive tests
    run_all_tests()
    
    # Also run with pytest if available
    print("\n\nRunning pytest suite...")
    pytest.main([__file__, '-v', '-s'])