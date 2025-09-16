"""
Survey Routes

Flask routes for survey functionality.
"""

import json
import logging
from flask import render_template, jsonify, request, session
from app.survey import survey_bp
from app.survey.models import survey_db
from app.survey.questions import SurveyQuestions

logger = logging.getLogger(__name__)


@survey_bp.route('/')
def survey_page():
    """Serve the survey HTML page."""
    # Get parameters from URL
    chatmrpt_session = request.args.get('session_id')
    context = request.args.get('context', '')
    trigger = request.args.get('trigger', '')

    # Parse context if it's JSON
    try:
        if context and context.startswith('{'):
            context = json.loads(context)
    except json.JSONDecodeError:
        pass

    return render_template('survey/index.html',
                         chatmrpt_session=chatmrpt_session,
                         context=context,
                         trigger=trigger)


@survey_bp.route('/api/status/<chatmrpt_session>')
def check_survey_status(chatmrpt_session):
    """Check if there are pending surveys for a ChatMRPT session."""
    try:
        pending_triggers = survey_db.get_pending_triggers(chatmrpt_session)

        return jsonify({
            'success': True,
            'pending_count': len(pending_triggers),
            'triggers': pending_triggers
        })

    except Exception as e:
        logger.error(f"Error checking survey status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@survey_bp.route('/api/start', methods=['POST'])
def start_survey():
    """Start a new survey session."""
    try:
        data = request.json
        chatmrpt_session = data.get('chatmrpt_session_id')
        trigger_type = data.get('trigger_type')
        context = data.get('context', {})

        if not chatmrpt_session:
            return jsonify({
                'success': False,
                'error': 'ChatMRPT session ID required'
            }), 400

        # Create survey session
        session_id = survey_db.create_survey_session(chatmrpt_session, context)

        # Get questions for this trigger
        questions = SurveyQuestions.get_questions_for_trigger(trigger_type, context)

        # Mark trigger as started if provided
        trigger_id = context.get('trigger_id')
        if trigger_id:
            survey_db.mark_trigger_completed(trigger_id, session_id)

        return jsonify({
            'success': True,
            'session_id': session_id,
            'questions': questions
        })

    except Exception as e:
        logger.error(f"Error starting survey: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@survey_bp.route('/api/questions/<session_id>')
def get_questions(session_id):
    """Get questions for a survey session."""
    try:
        # Get session details
        survey_session = survey_db.get_survey_session(session_id)

        if not survey_session:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404

        context = survey_session.get('context', {})
        trigger_type = context.get('trigger_type', 'general_usability')

        # Get questions based on trigger
        questions = SurveyQuestions.get_questions_for_trigger(trigger_type, context)

        # Get existing responses to track progress
        responses = survey_db.get_responses(session_id)
        answered_ids = [r['question_id'] for r in responses]

        # Mark answered questions
        for q in questions:
            q['answered'] = q.get('id') in answered_ids

        return jsonify({
            'success': True,
            'questions': questions,
            'progress': {
                'total': len(questions),
                'answered': len(answered_ids)
            }
        })

    except Exception as e:
        logger.error(f"Error getting questions: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@survey_bp.route('/api/submit', methods=['POST'])
def submit_response():
    """Submit a survey response."""
    try:
        data = request.json
        session_id = data.get('session_id')
        question_id = data.get('question_id')
        response = data.get('response')
        metadata = data.get('metadata', {})
        time_spent = data.get('time_spent')

        # Validate required fields
        if not all([session_id, question_id, response]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400

        # Validate response
        if not SurveyQuestions.validate_response(question_id, response):
            return jsonify({
                'success': False,
                'error': 'Invalid response for question type'
            }), 400

        # Save response
        survey_db.save_response(session_id, question_id, response, metadata, time_spent)

        return jsonify({
            'success': True,
            'message': 'Response saved'
        })

    except Exception as e:
        logger.error(f"Error saving response: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@survey_bp.route('/api/complete/<session_id>', methods=['POST'])
def complete_survey(session_id):
    """Mark a survey as completed."""
    try:
        survey_db.complete_session(session_id)

        return jsonify({
            'success': True,
            'message': 'Survey completed'
        })

    except Exception as e:
        logger.error(f"Error completing survey: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@survey_bp.route('/api/trigger', methods=['POST'])
def create_trigger():
    """Create a survey trigger from ChatMRPT interaction."""
    try:
        data = request.json
        chatmrpt_session = data.get('chatmrpt_session_id')
        trigger_type = data.get('trigger_type')
        context = data.get('context', {})

        if not chatmrpt_session or not trigger_type:
            return jsonify({
                'success': False,
                'error': 'Session ID and trigger type required'
            }), 400

        # Create trigger
        trigger_id = survey_db.create_trigger(chatmrpt_session, trigger_type, context)

        return jsonify({
            'success': True,
            'trigger_id': trigger_id
        })

    except Exception as e:
        logger.error(f"Error creating trigger: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@survey_bp.route('/api/export/<session_id>')
def export_responses(session_id):
    """Export survey responses for analysis."""
    try:
        # Get session details
        survey_session = survey_db.get_survey_session(session_id)

        if not survey_session:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404

        # Get all responses
        responses = survey_db.get_responses(session_id)

        # Format for export
        export_data = {
            'session': survey_session,
            'responses': responses,
            'summary': {
                'total_questions': len(responses),
                'completion_time': survey_session.get('completed_at'),
                'chatmrpt_session': survey_session.get('chatmrpt_session_id')
            }
        }

        return jsonify(export_data)

    except Exception as e:
        logger.error(f"Error exporting responses: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500