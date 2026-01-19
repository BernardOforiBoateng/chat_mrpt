"""
User model with database support for authentication
"""
import os
import sqlite3
import hashlib
import secrets
import json
from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), '../../instance/users.db')

# Redis for session tokens (shared across instances)
try:
    import redis
    REDIS_HOST = os.environ.get('REDIS_HOST', 'chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    # Test connection
    redis_client.ping()
    USE_REDIS = True
except Exception as e:
    print(f"⚠️ Redis not available: {e}. Falling back to SQLite for sessions.")
    redis_client = None
    USE_REDIS = False

class User(UserMixin):
    """User model with database persistence."""

    def __init__(self, user_id, email, username, created_at=None):
        self.id = user_id
        self.email = email
        self.username = username
        self.created_at = created_at or datetime.utcnow()

    @staticmethod
    def init_db():
        """Initialize the users database."""
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                role TEXT DEFAULT 'user'
            )
        ''')

        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        conn.commit()
        conn.close()

    @staticmethod
    def create_user(email, username, password):
        """Create a new user account."""
        User.init_db()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            # Check if email already exists
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            if cursor.fetchone():
                return None, "Email already registered"

            # Check if username already exists
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                return None, "Username already taken"

            # Create user
            user_id = secrets.token_hex(16)
            password_hash = generate_password_hash(password)

            cursor.execute('''
                INSERT INTO users (id, email, username, password_hash)
                VALUES (?, ?, ?, ?)
            ''', (user_id, email, username, password_hash))

            conn.commit()
            conn.close()

            return User(user_id, email, username), None

        except Exception as e:
            conn.close()
            return None, str(e)

    @staticmethod
    def authenticate(email, password):
        """Authenticate user with email and password."""
        User.init_db()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            # Get user by email
            cursor.execute('''
                SELECT id, email, username, password_hash, is_active
                FROM users WHERE email = ?
            ''', (email,))

            user_data = cursor.fetchone()

            if not user_data:
                return None, "Invalid email or password"

            user_id, email, username, password_hash, is_active = user_data

            # Check if account is active
            if not is_active:
                return None, "Account is disabled"

            # Verify password
            if not check_password_hash(password_hash, password):
                return None, "Invalid email or password"

            # Update last login
            cursor.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (user_id,))

            conn.commit()
            conn.close()

            return User(user_id, email, username), None

        except Exception as e:
            conn.close()
            return None, str(e)

    @staticmethod
    def get(user_id):
        """Get user by ID."""
        if user_id == 'admin':
            # Legacy admin support
            return User('admin', 'admin@chatmrpt.com', 'admin')

        User.init_db()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT id, email, username, created_at
                FROM users WHERE id = ?
            ''', (user_id,))

            user_data = cursor.fetchone()
            conn.close()

            if user_data:
                return User(*user_data)

            return None

        except Exception:
            conn.close()
            return None

    @staticmethod
    def get_by_email(email):
        """Get user by email."""
        User.init_db()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT id, email, username, created_at
                FROM users WHERE email = ?
            ''', (email,))

            user_data = cursor.fetchone()
            conn.close()

            if user_data:
                return User(*user_data)

            return None

        except Exception:
            conn.close()
            return None

    @staticmethod
    def create_session_token(user_id):
        """Create a session token for the user.

        Stores session in Redis (if available) with minimal user profile so
        token verification does not depend on local SQLite on each instance.
        """
        import logging
        logger = logging.getLogger(__name__)

        token = secrets.token_hex(32)
        expires_at = datetime.utcnow() + timedelta(days=7)

        if USE_REDIS and redis_client:
            try:
                # Try to enrich session with user profile (email/username)
                user_obj = User.get(user_id)
                # Store in Redis with TTL (shared across all instances)
                session_data = {
                    'user_id': user_id,
                    'email': getattr(user_obj, 'email', None),
                    'username': getattr(user_obj, 'username', None),
                    'expires_at': expires_at.isoformat()
                }
                # Set with 7-day expiration
                redis_client.setex(
                    f'session:{token}',
                    timedelta(days=7),
                    json.dumps(session_data)
                )
                logger.info(f"🔐 Created session token in Redis for user {user_id}")
                return token
            except Exception as e:
                logger.error(f"🔐 Redis error in create_session_token: {e}")
                # Fall through to SQLite

        # Fallback to SQLite (local instance only)
        User.init_db()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO user_sessions (token, user_id, expires_at)
                VALUES (?, ?, ?)
            ''', (token, user_id, expires_at))

            conn.commit()
            conn.close()
            logger.info(f"🔐 Created session token in SQLite for user {user_id}")
            return token

        except Exception as e:
            logger.error(f"🔐 SQLite error in create_session_token: {e}")
            conn.close()
            return None

    @staticmethod
    def verify_session_token(token):
        """Verify a session token and return the user.

        Prefers Redis-backed session and reconstructs a User object from
        session data if the local SQLite user record is not available on
        the current instance.
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"🔐 verify_session_token called with token: {token[:20] if token else 'NONE'}...")

        # Try Redis first (shared across instances)
        if USE_REDIS and redis_client:
            try:
                session_json = redis_client.get(f'session:{token}')
                logger.info(f"🔐 Redis lookup result: {session_json[:100] if session_json else 'NONE'}")

                if session_json:
                    session_data = json.loads(session_json)
                    user_id = session_data.get('user_id')
                    expires_at = session_data.get('expires_at')

                    logger.info(f"🔐 Found session in Redis - user_id: {user_id}, expires_at: {expires_at}")

                    # Check if token is expired
                    expires_dt = datetime.fromisoformat(expires_at)
                    now = datetime.utcnow()
                    logger.info(f"🔐 Token expiry check - expires: {expires_dt}, now: {now}, expired: {expires_dt < now}")

                    if expires_dt < now:
                        logger.info("🔐 Token expired, deleting from Redis")
                        redis_client.delete(f'session:{token}')
                        return None

                    # Try to fetch full user from local DB
                    user = User.get(user_id)
                    if user:
                        logger.info(f"🔐 Returning user from Redis (DB lookup success): {user.email}")
                        return user

                    # DB record not available on this instance; reconstruct from session
                    email = session_data.get('email') or f"{user_id[:8]}@users.local"
                    username = session_data.get('username') or (email.split('@')[0] if isinstance(email, str) else 'user')
                    logger.info(f"🔐 Reconstructing user from Redis session: {email}")
                    return User(user_id, email, username)
                else:
                    logger.info("🔐 No session found in Redis")
            except Exception as e:
                logger.error(f"🔐 Redis error in verify_session_token: {e}")
                # Fall through to SQLite

        # Fallback to SQLite (local instance only)
        User.init_db()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT user_id, expires_at FROM user_sessions
                WHERE token = ?
            ''', (token,))

            session_data = cursor.fetchone()
            logger.info(f"🔐 SQLite lookup result: {session_data}")

            if not session_data:
                logger.info("🔐 No session found in SQLite")
                conn.close()
                return None

            user_id, expires_at = session_data
            logger.info(f"🔐 Found session in SQLite - user_id: {user_id}, expires_at: {expires_at}")

            # Check if token is expired
            expires_dt = datetime.fromisoformat(expires_at)
            now = datetime.utcnow()
            logger.info(f"🔐 Token expiry check - expires: {expires_dt}, now: {now}, expired: {expires_dt < now}")

            if expires_dt < now:
                # Delete expired token
                logger.info("🔐 Token expired, deleting from SQLite")
                cursor.execute('DELETE FROM user_sessions WHERE token = ?', (token,))
                conn.commit()
                conn.close()
                return None

            conn.close()
            user = User.get(user_id)
            logger.info(f"🔐 Returning user from SQLite: {user.email if user else 'NONE'}")
            return user

        except Exception as e:
            logger.error(f"🔐 ERROR in verify_session_token: {str(e)}")
            logger.error(f"🔐 Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"🔐 Traceback: {traceback.format_exc()}")
            conn.close()
            return None

    @staticmethod
    def logout(token):
        """Logout by deleting the session token."""
        import logging
        logger = logging.getLogger(__name__)

        success = False

        # Delete from Redis if available
        if USE_REDIS and redis_client:
            try:
                redis_client.delete(f'session:{token}')
                logger.info(f"🔐 Deleted session from Redis")
                success = True
            except Exception as e:
                logger.error(f"🔐 Redis error in logout: {e}")

        # Also delete from SQLite (in case it's there)
        User.init_db()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            cursor.execute('DELETE FROM user_sessions WHERE token = ?', (token,))
            conn.commit()
            conn.close()
            logger.info(f"🔐 Deleted session from SQLite")
            success = True
        except Exception as e:
            logger.error(f"🔐 SQLite error in logout: {e}")
            conn.close()

        return success
