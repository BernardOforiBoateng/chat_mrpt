"""
Comprehensive unit tests for Arena Manager with Redis storage.
Tests cover battle session management, Redis persistence, and cross-worker functionality.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import fakeredis

from app.core.arena_manager import (
    ArenaManager, 
    BattleSession, 
    RedisStorage,
    ELORatingSystem
)


class TestBattleSession:
    """Test suite for BattleSession class."""
    
    def test_battle_session_initialization(self):
        """Test that BattleSession initializes correctly."""
        session = BattleSession(session_id='test-123')
        
        assert session.session_id == 'test-123'
        assert session.timestamp is not None
        assert session.models == []
        assert session.responses == {}
        assert session.user_query == ""
        assert session.vote is None
        assert session.revealed is False
        assert session.mode == 'general'
    
    def test_set_models(self):
        """Test setting models for a battle session."""
        session = BattleSession(session_id='test-123')
        models = ['llama3.2-3b', 'phi3-mini']
        
        session.set_models(models)
        
        assert session.models == models
        assert len(session.models) == 2
    
    def test_add_response(self):
        """Test adding responses from models."""
        session = BattleSession(session_id='test-123')
        session.set_models(['llama3.2-3b', 'phi3-mini'])
        
        session.add_response('llama3.2-3b', 'Response from Llama')
        session.add_response('phi3-mini', 'Response from Phi')
        
        assert 'llama3.2-3b' in session.responses
        assert session.responses['llama3.2-3b'] == 'Response from Llama'
        assert 'phi3-mini' in session.responses
        assert session.responses['phi3-mini'] == 'Response from Phi'
    
    def test_record_vote(self):
        """Test recording user votes."""
        session = BattleSession(session_id='test-123')
        session.set_models(['llama3.2-3b', 'phi3-mini'])
        
        session.record_vote('llama3.2-3b')
        
        assert session.vote == 'llama3.2-3b'
    
    def test_reveal_models(self):
        """Test revealing models after voting."""
        session = BattleSession(session_id='test-123')
        
        session.reveal_models()
        
        assert session.revealed is True
    
    def test_to_dict_serialization(self):
        """Test serialization to dictionary."""
        session = BattleSession(session_id='test-123')
        session.set_models(['llama3.2-3b', 'phi3-mini'])
        session.user_query = "Test query"
        session.add_response('llama3.2-3b', 'Response 1')
        session.record_vote('llama3.2-3b')
        
        data = session.to_dict()
        
        assert data['session_id'] == 'test-123'
        assert data['models'] == ['llama3.2-3b', 'phi3-mini']
        assert data['user_query'] == "Test query"
        assert data['responses']['llama3.2-3b'] == 'Response 1'
        assert data['vote'] == 'llama3.2-3b'
        assert data['revealed'] is False
        assert 'timestamp' in data
    
    def test_from_dict_deserialization(self):
        """Test deserialization from dictionary."""
        data = {
            'session_id': 'test-456',
            'timestamp': datetime.now().isoformat(),
            'models': ['gemma2-2b', 'qwen2.5-3b'],
            'responses': {
                'gemma2-2b': 'Gemma response',
                'qwen2.5-3b': 'Qwen response'
            },
            'user_query': 'Deserialized query',
            'vote': 'gemma2-2b',
            'revealed': True,
            'mode': 'tool_calling'
        }
        
        session = BattleSession.from_dict(data)
        
        assert session.session_id == 'test-456'
        assert session.models == ['gemma2-2b', 'qwen2.5-3b']
        assert session.user_query == 'Deserialized query'
        assert session.responses['gemma2-2b'] == 'Gemma response'
        assert session.vote == 'gemma2-2b'
        assert session.revealed is True
        assert session.mode == 'tool_calling'


class TestRedisStorage:
    """Test suite for RedisStorage class."""
    
    def test_redis_storage_initialization(self, fake_redis_client):
        """Test Redis storage initialization."""
        with patch('app.core.arena_manager.redis.StrictRedis', return_value=fake_redis_client):
            storage = RedisStorage(
                redis_host='localhost',
                redis_port=6379,
                redis_password=None,
                redis_db=1
            )
            
            assert storage.redis_host == 'localhost'
            assert storage.redis_port == 6379
            assert storage.redis_db == 1
            assert storage.redis_client is not None
    
    def test_store_battle(self, mock_redis_storage, sample_battle_session):
        """Test storing battle session in Redis."""
        result = mock_redis_storage.store_battle(sample_battle_session)
        
        assert result is True
        
        # Verify data was stored
        key = f"arena:battle:{sample_battle_session.session_id}"
        stored_data = mock_redis_storage.redis_client.get(key)
        assert stored_data is not None
        
        # Verify TTL was set
        ttl = mock_redis_storage.redis_client.ttl(key)
        assert ttl > 0
    
    def test_get_battle(self, mock_redis_storage, sample_battle_session):
        """Test retrieving battle session from Redis."""
        # Store the battle first
        mock_redis_storage.store_battle(sample_battle_session)
        
        # Retrieve it
        retrieved = mock_redis_storage.get_battle(sample_battle_session.session_id)
        
        assert retrieved is not None
        assert retrieved.session_id == sample_battle_session.session_id
        assert retrieved.user_query == sample_battle_session.user_query
        assert retrieved.models == sample_battle_session.models
    
    def test_get_nonexistent_battle(self, mock_redis_storage):
        """Test retrieving non-existent battle returns None."""
        result = mock_redis_storage.get_battle('nonexistent-id')
        
        assert result is None
    
    def test_update_battle(self, mock_redis_storage, sample_battle_session):
        """Test updating existing battle session."""
        # Store initial battle
        mock_redis_storage.store_battle(sample_battle_session)
        
        # Update the battle
        sample_battle_session.record_vote('llama3.2-3b')
        sample_battle_session.reveal_models()
        result = mock_redis_storage.update_battle(sample_battle_session)
        
        assert result is True
        
        # Verify updates were saved
        retrieved = mock_redis_storage.get_battle(sample_battle_session.session_id)
        assert retrieved.vote == 'llama3.2-3b'
        assert retrieved.revealed is True
    
    def test_delete_battle(self, mock_redis_storage, sample_battle_session):
        """Test deleting battle session from Redis."""
        # Store battle first
        mock_redis_storage.store_battle(sample_battle_session)
        
        # Delete it
        result = mock_redis_storage.delete_battle(sample_battle_session.session_id)
        
        assert result is True
        
        # Verify it's deleted
        retrieved = mock_redis_storage.get_battle(sample_battle_session.session_id)
        assert retrieved is None
    
    def test_list_battles(self, mock_redis_storage):
        """Test listing all battle sessions."""
        # Store multiple battles
        for i in range(3):
            battle = BattleSession(session_id=f'battle-{i}')
            battle.user_query = f"Query {i}"
            mock_redis_storage.store_battle(battle)
        
        battles = mock_redis_storage.list_battles()
        
        assert len(battles) == 3
        assert all(b.session_id.startswith('battle-') for b in battles)
    
    def test_connection_error_handling(self):
        """Test handling of Redis connection errors."""
        with patch('app.core.arena_manager.redis.StrictRedis') as mock_redis:
            mock_redis.side_effect = Exception("Connection refused")
            
            storage = RedisStorage(redis_host='invalid-host')
            
            # Should handle error gracefully
            assert storage.redis_client is None
            
            # Methods should return appropriate defaults
            assert storage.get_battle('any-id') is None
            assert storage.store_battle(BattleSession('test')) is False
            assert storage.list_battles() == []


class TestArenaModelManagement:
    """Test suite for Arena model management functionality."""
    
    @patch('app.core.arena_manager.RedisStorage')
    @patch('app.core.arena_manager.DatabaseManager')
    @patch('app.core.arena_manager.EventLogger')
    def test_available_models_initialization(self, mock_event_logger, mock_db_manager, mock_storage):
        """Test ArenaManager initializes with correct available models."""
        mock_storage_instance = MagicMock()
        mock_storage.return_value = mock_storage_instance
        
        manager = ArenaManager()
        
        assert len(manager.available_models) == 5
        assert 'llama3.2-3b' in manager.available_models
        assert 'phi3-mini' in manager.available_models
        assert 'gemma2-2b' in manager.available_models
        assert 'qwen2.5-3b' in manager.available_models
        assert 'mistral-7b' in manager.available_models
    
    @patch('app.core.arena_manager.RedisStorage')
    @patch('app.core.arena_manager.DatabaseManager')
    @patch('app.core.arena_manager.EventLogger')
    def test_get_model_pair_for_view(self, mock_event_logger, mock_db_manager, mock_storage):
        """Test getting specific model pairs by view index."""
        mock_storage_instance = MagicMock()
        mock_storage.return_value = mock_storage_instance
        
        manager = ArenaManager()
        
        # Test different view indices
        pair0 = manager.get_model_pair_for_view(0)
        assert pair0 == ('llama3.2-3b', 'phi3-mini')
        
        pair1 = manager.get_model_pair_for_view(1)
        assert pair1 == ('gemma2-2b', 'qwen2.5-3b')
        
        pair2 = manager.get_model_pair_for_view(2)
        assert pair2 == ('mistral-7b', 'llama3.2-3b')
    
    @patch('app.core.arena_manager.RedisStorage')
    @patch('app.core.arena_manager.DatabaseManager')
    @patch('app.core.arena_manager.EventLogger')
    def test_get_random_model_pair(self, mock_event_logger, mock_db_manager, mock_storage):
        """Test getting random model pairs."""
        mock_storage_instance = MagicMock()
        mock_storage.return_value = mock_storage_instance
        
        manager = ArenaManager()
        
        pair = manager.get_random_model_pair()
        
        assert len(pair) == 2
        assert pair[0] != pair[1]
        assert all(model in manager.available_models for model in pair)


class TestArenaManager:
    """Test suite for ArenaManager class."""
    
    @patch('app.core.arena_manager.RedisStorage')
    @patch('app.core.arena_manager.DatabaseManager')
    @patch('app.core.arena_manager.EventLogger')
    def test_arena_manager_initialization(self, mock_event_logger, mock_db_manager, mock_storage_class):
        """Test ArenaManager initialization."""
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage
        
        manager = ArenaManager()
        
        assert manager.storage is not None
        assert manager.available_models is not None
        assert len(manager.available_models) == 5
    
    @patch('app.core.arena_manager.RedisStorage')
    @patch('app.core.arena_manager.DatabaseManager')
    @patch('app.core.arena_manager.EventLogger')
    def test_create_battle(self, mock_event_logger, mock_db_manager, mock_storage_class):
        """Test creating a new battle."""
        mock_storage = MagicMock()
        mock_storage.store_battle.return_value = True
        mock_storage_class.return_value = mock_storage
        
        manager = ArenaManager()
        battle = manager.create_battle('session-789', 'What is AI?')
        
        assert battle is not None
        assert battle.session_id == 'session-789'
        assert battle.user_query == 'What is AI?'
        assert len(battle.models) == 2
        mock_storage.store_battle.assert_called_once()
    
    @patch('app.core.arena_manager.RedisStorage')
    @patch('app.core.arena_manager.DatabaseManager')
    @patch('app.core.arena_manager.EventLogger')
    def test_get_battle(self, mock_event_logger, mock_db_manager, mock_storage_class):
        """Test retrieving a battle."""
        mock_storage = MagicMock()
        mock_battle = BattleSession('test-session')
        mock_storage.get_battle.return_value = mock_battle
        mock_storage_class.return_value = mock_storage
        
        manager = ArenaManager()
        battle = manager.get_battle('test-session')
        
        assert battle == mock_battle
        mock_storage.get_battle.assert_called_once_with('test-session')
    
    @patch('app.core.arena_manager.RedisStorage')
    @patch('app.core.arena_manager.DatabaseManager')
    @patch('app.core.arena_manager.EventLogger')
    def test_add_model_response(self, mock_event_logger, mock_db_manager, mock_storage_class):
        """Test adding model response to battle."""
        mock_storage = MagicMock()
        mock_battle = BattleSession('test-session')
        mock_battle.set_models(['llama3.2-3b', 'phi3-mini'])
        mock_storage.get_battle.return_value = mock_battle
        mock_storage.update_battle.return_value = True
        mock_storage_class.return_value = mock_storage
        
        manager = ArenaManager()
        success = manager.add_model_response('test-session', 'llama3.2-3b', 'Test response')
        
        assert success is True
        assert 'llama3.2-3b' in mock_battle.responses
        assert mock_battle.responses['llama3.2-3b'] == 'Test response'
        mock_storage.update_battle.assert_called_once()
    
    @patch('app.core.arena_manager.RedisStorage')
    @patch('app.core.arena_manager.DatabaseManager')
    @patch('app.core.arena_manager.EventLogger')
    def test_record_vote(self, mock_event_logger, mock_db_manager, mock_storage_class):
        """Test recording user vote."""
        mock_storage = MagicMock()
        mock_battle = BattleSession('test-session')
        mock_battle.set_models(['llama3.2-3b', 'phi3-mini'])
        mock_storage.get_battle.return_value = mock_battle
        mock_storage.update_battle.return_value = True
        mock_storage_class.return_value = mock_storage
        
        manager = ArenaManager()
        success = manager.record_vote('test-session', 'llama3.2-3b')
        
        assert success is True
        assert mock_battle.vote == 'llama3.2-3b'
        mock_storage.update_battle.assert_called_once()
    
    @patch('app.core.arena_manager.RedisStorage')
    @patch('app.core.arena_manager.DatabaseManager')
    @patch('app.core.arena_manager.EventLogger')
    def test_reveal_models(self, mock_event_logger, mock_db_manager, mock_storage_class):
        """Test revealing models after voting."""
        mock_storage = MagicMock()
        mock_battle = BattleSession('test-session')
        mock_storage.get_battle.return_value = mock_battle
        mock_storage.update_battle.return_value = True
        mock_storage_class.return_value = mock_storage
        
        manager = ArenaManager()
        success = manager.reveal_models('test-session')
        
        assert success is True
        assert mock_battle.revealed is True
        mock_storage.update_battle.assert_called_once()
    
    @patch('app.core.arena_manager.RedisStorage')
    @patch('app.core.arena_manager.DatabaseManager')
    @patch('app.core.arena_manager.EventLogger')
    def test_get_active_battles(self, mock_event_logger, mock_db_manager, mock_storage_class):
        """Test getting list of active battles."""
        mock_storage = MagicMock()
        mock_battles = [
            BattleSession('battle-1'),
            BattleSession('battle-2'),
            BattleSession('battle-3')
        ]
        mock_storage.list_battles.return_value = mock_battles
        mock_storage_class.return_value = mock_storage
        
        manager = ArenaManager()
        battles = manager.get_active_battles()
        
        assert len(battles) == 3
        assert all(isinstance(b, BattleSession) for b in battles)
        mock_storage.list_battles.assert_called_once()
    
    @patch('app.core.arena_manager.RedisStorage')
    @patch('app.core.arena_manager.DatabaseManager')
    @patch('app.core.arena_manager.EventLogger')
    def test_storage_status(self, mock_event_logger, mock_db_manager, mock_storage_class):
        """Test getting storage status."""
        mock_storage = MagicMock()
        mock_storage.redis_client = MagicMock()
        mock_storage.redis_client.ping.return_value = True
        mock_storage_class.return_value = mock_storage
        
        manager = ArenaManager()
        status = manager.storage_status
        
        assert status == 'redis'
    
    @patch('app.core.arena_manager.RedisStorage')
    @patch('app.core.arena_manager.DatabaseManager')
    @patch('app.core.arena_manager.EventLogger')
    def test_cleanup_old_battles(self, mock_event_logger, mock_db_manager, mock_storage_class):
        """Test cleanup of old battles."""
        mock_storage = MagicMock()
        old_battle = BattleSession('old-battle')
        old_battle.timestamp = (datetime.now() - timedelta(hours=25)).isoformat()
        recent_battle = BattleSession('recent-battle')
        recent_battle.timestamp = datetime.now().isoformat()
        
        mock_storage.list_battles.return_value = [old_battle, recent_battle]
        mock_storage.delete_battle.return_value = True
        mock_storage_class.return_value = mock_storage
        
        manager = ArenaManager()
        cleaned = manager.cleanup_old_battles(max_age_hours=24)
        
        assert cleaned == 1
        mock_storage.delete_battle.assert_called_once_with('old-battle')


class TestCrossWorkerPersistence:
    """Test suite for cross-worker persistence functionality."""
    
    @patch('app.core.arena_manager.RedisStorage')
    def test_battle_accessible_across_workers(self, mock_storage_class):
        """Test that battles are accessible from different worker instances."""
        # Simulate Worker 1 creating a battle
        mock_storage_1 = MagicMock()
        mock_storage_class.return_value = mock_storage_1
        
        manager_1 = ArenaManager()
        battle = BattleSession('shared-session')
        battle.user_query = "Shared query"
        mock_storage_1.store_battle.return_value = True
        mock_storage_1.get_battle.return_value = battle
        
        # Store battle from worker 1
        manager_1.storage.store_battle(battle)
        
        # Simulate Worker 2 accessing the same battle
        mock_storage_2 = MagicMock()
        mock_storage_2.get_battle.return_value = battle
        mock_storage_class.return_value = mock_storage_2
        
        manager_2 = ArenaManager()
        retrieved_battle = manager_2.get_battle('shared-session')
        
        assert retrieved_battle is not None
        assert retrieved_battle.session_id == 'shared-session'
        assert retrieved_battle.user_query == "Shared query"
    
    @patch('app.core.arena_manager.RedisStorage')
    def test_concurrent_updates(self, mock_storage_class):
        """Test handling concurrent updates from multiple workers."""
        mock_storage = MagicMock()
        battle = BattleSession('concurrent-session')
        battle.set_models(['llama3.2-3b', 'phi3-mini'])
        
        mock_storage.get_battle.return_value = battle
        mock_storage.update_battle.return_value = True
        mock_storage_class.return_value = mock_storage
        
        # Simulate two workers updating simultaneously
        manager_1 = ArenaManager()
        manager_2 = ArenaManager()
        
        # Worker 1 adds a response
        manager_1.add_model_response('concurrent-session', 'llama3.2-3b', 'Response 1')
        
        # Worker 2 adds a different response
        manager_2.add_model_response('concurrent-session', 'phi3-mini', 'Response 2')
        
        # Both updates should succeed
        assert mock_storage.update_battle.call_count == 2


class TestEdgeCases:
    """Test suite for edge cases and error conditions."""
    
    @patch('app.core.arena_manager.RedisStorage')
    def test_empty_model_list(self, mock_storage_class):
        """Test handling empty model list."""
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage
        
        manager = ArenaManager()
        manager.model_pool.local_models = []
        
        # Should handle gracefully
        battle = manager.create_battle('empty-session', 'Query')
        
        # Should still create battle but with no models
        assert battle is not None
        assert battle.models == []
    
    @patch('app.core.arena_manager.RedisStorage')
    def test_invalid_session_id(self, mock_storage_class):
        """Test handling invalid session IDs."""
        mock_storage = MagicMock()
        mock_storage.get_battle.return_value = None
        mock_storage_class.return_value = mock_storage
        
        manager = ArenaManager()
        
        # Should return None or False for invalid operations
        assert manager.get_battle(None) is None
        assert manager.add_model_response(None, 'model', 'response') is False
        assert manager.record_vote('', 'model') is False
    
    @patch('app.core.arena_manager.RedisStorage')
    def test_redis_connection_failure(self, mock_storage_class):
        """Test graceful handling of Redis connection failures."""
        mock_storage = MagicMock()
        mock_storage.redis_client = None  # Simulate connection failure
        mock_storage.store_battle.return_value = False
        mock_storage.get_battle.return_value = None
        mock_storage_class.return_value = mock_storage
        
        manager = ArenaManager()
        
        # Should handle failures gracefully
        battle = manager.create_battle('failed-session', 'Query')
        assert battle is not None  # Battle object created even if storage fails
        
        retrieved = manager.get_battle('failed-session')
        assert retrieved is None  # Can't retrieve when Redis is down
    
    def test_malformed_battle_data(self):
        """Test handling malformed battle data from Redis."""
        malformed_data = {
            'session_id': 'malformed',
            # Missing required fields
        }
        
        # Should handle gracefully
        try:
            battle = BattleSession.from_dict(malformed_data)
            # Should use defaults for missing fields
            assert battle.session_id == 'malformed'
            assert battle.models == []
            assert battle.responses == {}
        except Exception:
            # Should not raise exception
            pytest.fail("Should handle malformed data gracefully")