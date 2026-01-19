"""
Pre-Post Test Routes

Flask routes for pre-post test functionality.
"""

import json
import logging
from flask import render_template, jsonify, request, send_from_directory, current_app
from app.prepost import prepost_bp
from app.prepost.models import prepost_db
from app.prepost.questions import PrePostQuestions

logger = logging.getLogger(__name__)


@prepost_bp.route('/')
def prepost_page():
    """Serve the pre-post test HTML page."""
    return render_template('prepost/index.html')


@prepost_bp.route('/map/vulnerability')
def prepost_vulnerability_map():
    """Serve a public vulnerability map for the pre/post survey without auth.

    This avoids requiring a session-bound file path or authentication. The file is
    the composite vulnerability map placed under static/visualizations.
    """
    try:
        import os
        viz_dir = os.path.join(current_app.root_path, 'static', 'visualizations')
        filename = 'vulnerability_map_composite.html'
        return send_from_directory(viz_dir, filename, mimetype='text/html')
    except Exception as e:
        logger.error(f"Error serving prepost vulnerability map: {e}")
        return jsonify({'error': 'Map not available'}), 404


@prepost_bp.route('/api/check-phone', methods=['POST'])
def check_phone():
    """
    Check if phone number exists and determine test type.

    Request:
        {
            "phone_last4": "1234"
        }

    Response:
        {
            "success": true,
            "exists": true/false,
            "test_type": "pre"/"post",
            "has_pre_test": true/false,
            "has_post_test": true/false,
            "message": "..."
        }
    """
    try:
        data = request.json
        phone_last4 = data.get('phone_last4', '').strip()

        # Validate phone number
        if not phone_last4 or len(phone_last4) != 4 or not phone_last4.isdigit():
            return jsonify({
                'success': False,
                'error': 'Phone number must be exactly 4 digits'
            }), 400

        # Check if phone exists
        result = prepost_db.check_phone_exists(phone_last4)

        # Generate appropriate message
        if not result['exists']:
            message = "Welcome! You will take the PRE-TEST (background information + concept assessment)."
        elif result['test_type'] == 'post':
            message = "Welcome back! You will take the POST-TEST (concept assessment only)."
        else:
            message = "Welcome! You will take the PRE-TEST."

        return jsonify({
            'success': True,
            'exists': result['exists'],
            'test_type': result['test_type'],
            'has_pre_test': result['has_pre_test'],
            'has_post_test': result['has_post_test'],
            'message': message
        })

    except Exception as e:
        logger.error(f"Error checking phone: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@prepost_bp.route('/api/start', methods=['POST'])
def start_test():
    """
    Start a new pre or post test session.

    Request:
        {
            "phone_last4": "1234",
            "test_type": "pre"/"post"
        }

    Response:
        {
            "success": true,
            "session_id": "...",
            "test_type": "pre"/"post",
            "questions": [...],
            "total_questions": 14,
            "background_data": {...} (if post-test)
        }
    """
    try:
        data = request.json
        phone_last4 = data.get('phone_last4', '').strip()
        test_type = data.get('test_type', 'pre')

        logger.info(f"Start test request: phone={phone_last4}, type={test_type}")

        # Validate inputs
        if not phone_last4 or len(phone_last4) != 4 or not phone_last4.isdigit():
            return jsonify({
                'success': False,
                'error': 'Invalid phone number'
            }), 400

        if test_type not in ['pre', 'post']:
            return jsonify({
                'success': False,
                'error': 'Test type must be "pre" or "post"'
            }), 400

        # Create session
        session_id = prepost_db.create_session(phone_last4, test_type)
        logger.info(f"Created session: {session_id}")

        # Get appropriate questions
        if test_type == 'pre':
            questions = PrePostQuestions.get_pre_test_questions()
        else:  # post
            questions = PrePostQuestions.get_post_test_questions()

        logger.info(f"Got {len(questions)} questions for {test_type} test")

        # Get background data if post-test
        background_data = None
        if test_type == 'post':
            participant_info = prepost_db.check_phone_exists(phone_last4)
            background_data = participant_info.get('background_data')

        return jsonify({
            'success': True,
            'session_id': session_id,
            'test_type': test_type,
            'questions': questions,
            'total_questions': len(questions),
            'background_data': background_data
        })

    except Exception as e:
        logger.error(f"Error starting test: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@prepost_bp.route('/api/submit-response', methods=['POST'])
def submit_response():
    """
    Submit a response to a question.

    Request:
        {
            "session_id": "...",
            "question_id": "...",
            "section": "background"/"concepts",
            "response": "...",
            "time_spent": 45
        }

    Response:
        {
            "success": true,
            "message": "Response saved"
        }
    """
    try:
        data = request.json
        session_id = data.get('session_id')
        question_id = data.get('question_id')
        section = data.get('section')
        response = data.get('response')
        time_spent = data.get('time_spent')

        # Validate required fields
        if not all([session_id, question_id, section]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400

        # Validate response
        if not PrePostQuestions.validate_response(question_id, response):
            return jsonify({
                'success': False,
                'error': 'Invalid response for question type'
            }), 400

        # Save response
        prepost_db.save_response(session_id, question_id, section, response, time_spent)

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


@prepost_bp.route('/api/save-background', methods=['POST'])
def save_background():
    """
    Save background data for a participant (pre-test only).

    Request:
        {
            "phone_last4": "1234",
            "background_data": {
                "job_title": "...",
                "experience": 5,
                "computer_skills": 3,
                ...
            }
        }

    Response:
        {
            "success": true,
            "message": "Background data saved"
        }
    """
    try:
        data = request.json
        phone_last4 = data.get('phone_last4')
        background_data = data.get('background_data')

        if not phone_last4 or not background_data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400

        prepost_db.save_background_data(phone_last4, background_data)

        return jsonify({
            'success': True,
            'message': 'Background data saved'
        })

    except Exception as e:
        logger.error(f"Error saving background data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@prepost_bp.route('/api/complete', methods=['POST'])
def complete_test():
    """
    Mark a test session as completed.

    Request:
        {
            "session_id": "..."
        }

    Response:
        {
            "success": true,
            "message": "Test completed",
            "score": {
                "total_questions": 14,
                "correct_answers": 10,
                "score_percentage": 71.43
            }
        }
    """
    try:
        data = request.json
        session_id = data.get('session_id')

        if not session_id:
            return jsonify({
                'success': False,
                'error': 'Session ID required'
            }), 400

        # Get responses to calculate score
        responses = prepost_db.get_responses(session_id)

        # Calculate score
        score = PrePostQuestions.calculate_score(responses)

        # Mark session as completed
        prepost_db.complete_session(session_id)

        return jsonify({
            'success': True,
            'message': 'Test completed',
            'score': score
        })

    except Exception as e:
        logger.error(f"Error completing test: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@prepost_bp.route('/api/export', methods=['GET'])
def export_data():
    """
    Export all pre-post test data for analysis.

    Response:
        {
            "success": true,
            "data": [
                {
                    "phone_last4": "1234",
                    "pre_test_score": 65.5,
                    "post_test_score": 85.7,
                    "improvement": 20.2,
                    "background_data": {...},
                    ...
                }
            ]
        }
    """
    try:
        # Get all participant data
        all_data = prepost_db.export_all_data()

        # Calculate scores and improvements
        export_list = []
        for participant in all_data:
            export_item = {
                'phone_last4': participant['phone_last4'],
                'background_data': participant.get('background_data'),
                'pre_test_started': participant.get('pre_test_started_at'),
                'pre_test_completed': participant.get('pre_test_completed_at'),
                'post_test_started': participant.get('post_test_started_at'),
                'post_test_completed': participant.get('post_test_completed_at')
            }

            # Calculate pre-test score
            if participant.get('pre_test_responses'):
                pre_score = PrePostQuestions.calculate_score(
                    participant['pre_test_responses']
                )
                export_item['pre_test_score'] = pre_score['score_percentage']
                export_item['pre_test_correct'] = pre_score['correct_answers']
                export_item['pre_test_total'] = pre_score['total_questions']

            # Calculate post-test score
            if participant.get('post_test_responses'):
                post_score = PrePostQuestions.calculate_score(
                    participant['post_test_responses']
                )
                export_item['post_test_score'] = post_score['score_percentage']
                export_item['post_test_correct'] = post_score['correct_answers']
                export_item['post_test_total'] = post_score['total_questions']

            # Calculate improvement
            if 'pre_test_score' in export_item and 'post_test_score' in export_item:
                export_item['improvement'] = (
                    export_item['post_test_score'] - export_item['pre_test_score']
                )

            export_list.append(export_item)

        return jsonify({
            'success': True,
            'data': export_list,
            'total_participants': len(export_list)
        })

    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
