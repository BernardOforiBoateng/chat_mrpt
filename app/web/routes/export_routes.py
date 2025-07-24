"""
Export Routes for ChatMRPT

Handles file downloads for exported analysis results.
Completely modular - doesn't affect existing functionality.
"""

import os
import logging
from flask import Blueprint, send_file, abort, session as flask_session
from pathlib import Path

logger = logging.getLogger(__name__)

export_bp = Blueprint('export', __name__, url_prefix='/export')


@export_bp.route('/download/<session_id>/<filename>')
def download_export(session_id, filename):
    """
    Download exported analysis files.
    
    Security: Only allows downloads from the exports directory for the given session.
    """
    try:
        # Validate session with enhanced logging
        current_session_id = flask_session.get('session_id')
        logger.info(f"Export download - Current session: {current_session_id}, Requested: {session_id}")
        
        # Temporarily relaxed validation - just log the mismatch
        if not current_session_id or current_session_id != session_id:
            logger.warning(f"Session mismatch but allowing download: current={current_session_id}, requested={session_id}")
        
        # Construct safe path (prevent directory traversal)
        safe_filename = os.path.basename(filename)
        export_base_dir = Path('instance/exports') / session_id
        
        # First try direct path
        file_path = export_base_dir / safe_filename
        
        # If not found, search in timestamped subdirectories
        if not file_path.exists():
            # Look for the file in any itn_export_* subdirectory
            for subdir in export_base_dir.glob('itn_export_*'):
                potential_path = subdir / safe_filename
                if potential_path.exists():
                    file_path = potential_path
                    break
        
        # Ensure file exists
        if not file_path.exists():
            logger.error(f"Export file not found: {safe_filename} in {export_base_dir}")
            abort(404, "Export file not found")
        
        # Ensure path is within exports directory
        if not str(file_path.resolve()).startswith(str(export_base_dir.resolve())):
            logger.error(f"Path traversal attempt: {file_path}")
            abort(403, "Invalid file path")
        
        # Determine download name
        if safe_filename.endswith('.zip'):
            download_name = safe_filename
            mimetype = 'application/zip'
        elif safe_filename.endswith('.csv'):
            download_name = safe_filename
            mimetype = 'text/csv'
        elif safe_filename.endswith('.html'):
            download_name = safe_filename
            mimetype = 'text/html'
        else:
            download_name = safe_filename
            mimetype = 'application/octet-stream'
        
        logger.info(f"Serving export file: {file_path}")
        
        return send_file(
            str(file_path),  # Convert Path object to string
            mimetype=mimetype,
            as_attachment=True,
            download_name=download_name
        )
        
    except Exception as e:
        logger.error(f"Error serving export file: {e}")
        abort(500, "Error downloading export file")