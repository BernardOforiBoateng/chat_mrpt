"""
Pre-Post Test Data Models

Manages database operations for the pre-post test survey system.
Separate from the main survey system for research/publication purposes.
"""

import json
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class PrePostDatabase:
    """Manages pre-post test database operations."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join('instance', 'prepost_test.db')

        # Ensure directory exists
        Path(os.path.dirname(db_path)).mkdir(parents=True, exist_ok=True)

        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Participants table - tracks unique users by phone number
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prepost_participants (
                phone_last4 TEXT PRIMARY KEY,
                pre_test_session_id TEXT,
                post_test_session_id TEXT,
                pre_test_started_at TIMESTAMP,
                pre_test_completed_at TIMESTAMP,
                post_test_started_at TIMESTAMP,
                post_test_completed_at TIMESTAMP,
                background_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Sessions table - tracks individual test sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prepost_sessions (
                id TEXT PRIMARY KEY,
                phone_last4 TEXT NOT NULL,
                test_type TEXT NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                status TEXT DEFAULT 'active',
                FOREIGN KEY (phone_last4) REFERENCES prepost_participants(phone_last4)
            )
        ''')

        # Responses table - stores individual question responses
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prepost_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                question_id TEXT NOT NULL,
                section TEXT NOT NULL,
                response TEXT NOT NULL,
                time_spent_seconds INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES prepost_sessions(id)
            )
        ''')

        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_participant_phone ON prepost_participants(phone_last4)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_phone ON prepost_sessions(phone_last4)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_response_session ON prepost_responses(session_id)')

        conn.commit()
        conn.close()

    def check_phone_exists(self, phone_last4: str) -> Dict[str, Any]:
        """
        Check if phone number exists and determine test type.

        Returns:
            {
                'exists': bool,
                'test_type': 'pre' or 'post',
                'has_pre_test': bool,
                'has_post_test': bool,
                'background_data': dict or None
            }
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT pre_test_session_id, post_test_session_id,
                   pre_test_completed_at, post_test_completed_at,
                   background_data
            FROM prepost_participants
            WHERE phone_last4 = ?
        ''', (phone_last4,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return {
                'exists': False,
                'test_type': 'pre',
                'has_pre_test': False,
                'has_post_test': False,
                'background_data': None
            }

        pre_session_id, post_session_id, pre_completed, post_completed, bg_data = row

        has_pre = bool(pre_session_id and pre_completed)
        has_post = bool(post_session_id and post_completed)

        # Determine next test type
        if not has_pre:
            test_type = 'pre'
        elif not has_post:
            test_type = 'post'
        else:
            # Both completed - default to post for retake
            test_type = 'post'

        return {
            'exists': True,
            'test_type': test_type,
            'has_pre_test': has_pre,
            'has_post_test': has_post,
            'background_data': json.loads(bg_data) if bg_data else None
        }

    def create_session(self, phone_last4: str, test_type: str) -> str:
        """
        Create a new test session.

        Args:
            phone_last4: Last 4 digits of phone number
            test_type: 'pre' or 'post'

        Returns:
            session_id: Unique session identifier
        """
        import uuid

        session_id = str(uuid.uuid4())

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create or update participant record
        cursor.execute('''
            INSERT INTO prepost_participants (phone_last4)
            VALUES (?)
            ON CONFLICT(phone_last4) DO NOTHING
        ''', (phone_last4,))

        # Create session
        cursor.execute('''
            INSERT INTO prepost_sessions (id, phone_last4, test_type)
            VALUES (?, ?, ?)
        ''', (session_id, phone_last4, test_type))

        # Update participant with session ID
        if test_type == 'pre':
            cursor.execute('''
                UPDATE prepost_participants
                SET pre_test_session_id = ?, pre_test_started_at = CURRENT_TIMESTAMP
                WHERE phone_last4 = ?
            ''', (session_id, phone_last4))
        else:  # post
            cursor.execute('''
                UPDATE prepost_participants
                SET post_test_session_id = ?, post_test_started_at = CURRENT_TIMESTAMP
                WHERE phone_last4 = ?
            ''', (session_id, phone_last4))

        conn.commit()
        conn.close()

        return session_id

    def save_response(self, session_id: str, question_id: str, section: str,
                     response: Any, time_spent: Optional[int] = None):
        """
        Save a question response.

        Args:
            session_id: Session identifier
            question_id: Question identifier
            section: 'background' or 'concepts'
            response: User's response (will be JSON encoded if dict/list)
            time_spent: Time spent on question in seconds
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Convert response to JSON if it's a complex type
        if isinstance(response, (dict, list)):
            response_str = json.dumps(response)
        else:
            response_str = str(response)

        cursor.execute('''
            INSERT INTO prepost_responses
            (session_id, question_id, section, response, time_spent_seconds)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, question_id, section, response_str, time_spent))

        conn.commit()
        conn.close()

    def save_background_data(self, phone_last4: str, background_data: Dict[str, Any]):
        """
        Save background information for a participant.

        Args:
            phone_last4: Last 4 digits of phone number
            background_data: Dictionary with background info (job_title, skills, etc.)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE prepost_participants
            SET background_data = ?
            WHERE phone_last4 = ?
        ''', (json.dumps(background_data), phone_last4))

        conn.commit()
        conn.close()

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session details."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM prepost_sessions WHERE id = ?
        ''', (session_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'id': row[0],
                'phone_last4': row[1],
                'test_type': row[2],
                'started_at': row[3],
                'completed_at': row[4],
                'status': row[5]
            }
        return None

    def get_responses(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all responses for a session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM prepost_responses
            WHERE session_id = ?
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
                'section': row[3],
                'response': row[4],
                'time_spent_seconds': row[5],
                'timestamp': row[6]
            })

        return responses

    def complete_session(self, session_id: str):
        """Mark a session as completed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get session info to determine test type
        cursor.execute('SELECT phone_last4, test_type FROM prepost_sessions WHERE id = ?',
                      (session_id,))
        row = cursor.fetchone()

        if row:
            phone_last4, test_type = row

            # Update session
            cursor.execute('''
                UPDATE prepost_sessions
                SET completed_at = CURRENT_TIMESTAMP, status = 'completed'
                WHERE id = ?
            ''', (session_id,))

            # Update participant
            if test_type == 'pre':
                cursor.execute('''
                    UPDATE prepost_participants
                    SET pre_test_completed_at = CURRENT_TIMESTAMP
                    WHERE phone_last4 = ?
                ''', (phone_last4,))
            else:  # post
                cursor.execute('''
                    UPDATE prepost_participants
                    SET post_test_completed_at = CURRENT_TIMESTAMP
                    WHERE phone_last4 = ?
                ''', (phone_last4,))

            conn.commit()

        conn.close()

    def get_participant_data(self, phone_last4: str) -> Optional[Dict[str, Any]]:
        """Get all data for a participant (both pre and post test)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM prepost_participants WHERE phone_last4 = ?',
                      (phone_last4,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return None

        participant = {
            'phone_last4': row[0],
            'pre_test_session_id': row[1],
            'post_test_session_id': row[2],
            'pre_test_started_at': row[3],
            'pre_test_completed_at': row[4],
            'post_test_started_at': row[5],
            'post_test_completed_at': row[6],
            'background_data': json.loads(row[7]) if row[7] else None,
            'created_at': row[8]
        }

        # Get pre-test responses if exists
        if participant['pre_test_session_id']:
            participant['pre_test_responses'] = self.get_responses(
                participant['pre_test_session_id']
            )

        # Get post-test responses if exists
        if participant['post_test_session_id']:
            participant['post_test_responses'] = self.get_responses(
                participant['post_test_session_id']
            )

        conn.close()
        return participant

    def export_all_data(self) -> List[Dict[str, Any]]:
        """
        Export all participant data for analysis.

        Returns a list of dictionaries with pre-test, post-test, and comparison data.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT phone_last4 FROM prepost_participants')
        phone_numbers = [row[0] for row in cursor.fetchall()]
        conn.close()

        export_data = []
        for phone in phone_numbers:
            participant = self.get_participant_data(phone)
            if participant:
                export_data.append(participant)

        return export_data


# Initialize database on module import
prepost_db = PrePostDatabase()
