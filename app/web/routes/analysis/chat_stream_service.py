"""Streaming chat handler for analysis workflow."""

from __future__ import annotations

import json
import os

from typing import Any, Dict

from flask import Response, current_app, jsonify, request, session

from ...core.exceptions import ValidationError
from app.runtime.tpr.workflow import reset_tpr_handler_cache

from . import logger
from .arena_helpers import ArenaSetupError, prepare_arena_preload
from .chat_routing import route_with_mistral
from .utils import resync_session_flags, run_async

__all__ = ["handle_send_message_streaming"]


def handle_send_message_streaming() -> Response:
    data = request.json or {}
    user_message = data.get('message', '')

    logger.info("=" * 60)
    logger.info("🔧 BACKEND: /send_message_streaming endpoint hit")
    logger.info("  📝 User Message: %s...", user_message[:100] if user_message else 'EMPTY')
    logger.info("  🆔 Session ID: %s", session.get('session_id', 'NO SESSION'))
    logger.info("  📂 Session Keys: %s", list(session.keys()))
    logger.info("  🎯 Analysis Complete: %s", session.get('analysis_complete', False))
    logger.info("  📊 Data Loaded: %s", session.get('data_loaded', False))
    logger.info("  🔄 TPR Complete: %s", session.get('tpr_workflow_complete', False))
    logger.info("=" * 60)

    if not user_message:
        def generate_error():
            yield json.dumps({
                'content': 'Please provide a message to continue.',
                'status': 'success',
                'done': True,
            })

        response = Response((f"data: {chunk}\n\n" for chunk in generate_error()), mimetype='text/event-stream')
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Connection'] = 'keep-alive'
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    tab_context = data.get('tab_context', 'standard-upload')
    is_data_analysis = data.get('is_data_analysis', False)

    if is_data_analysis:
        session['active_tab'] = 'data-analysis'
        session['use_data_analysis_v3'] = True
        logger.info("📊 Data Analysis tab active - setting V3 mode")

    session_id = session.get('session_id')

    if session.get('data_analysis_active', False):
        logger.info(
            "Data analysis workflow active for session %s, clearing legacy flag",
            session_id,
        )
        session.pop('data_analysis_active', None)
        session.modified = True
        logger.warning("Old data analysis flag detected, clearing and falling through to main chat")

    elif session.get('tpr_workflow_active', False):
        logger.info("TPR workflow active for session %s", session_id)
        try:
            from ...data_analysis_v3.core.tpr_workflow_handler import TPRWorkflowHandler
            from ...data_analysis_v3.core.state_manager import DataAnalysisStateManager
            from ...data_analysis_v3.core.tpr_data_analyzer import TPRDataAnalyzer

            state_manager = DataAnalysisStateManager(session_id)
            tpr_analyzer = TPRDataAnalyzer(session_id)
            handler = TPRWorkflowHandler(session_id, state_manager, tpr_analyzer)
            tpr_result = handler.handle_message(user_message)

            if tpr_result.get('response') == '__DATA_UPLOADED__' or tpr_result.get('status') == 'tpr_to_main_transition':
                logger.info("TPR router requesting transition to main interpreter for __DATA_UPLOADED__")
                session.pop('tpr_workflow_active', None)
                session.pop('tpr_session_id', None)
                session['csv_loaded'] = True
                session['has_uploaded_files'] = True
                session['analysis_complete'] = True
                session.modified = True
                user_message = '__DATA_UPLOADED__'
            else:
                return _response_from_tpr_result(tpr_result)
        except Exception as exc:
            logger.error("Error routing to TPR handler: %s", exc)

    if user_message == '__DATA_UPLOADED__':
        try:
            reset_tpr_handler_cache(session_id)
        except Exception:
            logger.debug("No TPR handler cache to reset for session %s", session_id)

    try:
        resync_session_flags(session_id)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("[DEBUG] streaming: resync session flags failed: %s", exc)

    has_uploaded_files = any(
        session.get(flag, False)
        for flag in ('data_loaded', 'analysis_complete', 'csv_loaded')
    )

    session_context = {
        'has_uploaded_files': has_uploaded_files,
        'session_id': session_id,
        'csv_loaded': session.get('csv_loaded', False),
        'shapefile_loaded': session.get('shapefile_loaded', False),
        'analysis_complete': session.get('analysis_complete', False),
        'use_data_analysis_v3': session.get('use_data_analysis_v3', False),
        'data_analysis_active': session.get('data_analysis_active', False),
    }

    if session.get('pending_clarification'):
        original_context = session['pending_clarification']
        combined_message = f"{original_context['original_message']} {user_message}"
        session.pop('pending_clarification', None)
        session.modified = True
        routing_decision = run_async(route_with_mistral(combined_message, session_context))
        logger.info("Clarification response routing: %s", routing_decision)
        user_message = original_context['original_message']
    else:
        routing_decision = run_async(route_with_mistral(user_message, session_context))
        if routing_decision == 'needs_clarification':
            if len(user_message.strip().split()) <= 3:
                routing_decision = 'can_answer'
            else:
                clarification = {
                    'needs_clarification': True,
                    'clarification_type': 'intent',
                    'message': "I need more information to help you. Are you looking to:",
                    'options': [
                        {
                            'id': 'analyze_data',
                            'label': 'Analyze your uploaded data',
                            'icon': '📊',
                            'value': 'tools',
                        },
                        {
                            'id': 'general_info',
                            'label': 'Get general information',
                            'icon': '📚',
                            'value': 'arena',
                        },
                    ],
                    'original_message': user_message,
                    'session_context': session_context,
                }
                session['pending_clarification'] = {
                    'original_message': user_message,
                    'context': session_context,
                }
                session.modified = True
                return _clarification_response(clarification)

    use_arena = (routing_decision == 'can_answer') and (os.getenv('CHATMRPT_ARENA', '0') != '0')
    use_tools = routing_decision == 'needs_tools'

    if use_arena:
        try:
            arena_preload = prepare_arena_preload(session_id, user_message, run_async)
        except ArenaSetupError as exc:
            logger.error("Arena streaming failed: %s", exc)
            use_arena = False
        else:
            if arena_preload.both_models_need_tools():
                session['last_tool_used'] = True
                session.modified = True
                use_arena = False
            else:
                return arena_preload.stream_response()

    if not use_arena:
        return _stream_request_interpreter(
            user_message=user_message,
            session_id=session_id,
            tab_context=tab_context,
            is_data_analysis=is_data_analysis,
        )

    return jsonify({'status': 'error', 'message': 'Unable to process streaming request'}), 500


def _clarification_response(payload: Dict[str, Any]) -> Response:
    def generate():
        yield json.dumps(payload)

    response = Response((f"data: {chunk}\n\n" for chunk in generate()), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


def _stream_request_interpreter(
    *,
    user_message: str,
    session_id: str,
    tab_context: str,
    is_data_analysis: bool,
) -> Response:
    request_interpreter = getattr(current_app.services, 'request_interpreter', None)
    if request_interpreter is None:
        logger.error("Request Interpreter not available")
        return jsonify({
            'status': 'error',
            'message': 'Error accessing request processing system',
        }), 500

    app = current_app._get_current_object()
    session_data = dict(session)

    def generate():
        def format_response(text: str) -> str:
            if not text:
                return ''
            import re

            s = text.replace('\r\n', '\n').replace('\r', '\n')
            s = re.sub(r'^(\s*)\*\s+', r'\1- ', s, flags=re.MULTILINE)
            s = re.sub(r'^(\s*)[\u2022•]\s+', r'\1- ', s, flags=re.MULTILINE)
            s = re.sub(r'^•\s*', '- ', s, flags=re.MULTILINE)
            s = re.sub(r'^-\s+', '- ', s, flags=re.MULTILINE)
            s = re.sub(r'\n{3,}', '\n\n', s)
            return s

        try:
            with app.app_context():
                logger.info("Processing streaming message: '%s...'", user_message[:100])
                final_chunk = None
                response_content = ''
                tools_used: list[str] = []

                for chunk in request_interpreter.process_message_streaming(
                    user_message,
                    session_id,
                    session_data,
                    is_data_analysis=is_data_analysis,
                    tab_context=tab_context,
                ):
                    if chunk.get('content'):
                        chunk['content'] = format_response(chunk['content'])
                        response_content += chunk.get('content', '')
                    if chunk.get('tools_used'):
                        tools_used.extend(chunk.get('tools_used', []))
                    if chunk.get('done'):
                        final_chunk = chunk
                    chunk_json = json.dumps(chunk)
                    logger.debug("Sending streaming chunk: %s", chunk_json)
                    yield f"data: {chunk_json}\n\n"

                from flask import session as flask_session
                if tools_used:
                    if any(tool in tools_used for tool in ['run_composite_analysis', 'run_pca_analysis', 'runcompleteanalysis']):
                        flask_session['analysis_complete'] = True
                        if 'runcompleteanalysis' in tools_used:
                            flask_session['analysis_type'] = 'dual_method'
                        elif 'run_composite_analysis' in tools_used:
                            flask_session['analysis_type'] = 'composite'
                        else:
                            flask_session['analysis_type'] = 'pca'
                        flask_session.modified = True
                        logger.info(
                            "Session %s: Analysis completed via streaming, session updated",
                            session_id,
                        )
                    if any(tool in tools_used for tool in ['run_composite_analysis', 'run_pca_analysis', 'runcompleteanalysis']):
                        flask_session.pop('pending_action', None)
                        flask_session.pop('pending_variables', None)
                        flask_session.modified = True

                if final_chunk:
                    _log_stream_completion(app, final_chunk, response_content, session_id)
        except Exception as exc:
            logger.error("Error in streaming processing: %s", exc)
            error_json = json.dumps({'content': f'Error: {str(exc)}', 'status': 'error', 'done': True})
            yield f"data: {error_json}\n\n"

    response = Response(generate(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['X-Accel-Buffering'] = 'no'
    return response


def _log_stream_completion(app, final_chunk: Dict[str, Any], response_content: str, session_id: str) -> None:
    tools_used = final_chunk.get('tools_used', [])
    if any(tool in tools_used for tool in ['run_composite_analysis', 'run_pca_analysis', 'runcompleteanalysis']):
        if 'runcompleteanalysis' in tools_used:
            analysis_type = 'dual_method'
        elif 'run_composite_analysis' in tools_used:
            analysis_type = 'composite'
        else:
            analysis_type = 'pca'
        logger.info(
            "Session %s: Analysis completed via streaming (%s)",
            session_id,
            analysis_type,
        )

    interaction_logger = getattr(app.services, 'interaction_logger', None)
    if interaction_logger:
        interaction_logger.log_message(
            session_id=session_id,
            sender='assistant',
            content=response_content,
            intent=final_chunk.get('intent_type', 'streaming'),
            entities={
                'streaming': True,
                'tools_used': tools_used,
                'status': final_chunk.get('status', 'success'),
            },
        )


def _response_from_tpr_result(tpr_result: Dict[str, Any]) -> Response:
    def generate():
        yield json.dumps(
            {
                'content': tpr_result.get('response', ''),
                'status': tpr_result.get('status', 'success'),
                'visualizations': tpr_result.get('visualizations', []),
                'tools_used': tpr_result.get('tools_used', []),
                'workflow': tpr_result.get('workflow', 'tpr'),
                'stage': tpr_result.get('stage'),
                'download_links': tpr_result.get('download_links', []),
                'trigger_data_uploaded': tpr_result.get('trigger_data_uploaded', False),
                'done': True,
            }
        )

    response = Response((f"data: {chunk}\n\n" for chunk in generate()), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response
