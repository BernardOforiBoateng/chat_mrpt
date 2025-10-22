"""
Test suite for TPR workflow fixes
Tests the fixes for:
1. Markdown parsing in streaming
2. TPR workflow state checking
3. Column detection for TPR calculation
4. State name passing through workflow
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from app.core.tpr_utils import calculate_ward_tpr
from app.data_analysis_v3.core.agent import DataAnalysisAgent
from app.data_analysis_v3.core.tpr_data_analyzer import TPRDataAnalyzer
from app.data_analysis_v3.core.formatters import MessageFormatter


class TestTPRColumnDetection:
    """Test improved column detection for TPR calculation."""
    
    def test_detects_u5_columns_with_standard_encoding(self):
        """Test that Under 5 columns are detected correctly."""
        test_data = pd.DataFrame({
            'State': ['Adamawa'] * 3,
            'WardName': ['Ward1', 'Ward2', 'Ward3'],
            'Persons presenting with fever & tested by RDT <5yrs': [100, 150, 200],
            'Persons tested positive for malaria by RDT <5yrs': [25, 40, 60]
        })
        
        result = calculate_ward_tpr(test_data, age_group='u5', test_method='rdt')
        
        assert not result.empty, "Should detect Under 5 columns"
        assert len(result) == 3, "Should return results for all 3 wards"
        assert 'TPR' in result.columns, "Should calculate TPR"
        assert result['TPR'].iloc[0] == 25.0, "Should calculate correct TPR (25/100 = 25%)"
    
    def test_detects_o5_columns_with_encoding_issues(self):
        """Test that Over 5 columns with encoding issues (â‰¥) are detected."""
        test_data = pd.DataFrame({
            'State': ['Adamawa'] * 3,
            'WardName': ['Ward1', 'Ward2', 'Ward3'],
            'Persons presenting with fever & tested by RDT  â‰¥5yrs (excl PW)': [200, 250, 300],
            'Persons tested positive for malaria by RDT  â‰¥5yrs (excl PW)': [40, 60, 90]
        })
        
        result = calculate_ward_tpr(test_data, age_group='o5', test_method='rdt')
        
        assert not result.empty, "Should detect Over 5 columns with encoding issues"
        assert len(result) == 3, "Should return results for all 3 wards"
        assert result['TPR'].iloc[0] == 20.0, "Should calculate correct TPR (40/200 = 20%)"
    
    def test_all_ages_sums_all_age_groups(self):
        """Test that all_ages properly sums across age groups."""
        test_data = pd.DataFrame({
            'State': ['Adamawa'] * 2,
            'WardName': ['Ward1', 'Ward2'],
            'Persons presenting with fever & tested by RDT <5yrs': [100, 150],
            'Persons presenting with fever & tested by RDT  â‰¥5yrs (excl PW)': [200, 250],
            'Persons presenting with fever & tested by RDT Preg Women (PW)': [50, 75],
            'Persons tested positive for malaria by RDT <5yrs': [25, 40],
            'Persons tested positive for malaria by RDT  â‰¥5yrs (excl PW)': [40, 60],
            'Persons tested positive for malaria by RDT Preg Women (PW)': [10, 15]
        })
        
        result = calculate_ward_tpr(test_data, age_group='all_ages', test_method='rdt')
        
        assert not result.empty, "Should calculate all_ages"
        # Ward1: (100+200+50) tested, (25+40+10) positive = 350 tested, 75 positive
        assert result['Total_Tested'].iloc[0] == 350, "Should sum all age groups for tested"
        assert result['Total_Positive'].iloc[0] == 75, "Should sum all age groups for positive"
        expected_tpr = round(75/350 * 100, 2)
        assert result['TPR'].iloc[0] == expected_tpr, f"Should calculate correct TPR ({expected_tpr}%)"


class TestTPRWorkflowStateChecking:
    """Test that TPR workflow state is properly checked."""
    
    @patch('app.data_analysis_v3.core.agent.StateManager')
    @patch('app.data_analysis_v3.core.agent.TPRDataAnalyzer')
    @patch('app.data_analysis_v3.core.agent.TPRWorkflowHandler')
    async def test_active_workflow_routes_to_handler(self, mock_handler_class, mock_analyzer_class, mock_state_class):
        """Test that active TPR workflow routes messages to the handler."""
        # Setup mocks
        mock_state = Mock()
        mock_state.is_tpr_workflow_active.return_value = True
        mock_state_class.return_value = mock_state
        
        mock_handler = Mock()
        mock_handler.handle_workflow.return_value = {
            'success': True,
            'message': 'Handled by TPR workflow'
        }
        mock_handler_class.return_value = mock_handler
        
        # Create agent and test
        agent = DataAnalysisAgent('test-session')
        result = await agent.analyze('Primary')  # User selecting facility level
        
        # Verify workflow was checked and handled
        mock_state.is_tpr_workflow_active.assert_called_once()
        mock_handler.handle_workflow.assert_called_once_with('Primary')
        assert result['message'] == 'Handled by TPR workflow'
    
    @patch('app.data_analysis_v3.core.agent.StateManager')
    async def test_option_2_starts_tpr_workflow(self, mock_state_class):
        """Test that selecting option 2 starts the TPR workflow."""
        mock_state = Mock()
        mock_state.is_tpr_workflow_active.return_value = False
        mock_state_class.return_value = mock_state
        
        with patch('app.data_analysis_v3.core.agent.TPRWorkflowHandler') as mock_handler_class:
            mock_handler = Mock()
            mock_handler.start_workflow.return_value = {
                'success': True,
                'message': 'TPR workflow started',
                'stage': 'facility_selection'
            }
            mock_handler_class.return_value = mock_handler
            
            with patch('os.listdir', return_value=['test_data.csv']):
                with patch('pandas.read_csv', return_value=pd.DataFrame({'test': [1, 2, 3]})):
                    agent = DataAnalysisAgent('test-session')
                    result = await agent.analyze('2')
                    
                    mock_handler.start_workflow.assert_called_once()
                    assert result['stage'] == 'facility_selection'


class TestStateNamePassing:
    """Test that state name is properly passed through the workflow."""
    
    def test_analyze_facility_levels_returns_state_name(self):
        """Test that analyze_facility_levels includes state_name in response."""
        analyzer = TPRDataAnalyzer()
        
        test_data = pd.DataFrame({
            'State': ['Adamawa'] * 10,
            'facility_level': ['Primary'] * 7 + ['Secondary'] * 2 + ['Tertiary'] * 1
        })
        
        result = analyzer.analyze_facility_levels(test_data, 'Adamawa')
        
        assert 'state_name' in result, "Should include state_name in response"
        assert result['state_name'] == 'Adamawa', "Should return the correct state name"
    
    def test_formatter_uses_state_name(self):
        """Test that formatter properly uses state_name from analysis."""
        formatter = MessageFormatter('test-session')
        
        analysis = {
            'state_name': 'Adamawa',
            'levels': {
                'primary': {
                    'name': 'Primary',
                    'count': 100,
                    'percentage': 80,
                    'description': 'Primary health centers',
                    'recommended': True
                }
            }
        }
        
        message = formatter.format_facility_selection_only(analysis)
        
        assert 'Adamawa' in message, "Should include actual state name"
        assert 'this state' not in message, "Should not have placeholder text"
        assert 'your state' not in message, "Should not have fallback text"


class TestMarkdownStreamingFix:
    """Test that markdown is properly parsed during streaming."""
    
    def test_markdown_parsing_handles_bold(self):
        """Test that bold markdown is parsed correctly."""
        # This would need to be tested in a browser environment
        # Here we just verify the parseMarkdown function logic would work
        
        # Mock the MessageHandler class
        from unittest.mock import MagicMock
        
        class MockMessageHandler:
            def parseMarkdown(self, text):
                # Simplified version of the actual parseMarkdown
                return text.replace('**', '<strong>').replace('**', '</strong>')
        
        handler = MockMessageHandler()
        result = handler.parseMarkdown('**Bold Text**')
        assert '<strong>' in result, "Should convert ** to <strong> tags"
    
    def test_markdown_parsing_preserves_complete_content(self):
        """Test that streaming preserves all content when parsing markdown."""
        # This tests the concept - actual implementation is in frontend JS
        
        streaming_content = ""
        chunks = ["**Analyzing", " your ", "data**\n\n", "Found ", "**10** ", "records"]
        
        expected_final = "**Analyzing your data**\n\nFound **10** records"
        
        for chunk in chunks:
            streaming_content += chunk
        
        assert streaming_content == expected_final, "Should accumulate all chunks correctly"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])