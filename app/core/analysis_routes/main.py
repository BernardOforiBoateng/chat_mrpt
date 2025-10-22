# app/web/routes/analysis_routes.py
"""
Analysis Routes module for data analysis operations.

This module contains the analysis-related routes for the ChatMRPT web application:
- Main analysis execution (run_analysis)
- Variable selection explanation
- AI chat message processing (send_message)
- Analysis state management
"""

import logging
from datetime import datetime

from flask import Blueprint, session

from ...core.decorators import handle_errors, log_execution_time, validate_session
from .chat import (
    handle_send_message,
    handle_send_message_streaming,
    handle_vote_arena,
)
from .handlers_sync import (
    explain_variable_selection as explain_variable_selection_handler,
    run_analysis as run_analysis_handler,
)

logger = logging.getLogger(__name__)


# Create the analysis routes blueprint
analysis_bp = Blueprint('analysis', __name__)






@analysis_bp.route('/run_analysis', methods=['POST'])
@validate_session
@handle_errors
@log_execution_time
def run_analysis():
    session_id = session.get('session_id', 'default')
    return run_analysis_handler(session_id)


@analysis_bp.route('/explain_variable_selection', methods=['GET'])
@validate_session
@handle_errors
@log_execution_time
def explain_variable_selection():
    session_id = session.get('session_id')
    return explain_variable_selection_handler(session_id)


@analysis_bp.route('/send_message', methods=['POST'])
@validate_session
@handle_errors
@log_execution_time
def send_message():
    return handle_send_message()


@analysis_bp.route('/send_message_streaming', methods=['POST'])
@validate_session
@handle_errors
@log_execution_time
def send_message_streaming():
    return handle_send_message_streaming()


@analysis_bp.route('/api/vote_arena', methods=['POST'])
@validate_session
@handle_errors
def vote_arena():
    return handle_vote_arena()








# ========================================================================
# ANALYSIS UTILITY FUNCTIONS
# ========================================================================

def validate_analysis_requirements(session_state, data_handler=None):
    """
    Validate that analysis requirements are met.
    
    Args:
        session_state: Current session state
        data_handler: Data handler instance
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not session_state.get('csv_loaded', False):
        return False, 'CSV data must be loaded before running analysis'
    
    if not session_state.get('shapefile_loaded', False):
        return False, 'Shapefile data must be loaded before running analysis'
    
    if not data_handler:
        return False, 'Data handler not available'
    
    # Check if data handler has required data
    if not hasattr(data_handler, 'df') or data_handler.df is None:
        return False, 'No CSV data found in data handler'
    
    if not hasattr(data_handler, 'shapefile_data') or data_handler.shapefile_data is None:
        return False, 'No shapefile data found in data handler'
    
    return True, ''


def get_analysis_status(session_state, data_handler=None):
    """
    Get current analysis status and progress.
    
    Args:
        session_state: Current session state
        data_handler: Data handler instance
        
    Returns:
        dict: Analysis status information
    """
    status = {
        'csv_loaded': session_state.get('csv_loaded', False),
        'shapefile_loaded': session_state.get('shapefile_loaded', False),
        'analysis_complete': session_state.get('analysis_complete', False),
        'variables_used': session_state.get('variables_used', []),
        'analysis_type': session_state.get('analysis_type', 'none'),
        'can_run_analysis': False,
        'can_view_results': False
    }
    
    # Check if analysis can be run
    if status['csv_loaded'] and status['shapefile_loaded']:
        status['can_run_analysis'] = True
    
    # Check if results can be viewed
    if status['analysis_complete'] and data_handler:
        if hasattr(data_handler, 'vulnerability_rankings') and data_handler.vulnerability_rankings is not None:
            status['can_view_results'] = True
    
    return status


def extract_risk_wards(data_handler, limit=10):
    """
    Extract high, medium, and low risk wards from analysis results.
    
    Args:
        data_handler: Data handler with analysis results
        limit: Maximum number of wards to return per category
        
    Returns:
        dict: Dictionary with high_risk, medium_risk, and low_risk ward lists
    """
    risk_wards = {
        'high_risk': [],
        'medium_risk': [],
        'low_risk': []
    }
    
    if not data_handler or not hasattr(data_handler, 'vulnerability_rankings'):
        return risk_wards
    
    rankings = data_handler.vulnerability_rankings
    if rankings is None or 'vulnerability_category' not in rankings.columns:
        return risk_wards
    
    try:
        if 'WardName' in rankings.columns:
            risk_wards['high_risk'] = rankings[
                rankings['vulnerability_category'] == 'High'
            ]['WardName'].tolist()[:limit]
            
            risk_wards['medium_risk'] = rankings[
                rankings['vulnerability_category'] == 'Medium'
            ]['WardName'].tolist()[:limit]
            
            risk_wards['low_risk'] = rankings[
                rankings['vulnerability_category'] == 'Low'
            ]['WardName'].tolist()[:limit]
            
    except Exception as e:
        logger.error(f"Error extracting risk wards: {e}")
    
    return risk_wards


def update_analysis_session_state(session, analysis_result):
    """
    Update session state based on analysis results.
    
    Args:
        session: Flask session object
        analysis_result: Analysis result dictionary
    """
    if analysis_result.get('status') == 'success':
        session['analysis_complete'] = True
        session['variables_used'] = analysis_result.get('variables_used', [])
        
        # Set analysis type if provided
        if 'analysis_type' in analysis_result:
            session['analysis_type'] = analysis_result['analysis_type']
            
        # CRITICAL: Mark session as modified for filesystem sessions
        session.modified = True
        
        # Clear any pending actions
        session.pop('pending_action', None)
        session.pop('pending_variables', None)
        
        # Update timestamp
        session['analysis_completion_time'] = datetime.utcnow().isoformat()
        
        logger.info(f"Session {session.get('session_id')}: Analysis completed with {len(session['variables_used'])} variables")


def clear_analysis_session_state(session):
    """
    Clear analysis-related session state.
    
    Args:
        session: Flask session object
    """
    # Clear analysis flags
    session.pop('analysis_complete', None)
    session.pop('variables_used', None)
    session.pop('analysis_type', None)
    session.pop('analysis_completion_time', None)
    
    # Clear pending actions
    session.pop('pending_action', None)
    session.pop('pending_variables', None)
    
    # Clear visualization state
    session.pop('last_visualization', None)
    
    # CRITICAL: Mark session as modified after clearing state
    session.modified = True
    
    logger.info(f"Session {session.get('session_id')}: Analysis state cleared") 
