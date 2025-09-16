"""
Survey Module for ChatMRPT Cognitive Assessment

This module handles survey functionality for evaluating user comprehension,
preferences, and understanding of ChatMRPT outputs during training sessions.
"""

from flask import Blueprint

# Create survey blueprint
survey_bp = Blueprint('survey', __name__, url_prefix='/survey')

from . import routes