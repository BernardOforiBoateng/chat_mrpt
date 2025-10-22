"""
Comprehensive integration tests for Arena routes.
Tests cover API endpoints, request/response handling, and end-to-end workflows.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import session

from app import create_app
from app.core.arena_manager import ArenaManager, BattleSession


class TestArenaRoutes:
    """Test suite for Arena route endpoints."""
    
    @pytest.fixture
    def app(self):
        """Create and configure a test Flask application."""
        app = create_app()
        app.config.update({
            'TESTING': True,
            'WTF_CSRF_ENABLED': False,
            'SECRET_KEY': 'test-secret-key'
        })
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create a test client for the Flask application."""
        return app.test_client()
    
    @pytest.fixture
    def auth_client(self, client):
        """Create an authenticated test client."""
        with client.session_transaction() as sess:
            sess['session_id'] = 'test-session-123'
            sess['arena_mode'] = True
        return client
    
    @patch('app.web.routes.arena_routes.arena_manager')
    def test_create_battle_endpoint(self, mock_manager, auth_client):
        """Test POST /arena/battle endpoint for creating battles."""
        mock_battle = BattleSession('test-session-123')
        mock_battle.set_models(['llama3.2-3b', 'phi3-mini'])
        mock_manager.create_battle.return_value = mock_battle
        
        response = auth_client.post('/arena/battle', 
            json={'query': 'What is Python?'},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['session_id'] == 'test-session-123'
        assert len(data['models']) == 2
        mock_manager.create_battle.assert_called_once_with('test-session-123', 'What is Python?')
    
    @patch('app.web.routes.arena_routes.arena_manager')
    def test_get_battle_endpoint(self, mock_manager, auth_client):
        """Test GET /arena/battle/<session_id> endpoint."""
        mock_battle = BattleSession('test-session-123')
        mock_battle.user_query = 'Test query'
        mock_battle.set_models(['gemma2-2b', 'qwen2.5-3b'])
        mock_battle.add_response('gemma2-2b', 'Response from Gemma')
        mock_manager.get_battle.return_value = mock_battle
        
        response = auth_client.get('/arena/battle/test-session-123')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['session_id'] == 'test-session-123'
        assert data['query'] == 'Test query'
        assert 'gemma2-2b' in data['responses']
    
    @patch('app.web.routes.arena_routes.arena_manager')
    def test_get_nonexistent_battle(self, mock_manager, auth_client):
        """Test getting non-existent battle returns 404."""
        mock_manager.get_battle.return_value = None
        
        response = auth_client.get('/arena/battle/nonexistent')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'Battle not found'
    
    @patch('app.web.routes.arena_routes.arena_manager')
    def test_add_response_endpoint(self, mock_manager, auth_client):
        """Test POST /arena/battle/<session_id>/response endpoint."""
        mock_manager.add_model_response.return_value = True
        
        response = auth_client.post('/arena/battle/test-session-123/response',
            json={
                'model': 'llama3.2-3b',
                'response': 'This is a test response'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        mock_manager.add_model_response.assert_called_once_with(
            'test-session-123', 
            'llama3.2-3b', 
            'This is a test response'
        )
    
    @patch('app.web.routes.arena_routes.arena_manager')
    def test_vote_endpoint(self, mock_manager, auth_client):
        """Test POST /arena/battle/<session_id>/vote endpoint."""
        mock_manager.record_vote.return_value = True
        
        response = auth_client.post('/arena/battle/test-session-123/vote',
            json={'model': 'phi3-mini'},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        mock_manager.record_vote.assert_called_once_with('test-session-123', 'phi3-mini')
    
    @patch('app.web.routes.arena_routes.arena_manager')
    def test_reveal_models_endpoint(self, mock_manager, auth_client):
        """Test POST /arena/battle/<session_id>/reveal endpoint."""
        mock_battle = BattleSession('test-session-123')
        mock_battle.set_models(['llama3.2-3b', 'phi3-mini'])
        mock_battle.revealed = True
        mock_manager.reveal_models.return_value = True
        mock_manager.get_battle.return_value = mock_battle
        
        response = auth_client.post('/arena/battle/test-session-123/reveal')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['models'] == ['llama3.2-3b', 'phi3-mini']
        mock_manager.reveal_models.assert_called_once_with('test-session-123')
    
    @patch('app.web.routes.arena_routes.arena_manager')
    def test_status_endpoint(self, mock_manager, auth_client):
        """Test GET /arena/status endpoint."""
        mock_battles = [
            BattleSession('battle-1'),
            BattleSession('battle-2')
        ]
        mock_manager.get_active_battles.return_value = mock_battles
        mock_manager.storage_status = 'redis'
        
        response = auth_client.get('/arena/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['active_battles'] == 2
        assert data['storage_status'] == 'redis'
        assert data['arena_enabled'] is True
    
    def test_unauthenticated_access(self, client):
        """Test that unauthenticated requests are handled properly."""
        response = client.post('/arena/battle',
            json={'query': 'Test'},
            content_type='application/json'
        )
        
        # Should either redirect to login or return 401
        assert response.status_code in [302, 401]
    
    @patch('app.web.routes.arena_routes.arena_manager')
    def test_invalid_json_handling(self, mock_manager, auth_client):
        """Test handling of invalid JSON in requests."""
        response = auth_client.post('/arena/battle',
            data='invalid json{',
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    @patch('app.web.routes.arena_routes.arena_manager')
    def test_missing_required_fields(self, mock_manager, auth_client):
        """Test handling of missing required fields in requests."""
        # Missing 'query' field
        response = auth_client.post('/arena/battle',
            json={},
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    @patch('app.web.routes.arena_routes.arena_manager')
    def test_concurrent_battle_creation(self, mock_manager, auth_client):
        """Test handling concurrent battle creation requests."""
        mock_battle = BattleSession('test-session-123')
        mock_manager.create_battle.return_value = mock_battle
        
        # Simulate concurrent requests
        responses = []
        for i in range(3):
            response = auth_client.post('/arena/battle',
                json={'query': f'Query {i}'},
                content_type='application/json'
            )
            responses.append(response)
        
        # All should succeed
        assert all(r.status_code == 200 for r in responses)
        assert mock_manager.create_battle.call_count == 3


class TestArenaMessageFlow:
    """Test suite for complete Arena message flow."""
    
    @pytest.fixture
    def app(self):
        """Create test Flask application."""
        app = create_app()
        app.config.update({
            'TESTING': True,
            'SECRET_KEY': 'test-key'
        })
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    @patch('app.web.routes.analysis_routes.arena_manager')
    @patch('app.web.routes.analysis_routes.openai_client')
    @patch('app.web.routes.analysis_routes.ollama_adapter')
    def test_arena_mode_message_flow(self, mock_ollama, mock_openai, mock_arena, client):
        """Test complete Arena mode message flow through /send_message."""
        # Setup mocks
        mock_battle = BattleSession('test-session')
        mock_battle.set_models(['llama3.2-3b', 'phi3-mini'])
        mock_arena.get_battle.return_value = mock_battle
        mock_arena.create_battle.return_value = mock_battle
        
        mock_ollama.generate.return_value = {
            'response': 'Ollama response',
            'done': True
        }
        
        # Set session for Arena mode
        with client.session_transaction() as sess:
            sess['session_id'] = 'test-session'
            sess['arena_mode'] = True
        
        # Send message
        response = client.post('/send_message',
            json={
                'message': 'What is AI?',
                'mode': 'arena'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        # Verify Arena battle was created
        mock_arena.create_battle.assert_called_once()
        
        # Verify Ollama was called for local models
        assert mock_ollama.generate.call_count >= 1
    
    @patch('app.web.routes.analysis_routes.openai_client')
    def test_tool_calling_mode_flow(self, mock_openai, client):
        """Test tool-calling mode using GPT-4o."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='GPT-4o response'))
        ]
        mock_openai.chat.completions.create.return_value = mock_response
        
        with client.session_transaction() as sess:
            sess['session_id'] = 'test-session'
            sess['arena_mode'] = False
        
        response = client.post('/send_message',
            json={
                'message': 'Analyze this data',
                'mode': 'tool_calling'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        mock_openai.chat.completions.create.assert_called_once()
    
    @patch('app.web.routes.analysis_routes.arena_manager')
    def test_arena_mode_toggle(self, mock_arena, client):
        """Test toggling Arena mode on and off."""
        with client.session_transaction() as sess:
            sess['session_id'] = 'test-session'
        
        # Enable Arena mode
        response = client.post('/arena/toggle',
            json={'enabled': True},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        with client.session_transaction() as sess:
            assert sess.get('arena_mode') is True
        
        # Disable Arena mode
        response = client.post('/arena/toggle',
            json={'enabled': False},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        with client.session_transaction() as sess:
            assert sess.get('arena_mode') is False


class TestArenaErrorHandling:
    """Test suite for Arena error handling scenarios."""
    
    @pytest.fixture
    def app(self):
        """Create test Flask application."""
        app = create_app()
        app.config.update({'TESTING': True})
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    @patch('app.web.routes.arena_routes.arena_manager')
    def test_redis_connection_failure(self, mock_arena, client):
        """Test handling when Redis connection fails."""
        mock_arena.create_battle.side_effect = Exception("Redis connection failed")
        
        with client.session_transaction() as sess:
            sess['session_id'] = 'test-session'
            sess['arena_mode'] = True
        
        response = client.post('/arena/battle',
            json={'query': 'Test query'},
            content_type='application/json'
        )
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
    
    @patch('app.web.routes.analysis_routes.ollama_adapter')
    def test_ollama_failure_fallback(self, mock_ollama, client):
        """Test fallback when Ollama fails."""
        mock_ollama.generate.return_value = None
        
        with client.session_transaction() as sess:
            sess['session_id'] = 'test-session'
            sess['arena_mode'] = True
        
        response = client.post('/send_message',
            json={
                'message': 'Test message',
                'mode': 'arena'
            },
            content_type='application/json'
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 503]
    
    @patch('app.web.routes.arena_routes.arena_manager')
    def test_invalid_model_vote(self, mock_arena, client):
        """Test voting for invalid model."""
        mock_arena.record_vote.return_value = False
        
        with client.session_transaction() as sess:
            sess['session_id'] = 'test-session'
        
        response = client.post('/arena/battle/test-session/vote',
            json={'model': 'invalid-model'},
            content_type='application/json'
        )
        
        assert response.status_code in [400, 500]
        data = json.loads(response.data)
        assert data['success'] is False


class TestArenaPerformance:
    """Test suite for Arena performance and scalability."""
    
    @patch('app.core.arena_manager.RedisStorage')
    def test_large_response_handling(self, mock_storage):
        """Test handling of large model responses."""
        from app.core.arena_manager import ArenaManager
        
        mock_storage_instance = MagicMock()
        mock_storage.return_value = mock_storage_instance
        
        manager = ArenaManager()
        battle = manager.create_battle('test-session', 'Query')
        
        # Add large response (10KB)
        large_response = 'x' * 10000
        success = manager.add_model_response('test-session', 'llama3.2-3b', large_response)
        
        # Should handle large responses
        assert success is not False
    
    @patch('app.core.arena_manager.RedisStorage')
    def test_many_concurrent_battles(self, mock_storage):
        """Test handling many concurrent battles."""
        from app.core.arena_manager import ArenaManager
        
        mock_storage_instance = MagicMock()
        mock_storage_instance.store_battle.return_value = True
        mock_storage.return_value = mock_storage_instance
        
        manager = ArenaManager()
        
        # Create many battles
        battles = []
        for i in range(100):
            battle = manager.create_battle(f'session-{i}', f'Query {i}')
            battles.append(battle)
        
        assert len(battles) == 100
        assert mock_storage_instance.store_battle.call_count == 100
    
    @patch('app.core.arena_manager.RedisStorage')
    def test_cleanup_performance(self, mock_storage):
        """Test performance of cleanup operation."""
        from app.core.arena_manager import ArenaManager
        from datetime import datetime, timedelta
        
        # Create old and new battles
        old_battles = []
        new_battles = []
        
        for i in range(50):
            old_battle = BattleSession(f'old-{i}')
            old_battle.timestamp = (datetime.now() - timedelta(hours=25)).isoformat()
            old_battles.append(old_battle)
            
            new_battle = BattleSession(f'new-{i}')
            new_battle.timestamp = datetime.now().isoformat()
            new_battles.append(new_battle)
        
        mock_storage_instance = MagicMock()
        mock_storage_instance.list_battles.return_value = old_battles + new_battles
        mock_storage_instance.delete_battle.return_value = True
        mock_storage.return_value = mock_storage_instance
        
        manager = ArenaManager()
        cleaned = manager.cleanup_old_battles(max_age_hours=24)
        
        assert cleaned == 50
        assert mock_storage_instance.delete_battle.call_count == 50