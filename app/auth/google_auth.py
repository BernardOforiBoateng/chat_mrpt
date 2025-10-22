"""
Google OAuth Authentication
"""
from flask import Blueprint, redirect, url_for, session, request, jsonify, current_app
from flask_login import login_user
from authlib.integrations.flask_client import OAuth
import os
import secrets
from app.auth.user_model import User

google_auth = Blueprint('google_auth', __name__, url_prefix='/auth')

# OAuth setup
oauth = OAuth()

def init_google_oauth(app):
    """Initialize Google OAuth with the Flask app."""
    oauth.init_app(app)

    # Register Google OAuth
    google = oauth.register(
        name='google',
        client_id=os.environ.get('GOOGLE_CLIENT_ID'),
        client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    return google

@google_auth.route('/google')
def google_login():
    """Initiate Google OAuth login with a callback URL bound to the current host.

    Ensures the OAuth redirect_uri uses the same host and scheme as the
    initiating request (via X-Forwarded-* headers when behind ALB/CloudFront),
    preventing CSRF state mismatch due to cross-domain callbacks.
    """
    google = oauth.create_client('google')

    # Respect proxy headers to compute the public URL users see
    forwarded_host = request.headers.get('X-Forwarded-Host')
    host = forwarded_host or request.host
    proto = request.headers.get('X-Forwarded-Proto', 'https')

    # Build callback URL on the same host/scheme
    callback_path = url_for('google_auth.google_callback')
    redirect_uri = f"{proto}://{host}{callback_path}"

    return google.authorize_redirect(redirect_uri)

@google_auth.route('/google/callback')
def google_callback():
    """Handle Google OAuth callback with robust state and userinfo handling."""
    google = oauth.create_client('google')

    # Compute the same redirect_uri as the login step (public host + proto)
    forwarded_host = request.headers.get('X-Forwarded-Host')
    host = forwarded_host or request.host
    proto = request.headers.get('X-Forwarded-Proto', 'https')
    callback_path = url_for('google_auth.google_callback')
    redirect_uri = f"{proto}://{host}{callback_path}"

    try:
        # Exchange code for tokens; align redirect_uri for providers that validate it strictly
        token = google.authorize_access_token(redirect_uri=redirect_uri)

        # Try to obtain userinfo from OIDC endpoint if not included in token payload
        user_info = token.get('userinfo') if isinstance(token, dict) else None
        if not user_info:
            try:
                resp = google.get('userinfo')
                if resp and resp.ok:
                    user_info = resp.json()
            except Exception as e:
                current_app.logger.warning(f"Google userinfo fetch failed: {e}")

        if not user_info:
            current_app.logger.error("Google OAuth: userinfo missing after token exchange")
            return jsonify({'error': 'Failed to get user info from Google'}), 400

        email = user_info.get('email')
        if not email:
            current_app.logger.error(f"Google OAuth: email missing in userinfo: {user_info}")
            return jsonify({'error': 'Email not provided by Google'}), 400
        name = user_info.get('name', email.split('@')[0])

        # Ensure user exists
        user = User.get_by_email(email)
        if not user:
            username = email.split('@')[0] + str(secrets.randbits(16))
            random_password = secrets.token_hex(32)
            user, error = User.create_user(email, username, random_password)
            if error:
                current_app.logger.error(f"User creation failed: {error}")
                return jsonify({'error': error}), 400

        # Create session token and login
        session_token = User.create_session_token(user.id)
        login_user(user, remember=True)

        # Persist session data
        session['user_id'] = user.id
        session['user_email'] = email
        session['auth_token'] = session_token
        session['auth_method'] = 'google'

        # Redirect to frontend root with token for client-side capture
        return redirect(f'/?token={session_token}&user={user.username}')

    except Exception as e:
        # Log as much diagnostic context as possible
        current_app.logger.error(
            "Google OAuth callback failed: %s | Host=%s Proto=%s Cookie=%s",
            str(e), host, proto, request.headers.get('Cookie', '')
        )
        # Explicitly signal state mismatch for client clarity if present in message
        msg = str(e)
        if 'mismatching_state' in msg or 'State not equal' in msg:
            return jsonify({'error': 'mismatching_state', 'detail': msg}), 400
        return jsonify({'error': 'oauth_callback_failed', 'detail': msg}), 500
