"""Synchronous analysis route handlers (run_analysis, explain_variable_selection)."""

from __future__ import annotations

import logging
from typing import Tuple

from flask import current_app, jsonify, request, session

from ...core.exceptions import ValidationError

logger = logging.getLogger(__name__)


def run_analysis(session_id: str):
    """Execute the malaria risk analysis for the current session."""
    data_service = current_app.services.data_service
    analysis_service = current_app.services.analysis_service

    data_handler = data_service.get_handler(session_id)
    if not data_handler:
        raise ValidationError('Data handler not initialized. Please upload data files first.')

    payload = request.json or {}
    selected_variables = payload.get('selected_variables')

    if not session.get('csv_loaded', False) or not session.get('shapefile_loaded', False):
        raise ValidationError('Please upload both CSV and shapefile data before running analysis')

    if selected_variables:
        result = analysis_service.run_custom_analysis(
            data_handler=data_handler,
            selected_variables=selected_variables,
            session_id=session_id,
        )
    else:
        result = analysis_service.run_standard_analysis(
            data_handler=data_handler,
            session_id=session_id,
        )

    if result['status'] != 'success':
        return jsonify({'status': 'error', 'message': result.get('message', 'Error running analysis')}), 400

    session['analysis_complete'] = True
    session['variables_used'] = result.get('variables_used', [])
    session.modified = True

    high, medium, low = _extract_risk_wards(data_handler, result)

    return jsonify({
        'status': 'success',
        'message': 'Analysis completed successfully',
        'variables_used': result.get('variables_used', []),
        'high_risk_wards': high[:10],
        'medium_risk_wards': medium[:10],
        'low_risk_wards': low[:10],
    })


def explain_variable_selection(session_id: str):
    """Explain why specific variables were chosen during analysis."""
    data_service = current_app.services.data_service
    analysis_service = current_app.services.analysis_service

    data_handler = data_service.get_handler(session_id)
    if not data_handler:
        raise ValidationError('No data available for explanation')

    if not session.get('analysis_complete', False) or not session.get('variables_used'):
        raise ValidationError('Analysis not yet performed')

    variables = session.get('variables_used', [])
    if not variables:
        raise ValidationError('No variables found from analysis')

    result = analysis_service.explain_variable_selection(variables=variables, data_handler=data_handler)
    if result['status'] != 'success':
        return jsonify({'status': 'error', 'message': result.get('message', 'Error generating explanation')}), 400

    return jsonify({
        'status': 'success',
        'message': 'Generated variable selection explanation',
        'explanation': result.get('explanations', {}),
        'variables': variables,
    })


def _extract_risk_wards(data_handler, result):
    """Return ward lists grouped by vulnerability level."""
    high, medium, low = [], [], []

    rankings = getattr(data_handler, 'vulnerability_rankings', None)
    if rankings is not None and 'vulnerability_category' in rankings.columns and 'WardName' in rankings.columns:
        high = rankings[rankings['vulnerability_category'] == 'High']['WardName'].tolist()
        medium = rankings[rankings['vulnerability_category'] == 'Medium']['WardName'].tolist()
        low = rankings[rankings['vulnerability_category'] == 'Low']['WardName'].tolist()

    return (
        high or result.get('high_risk_wards', []),
        medium or result.get('medium_risk_wards', []),
        low or result.get('low_risk_wards', []),
    )

__all__ = ['run_analysis', 'explain_variable_selection']
