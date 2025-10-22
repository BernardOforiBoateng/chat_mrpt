"""
Pytest configuration file for ChatMRPT Arena system tests.
Contains fixtures and configuration for all tests.
"""

import os
import sys
import json
import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
try:
    import fakeredis
except ImportError:
    fakeredis = None

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set test environment variables
os.environ['FLASK_ENV'] = 'testing'
os.environ['REDIS_HOST'] = 'localhost'
os.environ['REDIS_PORT'] = '6379'
os.environ['OPENAI_API_KEY'] = 'test-key-123'
os.environ.setdefault('SECRET_KEY', 'test-secret-key')
os.environ.setdefault('ADMIN_KEY', 'test-admin-key')


@pytest.fixture
def fake_redis_client():
    """Provides a fake Redis client for testing."""
    if fakeredis is None:
        class SimpleFakeRedis:
            def __init__(self):
                self.store = {}

            def set(self, key, value):
                self.store[key] = value

            def get(self, key):
                return self.store.get(key)

            def delete(self, key):
                self.store.pop(key, None)

            def hset(self, name, key, value):
                bucket = self.store.setdefault(name, {})
                bucket[key] = value

            def hget(self, name, key):
                return self.store.get(name, {}).get(key)

            def hgetall(self, name):
                return dict(self.store.get(name, {}))

            def exists(self, key):
                return key in self.store

            def keys(self, pattern='*'):
                return list(self.store.keys())

        return SimpleFakeRedis()
    return fakeredis.FakeStrictRedis(decode_responses=False)


@pytest.fixture
def mock_redis_storage(fake_redis_client):
    """Provides a mock Redis storage with fake Redis client."""
    with patch('app.core.arena_manager.redis.StrictRedis', return_value=fake_redis_client):
        from app.core.arena_manager import RedisStorage
        storage = RedisStorage(
            redis_host='localhost',
            redis_port=6379,
            redis_db=1
        )
        storage.redis_client = fake_redis_client
        return storage


@pytest.fixture
def sample_battle_session():
    """Provides a sample battle session for testing."""
    from app.core.arena_manager import BattleSession
    
    battle = BattleSession(
        session_id='test-session-123',
        timestamp=datetime.now().isoformat()
    )
    battle.set_models(['llama3.2-3b', 'phi3-mini'])
    battle.user_query = "What is machine learning?"
    battle.add_response('llama3.2-3b', "Machine learning is a type of AI...")
    battle.add_response('phi3-mini', "ML is a subset of artificial intelligence...")
    
    return battle


@pytest.fixture
def mock_ollama_client():
    """Provides a mock Ollama client."""
    mock = MagicMock()
    mock.generate.return_value = {
        'response': 'This is a test response from Ollama',
        'model': 'llama3.2:3b',
        'done': True
    }
    return mock


@pytest.fixture
def mock_openai_client():
    """Provides a mock OpenAI client."""
    mock = MagicMock()
    mock.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content='This is a test response from GPT-4o'
                )
            )
        ]
    )
    return mock


@pytest.fixture
def flask_app():
    """Creates a Flask app for testing."""
    from app import create_app
    
    app = create_app()
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })
    
    return app


@pytest.fixture
def client(flask_app):
    """Creates a Flask test client."""
    return flask_app.test_client()


@pytest.fixture
def app_context(flask_app):
    """Provides an application context for testing."""
    with flask_app.app_context():
        yield flask_app


@pytest.fixture
def mock_session():
    """Provides a mock Flask session."""
    return {
        'session_id': 'test-session-123',
        'user_id': 'test-user-456',
        'arena_mode': True
    }


@pytest.fixture
def sample_messages():
    """Provides sample messages for testing."""
    return [
        {
            'role': 'user',
            'content': 'What is the weather like?'
        },
        {
            'role': 'assistant',
            'content': 'I can help you with that...'
        }
    ]