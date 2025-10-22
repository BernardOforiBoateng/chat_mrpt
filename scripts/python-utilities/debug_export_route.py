"""
Debug version of export route with enhanced logging
"""

import os
import logging
from flask import Blueprint, send_file, abort, session as flask_session, current_app
from pathlib import Path

logger = logging.getLogger(__name__)

export_bp = Blueprint('export', __name__, url_prefix='/export')


@export_bp.route('/download/<session_id>/<filename>')
def download_export(session_id, filename):
    """
    Download exported analysis files with enhanced debugging.
    """
    try:
        # Enhanced logging
        current_session_id = flask_session.get('session_id')
        logger.info(f"Export download request:")
        logger.info(f"  - Requested session: {session_id}")
        logger.info(f"  - Current session: {current_session_id}")
        logger.info(f"  - Filename: {filename}")
        logger.info(f"  - Session keys: {list(flask_session.keys())}")
        
        # Temporarily bypass session check for debugging
        # In production, uncomment the session validation
        """
        if not current_session_id or current_session_id != session_id:
            logger.warning(f"Session mismatch - current: {current_session_id}, requested: {session_id}")
            abort(403, "Session mismatch - please try refreshing the page")
        """
        
        # Construct safe path (prevent directory traversal)
        safe_filename = os.path.basename(filename)
        export_base_dir = Path('instance/exports') / session_id
        file_path = export_base_dir / safe_filename
        
        logger.info(f"Looking for file at: {file_path}")
        logger.info(f"File exists: {file_path.exists()}")
        
        # Ensure file exists and is within allowed directory
        if not file_path.exists():
            logger.error(f"Export file not found: {file_path}")
            abort(404, f"Export file not found: {safe_filename}")
        
        # Ensure path is within exports directory
        try:
            resolved_file = file_path.resolve()
            resolved_base = export_base_dir.resolve()
            if not str(resolved_file).startswith(str(resolved_base)):
                logger.error(f"Path traversal attempt: {file_path}")
                abort(403, "Invalid file path")
        except Exception as e:
            logger.error(f"Path resolution error: {e}")
            abort(500, "Error resolving file path")
        
        # Determine download name and mimetype
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
        
        logger.info(f"Serving export file: {file_path} as {mimetype}")
        
        # Try to send the file
        try:
            return send_file(
                str(file_path),  # Convert Path to string
                mimetype=mimetype,
                as_attachment=True,
                download_name=download_name
            )
        except Exception as e:
            logger.error(f"Error in send_file: {e}", exc_info=True)
            abort(500, f"Error sending file: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error serving export file: {e}", exc_info=True)
        abort(500, f"Error downloading export file: {str(e)}")