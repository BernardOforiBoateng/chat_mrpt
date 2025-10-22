#!/usr/bin/env python3
"""
Cleanup script to remove problematic Flask files and prepare for AWS migration.
This script identifies and removes files with singleton patterns and data bleed issues.
"""

import os
import sys
import shutil
import json
from pathlib import Path
from datetime import datetime
import argparse
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FlaskCleanup:
    """Handle cleanup of problematic Flask application files."""

    def __init__(self, backup: bool = True, dry_run: bool = False):
        """
        Initialize cleanup.

        Args:
            backup: If True, create backups before deletion
            dry_run: If True, only show what would be deleted
        """
        self.backup = backup
        self.dry_run = dry_run
        self.backup_dir = Path(f"backups/flask_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

        # Files to be completely removed (critical data bleed issues)
        self.files_to_delete = [
            'app/core/unified_data_state.py',  # Global singleton causing data bleed
            'app/core/analysis_state_handler.py',  # Another problematic singleton
            'app/core/request_interpreter.py',  # Shared conversation history
            'app/core/redis_state_manager.py',  # Flawed Redis implementation
            'app/core/session_state.py',  # Session management issues
            'app/core/llm_orchestrator.py',  # Contains singletons
            'app/core/arena_manager.py',  # Arena with shared state
            'app/core/enhanced_arena_manager.py',  # Enhanced version with same issues
        ]

        # Files to be modified (remove singleton patterns)
        self.files_to_modify = [
            'app/core/llm_manager.py',  # Remove singleton, make request-scoped
            'app/core/tool_registry.py',  # Remove global registry
            'app/services/container.py',  # Remove service container singleton
        ]

        # Directories to clean up
        self.dirs_to_clean = [
            'instance/uploads',  # User data (migrate first!)
            'instance/*.db',  # Databases (migrate first!)
            '__pycache__',  # Python cache
            '*.pyc',  # Compiled Python files
        ]

        # Files to preserve (will be migrated)
        self.files_to_preserve = [
            'app/analysis/pipeline_stages',  # Core analysis logic
            'app/tools',  # Analysis tools
            'app/data/processing.py',  # Data processing logic
            'kano_settlement_data',  # Settlement data
        ]

        # Statistics
        self.stats = {
            'files_deleted': 0,
            'files_modified': 0,
            'files_backed_up': 0,
            'errors': []
        }

    def run_cleanup(self):
        """Execute the cleanup process."""
        logger.info("Starting Flask application cleanup")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info(f"Backup enabled: {self.backup}")

        try:
            # Create backup directory if needed
            if self.backup and not self.dry_run:
                self.backup_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Backup directory: {self.backup_dir}")

            # 1. Check for data that needs migration
            self.check_migration_status()

            # 2. Backup critical files
            if self.backup:
                self.backup_files()

            # 3. Delete problematic files
            self.delete_problematic_files()

            # 4. Modify files with singleton patterns
            self.modify_singleton_files()

            # 5. Clean temporary files
            self.clean_temp_files()

            # 6. Generate cleanup report
            self.generate_report()

            logger.info("Cleanup completed successfully!")

        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            self.stats['errors'].append(str(e))
            self.generate_report()
            raise

    def check_migration_status(self):
        """Check if data has been migrated before cleanup."""
        logger.info("Checking migration status...")

        # Check for user data
        uploads_dir = Path('instance/uploads')
        if uploads_dir.exists():
            file_count = sum(1 for _ in uploads_dir.rglob('*') if _.is_file())
            if file_count > 0:
                logger.warning(f"Found {file_count} files in uploads directory")
                logger.warning("⚠️  Make sure data has been migrated before proceeding!")

                if not self.dry_run:
                    response = input("Has data been migrated to AWS? (yes/no): ")
                    if response.lower() != 'yes':
                        logger.error("Please run migration script first: python scripts/migrate_to_aws.py")
                        sys.exit(1)

        # Check for databases
        db_files = list(Path('instance').glob('*.db'))
        if db_files:
            logger.warning(f"Found {len(db_files)} database files")
            logger.warning("⚠️  Make sure databases have been migrated!")

    def backup_files(self):
        """Create backups of files before deletion."""
        logger.info("Creating backups...")

        for file_path in self.files_to_delete + self.files_to_modify:
            source = Path(file_path)
            if source.exists():
                try:
                    if not self.dry_run:
                        dest = self.backup_dir / file_path
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source, dest)

                    self.stats['files_backed_up'] += 1
                    logger.debug(f"Backed up: {file_path}")

                except Exception as e:
                    logger.error(f"Error backing up {file_path}: {str(e)}")
                    self.stats['errors'].append(f"Backup {file_path}: {str(e)}")

    def delete_problematic_files(self):
        """Delete files with critical issues."""
        logger.info("Deleting problematic files...")

        for file_path in self.files_to_delete:
            source = Path(file_path)
            if source.exists():
                try:
                    if not self.dry_run:
                        source.unlink()

                    self.stats['files_deleted'] += 1
                    logger.info(f"Deleted: {file_path}")

                except Exception as e:
                    logger.error(f"Error deleting {file_path}: {str(e)}")
                    self.stats['errors'].append(f"Delete {file_path}: {str(e)}")
            else:
                logger.debug(f"File not found: {file_path}")

    def modify_singleton_files(self):
        """Modify files to remove singleton patterns."""
        logger.info("Modifying files with singleton patterns...")

        for file_path in self.files_to_modify:
            source = Path(file_path)
            if source.exists():
                try:
                    if not self.dry_run:
                        # Read file content
                        with open(source, 'r') as f:
                            content = f.read()

                        # Remove singleton patterns
                        modified_content = self.remove_singleton_pattern(content, file_path)

                        # Write modified content
                        with open(source, 'w') as f:
                            f.write(modified_content)

                    self.stats['files_modified'] += 1
                    logger.info(f"Modified: {file_path}")

                except Exception as e:
                    logger.error(f"Error modifying {file_path}: {str(e)}")
                    self.stats['errors'].append(f"Modify {file_path}: {str(e)}")

    def remove_singleton_pattern(self, content: str, file_path: str) -> str:
        """Remove singleton pattern from file content."""
        logger.debug(f"Removing singleton pattern from {file_path}")

        # Add deprecation warning at top of file
        warning = '''"""
⚠️ DEPRECATED: This file contains patterns that cause data bleed in multi-worker environments.
   Migration to AWS serverless architecture in progress.
   DO NOT USE IN PRODUCTION.
"""

'''

        # Replace global instance patterns
        replacements = [
            ('_instance = None', '# _instance = None  # REMOVED: Singleton pattern'),
            ('global _instance', '# global _instance  # REMOVED: Singleton pattern'),
            ('if _instance is None:', 'if True:  # MODIFIED: Removed singleton check'),
            ('return _instance', 'return cls()  # MODIFIED: Return new instance'),
        ]

        modified_content = warning + content

        for old, new in replacements:
            if old in modified_content:
                modified_content = modified_content.replace(old, new)
                logger.debug(f"Replaced pattern: {old}")

        return modified_content

    def clean_temp_files(self):
        """Clean temporary and cache files."""
        logger.info("Cleaning temporary files...")

        # Clean Python cache
        for cache_dir in Path('.').rglob('__pycache__'):
            try:
                if not self.dry_run:
                    shutil.rmtree(cache_dir)
                logger.debug(f"Removed cache: {cache_dir}")
            except Exception as e:
                logger.error(f"Error removing {cache_dir}: {str(e)}")

        # Clean .pyc files
        for pyc_file in Path('.').rglob('*.pyc'):
            try:
                if not self.dry_run:
                    pyc_file.unlink()
                logger.debug(f"Removed: {pyc_file}")
            except Exception as e:
                logger.error(f"Error removing {pyc_file}: {str(e)}")

    def generate_report(self):
        """Generate cleanup report."""
        report = {
            'cleanup_date': datetime.now().isoformat(),
            'dry_run': self.dry_run,
            'backup_enabled': self.backup,
            'backup_location': str(self.backup_dir) if self.backup else None,
            'statistics': self.stats,
            'files_deleted': self.files_to_delete,
            'files_modified': self.files_to_modify,
            'preserved_files': self.files_to_preserve
        }

        report_file = f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Cleanup report saved to: {report_file}")
        logger.info(f"Statistics:")
        logger.info(f"  Files deleted: {self.stats['files_deleted']}")
        logger.info(f"  Files modified: {self.stats['files_modified']}")
        logger.info(f"  Files backed up: {self.stats['files_backed_up']}")
        logger.info(f"  Errors: {len(self.stats['errors'])}")

        if self.stats['errors']:
            logger.warning(f"Errors encountered during cleanup:")
            for error in self.stats['errors']:
                logger.warning(f"  - {error}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Clean up problematic Flask application files')
    parser.add_argument('--no-backup', action='store_true',
                       help='Skip backup creation (not recommended)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--force', action='store_true',
                       help='Force cleanup without migration check')

    args = parser.parse_args()

    # Safety check
    if not args.dry_run and not args.force:
        logger.warning("⚠️  WARNING: This will permanently modify/delete files!")
        logger.warning("Make sure you have:")
        logger.warning("  1. Run the migration script (scripts/migrate_to_aws.py)")
        logger.warning("  2. Verified the migration was successful")
        logger.warning("  3. Have a complete backup of the application")

        response = input("\nProceed with cleanup? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Cleanup cancelled")
            sys.exit(0)

    # Create cleanup instance
    cleanup = FlaskCleanup(backup=not args.no_backup, dry_run=args.dry_run)

    # Run cleanup
    cleanup.run_cleanup()


if __name__ == '__main__':
    main()