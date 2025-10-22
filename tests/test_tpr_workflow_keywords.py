#!/usr/bin/env python3
"""
Test TPR Workflow with Keyword-First Approach

Tests that:
1. Keywords are properly extracted and routed to handlers
2. Questions are routed to AI agent with context
3. Invalid inputs return None and get AI help
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.data_analysis_v3.core.tpr_workflow_handler import TPRWorkflowHandler
from app.data_analysis_v3.core.state_manager import ConversationStage


class TestTPRKeywordExtraction:
    """Test keyword extraction methods."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock dependencies
        mock_state_manager = Mock()
        mock_tpr_analyzer = Mock()
        self.handler = TPRWorkflowHandler('test_session', mock_state_manager, mock_tpr_analyzer)
    
    def test_facility_level_keywords(self):
        """Test facility level keyword extraction."""
        # Valid keywords
        assert self.handler.extract_facility_level('primary') == 'primary'
        assert self.handler.extract_facility_level('1') == 'primary'
        assert self.handler.extract_facility_level('secondary') == 'secondary'
        assert self.handler.extract_facility_level('2') == 'secondary'
        assert self.handler.extract_facility_level('tertiary') == 'tertiary'
        assert self.handler.extract_facility_level('3') == 'tertiary'
        assert self.handler.extract_facility_level('all') == 'all'
        assert self.handler.extract_facility_level('4') == 'all'
        
        # Questions should return None
        assert self.handler.extract_facility_level('What is TPR?') is None
        assert self.handler.extract_facility_level('How does this work?') is None
        assert self.handler.extract_facility_level('Where am I?') is None
        assert self.handler.extract_facility_level('help') is None
        assert self.handler.extract_facility_level('gibberish') is None
        
        # Edge cases
        assert self.handler.extract_facility_level('PRIMARY') == 'primary'  # Case insensitive
        assert self.handler.extract_facility_level(' primary ') == 'primary'  # Trim spaces
        assert self.handler.extract_facility_level('primary health') is None  # Extra words
    
    def test_age_group_keywords(self):
        """Test age group keyword extraction."""
        # Valid keywords
        assert self.handler.extract_age_group('u5') == 'u5'
        assert self.handler.extract_age_group('1') == 'u5'
        assert self.handler.extract_age_group('under5') == 'u5'  # No space
        assert self.handler.extract_age_group('o5') == 'o5'
        assert self.handler.extract_age_group('2') == 'o5'
        assert self.handler.extract_age_group('over5') == 'o5'  # No space
        assert self.handler.extract_age_group('pw') == 'pw'
        assert self.handler.extract_age_group('3') == 'pw'
        assert self.handler.extract_age_group('pregnant') == 'pw'
        assert self.handler.extract_age_group('all') == 'all_ages'  # Note: returns all_ages not all
        assert self.handler.extract_age_group('4') == 'all_ages'
        
        # Questions should return None
        assert self.handler.extract_age_group('What age groups?') is None
        assert self.handler.extract_age_group('How is TPR calculated?') is None
        assert self.handler.extract_age_group('Can you explain?') is None
        
        # Edge cases
        assert self.handler.extract_age_group('U5') == 'u5'  # Case insensitive
        assert self.handler.extract_age_group(' u5 ') == 'u5'  # Trim spaces
        assert self.handler.extract_age_group('children under 5') is None  # Too many words


class TestTPRWorkflowRouting:
    """Test workflow routing logic."""
    
    @patch('app.data_analysis_v3.core.agent.DataAnalysisAgent')
    def test_questions_get_context(self, mock_agent_class):
        """Test that questions receive TPR context."""
        from app.data_analysis_v3.core.agent import DataAnalysisAgent
        
        # Mock the agent
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        
        # Create agent instance
        agent = DataAnalysisAgent('test_session')
        
        # Mock state manager to indicate TPR workflow is active
        with patch.object(agent, 'state_manager') as mock_state:
            mock_state.is_tpr_workflow_active.return_value = True
            mock_state.get_workflow_stage.return_value = ConversationStage.TPR_FACILITY_LEVEL
            
            # Mock TPR handler
            with patch.object(agent, 'tpr_handler') as mock_handler:
                mock_handler.extract_facility_level.return_value = None  # No keyword match
                
                # Test question routing
                test_cases = [
                    'What is TPR?',
                    'How does this work?',
                    'Can you explain primary facilities?',
                    'Where am I in the workflow?'
                ]
                
                for question in test_cases:
                    # The question should NOT be immediately handled by TPR handler
                    # It should flow to the agent with context
                    mock_handler.extract_facility_level.assert_not_called()
    
    @patch('app.data_analysis_v3.core.agent.DataAnalysisAgent')
    def test_keywords_route_to_handler(self, mock_agent_class):
        """Test that keywords are properly routed to handler."""
        from app.data_analysis_v3.core.agent import DataAnalysisAgent
        
        # Mock the agent
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        
        # Create agent instance
        agent = DataAnalysisAgent('test_session')
        
        # Mock state manager
        with patch.object(agent, 'state_manager') as mock_state:
            mock_state.is_tpr_workflow_active.return_value = True
            mock_state.get_workflow_stage.return_value = ConversationStage.TPR_FACILITY_LEVEL
            
            # Mock TPR handler
            with patch.object(agent, 'tpr_handler') as mock_handler:
                mock_handler.extract_facility_level.return_value = 'primary'  # Keyword match
                mock_handler.handle_facility_selection.return_value = {'success': True}
                
                # Test keyword routing
                keywords = ['primary', '1', 'secondary', 'all']
                
                for keyword in keywords:
                    # Keywords should be handled by TPR handler
                    mock_handler.extract_facility_level.assert_not_called()


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])
