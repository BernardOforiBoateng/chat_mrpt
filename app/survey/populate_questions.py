#!/usr/bin/env python3
"""
Populate Survey Questions Database
Inserts Appendix 5 questions from questions.py into the survey database
"""

import sqlite3
import json
import os
from pathlib import Path
from app.survey.questions import SurveyQuestions

def populate_survey_questions(db_path='instance/survey.db'):
    """Populate survey questions into the database"""

    # Ensure database directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables if they don't exist (matching actual AWS schema)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS survey_questions (
            id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            question_text TEXT NOT NULL,
            question_type TEXT NOT NULL,
            options TEXT,
            required BOOLEAN DEFAULT TRUE,
            order_index INTEGER,
            trigger_context TEXT
        )
    ''')

    # Clear existing questions
    cursor.execute('DELETE FROM survey_questions')

    # Insert questions from new structure
    questions = SurveyQuestions.get_all_questions()
    question_count = 0

    for idx, question in enumerate(questions):
        question_id = question['id']
        text = question['text']
        q_type = question['type']
        required = question.get('required', True)
        category = f"{question['section']} - {question['topic']}"

        # Handle options
        options = None
        if 'options' in question:
            options = json.dumps(question['options'])
        elif 'labels' in question:
            # For scale questions
            options = json.dumps({
                'min': question.get('min', 1),
                'max': question.get('max', 5),
                'labels': question['labels']
            })

        # Insert the question
        cursor.execute('''
            INSERT INTO survey_questions
            (id, category, question_text, question_type, options, required, order_index, trigger_context)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (question_id, category, text, q_type, options, required, idx, None))

        question_count += 1

    conn.commit()
    print(f"✅ Successfully populated {question_count} questions into the database")

    # Verify insertion
    cursor.execute('SELECT COUNT(*) FROM survey_questions')
    total = cursor.fetchone()[0]
    print(f"📊 Total questions in database: {total}")

    # Show sample questions
    cursor.execute('SELECT id, category, question_text FROM survey_questions LIMIT 5')
    print("\n📝 Sample questions:")
    for row in cursor.fetchall():
        print(f"  - {row[0]} ({row[1]}): {row[2][:60]}...")

    conn.close()
    return question_count

if __name__ == '__main__':
    # Check if running from project root or survey directory
    if os.path.exists('instance/survey.db'):
        db_path = 'instance/survey.db'
    elif os.path.exists('../../instance/survey.db'):
        db_path = '../../instance/survey.db'
    else:
        # Create in current directory's instance folder
        db_path = 'instance/survey.db'

    populate_survey_questions(db_path)