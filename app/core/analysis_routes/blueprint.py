"""Blueprint registration for analysis routes."""

from __future__ import annotations

from flask import Blueprint

from ...core.decorators import handle_errors, log_execution_time, validate_session
from .handlers import run_analysis, explain_variable_selection

analysis_bp = Blueprint('analysis', __name__)


@analysis_bp.route('/run_analysis', methods=['POST'])
@handle_errors
@log_execution_time
@validate_session
def run_analysis_route():
    session_id = session.get('session_id', 'default')
    return run_analysis(session_id)


@analysis_bp.route('/explain_variable_selection', methods=['GET'])
@validate_session
@handle_errors
@log_execution_time
def explain_variable_selection_route():
    session_id = session.get('session_id')
    return explain_variable_selection(session_id)


__all__ = ['analysis_bp']
