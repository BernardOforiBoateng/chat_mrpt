"""
Survey Module for ChatMRPT Cognitive Assessment

This module handles survey functionality for evaluating user comprehension,
preferences, and understanding of ChatMRPT outputs during training sessions.
"""

import logging
from flask import Blueprint
from pathlib import Path

logger = logging.getLogger(__name__)

# Create survey blueprint
survey_bp = Blueprint('survey', __name__, url_prefix='/survey')

def init_survey_database():
    """Initialize survey database and populate questions if needed"""
    try:
        from app.survey.models import survey_db

        # Check if questions exist
        question_count = survey_db.get_question_count()

        if question_count == 0:
            logger.info("No questions found in database. Populating from Appendix 5...")

            # Import and run the population script
            from app.survey.populate_questions import populate_survey_questions

            # Get the correct database path
            db_path = Path('instance/survey.db')
            if not db_path.exists():
                db_path = Path(__file__).parent.parent.parent / 'instance' / 'survey.db'

            count = populate_survey_questions(str(db_path))
            logger.info(f"✅ Populated {count} questions into survey database")
        else:
            logger.info(f"✅ Survey database already has {question_count} questions")

    except Exception as e:
        logger.error(f"Error initializing survey database: {e}")
        logger.exception(e)

# Initialize database on module load
init_survey_database()

from . import routes