"""
Comprehensive test suite for Intent Clarification System
Tests all aspects of the new interactive intent detection and routing
"""

import pytest
import json
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.intent_clarifier import IntentClarifier, IntentType


class TestIntentClarifier:
    """Test the IntentClarifier class"""
    
    @pytest.fixture
    def clarifier(self):
        """Create an IntentClarifier instance for testing"""
        return IntentClarifier()
    
    @pytest.fixture
    def session_context_no_data(self):
        """Session context with no uploaded data"""
        return {
            'has_uploaded_files': False,
            'session_id': 'test_session_123',
            'csv_loaded': False,
            'shapefile_loaded': False,
            'analysis_complete': False
        }
    
    @pytest.fixture
    def session_context_with_data(self):
        """Session context with uploaded data"""
        return {
            'has_uploaded_files': True,
            'session_id': 'test_session_456',
            'csv_loaded': True,
            'shapefile_loaded': True,
            'analysis_complete': False
        }
    
    @pytest.fixture
    def session_context_with_analysis(self):
        """Session context with completed analysis"""
        return {
            'has_uploaded_files': True,
            'session_id': 'test_session_789',
            'csv_loaded': True,
            'shapefile_loaded': True,
            'analysis_complete': True
        }
    
    def test_no_data_general_question(self, clarifier, session_context_no_data):
        """Test that general questions without data go to Arena"""
        messages = [
            "What is malaria?",
            "How does mosquito transmission work?",
            "Explain vector control",
            "Tell me about ITN distribution"
        ]
        
        for message in messages:
            intent = clarifier.analyze_intent(message, session_context_no_data)
            assert intent == 'arena', f"Message '{message}' should route to arena"
    
    def test_no_data_action_requests(self, clarifier, session_context_no_data):
        """Test that action requests without data still go to Arena (no tools available)"""
        messages = [
            "Calculate the risk score",
            "Analyze the data",
            "Show me the rankings"
        ]
        
        for message in messages:
            intent = clarifier.analyze_intent(message, session_context_no_data)
            assert intent == 'arena', f"Message '{message}' without data should route to arena"
    
    def test_with_data_clear_action(self, clarifier, session_context_with_data):
        """Test that clear action requests with data go to Tools"""
        messages = [
            "Analyze my data",
            "Run analysis on my uploaded file",
            "Process the data I uploaded"
        ]
        
        for message in messages:
            intent = clarifier.analyze_intent(message, session_context_with_data)
            assert intent == 'tools', f"Message '{message}' with data should route to tools"
    
    def test_with_data_clear_explanation(self, clarifier, session_context_with_data):
        """Test that clear explanation requests go to Arena even with data"""
        messages = [
            "What is PCA analysis?",
            "How does composite scoring work?",
            "Explain malaria transmission"
        ]
        
        for message in messages:
            intent = clarifier.analyze_intent(message, session_context_with_data)
            assert intent == 'arena', f"Message '{message}' should route to arena for explanation"
    
    def test_ambiguous_requests(self, clarifier, session_context_with_data):
        """Test that ambiguous requests trigger clarification"""
        messages = [
            "Tell me how to analyze",
            "Show me how to process",
            "Explain how to calculate"
        ]
        
        for message in messages:
            intent = clarifier.analyze_intent(message, session_context_with_data)
            assert intent == 'ambiguous', f"Message '{message}' should be ambiguous"
    
    def test_generate_clarification_with_data(self, clarifier, session_context_with_data):
        """Test clarification generation with uploaded data"""
        message = "Tell me about vulnerability"
        clarification = clarifier.generate_clarification(message, session_context_with_data)
        
        assert clarification['needs_clarification'] == True
        assert clarification['clarification_type'] == 'intent'
        assert len(clarification['options']) == 2
        assert clarification['original_message'] == message
        assert any('analyze' in opt['id'].lower() for opt in clarification['options'])
        assert any('explain' in opt['id'].lower() or 'general' in opt['id'].lower() 
                  for opt in clarification['options'])
    
    def test_generate_clarification_with_analysis(self, clarifier, session_context_with_analysis):
        """Test clarification generation after analysis completion"""
        message = "Explain the rankings"
        clarification = clarifier.generate_clarification(message, session_context_with_analysis)
        
        assert clarification['needs_clarification'] == True
        assert len(clarification['options']) == 2
        # Should offer to explain results or general concept
        assert any('results' in opt['label'].lower() for opt in clarification['options'])
        assert any('concept' in opt['label'].lower() for opt in clarification['options'])
    
    def test_handle_clarification_response_numeric(self, clarifier):
        """Test handling numeric clarification responses"""
        original_context = {
            'original_message': 'Tell me about rankings'
        }
        
        # Test selecting option 1 (tools)
        intent, message = clarifier.handle_clarification_response('1', original_context)
        assert intent == 'tools'
        assert message == 'Tell me about rankings'
        
        # Test selecting option 2 (arena)
        intent, message = clarifier.handle_clarification_response('2', original_context)
        assert intent == 'arena'
        assert message == 'Tell me about rankings'
    
    def test_handle_clarification_response_text(self, clarifier):
        """Test handling text clarification responses"""
        original_context = {
            'original_message': 'Explain vulnerability'
        }
        
        # Test selecting by keyword
        intent, message = clarifier.handle_clarification_response('analyze my data', original_context)
        assert intent == 'tools'
        
        intent, message = clarifier.handle_clarification_response('explain the concept', original_context)
        assert intent == 'arena'
    
    def test_direct_tool_commands(self, clarifier, session_context_with_data):
        """Test that direct tool commands are recognized"""
        messages = [
            "run analysis",
            "start analysis",
            "perform analysis",
            "generate report",
            "export results"
        ]
        
        for message in messages:
            intent = clarifier.analyze_intent(message, session_context_with_data)
            assert intent == 'tools', f"Direct command '{message}' should route to tools"
    
    def test_references_user_data(self, clarifier, session_context_with_data):
        """Test detection of references to user's data"""
        clarifier_inst = clarifier
        
        # Should detect references
        assert clarifier_inst._references_user_data("analyze my data", session_context_with_data)
        assert clarifier_inst._references_user_data("the uploaded file", session_context_with_data)
        assert clarifier_inst._references_user_data("our data", session_context_with_data)
        
        # Should not detect references (no possessive or direct reference)
        assert not clarifier_inst._references_user_data("what is malaria", session_context_with_data)
        assert not clarifier_inst._references_user_data("explain PCA", session_context_with_data)


class TestRoutingIntegration:
    """Test the integration with analysis_routes.py"""
    
    @pytest.fixture
    def app(self):
        """Create a Flask app for testing"""
        from app import create_app
        app = create_app('testing')
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create a test client"""
        return app.test_client()
    
    def test_send_message_no_data_arena(self, client):
        """Test that messages without data go to Arena"""
        with client.session_transaction() as sess:
            sess['session_id'] = 'test_no_data'
        
        response = client.post('/send_message', 
                              json={'message': 'What is malaria?'},
                              content_type='application/json')
        
        # Should not return clarification
        assert response.status_code == 200
        data = response.get_json()
        assert 'needs_clarification' not in data or data.get('needs_clarification') == False
    
    def test_send_message_with_data_ambiguous(self, client, tmpdir):
        """Test that ambiguous messages with data trigger clarification"""
        # Create a mock uploaded file
        session_id = 'test_with_data'
        upload_dir = Path('instance/uploads') / session_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a dummy CSV file
        csv_file = upload_dir / 'data.csv'
        csv_file.write_text('ward,value\nWard1,10\nWard2,20')
        
        try:
            with client.session_transaction() as sess:
                sess['session_id'] = session_id
                sess['csv_loaded'] = True
                sess['has_uploaded_files'] = True
            
            response = client.post('/send_message',
                                  json={'message': 'Tell me about the rankings'},
                                  content_type='application/json')
            
            assert response.status_code == 200
            data = response.get_json()
            
            # Should return clarification
            assert data.get('needs_clarification') == True
            assert 'options' in data
            assert len(data['options']) > 0
            
        finally:
            # Cleanup
            import shutil
            if upload_dir.exists():
                shutil.rmtree(upload_dir)
    
    def test_send_message_clarification_response(self, client):
        """Test handling of clarification responses"""
        session_id = 'test_clarification'
        
        with client.session_transaction() as sess:
            sess['session_id'] = session_id
            sess['pending_clarification'] = {
                'original_message': 'Explain the results',
                'context': {'has_uploaded_files': True}
            }
        
        # Send response selecting option 1 (tools)
        response = client.post('/send_message',
                              json={'message': '1'},
                              content_type='application/json')
        
        assert response.status_code == 200
        
        # Check that pending_clarification was cleared
        with client.session_transaction() as sess:
            assert 'pending_clarification' not in sess
    
    @patch('app.web.routes.analysis_routes.request_interpreter')
    def test_streaming_endpoint_clarification(self, mock_interpreter, client):
        """Test that streaming endpoint also handles clarification"""
        session_id = 'test_streaming'
        upload_dir = Path('instance/uploads') / session_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a dummy CSV file
        csv_file = upload_dir / 'data.csv'
        csv_file.write_text('ward,value\nWard1,10')
        
        try:
            with client.session_transaction() as sess:
                sess['session_id'] = session_id
                sess['csv_loaded'] = True
            
            response = client.post('/send_message_streaming',
                                  json={'message': 'Explain vulnerability'},
                                  content_type='application/json')
            
            assert response.status_code == 200
            assert response.content_type == 'text/event-stream'
            
            # Read streaming response
            data = b''.join(response.response)
            # Should contain clarification in the stream
            assert b'needs_clarification' in data or b'arena_mode' in data
            
        finally:
            # Cleanup
            import shutil
            if upload_dir.exists():
                shutil.rmtree(upload_dir)


class TestEndToEndScenarios:
    """Test complete user scenarios"""
    
    @pytest.fixture
    def app(self):
        """Create a Flask app for testing"""
        from app import create_app
        app = create_app('testing')
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create a test client"""
        return app.test_client()
    
    def test_scenario_no_data_conversation(self, client):
        """Test a conversation without uploaded data"""
        session_id = 'scenario_no_data'
        
        with client.session_transaction() as sess:
            sess['session_id'] = session_id
        
        # All questions should go to Arena without clarification
        questions = [
            "What is malaria?",
            "How is it transmitted?",
            "What are ITNs?",
            "Explain vector control"
        ]
        
        for question in questions:
            response = client.post('/send_message',
                                  json={'message': question},
                                  content_type='application/json')
            
            assert response.status_code == 200
            data = response.get_json()
            # Should not ask for clarification
            assert not data.get('needs_clarification', False)
    
    def test_scenario_with_data_mixed_intents(self, client):
        """Test a conversation with data and mixed intents"""
        session_id = 'scenario_with_data'
        upload_dir = Path('instance/uploads') / session_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Create dummy files
        csv_file = upload_dir / 'data.csv'
        csv_file.write_text('ward,population,cases\nWard1,1000,50\nWard2,2000,30')
        
        try:
            with client.session_transaction() as sess:
                sess['session_id'] = session_id
                sess['csv_loaded'] = True
                sess['has_uploaded_files'] = True
            
            # Clear action - should go to tools
            response = client.post('/send_message',
                                  json={'message': 'Analyze my data'},
                                  content_type='application/json')
            assert response.status_code == 200
            assert not response.get_json().get('needs_clarification', False)
            
            # Clear explanation - should go to arena
            response = client.post('/send_message',
                                  json={'message': 'What is PCA analysis?'},
                                  content_type='application/json')
            assert response.status_code == 200
            assert not response.get_json().get('needs_clarification', False)
            
            # Ambiguous - should trigger clarification
            response = client.post('/send_message',
                                  json={'message': 'Tell me about the rankings'},
                                  content_type='application/json')
            assert response.status_code == 200
            data = response.get_json()
            assert data.get('needs_clarification') == True
            
            # Store pending clarification
            with client.session_transaction() as sess:
                sess['pending_clarification'] = {
                    'original_message': 'Tell me about the rankings',
                    'context': {'has_uploaded_files': True}
                }
            
            # Respond to clarification
            response = client.post('/send_message',
                                  json={'message': '1'},  # Choose analysis
                                  content_type='application/json')
            assert response.status_code == 200
            
        finally:
            # Cleanup
            import shutil
            if upload_dir.exists():
                shutil.rmtree(upload_dir)
    
    def test_scenario_tpr_workflow(self, client):
        """Test that TPR workflow bypasses clarification"""
        session_id = 'scenario_tpr'
        
        with client.session_transaction() as sess:
            sess['session_id'] = session_id
            sess['tpr_workflow_active'] = True
        
        # Should not trigger clarification even for ambiguous messages
        response = client.post('/send_message',
                              json={'message': 'Explain the results'},
                              content_type='application/json')
        
        # TPR workflow should handle this directly
        assert response.status_code == 200
        # Note: Actual TPR handling depends on TPR module availability


class TestArenaIntegration:
    """Test Arena mode integration"""
    
    @pytest.fixture
    def app(self):
        """Create a Flask app for testing"""
        from app import create_app
        app = create_app('testing')
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create a test client"""
        return app.test_client()
    
    @patch('app.web.routes.analysis_routes.ArenaManager')
    @patch('app.web.routes.analysis_routes.requests')
    def test_arena_mode_activated(self, mock_requests, mock_arena_manager, client):
        """Test that Arena mode is properly activated"""
        session_id = 'test_arena'
        
        # Mock Arena responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Arena response'}}]
        }
        mock_requests.post.return_value = mock_response
        
        # Mock Arena manager
        mock_arena_instance = Mock()
        mock_arena_instance.start_battle = Mock(return_value={
            'battle_id': 'battle_123'
        })
        mock_arena_instance.get_random_model_pair = Mock(return_value=(
            'llama3.1:8b', 'mistral:7b'
        ))
        mock_arena_manager.return_value = mock_arena_instance
        
        with client.session_transaction() as sess:
            sess['session_id'] = session_id
        
        response = client.post('/send_message',
                              json={'message': 'What is malaria?'},
                              content_type='application/json')
        
        assert response.status_code == 200


if __name__ == '__main__':
    # Run tests with coverage
    pytest.main([__file__, '-v', '--cov=app.core.intent_clarifier', '--cov=app.web.routes.analysis_routes'])