"""
Survey Data Models

Defines the database schema for survey sessions, questions, and responses.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import sqlite3
import os
from pathlib import Path


class SurveyDatabase:
    """Manages survey database operations."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join('instance', 'survey.db')

        # Ensure directory exists
        Path(os.path.dirname(db_path)).mkdir(parents=True, exist_ok=True)

        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Survey sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS survey_sessions (
                id TEXT PRIMARY KEY,
                chatmrpt_session_id TEXT NOT NULL,
                user_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                context TEXT,
                status TEXT DEFAULT 'active'
            )
        ''')

        # Survey questions table
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

        # Survey responses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS survey_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                question_id TEXT NOT NULL,
                response TEXT NOT NULL,
                response_metadata TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                time_spent_seconds INTEGER,
                FOREIGN KEY (session_id) REFERENCES survey_sessions(id),
                FOREIGN KEY (question_id) REFERENCES survey_questions(id)
            )
        ''')

        # Survey triggers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS survey_triggers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chatmrpt_session_id TEXT NOT NULL,
                trigger_type TEXT NOT NULL,
                trigger_context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed BOOLEAN DEFAULT FALSE,
                survey_session_id TEXT,
                FOREIGN KEY (survey_session_id) REFERENCES survey_sessions(id)
            )
        ''')

        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_chatmrpt ON survey_sessions(chatmrpt_session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_response_session ON survey_responses(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trigger_session ON survey_triggers(chatmrpt_session_id)')

        conn.commit()
        conn.close()

    def create_survey_session(self, chatmrpt_session_id: str, context: Dict[str, Any]) -> str:
        """Create a new survey session."""
        import uuid

        session_id = str(uuid.uuid4())

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO survey_sessions (id, chatmrpt_session_id, context)
            VALUES (?, ?, ?)
        ''', (session_id, chatmrpt_session_id, json.dumps(context)))

        conn.commit()
        conn.close()

        return session_id

    def get_survey_session(self, session_id: str) -> Optional[Dict]:
        """Get survey session details."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM survey_sessions WHERE id = ?
        ''', (session_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'id': row[0],
                'chatmrpt_session_id': row[1],
                'user_id': row[2],
                'created_at': row[3],
                'completed_at': row[4],
                'context': json.loads(row[5]) if row[5] else {},
                'status': row[6]
            }
        return None

    def save_response(self, session_id: str, question_id: str, response: str,
                     metadata: Optional[Dict] = None, time_spent: Optional[int] = None):
        """Save a survey response."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO survey_responses
            (session_id, question_id, response, response_metadata, time_spent_seconds)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            session_id,
            question_id,
            response,
            json.dumps(metadata) if metadata else None,
            time_spent
        ))

        conn.commit()
        conn.close()

    def get_responses(self, session_id: str) -> List[Dict]:
        """Get all responses for a session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM survey_responses WHERE session_id = ?
            ORDER BY timestamp
        ''', (session_id,))

        rows = cursor.fetchall()
        conn.close()

        responses = []
        for row in rows:
            responses.append({
                'id': row[0],
                'session_id': row[1],
                'question_id': row[2],
                'response': row[3],
                'metadata': json.loads(row[4]) if row[4] else None,
                'timestamp': row[5],
                'time_spent_seconds': row[6]
            })

        return responses

    def create_trigger(self, chatmrpt_session_id: str, trigger_type: str, context: Dict) -> int:
        """Create a survey trigger."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO survey_triggers (chatmrpt_session_id, trigger_type, trigger_context)
            VALUES (?, ?, ?)
        ''', (chatmrpt_session_id, trigger_type, json.dumps(context)))

        trigger_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return trigger_id

    def get_pending_triggers(self, chatmrpt_session_id: str) -> List[Dict]:
        """Get pending survey triggers for a session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM survey_triggers
            WHERE chatmrpt_session_id = ? AND completed = FALSE
            ORDER BY created_at
        ''', (chatmrpt_session_id,))

        rows = cursor.fetchall()
        conn.close()

        triggers = []
        for row in rows:
            triggers.append({
                'id': row[0],
                'chatmrpt_session_id': row[1],
                'trigger_type': row[2],
                'trigger_context': json.loads(row[3]) if row[3] else {},
                'created_at': row[4],
                'completed': bool(row[5]),
                'survey_session_id': row[6]
            })

        return triggers

    def mark_trigger_completed(self, trigger_id: int, survey_session_id: str):
        """Mark a trigger as completed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE survey_triggers
            SET completed = TRUE, survey_session_id = ?
            WHERE id = ?
        ''', (survey_session_id, trigger_id))

        conn.commit()
        conn.close()

    def complete_session(self, session_id: str):
        """Mark a survey session as completed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE survey_sessions
            SET completed_at = CURRENT_TIMESTAMP, status = 'completed'
            WHERE id = ?
        ''', (session_id,))

        conn.commit()
        conn.close()


# Initialize database on module import
survey_db = SurveyDatabase()