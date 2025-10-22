"""Chat request handlers for analysis routes."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import traceback
from typing import Dict, Optional, Tuple

from flask import Response, current_app, jsonify, request, session, stream_with_context

from app.core.exceptions import ValidationError
from app.core.utils import convert_to_json_serializable
from app.runtime.tpr.workflow import (
    process_tpr_message as runtime_process_tpr_message,
    reset_tpr_handler_cache,
)

from .arena import process_arena_message, process_arena_streaming
from .routing import route_with_mistral

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public handlers
# ---------------------------------------------------------------------------

def handle_send_message() -> Response:
    """Entry point for synchronous chat processing."""
    try:
        payload = request.json or {}
        user_message = (payload.get('message') or '').strip()
        if not user_message:
            raise ValidationError('No message provided')

        tab_context = payload.get('tab_context', 'standard-upload')
        is_data_analysis = payload.get('is_data_analysis', False)

        if is_data_analysis:
            session['active_tab'] = 'data-analysis'
            session['use_data_analysis_v3'] = True
            logger.info('📊 Data Analysis tab active - setting V3 mode')

        session_id = session.get('session_id')
        request_start_time = time.time()
        interaction_logger = getattr(current_app.services, 'interaction_logger', None)

        _log_user_message(interaction_logger, session_id, user_message, request_start_time)

        tpr_response = _handle_tpr_workflow(session_id, user_message)
        if tpr_response is not None:
            return tpr_response

        has_uploaded_files = _detect_uploaded_files(session_id)
        session_context = _build_session_context(has_uploaded_files)

        routing_decision, clarification_response, effective_message = _resolve_routing(
            user_message, session_context
        )
        if clarification_response is not None:
            return clarification_response

        use_arena = routing_decision == 'can_answer'
        use_tools = routing_decision == 'needs_tools'
        processing_start_time = time.time()

        if use_arena:
            arena_result, arena_response = process_arena_message(
                user_message=effective_message,
                session_id=session_id,
                is_data_analysis=is_data_analysis,
                processing_start_time=processing_start_time,
            )
            if arena_response is not None:
                return arena_response
            response_payload = arena_result or {}
        else:
            interpreter = _get_request_interpreter()
            response_payload = interpreter.process_message(
                effective_message,
                session_id,
                is_data_analysis=is_data_analysis,
                tab_context=tab_context,
            )

        processing_duration = time.time() - processing_start_time
        total_response_time = time.time() - request_start_time

        _log_assistant_response(
            interaction_logger,
            session_id,
            user_message,
            response_payload,
            processing_duration,
            total_response_time,
        )

        formatted = _prepare_response_payload(
            response_payload,
            processing_duration,
            total_response_time,
        )
        _update_session_from_response(response_payload, session_id)

        return jsonify(convert_to_json_serializable(formatted))

    except ValidationError as exc:
        _log_validation_error(exc)
        return jsonify({'status': 'error', 'message': str(exc)}), 400
    except Exception as exc:  # pragma: no cover - defensive logging
        return _handle_unexpected_error(exc)


def handle_send_message_streaming() -> Response:
    """Entry point for streaming chat responses."""
    try:
        payload = request.json or {}
        user_message = (payload.get('message') or '').strip()
        if not user_message:
            return _stream_error('Please provide a message to continue.')

        tab_context = payload.get('tab_context', 'standard-upload')
        is_data_analysis = payload.get('is_data_analysis', False)

        if is_data_analysis:
            session['active_tab'] = 'data-analysis'
            session['use_data_analysis_v3'] = True
            logger.info('📊 Data Analysis tab active - setting V3 mode (streaming)')

        session_id = session.get('session_id')
        interaction_logger = getattr(current_app.services, 'interaction_logger', None)
        request_start_time = time.time()
        _log_user_message(interaction_logger, session_id, user_message, request_start_time, endpoint='/send_message_streaming')

        tpr_stream = _handle_tpr_workflow_streaming(session_id, user_message)
        if tpr_stream is not None:
            return tpr_stream

        has_uploaded_files = _detect_uploaded_files(session_id)
        session_context = _build_session_context(has_uploaded_files)

        routing_decision, clarification_response, effective_message = _resolve_routing(
            user_message, session_context
        )
        if clarification_response is not None:
            return clarification_response

        if routing_decision != 'needs_tools':
            arena_stream = process_arena_streaming(effective_message)
            if arena_stream is not None:
                return arena_stream
            return _stream_error('Streaming requires tool routing.')

        interpreter = _get_request_interpreter()

        def stream():
            try:
                for chunk in interpreter.process_message_streaming(
                    effective_message,
                    session_id=session_id,
                    session_data=session,
                ):
                    yield f"data: {json.dumps(chunk)}\n\n"
            except Exception as exc:  # pragma: no cover - streaming fallback
                logger.error('Error in streaming processing: %s', exc)
                error_chunk = {'content': f'Error: {exc}', 'status': 'error', 'done': True}
                yield f"data: {json.dumps(error_chunk)}\n\n"
            finally:
                _log_streaming_completion(interaction_logger, session_id)

        response = Response(stream_with_context(stream()), mimetype='text/event-stream')
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Connection'] = 'keep-alive'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['X-Accel-Buffering'] = 'no'
        return response

    except ValidationError as exc:
        _log_validation_error(exc)
        return jsonify({'status': 'error', 'message': str(exc)}), 400
    except Exception as exc:  # pragma: no cover - defensive logging
        return _handle_unexpected_error(exc)


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _log_user_message(interaction_logger, session_id: str, message: str, start_time: float, *, endpoint: str = '/send_message') -> None:
    if not interaction_logger:
        return

    interaction_logger.log_message(
        session_id=session_id,
        sender='user',
        content=message,
        intent=None,
        entities={
            'message_length': len(message),
            'timestamp': start_time,
            'session_message_count': session.get('message_count', 0) + 1,
            'request_endpoint': endpoint,
        },
    )
    interaction_logger.log_analysis_event(
        session_id=session_id,
        event_type='user_interaction',
        details={
            'action': 'message_sent',
            'message_type': 'chat_request',
            'session_duration': time.time() - session.get('session_start_time', time.time()),
            'is_follow_up': session.get('message_count', 0) > 0,
        },
        success=True,
    )
    session['message_count'] = session.get('message_count', 0) + 1


def _handle_tpr_workflow(session_id: str, user_message: str) -> Optional[Response]:
    if not session.get('tpr_workflow_active', False):
        return None

    logger.info('TPR workflow active for session %s, routing via runtime handler', session_id)
    try:
        tpr_result = runtime_process_tpr_message(session_id, user_message)
    except Exception as exc:
        logger.error('Error routing TPR workflow: %s', exc, exc_info=True)
        return jsonify({'status': 'error', 'message': f'Failed to process TPR workflow: {exc}'}), 500

    if tpr_result.get('workflow') in {'exit', 'data_upload'} or tpr_result.get('exit_data_analysis_mode'):
        session.pop('tpr_workflow_active', None)
        session.pop('tpr_session_id', None)
        session.modified = True
        reset_tpr_handler_cache(session_id)
    else:
        return jsonify(tpr_result)
    return None


def _handle_tpr_workflow_streaming(session_id: str, user_message: str) -> Optional[Response]:
    if not session.get('tpr_workflow_active', False):
        return None

    logger.info('TPR workflow active for session %s (streaming)', session_id)
    try:
        tpr_result = runtime_process_tpr_message(session_id, user_message)
    except Exception as exc:
        logger.error('Error routing to TPR handler: %s', exc, exc_info=True)
        return _stream_error(f'Failed to process TPR workflow: {exc}', status='error', workflow='tpr')

    if tpr_result.get('workflow') in {'exit', 'data_upload'} or tpr_result.get('exit_data_analysis_mode'):
        session.pop('tpr_workflow_active', None)
        session.pop('tpr_session_id', None)
        session['csv_loaded'] = True
        session['has_uploaded_files'] = True
        session['analysis_complete'] = True
        session.modified = True
        reset_tpr_handler_cache(session_id)
        return _stream_info('__DATA_UPLOADED__')

    payload = {
        'content': tpr_result.get('message') or tpr_result.get('response', ''),
        'status': tpr_result.get('status', 'success'),
        'visualizations': tpr_result.get('visualizations', []),
        'tools_used': tpr_result.get('tools_used', []),
        'workflow': tpr_result.get('workflow', 'tpr'),
        'stage': tpr_result.get('stage'),
        'download_links': tpr_result.get('download_links', []),
        'done': True,
    }
    return _stream_payload(payload)


def _detect_uploaded_files(session_id: str) -> bool:
    session_folder = os.path.join('instance', 'uploads', session_id or '')
    if os.path.exists(session_folder):
        for name in os.listdir(session_folder):
            if name.endswith(('.csv', '.xlsx', '.xls', '.shp', '.zip')) and not name.startswith('.'):
                return True
    return session.get('csv_loaded', False) or session.get('analysis_complete', False)


def _build_session_context(has_uploaded_files: bool) -> Dict[str, bool]:
    return {
        'has_uploaded_files': has_uploaded_files,
        'session_id': session.get('session_id'),
        'csv_loaded': session.get('csv_loaded', False),
        'shapefile_loaded': session.get('shapefile_loaded', False),
        'analysis_complete': session.get('analysis_complete', False),
        'use_data_analysis_v3': session.get('use_data_analysis_v3', False),
    }


def _resolve_routing(user_message: str, session_context: Dict) -> Tuple[str, Optional[Response], str]:
    original_message = user_message

    if session.get('pending_clarification'):
        pending = session.pop('pending_clarification')
        session.modified = True
        combined_message = f"{pending['original_message']} {user_message}"
        user_message = pending['original_message']
        routing_decision = _call_mistral(combined_message, session_context)
    else:
        routing_decision = _call_mistral(user_message, session_context)
        if routing_decision == 'needs_clarification':
            if len(user_message.split()) <= 3:
                routing_decision = 'can_answer'
            else:
                clarification = {
                    'needs_clarification': True,
                    'clarification_type': 'intent',
                    'message': 'I need more information to help you. Are you looking to:',
                    'options': [
                        {'id': 'analyze_data', 'label': 'Analyze your uploaded data', 'icon': '📊', 'value': 'tools'},
                        {'id': 'general_info', 'label': 'Get general information', 'icon': '📚', 'value': 'arena'},
                    ],
                    'original_message': user_message,
                    'session_context': session_context,
                }
                session['pending_clarification'] = {
                    'original_message': user_message,
                    'context': session_context,
                }
                session.modified = True
                return routing_decision, jsonify(clarification), original_message

    return routing_decision, None, user_message


def _call_mistral(message: str, session_context: Dict) -> str:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(route_with_mistral(message, session_context))
    finally:
        loop.close()


def _get_request_interpreter():
    try:
        interpreter = current_app.services.request_interpreter
    except Exception as exc:
        logger.error('Error getting Request Interpreter: %s', exc)
        raise ValidationError('Request processing system not available') from exc
    if interpreter is None:
        raise ValidationError('Request processing system not available')
    return interpreter


def _log_assistant_response(
    interaction_logger,
    session_id: str,
    user_message: str,
    response: Dict,
    processing_duration: float,
    total_response_time: float,
) -> None:
    if not interaction_logger:
        return

    overhead_time = total_response_time - processing_duration
    ai_response_content = response.get('response', 'Request processed successfully')

    interaction_logger.log_message(
        session_id=session_id,
        sender='assistant',
        content=ai_response_content,
        intent=response.get('intent_type'),
        entities={
            'response_length': len(ai_response_content),
            'processing_time_seconds': processing_duration,
            'total_response_time_seconds': total_response_time,
            'overhead_time_seconds': overhead_time,
            'response_efficiency': round(processing_duration / total_response_time * 100, 1) if total_response_time > 0 else 100,
            'tools_used': response.get('tools_used', []),
            'tools_count': len(response.get('tools_used', [])),
            'visualizations_created': len(response.get('visualizations', [])),
            'status': response.get('status', 'success'),
            'timestamp': time.time(),
            'performance_category': 'fast' if total_response_time < 5 else 'medium' if total_response_time < 15 else 'slow',
        },
    )

    detailed_timing = response.get('timing_breakdown', {})
    performance_metrics = response.get('performance_metrics', {})

    interaction_logger.log_analysis_event(
        session_id=session_id,
        event_type='response_timing',
        details={
            'total_response_time_seconds': total_response_time,
            'processing_time_seconds': processing_duration,
            'overhead_time_seconds': overhead_time,
            'response_efficiency_percent': round(processing_duration / total_response_time * 100, 1) if total_response_time > 0 else 100,
            'performance_category': 'fast' if total_response_time < 5 else 'medium' if total_response_time < 15 else 'slow',
            'message_length': len(user_message),
            'response_length': len(ai_response_content),
            'complexity_score': len(response.get('tools_used', [])) * 2 + len(response.get('visualizations', [])),
            'endpoint': '/send_message',
            'timing_breakdown': {
                'context_retrieval_ms': detailed_timing.get('context_retrieval', 0) * 1000,
                'prompt_building_ms': detailed_timing.get('prompt_building', 0) * 1000,
                'llm_processing_ms': detailed_timing.get('llm_processing', 0) * 1000,
                'tool_execution_ms': detailed_timing.get('tool_execution', 0) * 1000,
                'response_formatting_ms': detailed_timing.get('response_formatting', 0) * 1000,
                'total_duration_ms': detailed_timing.get('total_duration', 0) * 1000,
            },
            'performance_metrics': {
                'llm_percentage': performance_metrics.get('llm_percentage', 0),
                'tool_percentage': performance_metrics.get('tool_percentage', 0),
                'context_percentage': performance_metrics.get('context_percentage', 0),
                'bottleneck': performance_metrics.get('bottleneck', 'unknown'),
            },
        },
        success=True,
    )


def _prepare_response_payload(response: Dict, processing_duration: float, total_response_time: float) -> Dict:
    if response.get('arena_mode'):
        payload = {
            'status': response.get('status', 'success'),
            'message': response.get('response', 'Arena comparison ready'),
            'response': response.get('response', 'Arena comparison ready'),
            'arena_mode': True,
            'battle_id': response.get('battle_id'),
            'response_a': response.get('response_a'),
            'response_b': response.get('response_b'),
            'latency_a': response.get('latency_a'),
            'latency_b': response.get('latency_b'),
            'view_index': response.get('view_index'),
            'model_a': response.get('model_a'),
            'model_b': response.get('model_b'),
        }
    else:
        payload = {
            'status': response.get('status', 'success'),
            'message': response.get('response', 'Request processed successfully'),
            'response': response.get('response', 'Request processed successfully'),
            'explanations': response.get('explanations', []),
            'data_summary': response.get('data_summary'),
            'tools_used': response.get('tools_used', []),
            'intent_type': response.get('intent_type'),
        }

    payload['processing_time'] = f"{processing_duration:.2f}s"
    payload['total_response_time'] = f"{total_response_time:.2f}s"
    payload['response_efficiency'] = (
        f"{round(processing_duration / total_response_time * 100, 1) if total_response_time > 0 else 100}%"
    )

    visualizations = response.get('visualizations', [])
    if visualizations:
        valid = [
            viz
            for viz in visualizations
            if isinstance(viz, dict) and (viz.get('url') or viz.get('path') or viz.get('html'))
        ]
        if valid:
            payload['visualizations'] = valid

    return payload


def _update_session_from_response(response: Dict, session_id: str) -> None:
    tools_used = response.get('tools_used', [])
    analysis_tools = {'run_composite_analysis', 'run_pca_analysis', 'runcompleteanalysis'}
    if any(tool in tools_used for tool in analysis_tools):
        session['analysis_complete'] = True
        if 'runcompleteanalysis' in tools_used:
            session['analysis_type'] = 'dual_method'
        elif 'run_composite_analysis' in tools_used:
            session['analysis_type'] = 'composite'
        else:
            session['analysis_type'] = 'pca'
        session.modified = True
        logger.info('Session %s: Analysis completed via Request Interpreter (%s)', session_id, session.get('analysis_type'))

        session.pop('pending_action', None)
        session.pop('pending_variables', None)
        session.modified = True


def _log_validation_error(exc: ValidationError) -> None:
    interaction_logger = getattr(current_app.services, 'interaction_logger', None)
    if interaction_logger:
        interaction_logger.log_error(
            session_id=session.get('session_id'),
            error_type='ValidationError',
            error_message=str(exc),
            stack_trace=traceback.format_exc(),
        )


def _handle_unexpected_error(exc: Exception) -> Response:
    session_id = session.get('session_id')
    interaction_logger = getattr(current_app.services, 'interaction_logger', None)

    error_details = {
        'error_type': type(exc).__name__,
        'error_message': str(exc),
        'endpoint': '/send_message',
        'user_message': (locals().get('user_message') or '')[:100],
        'processing_stage': 'request_interpreter_processing',
        'timestamp': time.time(),
    }

    if interaction_logger:
        interaction_logger.log_error(
            session_id=session_id,
            error_type=type(exc).__name__,
            error_message=str(exc),
            stack_trace=traceback.format_exc(),
        )
        interaction_logger.log_analysis_event(
            session_id=session_id,
            event_type='system_error',
            details=error_details,
            success=False,
        )

    logger.error('Error processing message: %s', exc, exc_info=True)
    return jsonify({'status': 'error', 'message': f'Error processing message: {exc}'}), 500


def _stream_payload(payload: Dict) -> Response:
    def generator():
        yield f"data: {json.dumps(payload)}\n\n"

    response = Response(generator(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['X-Accel-Buffering'] = 'no'
    return response


def _stream_error(message: str, *, status: str = 'success', workflow: Optional[str] = None) -> Response:
    payload = {'content': message, 'status': status, 'done': True}
    if workflow:
        payload['workflow'] = workflow
    return _stream_payload(payload)


def _stream_info(message: str) -> Response:
    return _stream_payload({'content': message, 'status': 'success', 'done': True})


def _log_streaming_completion(interaction_logger, session_id: str) -> None:
    if not interaction_logger:
        return
    interaction_logger.log_analysis_event(
        session_id=session_id,
        event_type='streaming_complete',
        details={'status': 'finished'},
        success=True,
    )


__all__ = ['handle_send_message', 'handle_send_message_streaming']
