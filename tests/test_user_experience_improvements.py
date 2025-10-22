"""
Test suite for user experience improvements in ChatMRPT.

Tests cover:
- Welcome message system
- TPR workflow flexibility and intent classification
- Navigation commands during TPR
- Progressive disclosure based on user expertise
- Red warning text removal
- Session isolation
"""

import pytest
import json
from unittest.mock import patch, MagicMock, mock_open
from flask import session
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.data_analysis_v3.core.tpr_intent_classifier import TPRIntent, TPRIntentClassifier
from app.data_analysis_v3.core.tpr_workflow_handler import TPRWorkflowHandler
from app.data_analysis_v3.core.agent import DataAnalysisAgent


class TestWelcomeMessage:
    """Test the welcome message system in analysis_routes."""

    @pytest.fixture
    def app(self):
        """Create a test Flask app."""
        from app import create_app
        app = create_app('testing')
        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return app.test_client()

    def test_welcome_message_appears_on_first_interaction(self, client):
        """Test that welcome message appears on first 'hi' or 'hello'."""
        with client.session_transaction() as sess:
            sess['session_id'] = 'test-session-123'

        # Test with 'hi'
        response = client.post('/analyze',
                              json={'message': 'hi'},
                              content_type='application/json')

        data = json.loads(response.data)
        assert response.status_code == 200
        assert 'Welcome to ChatMRPT!' in data['response']
        assert '👋' in data['response']
        assert 'AI assistant for malaria risk assessment' in data['response']

    def test_welcome_message_only_appears_once(self, client):
        """Test that welcome message doesn't appear twice in same session."""
        with client.session_transaction() as sess:
            sess['session_id'] = 'test-session-123'

        # First interaction
        response1 = client.post('/analyze',
                               json={'message': 'hello'},
                               content_type='application/json')
        data1 = json.loads(response1.data)
        assert 'Welcome to ChatMRPT!' in data1['response']

        # Second interaction with greeting
        with patch('app.web.routes.analysis_routes.RequestInterpreter') as mock_interpreter:
            mock_instance = MagicMock()
            mock_instance.interpret.return_value = {'response': 'Regular response'}
            mock_interpreter.return_value = mock_instance

            response2 = client.post('/analyze',
                                   json={'message': 'hello'},
                                   content_type='application/json')
            data2 = json.loads(response2.data)
            assert 'Welcome to ChatMRPT!' not in data2['response']

    def test_welcome_not_shown_for_non_greeting(self, client):
        """Test that welcome message doesn't appear for non-greeting messages."""
        with client.session_transaction() as sess:
            sess['session_id'] = 'test-session-123'

        with patch('app.web.routes.analysis_routes.RequestInterpreter') as mock_interpreter:
            mock_instance = MagicMock()
            mock_instance.interpret.return_value = {'response': 'Analysis response'}
            mock_interpreter.return_value = mock_instance

            response = client.post('/analyze',
                                 json={'message': 'analyze my data'},
                                 content_type='application/json')
            data = json.loads(response.data)
            assert 'Welcome to ChatMRPT!' not in data['response']


class TestTPRIntentClassifier:
    """Test the TPR intent classification system."""

    @pytest.fixture
    def classifier(self):
        """Create a TPR intent classifier instance."""
        return TPRIntentClassifier()

    def test_help_request_classification(self, classifier):
        """Test that help requests are correctly identified."""
        help_queries = [
            "what is TPR?",
            "explain test positivity rate",
            "I don't understand",
            "can you help me?",
            "what does this mean?",
            "tell me more about facility levels"
        ]

        for query in help_queries:
            intent = classifier.classify(query, 'facility_selection')
            assert intent == TPRIntent.HELP_REQUEST, f"Failed for query: {query}"

    def test_navigation_command_detection(self, classifier):
        """Test that navigation commands are correctly identified."""
        nav_commands = {
            "go back": "back",
            "previous": "back",
            "skip this": "skip",
            "use default": "skip",
            "restart": "restart",
            "start over": "restart",
            "exit": "exit",
            "where am i": "status"
        }

        for query, expected_nav in nav_commands.items():
            intent = classifier.classify(query, 'state_selection')
            assert intent == TPRIntent.NAVIGATION
            nav_type = classifier.get_navigation_type(query)
            assert nav_type == expected_nav, f"Failed for query: {query}"

    def test_selection_detection_facility(self, classifier):
        """Test facility level selection detection."""
        selections = [
            "primary",
            "secondary",
            "tertiary",
            "all levels",
            "1",
            "2",
            "3"
        ]

        for query in selections:
            intent = classifier.classify(query, 'facility_selection')
            assert intent == TPRIntent.SELECTION, f"Failed for query: {query}"

    def test_selection_detection_age(self, classifier):
        """Test age group selection detection."""
        selections = [
            "under-5",
            "under 5",
            "5-15",
            "above 15",
            "all ages",
            "1",
            "2"
        ]

        for query in selections:
            intent = classifier.classify(query, 'age_selection')
            assert intent == TPRIntent.SELECTION, f"Failed for query: {query}"

    def test_selection_extraction(self, classifier):
        """Test that selections are correctly extracted."""
        test_cases = [
            ("primary", "facility_selection", "primary"),
            ("I'll choose secondary", "facility_selection", "secondary"),
            ("under 5", "age_selection", "under-5"),
            ("all ages please", "age_selection", "all_ages"),
            ("1", "any_selection", "1")
        ]

        for query, stage, expected in test_cases:
            extracted = classifier.extract_selection(query, stage)
            assert extracted == expected, f"Failed for query: {query}"

    def test_question_classification(self, classifier):
        """Test that general questions are identified."""
        questions = [
            "how does TPR work?",
            "what factors affect malaria?",
            "can you show me statistics?",
            "is this data accurate?"
        ]

        for query in questions:
            intent = classifier.classify(query, 'any_stage')
            assert intent in [TPRIntent.QUESTION, TPRIntent.HELP_REQUEST]


class TestTPRWorkflowFlexibility:
    """Test the flexible TPR workflow handling."""

    @pytest.fixture
    def workflow_handler(self):
        """Create a TPR workflow handler instance."""
        handler = TPRWorkflowHandler()
        handler.state = {
            'messages': [],
            'stage': 'state_selection',
            'selections': {},
            'available_states': ['Kano', 'Lagos', 'Abuja']
        }
        return handler

    def test_handle_navigation_back(self, workflow_handler):
        """Test handling 'back' navigation command."""
        workflow_handler.state['stage'] = 'facility_selection'
        workflow_handler.state['selections'] = {'state': 'Kano'}

        result = workflow_handler.handle_navigation('back')

        assert workflow_handler.state['stage'] == 'state_selection'
        assert 'state' not in workflow_handler.state['selections']
        assert 'going back' in result.lower()

    def test_handle_navigation_status(self, workflow_handler):
        """Test handling 'status' navigation command."""
        workflow_handler.state['selections'] = {
            'state': 'Kano',
            'facility_level': 'primary'
        }
        workflow_handler.state['stage'] = 'age_selection'

        result = workflow_handler.handle_navigation('status')

        assert 'Current selections' in result
        assert 'Kano' in result
        assert 'primary' in result
        assert 'age group' in result.lower()

    def test_handle_navigation_exit(self, workflow_handler):
        """Test handling 'exit' navigation command."""
        result = workflow_handler.handle_navigation('exit')

        assert workflow_handler.state['stage'] == 'completed'
        assert 'exiting' in result.lower()

    def test_acknowledgment_after_selection(self, workflow_handler):
        """Test that selections are acknowledged conversationally."""
        workflow_handler.state['stage'] = 'state_selection'

        # Mock the selection process
        with patch.object(workflow_handler, '_validate_state_selection', return_value='Kano'):
            result = workflow_handler.select_state('Kano')

            assert 'Great choice!' in result or 'selected' in result.lower()
            assert 'Kano' in result


class TestProgressiveDisclosure:
    """Test progressive disclosure based on user expertise."""

    @pytest.fixture
    def workflow_handler(self):
        """Create a TPR workflow handler instance."""
        handler = TPRWorkflowHandler()
        return handler

    def test_novice_user_gets_tips(self, workflow_handler):
        """Test that novice users receive helpful tips."""
        workflow_handler.state['messages'] = []  # Empty history = novice

        expertise = workflow_handler._determine_user_expertise()
        assert expertise == 'novice'

        # Start workflow should include tips for novice
        with patch('builtins.open', mock_open(read_data='["Kano", "Lagos"]')):
            message = workflow_handler.start_workflow()
            assert '💡' in message or 'Tip' in message or 'help' in message.lower()

    def test_expert_user_gets_concise_info(self, workflow_handler):
        """Test that expert users get concise information."""
        # Simulate expert user with technical queries in history
        workflow_handler.state['messages'] = [
            ('user', 'analyze TPR trends'),
            ('assistant', 'TPR analysis...'),
            ('user', 'show me facility-level breakdowns'),
            ('assistant', 'Facility data...'),
            ('user', 'calculate confidence intervals')
        ]

        expertise = workflow_handler._determine_user_expertise()
        assert expertise in ['intermediate', 'expert']

        # Expert users shouldn't get beginner tips
        with patch('builtins.open', mock_open(read_data='["Kano", "Lagos"]')):
            message = workflow_handler.start_workflow()
            # Message should be more concise for experts
            assert len(message) < 2000  # Arbitrary length check


class TestRedWarningTextRemoval:
    """Test that red warning text has been replaced with friendly messages."""

    def test_upload_confirmation_message(self):
        """Test that upload confirmation is friendly, not alarming."""
        from app.data_analysis_v3.core.agent import DataAnalysisAgent

        agent = DataAnalysisAgent()
        agent.state = {
            'messages': [],
            'data_loaded': True,
            'analysis_complete': False
        }

        # Mock file operations
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data='column1,column2\nval1,val2')):
                # Simulate upload confirmation
                message = agent._format_upload_confirmation()

                # Should not have warning symbols
                assert '⚠️' not in message
                assert 'IMPORTANT:' not in message

                # Should have friendly confirmation
                assert '📊' in message or 'successfully' in message.lower()
                assert 'uploaded' in message.lower()


class TestSessionIsolation:
    """Test that session data is properly isolated between users."""

    @pytest.fixture
    def app(self):
        """Create a test Flask app."""
        from app import create_app
        app = create_app('testing')
        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return app.test_client()

    def test_different_sessions_have_different_ids(self, client):
        """Test that different sessions get different IDs."""
        # First client session
        with client.session_transaction() as sess1:
            sess1['session_id'] = 'user-1-session'

        response1 = client.post('/analyze',
                               json={'message': 'hello'},
                               content_type='application/json')

        # Second client session (simulating different user)
        client = client.application.test_client()  # New client
        with client.session_transaction() as sess2:
            sess2['session_id'] = 'user-2-session'

        response2 = client.post('/analyze',
                               json={'message': 'hello'},
                               content_type='application/json')

        # Both should get welcome messages (different sessions)
        data1 = json.loads(response1.data)
        data2 = json.loads(response2.data)

        assert 'Welcome to ChatMRPT!' in data1['response']
        assert 'Welcome to ChatMRPT!' in data2['response']

    def test_session_data_paths_are_isolated(self):
        """Test that session data is stored in separate directories."""
        from app.core.unified_data_state import UnifiedDataState

        # Create two different session states
        state1 = UnifiedDataState('session-abc-123')
        state2 = UnifiedDataState('session-xyz-789')

        # Paths should be different
        assert state1.session_id != state2.session_id
        assert 'session-abc-123' in state1.base_path
        assert 'session-xyz-789' in state2.base_path
        assert state1.base_path != state2.base_path


class TestIntegrationFlow:
    """Test the complete user flow from welcome to TPR analysis."""

    @pytest.fixture
    def app(self):
        """Create a test Flask app."""
        from app import create_app
        app = create_app('testing')
        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return app.test_client()

    @patch('app.web.routes.analysis_routes.RequestInterpreter')
    @patch('app.data_analysis_v3.core.agent.DataAnalysisAgent')
    def test_complete_user_journey(self, mock_agent, mock_interpreter, client):
        """Test complete flow: welcome → upload → TPR with flexibility."""
        with client.session_transaction() as sess:
            sess['session_id'] = 'test-journey-123'

        # Step 1: User says hello, gets welcome
        response = client.post('/analyze',
                             json={'message': 'hello'},
                             content_type='application/json')
        data = json.loads(response.data)
        assert 'Welcome to ChatMRPT!' in data['response']

        # Step 2: User uploads data (mocked)
        mock_instance = MagicMock()
        mock_instance.interpret.return_value = {
            'response': '📊 **Your data has been uploaded successfully!**\n\nI can see your dataset contains...'
        }
        mock_interpreter.return_value = mock_instance

        response = client.post('/analyze',
                             json={'message': 'I uploaded my data'},
                             content_type='application/json')
        data = json.loads(response.data)
        assert '📊' in data['response']
        assert 'successfully' in data['response']
        assert '⚠️' not in data['response']  # No warning symbol

        # Step 3: User starts TPR, can ask for help
        mock_agent_instance = MagicMock()
        mock_agent_instance.process.return_value = {
            'output': 'TPR stands for Test Positivity Rate...',
            'tool_calls': []
        }
        mock_agent.return_value = mock_agent_instance

        # Simulate asking for help during TPR
        response = client.post('/data-analysis-v3',
                             json={'message': 'what is TPR?'},
                             content_type='application/json')

        # Should get help without breaking workflow
        mock_agent_instance.process.assert_called()

        # Step 4: User navigates back
        mock_agent_instance.process.return_value = {
            'output': "I'll take you back to the previous step...",
            'tool_calls': []
        }

        response = client.post('/data-analysis-v3',
                             json={'message': 'go back'},
                             content_type='application/json')

        # Navigation should work
        mock_agent_instance.process.assert_called()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])