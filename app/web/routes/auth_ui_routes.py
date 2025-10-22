"""
Authentication UI routes - serves login/signup page
"""
from flask import Blueprint, render_template, redirect, session

auth_ui_bp = Blueprint('auth_ui', __name__)

@auth_ui_bp.route('/login')
@auth_ui_bp.route('/signup')
@auth_ui_bp.route('/auth')
def auth_page():
    """Serve the authentication page."""
    # If user is already authenticated, redirect to home
    if 'user_id' in session or 'auth_token' in session:
        return redirect('/')

    return render_template('auth.html')

@auth_ui_bp.route('/')
def index():
    """Main route - show auth page if not logged in."""
    # Check if user has auth token
    if 'user_id' not in session and 'auth_token' not in session:
        return render_template('auth.html')

    # Otherwise show the React app
    return render_template('index.html')