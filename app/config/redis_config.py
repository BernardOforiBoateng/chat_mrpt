# app/config/redis_config.py
"""
Redis configuration for Flask-Session.

This module provides Redis session configuration for multi-worker
environments to ensure session persistence across Gunicorn workers.

For local development, falls back to filesystem sessions if Redis is unavailable.
"""

import os
import redis
from flask_session import Session

class RedisConfig:
    """Redis configuration for session management."""

    # Redis connection settings
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))

    # Session configuration
    SESSION_TYPE = 'redis'
    SESSION_REDIS = None  # Will be set in init_redis_session
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'chatmrpt:'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours in seconds

    # Additional Redis settings
    SESSION_REDIS_SOCKET_TIMEOUT = 30
    SESSION_REDIS_RETRY_ON_TIMEOUT = True
    SESSION_REDIS_HEALTH_CHECK = True

    @classmethod
    def init_redis_session(cls, app):
        """Initialize Redis session store, with filesystem fallback for local dev."""

        # Check if we should skip Redis (for local development)
        use_filesystem = os.environ.get('USE_FILESYSTEM_SESSIONS', 'false').lower() == 'true'
        flask_env = os.environ.get('FLASK_ENV', 'production')

        if use_filesystem:
            return cls._init_filesystem_session(app)

        try:
            # Create Redis client
            redis_client = redis.StrictRedis(
                host=cls.REDIS_HOST,
                port=cls.REDIS_PORT,
                password=cls.REDIS_PASSWORD,
                db=cls.REDIS_DB,
                decode_responses=False,  # Required for Flask-Session
                socket_connect_timeout=cls.SESSION_REDIS_SOCKET_TIMEOUT,
                socket_timeout=cls.SESSION_REDIS_SOCKET_TIMEOUT,
                retry_on_timeout=cls.SESSION_REDIS_RETRY_ON_TIMEOUT,
                health_check_interval=30 if cls.SESSION_REDIS_HEALTH_CHECK else 0
            )

            # Test connection
            redis_client.ping()

            # Configure Flask app
            app.config['SESSION_TYPE'] = cls.SESSION_TYPE
            app.config['SESSION_REDIS'] = redis_client
            app.config['SESSION_PERMANENT'] = cls.SESSION_PERMANENT
            app.config['SESSION_USE_SIGNER'] = cls.SESSION_USE_SIGNER
            app.config['SESSION_KEY_PREFIX'] = cls.SESSION_KEY_PREFIX
            app.config['PERMANENT_SESSION_LIFETIME'] = cls.PERMANENT_SESSION_LIFETIME

            # Initialize Flask-Session
            Session(app)

            app.logger.info(f"✅ Redis session store initialized at {cls.REDIS_HOST}:{cls.REDIS_PORT}")
            return True

        except redis.ConnectionError as e:
            app.logger.warning(f"⚠️ Redis not available: {e}")

            # In development mode, fall back to filesystem sessions
            if flask_env == 'development':
                app.logger.info("📁 Falling back to filesystem sessions for local development")
                return cls._init_filesystem_session(app)
            else:
                # In production, Redis is required
                app.logger.error("❌ Redis is required in production mode")
                raise RuntimeError('Redis session store is required for ChatMRPT in production') from e
        except Exception as e:
            app.logger.error(f"❌ Redis session initialization error: {e}")
            raise

    @classmethod
    def _init_filesystem_session(cls, app):
        """Initialize filesystem-based sessions for local development."""
        # Create session directory in instance folder
        instance_path = app.instance_path if hasattr(app, 'instance_path') else 'instance'
        session_dir = os.path.join(instance_path, 'flask_session')
        os.makedirs(session_dir, exist_ok=True)

        # Configure filesystem sessions
        app.config['SESSION_TYPE'] = 'filesystem'
        app.config['SESSION_FILE_DIR'] = session_dir
        app.config['SESSION_PERMANENT'] = cls.SESSION_PERMANENT
        app.config['SESSION_USE_SIGNER'] = cls.SESSION_USE_SIGNER
        app.config['SESSION_KEY_PREFIX'] = cls.SESSION_KEY_PREFIX
        app.config['PERMANENT_SESSION_LIFETIME'] = cls.PERMANENT_SESSION_LIFETIME

        # Initialize Flask-Session
        Session(app)

        app.logger.info(f"✅ Filesystem session store initialized at {session_dir}")
        return True
    
    @classmethod
    def get_redis_info(cls, app):
        """Get Redis server information."""
        try:
            if app.config.get('SESSION_REDIS'):
                info = app.config['SESSION_REDIS'].info()
                return {
                    'connected': True,
                    'version': info.get('redis_version'),
                    'used_memory': info.get('used_memory_human'),
                    'connected_clients': info.get('connected_clients'),
                    'db_keys': app.config['SESSION_REDIS'].dbsize()
                }
        except:
            pass
        return {'connected': False}