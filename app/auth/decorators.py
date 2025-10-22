"""
Authentication decorators for route protection.
"""
import os
from functools import wraps
from flask import request, jsonify, session, current_app
from flask_login import current_user
from app.auth.user_model import User
import logging

logger = logging.getLogger(__name__)


def require_auth(f):
    """
    Decorator to require authentication for a route.

    Checks for authentication via:
    1. Flask-Login session (current_user.is_authenticated)
    2. Bearer token in Authorization header
    3. Token in session

    Returns 401 Unauthorized if not authenticated.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Temporary bypass for testing when DISABLE_AUTH=true
        try:
            if os.environ.get('DISABLE_AUTH', 'false').lower() == 'true' or \
               (current_app and current_app.config.get('DISABLE_AUTH', False)):
                return f(*args, **kwargs)
        except Exception:
            pass
        # Check Flask-Login session first
        if current_user.is_authenticated:
            return f(*args, **kwargs)

        # Check for Bearer token in Authorization header
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')
            user = User.verify_session_token(token)

            if user:
                # Valid token, allow access
                return f(*args, **kwargs)

        # Check for token in session (fallback)
        session_token = session.get('auth_token')
        if session_token:
            user = User.verify_session_token(session_token)
            if user:
                return f(*args, **kwargs)

        # No valid authentication found
        logger.warning(f"Unauthorized access attempt to {request.endpoint} from {request.remote_addr}")
        return jsonify({
            'success': False,
            'error': 'Authentication required',
            'message': 'Please sign in to access this resource'
        }), 401

    return decorated_function


def optional_auth(f):
    """
    Decorator that checks for authentication but doesn't require it.

    Sets request.current_user if authenticated, otherwise None.
    Useful for routes that behave differently for authenticated users.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        request.current_user = None

        # If auth is disabled, proceed without checks
        try:
            if os.environ.get('DISABLE_AUTH', 'false').lower() == 'true' or \
               (current_app and current_app.config.get('DISABLE_AUTH', False)):
                return f(*args, **kwargs)
        except Exception:
            pass

        # Check Flask-Login session
        if current_user.is_authenticated:
            request.current_user = current_user
            return f(*args, **kwargs)

        # Check Bearer token
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')
            user = User.verify_session_token(token)
            if user:
                request.current_user = user

        return f(*args, **kwargs)

    return decorated_function
