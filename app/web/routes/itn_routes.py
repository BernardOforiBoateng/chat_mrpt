"""ITN Distribution Routes."""
from flask import Blueprint, request, jsonify, session, send_from_directory, current_app
from app.analysis.itn_pipeline import calculate_itn_distribution
from app.models.data_handler import DataHandler
import logging
import os

logger = logging.getLogger(__name__)

itn_bp = Blueprint('itn', __name__, url_prefix='/api/itn')

@itn_bp.route('/update-distribution', methods=['POST'])
def update_itn_distribution():
    """Update ITN distribution with new threshold."""
    try:
        data = request.get_json()
        session_id = session.get('session_id')
        
        if not session_id:
            return jsonify({'status': 'error', 'message': 'No active session'}), 400
            
        # Get parameters
        urban_threshold = float(data.get('urban_threshold', 30))
        total_nets = int(data.get('total_nets', 10000))
        avg_household_size = float(data.get('avg_household_size', 5.0))
        method = data.get('method', 'composite')
        
        # Load data handler
        data_handler = DataHandler()
        data_handler.load_from_session(session_id)
        
        # Recalculate distribution
        result = calculate_itn_distribution(
            data_handler,
            session_id=session_id,
            total_nets=total_nets,
            avg_household_size=avg_household_size,
            urban_threshold=urban_threshold,
            method=method
        )
        
        if result['status'] == 'success':
            return jsonify({
                'status': 'success',
                'map_path': result['map_path'],
                'stats': result['stats']
            })
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error updating ITN distribution: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# Create a separate blueprint for the embed route (no URL prefix)
itn_embed_bp = Blueprint('itn_embed', __name__)

@itn_embed_bp.route('/itn_embed/<session_id>')
def serve_itn_embed(session_id):
    """Serve ITN map HTML file for embedding."""
    try:
        # For now, skip session validation to debug the issue
        # We'll add it back once we confirm the route works
        
        # Serve the ITN map HTML file from static/visualizations
        filename = f'itn_map_{session_id}.html'
        
        # Use absolute path based on current_app root
        viz_dir = os.path.join(current_app.root_path, 'static', 'visualizations')
        
        # Check if file exists
        file_path = os.path.join(viz_dir, filename)
        if not os.path.exists(file_path):
            logger.error(f"ITN map file not found: {file_path}")
            return f"<h1>File not found: {file_path}</h1>", 404
        
        # Log successful file access
        logger.info(f"Serving ITN map from: {file_path}")
        
        return send_from_directory(viz_dir, filename)
        
    except Exception as e:
        logger.error(f"Error serving ITN embed: {str(e)}", exc_info=True)
        return f"<h1>Error: {str(e)}</h1>", 500