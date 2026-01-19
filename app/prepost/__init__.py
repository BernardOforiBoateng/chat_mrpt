"""
Pre-Post Test Module

Standalone pre-post test survey system for measuring knowledge improvement.
"""

from flask import Blueprint

# Create blueprint
prepost_bp = Blueprint('prepost', __name__, url_prefix='/prepost')

# Import routes
from app.prepost import routes
