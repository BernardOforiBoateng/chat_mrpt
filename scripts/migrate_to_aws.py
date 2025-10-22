#!/usr/bin/env python3
"""
Migration script from Flask to AWS serverless architecture.
Handles data migration from SQLite/PostgreSQL to DynamoDB and file migration to S3.
"""

import os
import sys
import json
import sqlite3
import boto3
import pandas as pd
from datetime import datetime
from pathlib import Path
import shutil
import hashlib
from typing import Dict, List, Any, Optional
import argparse
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AWSMigration:
    """Handle migration from Flask app to AWS serverless."""

    def __init__(self, env: str = 'prod', dry_run: bool = False):
        """
        Initialize migration.

        Args:
            env: Environment (dev/staging/prod)
            dry_run: If True, don't actually perform migrations
        """
        self.env = env
        self.dry_run = dry_run
        self.project_name = 'chatmrpt'

        # Initialize AWS clients
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
        self.s3 = boto3.client('s3', region_name='us-east-2')
        self.cognito = boto3.client('cognito-idp', region_name='us-east-2')

        # Table names
        self.users_table = f"{self.project_name}-users-{env}"
        self.analyses_table = f"{self.project_name}-analyses-{env}"
        self.sessions_table = f"{self.project_name}-sessions-{env}"
        self.audit_table = f"{self.project_name}-audit-{env}"

        # S3 bucket names
        self.data_bucket = f"{self.project_name}-data-{env}"
        self.frontend_bucket = f"{self.project_name}-frontend-{env}"

        # User pool
        self.user_pool_id = os.environ.get(f'COGNITO_USER_POOL_ID_{env.upper()}')

        # Migration stats
        self.stats = {
            'users_migrated': 0,
            'analyses_migrated': 0,
            'files_migrated': 0,
            'errors': []
        }

    def migrate_all(self):
        """Run complete migration."""
        logger.info(f"Starting migration to AWS ({self.env})")
        logger.info(f"Dry run: {self.dry_run}")

        try:
            # 1. Migrate users
            self.migrate_users()

            # 2. Migrate analysis data
            self.migrate_analyses()

            # 3. Migrate uploaded files
            self.migrate_files()

            # 4. Generate migration report
            self.generate_report()

            logger.info("Migration completed successfully!")

        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            self.stats['errors'].append(str(e))
            self.generate_report()
            raise

    def migrate_users(self):
        """Migrate users from SQLite to Cognito and DynamoDB."""
        logger.info("Migrating users...")

        # Check for existing user database
        db_path = Path('instance/interactions.db')
        if not db_path.exists():
            logger.warning("No user database found, skipping user migration")
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            # Get all users (adjust query based on actual schema)
            cursor.execute("""
                SELECT DISTINCT user_id, session_id, created_at
                FROM interactions
                WHERE user_id IS NOT NULL
            """)
            users = cursor.fetchall()

            for user_id, session_id, created_at in users:
                try:
                    # Generate email if not available
                    email = f"user_{user_id}@migration.chatmrpt.com"

                    if not self.dry_run:
                        # Create Cognito user
                        self.create_cognito_user(user_id, email)

                        # Create DynamoDB user profile
                        self.create_dynamodb_user(user_id, email, created_at)

                    self.stats['users_migrated'] += 1
                    logger.info(f"Migrated user: {user_id}")

                except Exception as e:
                    logger.error(f"Error migrating user {user_id}: {str(e)}")
                    self.stats['errors'].append(f"User {user_id}: {str(e)}")

        finally:
            conn.close()

    def create_cognito_user(self, user_id: str, email: str):
        """Create user in Cognito User Pool."""
        if not self.user_pool_id:
            logger.warning("No User Pool ID configured, skipping Cognito creation")
            return

        try:
            # Generate temporary password
            temp_password = self.generate_temp_password(user_id)

            response = self.cognito.admin_create_user(
                UserPoolId=self.user_pool_id,
                Username=email,
                UserAttributes=[
                    {'Name': 'email', 'Value': email},
                    {'Name': 'email_verified', 'Value': 'true'},
                    {'Name': 'custom:migration_id', 'Value': user_id},
                    {'Name': 'custom:role', 'Value': 'researcher'}
                ],
                TemporaryPassword=temp_password,
                MessageAction='SUPPRESS'  # Don't send welcome email
            )

            # Store migration info for user notification
            self.store_migration_info(user_id, email, temp_password)

        except self.cognito.exceptions.UsernameExistsException:
            logger.info(f"User {email} already exists in Cognito")
        except Exception as e:
            logger.error(f"Error creating Cognito user: {str(e)}")
            raise

    def create_dynamodb_user(self, user_id: str, email: str, created_at: str):
        """Create user profile in DynamoDB."""
        table = self.dynamodb.Table(self.users_table)

        try:
            item = {
                'user_id': user_id,
                'email': email.lower(),
                'username': email,
                'created_at': int(datetime.fromisoformat(created_at).timestamp()) if created_at else int(datetime.now().timestamp()),
                'last_login': int(datetime.now().timestamp()),
                'status': 'active',
                'migration_date': int(datetime.now().timestamp()),
                'organization': 'Migrated User',
                'role': 'researcher',
                'preferences': {
                    'theme': 'light',
                    'notifications': True
                },
                'usage_stats': {
                    'analyses_count': 0,
                    'last_analysis': None,
                    'total_data_processed_mb': 0
                }
            }

            table.put_item(Item=item)
            logger.debug(f"Created DynamoDB profile for {user_id}")

        except Exception as e:
            logger.error(f"Error creating DynamoDB user: {str(e)}")
            raise

    def migrate_analyses(self):
        """Migrate analysis history from SQLite to DynamoDB."""
        logger.info("Migrating analyses...")

        db_path = Path('instance/interactions.db')
        if not db_path.exists():
            logger.warning("No interactions database found, skipping analysis migration")
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            # Get all analyses (adjust based on actual schema)
            cursor.execute("""
                SELECT id, user_id, session_id, request_type, request_data,
                       response_data, created_at, duration_ms
                FROM interactions
                WHERE request_type LIKE '%analysis%'
                ORDER BY created_at
            """)
            analyses = cursor.fetchall()

            table = self.dynamodb.Table(self.analyses_table)

            for analysis in analyses:
                try:
                    analysis_id, user_id, session_id, request_type, request_data, response_data, created_at, duration = analysis

                    if not self.dry_run:
                        item = {
                            'user_id': user_id or 'anonymous',
                            'analysis_id': f"migrated_{analysis_id}",
                            'session_id': session_id,
                            'analysis_type': self.map_analysis_type(request_type),
                            'status': 'completed',
                            'created_at': int(datetime.fromisoformat(created_at).timestamp()) if created_at else int(datetime.now().timestamp()),
                            'updated_at': int(datetime.now().timestamp()),
                            'request': json.loads(request_data) if request_data else {},
                            'response': json.loads(response_data) if response_data else {},
                            'duration_ms': duration,
                            'migration_date': int(datetime.now().timestamp()),
                            'ttl': int(datetime.now().timestamp()) + (365 * 24 * 60 * 60)  # 1 year TTL
                        }

                        table.put_item(Item=item)

                    self.stats['analyses_migrated'] += 1
                    logger.debug(f"Migrated analysis: {analysis_id}")

                except Exception as e:
                    logger.error(f"Error migrating analysis {analysis_id}: {str(e)}")
                    self.stats['errors'].append(f"Analysis {analysis_id}: {str(e)}")

        finally:
            conn.close()

    def migrate_files(self):
        """Migrate uploaded files and results from local storage to S3."""
        logger.info("Migrating files to S3...")

        uploads_dir = Path('instance/uploads')
        if not uploads_dir.exists():
            logger.warning("No uploads directory found, skipping file migration")
            return

        # Iterate through session directories
        for session_dir in uploads_dir.iterdir():
            if not session_dir.is_dir():
                continue

            session_id = session_dir.name
            logger.info(f"Migrating files for session: {session_id}")

            for file_path in session_dir.rglob('*'):
                if file_path.is_file():
                    try:
                        # Determine S3 key based on file type
                        relative_path = file_path.relative_to(uploads_dir)
                        s3_key = f"migrated/{relative_path}"

                        if not self.dry_run:
                            # Upload to S3
                            self.s3.upload_file(
                                str(file_path),
                                self.data_bucket,
                                s3_key,
                                ExtraArgs={
                                    'Metadata': {
                                        'migration_date': datetime.now().isoformat(),
                                        'original_path': str(relative_path)
                                    }
                                }
                            )

                        self.stats['files_migrated'] += 1
                        logger.debug(f"Uploaded: {relative_path} -> s3://{self.data_bucket}/{s3_key}")

                    except Exception as e:
                        logger.error(f"Error uploading {file_path}: {str(e)}")
                        self.stats['errors'].append(f"File {file_path}: {str(e)}")

    def map_analysis_type(self, request_type: str) -> str:
        """Map old analysis types to new schema."""
        mapping = {
            'composite_analysis': 'composite_scoring',
            'pca_analysis': 'pca',
            'ranking': 'vulnerability_ranking',
            'settlement': 'settlement_analysis'
        }

        for old, new in mapping.items():
            if old in request_type.lower():
                return new

        return 'unknown'

    def generate_temp_password(self, user_id: str) -> str:
        """Generate temporary password for migrated user."""
        # Generate deterministic but secure password
        hash_input = f"{user_id}_{self.env}_migration_2024"
        hash_output = hashlib.sha256(hash_input.encode()).hexdigest()
        return f"Temp_{hash_output[:8]}!Migrate2024"

    def store_migration_info(self, user_id: str, email: str, temp_password: str):
        """Store migration info for user notification."""
        migration_file = Path(f"migration_users_{self.env}.json")

        data = []
        if migration_file.exists():
            with open(migration_file, 'r') as f:
                data = json.load(f)

        data.append({
            'user_id': user_id,
            'email': email,
            'temp_password': temp_password,
            'migration_date': datetime.now().isoformat()
        })

        with open(migration_file, 'w') as f:
            json.dump(data, f, indent=2)

    def generate_report(self):
        """Generate migration report."""
        report = {
            'migration_date': datetime.now().isoformat(),
            'environment': self.env,
            'dry_run': self.dry_run,
            'statistics': self.stats,
            'tables': {
                'users_table': self.users_table,
                'analyses_table': self.analyses_table,
                'sessions_table': self.sessions_table
            },
            'buckets': {
                'data_bucket': self.data_bucket,
                'frontend_bucket': self.frontend_bucket
            }
        }

        report_file = f"migration_report_{self.env}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Migration report saved to: {report_file}")
        logger.info(f"Statistics:")
        logger.info(f"  Users migrated: {self.stats['users_migrated']}")
        logger.info(f"  Analyses migrated: {self.stats['analyses_migrated']}")
        logger.info(f"  Files migrated: {self.stats['files_migrated']}")
        logger.info(f"  Errors: {len(self.stats['errors'])}")

        if self.stats['errors']:
            logger.warning(f"Errors encountered during migration:")
            for error in self.stats['errors'][:10]:  # Show first 10 errors
                logger.warning(f"  - {error}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Migrate ChatMRPT from Flask to AWS')
    parser.add_argument('--env', choices=['dev', 'staging', 'prod'], default='prod',
                       help='Target environment')
    parser.add_argument('--dry-run', action='store_true',
                       help='Perform dry run without actual migration')
    parser.add_argument('--users-only', action='store_true',
                       help='Migrate only users')
    parser.add_argument('--analyses-only', action='store_true',
                       help='Migrate only analyses')
    parser.add_argument('--files-only', action='store_true',
                       help='Migrate only files')

    args = parser.parse_args()

    # Create migration instance
    migration = AWSMigration(env=args.env, dry_run=args.dry_run)

    # Run migration based on flags
    if args.users_only:
        migration.migrate_users()
    elif args.analyses_only:
        migration.migrate_analyses()
    elif args.files_only:
        migration.migrate_files()
    else:
        migration.migrate_all()

    # Generate report
    migration.generate_report()


if __name__ == '__main__':
    main()