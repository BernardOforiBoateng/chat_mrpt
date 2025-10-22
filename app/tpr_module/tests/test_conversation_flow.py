"""
Unit tests for TPR Conversation Flow.

Tests the conversational interface and state management.
"""

import unittest
from unittest.mock import Mock, MagicMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from app.tpr_module.core.tpr_conversation_manager import TPRConversationManager, ConversationStage
from app.tpr_module.core.tpr_state_manager import TPRStateManager
from .test_helpers import setup_conversation_manager_for_test, create_test_metadata


class TestConversationFlow(unittest.TestCase):
    """Test the conversational flow for TPR analysis."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.state_manager = TPRStateManager('test_session')
        self.conversation_manager = TPRConversationManager(
            self.state_manager,
            llm_client=None  # No LLM for unit tests
        )
    
    def tearDown(self):
        """Clean up after tests."""
        self.state_manager.clear_state()
    
    def test_initial_greeting(self):
        """Test initial greeting message after file upload."""
        # Simulate file upload with metadata
        test_states = ['Kano', 'Lagos', 'Kaduna']
        metadata = create_test_metadata(test_states)
        
        # This simulates what happens after file parsing
        response = self.conversation_manager.generate_response(
            'start',
            {'metadata': metadata}
        )
        
        self.assertIn('response', response)
        self.assertIn('suggestions', response)
        
        # Should mention TPR
        self.assertIn('TPR', response['response'].upper())
        
        # Should have state suggestions
        self.assertIsInstance(response['suggestions'], list)
        self.assertEqual(response['suggestions'], test_states)
    
    def test_state_selection_valid(self):
        """Test valid state selection."""
        # First initialize the conversation properly
        test_states = ['Kano', 'Lagos', 'Kaduna']
        setup_conversation_manager_for_test(self.conversation_manager, test_states)
        
        # Start the conversation
        metadata = create_test_metadata(test_states)
        self.conversation_manager.generate_response('start', {'metadata': metadata})
        
        # Process state selection
        response = self.conversation_manager.process_user_input('I want to analyze Kano')
        
        # Should recognize state
        self.assertIn('response', response)
        
        # Check state was saved
        state = self.state_manager.get_state()
        self.assertEqual(state.get('selected_state'), 'Kano')
        self.assertEqual(state.get('workflow_stage'), 'facility_selection')
    
    def test_state_selection_invalid(self):
        """Test invalid state selection."""
        self.state_manager.update_state({
            'available_states': ['Kano', 'Lagos', 'Kaduna'],
            'workflow_stage': 'state_selection'
        })
        
        # Try invalid state
        response = self.conversation_manager.process_user_input('I want XYZ state')
        
        # Should not progress
        state = self.state_manager.get_state()
        self.assertEqual(state.get('workflow_stage'), 'state_selection')
        
        # Should provide helpful response
        self.assertIn('response', response)
    
    def test_facility_level_selection(self):
        """Test facility level selection."""
        # Set up state
        self.state_manager.update_state({
            'selected_state': 'Kano',
            'workflow_stage': 'facility_selection'
        })
        
        # Test various inputs
        test_cases = [
            ('primary facilities only', 'primary'),
            ('just secondary', 'secondary'),
            ('tertiary hospitals', 'tertiary'),
            ('all facilities', 'all'),
            ('every facility', 'all')
        ]
        
        for user_input, expected_level in test_cases:
            self.state_manager.update_state({'workflow_stage': 'facility_selection'})
            
            response = self.conversation_manager.process_user_input(user_input)
            
            state = self.state_manager.get_state()
            self.assertEqual(state.get('facility_level'), expected_level,
                           f"Failed to extract '{expected_level}' from '{user_input}'")
    
    def test_age_group_selection(self):
        """Test age group selection."""
        # Set up the conversation manager to be in age group selection stage
        self.conversation_manager.current_stage = ConversationStage.AGE_GROUP_SELECTION
        self.conversation_manager.selected_state = 'Kano'
        self.conversation_manager.selected_facility_level = 'All'
        
        self.state_manager.update_state({
            'selected_state': 'Kano',
            'facility_level': 'all',
            'workflow_stage': 'age_group_selection'
        })
        
        # Test age group inputs
        test_cases = [
            ('under 5 years', 'u5'),
            ('children under five', 'u5'),
            ('over 5', 'o5'),
            ('all age groups', 'all'),
            ('everyone', 'all')
        ]
        
        for user_input, expected_age in test_cases:
            self.state_manager.update_state({'workflow_stage': 'age_group_selection'})
            
            response = self.conversation_manager.process_user_input(user_input)
            
            state = self.state_manager.get_state()
            self.assertEqual(state.get('age_group'), expected_age,
                           f"Failed to extract '{expected_age}' from '{user_input}'")
    
    def test_confirmation_flow(self):
        """Test analysis confirmation."""
        # Set up complete state
        self.state_manager.update_state({
            'selected_state': 'Kano',
            'facility_level': 'primary',
            'age_group': 'under_5',
            'workflow_stage': 'confirmation'
        })
        
        # Test confirmation
        response = self.conversation_manager.process_user_input('yes, proceed')
        
        # Should be ready for analysis
        self.assertTrue(response.get('ready_for_analysis'))
        
        # Should have parameters
        params = response.get('parameters', {})
        self.assertEqual(params.get('state'), 'Kano')
        self.assertEqual(params.get('facility_level'), 'primary')
        self.assertEqual(params.get('age_group'), 'under_5')
    
    def test_skip_optional_parameters(self):
        """Test skipping optional parameters."""
        self.state_manager.update_state({
            'selected_state': 'Lagos',
            'workflow_stage': 'facility_selection'
        })
        
        # Skip facility level
        response = self.conversation_manager.process_user_input('skip')
        
        state = self.state_manager.get_state()
        self.assertEqual(state.get('facility_level'), 'all')
        self.assertEqual(state.get('workflow_stage'), 'age_selection')
        
        # Skip age group
        response = self.conversation_manager.process_user_input('skip this too')
        
        state = self.state_manager.get_state()
        self.assertEqual(state.get('age_group'), 'all_ages')
        self.assertEqual(state.get('workflow_stage'), 'confirmation')
    
    def test_workflow_progression(self):
        """Test complete workflow progression."""
        stages = []
        
        # Track stage progression
        def track_stage():
            stages.append(self.state_manager.get_state().get('workflow_stage'))
        
        # Start
        self.conversation_manager.generate_response('start', {'metadata': {}})
        track_stage()
        
        # Select state
        self.state_manager.update_state({
            'available_states': ['Kano'],
            'workflow_stage': 'state_selection'
        })
        self.conversation_manager.process_user_input('Kano')
        track_stage()
        
        # Select facility
        self.conversation_manager.process_user_input('all')
        track_stage()
        
        # Select age
        self.conversation_manager.process_user_input('all ages')
        track_stage()
        
        # Confirm
        response = self.conversation_manager.process_user_input('yes')
        track_stage()
        
        # Check progression
        expected_stages = [
            'state_selection',
            'facility_selection', 
            'age_selection',
            'confirmation',
            'ready'
        ]
        
        self.assertEqual(stages, expected_stages)
        self.assertTrue(response.get('ready_for_analysis'))
    
    def test_intent_extraction(self):
        """Test intent extraction from user input."""
        # Test state intent
        intent = self.conversation_manager._simple_intent_extraction(
            "I'd like to analyze data for Kano state"
        )
        self.assertEqual(intent['intent'], 'state_selection')
        self.assertEqual(intent['value'], 'Kano')
        
        # Test facility intent
        intent = self.conversation_manager._simple_intent_extraction(
            "Show me primary health facilities"
        )
        self.assertEqual(intent['intent'], 'facility_selection')
        self.assertEqual(intent['value'], 'primary')
        
        # Test confirmation intent
        intent = self.conversation_manager._simple_intent_extraction(
            "Yes, that looks good"
        )
        self.assertEqual(intent['intent'], 'confirmation')
        self.assertTrue(intent['confirmed'])
    
    def test_natural_language_flexibility(self):
        """Test that various phrasings work."""
        self.state_manager.update_state({
            'available_states': ['Kano', 'Lagos'],
            'workflow_stage': 'state_selection'
        })
        
        # Various ways to select Kano
        test_phrases = [
            "Kano",
            "Let's look at Kano",
            "I want to analyze Kano state",
            "Show me Kano data",
            "kano please",
            "KANO STATE"
        ]
        
        for phrase in test_phrases:
            self.state_manager.update_state({'workflow_stage': 'state_selection'})
            
            response = self.conversation_manager.process_user_input(phrase)
            state = self.state_manager.get_state()
            
            self.assertEqual(state.get('selected_state'), 'Kano',
                           f"Failed to extract 'Kano' from '{phrase}'")


class TestStateManager(unittest.TestCase):
    """Test TPR state management."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.state_manager = TPRStateManager('test_session')
    
    def tearDown(self):
        """Clean up after tests."""
        self.state_manager.clear_state()
    
    def test_state_persistence(self):
        """Test that state persists across operations."""
        # Set initial state
        self.state_manager.update_state({
            'selected_state': 'Kano',
            'facility_level': 'primary'
        })
        
        # Get state
        state = self.state_manager.get_state()
        self.assertEqual(state['selected_state'], 'Kano')
        self.assertEqual(state['facility_level'], 'primary')
        
        # Update partial state
        self.state_manager.update_state({
            'age_group': 'under_5'
        })
        
        # Check all values persist
        state = self.state_manager.get_state()
        self.assertEqual(state['selected_state'], 'Kano')
        self.assertEqual(state['facility_level'], 'primary')
        self.assertEqual(state['age_group'], 'under_5')
    
    def test_clear_state(self):
        """Test state clearing."""
        # Set state
        self.state_manager.update_state({
            'selected_state': 'Lagos',
            'workflow_stage': 'confirmation'
        })
        
        # Clear
        self.state_manager.clear_state()
        
        # Check reset
        state = self.state_manager.get_state()
        self.assertIsNone(state.get('selected_state'))
        self.assertIsNone(state.get('workflow_stage'))
        self.assertEqual(state.get('current_stage'), 'initial')
    
    def test_workflow_stage_tracking(self):
        """Test workflow stage transitions."""
        stages = [
            'awaiting_file',
            'state_selection',
            'facility_selection',
            'age_selection',
            'confirmation',
            'ready',
            'processing',
            'completed'
        ]
        
        for stage in stages:
            self.state_manager.update_state({'workflow_stage': stage})
            state = self.state_manager.get_state()
            self.assertEqual(state['workflow_stage'], stage)


if __name__ == '__main__':
    unittest.main()