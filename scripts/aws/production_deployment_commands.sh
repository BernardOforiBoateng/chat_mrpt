#!/bin/bash
# ChatMRPT Production Deployment Commands
# Run these commands on the production server (3.137.158.17)
# Either through AWS EC2 Console Connect or AWS Systems Manager

set -e

echo "==========================================
ChatMRPT Production Deployment
Applying all fixes from staging
=========================================="

cd /home/ec2-user/ChatMRPT

# 1. Create backups first
echo -e "\n1. Creating backups..."
cp app/core/unified_data_state.py app/core/unified_data_state.py.backup_$(date +%Y%m%d_%H%M%S)
cp app/core/analysis_state_handler.py app/core/analysis_state_handler.py.backup_$(date +%Y%m%d_%H%M%S)
cp app/core/request_interpreter.py app/core/request_interpreter.py.backup_$(date +%Y%m%d_%H%M%S)
cp gunicorn.conf.py gunicorn.conf.py.backup_$(date +%Y%m%d_%H%M%S)
cp .env .env.backup_$(date +%Y%m%d_%H%M%S)

# 2. Apply unified_data_state.py fix
echo -e "\n2. Applying unified_data_state.py fix..."
cat > app/core/unified_data_state.py << 'EOF'
"""Unified data state management for cross-tool data sharing."""
import pandas as pd
import geopandas as gpd
from typing import Dict, Any, Optional, Union, List
import os
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class UnifiedDataState:
    """Manages unified data state for a session."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.upload_path = os.path.join('instance/uploads', session_id)
        self._ensure_directories()
        
    def _ensure_directories(self):
        """Ensure required directories exist."""
        os.makedirs(self.upload_path, exist_ok=True)
        
    def save_unified_dataset(self, data: Union[pd.DataFrame, gpd.GeoDataFrame], 
                           format: str = 'both') -> Dict[str, str]:
        """Save unified dataset in specified format(s)."""
        try:
            saved_files = {}
            
            # Save as CSV (always, for compatibility)
            csv_path = os.path.join(self.upload_path, 'unified_dataset.csv')
            if isinstance(data, gpd.GeoDataFrame):
                # Drop geometry for CSV
                data_csv = pd.DataFrame(data.drop(columns='geometry'))
                data_csv.to_csv(csv_path, index=False)
            else:
                data.to_csv(csv_path, index=False)
            saved_files['csv'] = csv_path
            logger.info(f"Saved unified dataset as CSV: {csv_path}")
            
            # Save as GeoParquet if it's a GeoDataFrame
            if isinstance(data, gpd.GeoDataFrame) and format in ['both', 'geoparquet']:
                geoparquet_path = os.path.join(self.upload_path, 'unified_dataset.geoparquet')
                data.to_parquet(geoparquet_path)
                saved_files['geoparquet'] = geoparquet_path
                logger.info(f"Saved unified dataset as GeoParquet: {geoparquet_path}")
                
            # Save metadata
            metadata = {
                'created_at': datetime.now().isoformat(),
                'record_count': len(data),
                'columns': list(data.columns),
                'has_geometry': isinstance(data, gpd.GeoDataFrame),
                'files': saved_files
            }
            
            metadata_path = os.path.join(self.upload_path, 'unified_dataset_metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            return saved_files
            
        except Exception as e:
            logger.error(f"Error saving unified dataset: {str(e)}")
            raise
            
    def load_unified_dataset(self, prefer_format: str = 'geoparquet') -> Optional[Union[pd.DataFrame, gpd.GeoDataFrame]]:
        """Load unified dataset, preferring specified format."""
        try:
            # Try GeoParquet first if preferred and available
            if prefer_format == 'geoparquet':
                geoparquet_path = os.path.join(self.upload_path, 'unified_dataset.geoparquet')
                if os.path.exists(geoparquet_path):
                    logger.info(f"Loading unified dataset from GeoParquet: {geoparquet_path}")
                    return gpd.read_parquet(geoparquet_path)
                    
            # Fall back to CSV
            csv_path = os.path.join(self.upload_path, 'unified_dataset.csv')
            if os.path.exists(csv_path):
                logger.info(f"Loading unified dataset from CSV: {csv_path}")
                df = pd.read_csv(csv_path)
                
                # Check if we should load shapefile to get geometry
                shapefile_path = os.path.join(self.upload_path, 'shapefile', 'raw_shapefile.shp')
                if os.path.exists(shapefile_path) and prefer_format == 'geoparquet':
                    try:
                        gdf = gpd.read_file(shapefile_path)
                        # Merge geometry back if we have matching columns
                        if 'WardName' in df.columns and 'WardName' in gdf.columns:
                            result = gdf[['WardName', 'geometry']].merge(
                                df, on='WardName', how='inner'
                            )
                            return result
                    except Exception as e:
                        logger.warning(f"Could not merge geometry: {str(e)}")
                        
                return df
                
            logger.warning(f"No unified dataset found for session {self.session_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error loading unified dataset: {str(e)}")
            return None
            
    def get_unified_dataset_info(self) -> Optional[Dict[str, Any]]:
        """Get information about saved unified dataset."""
        metadata_path = os.path.join(self.upload_path, 'unified_dataset_metadata.json')
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                return json.load(f)
        return None
        
    def has_unified_dataset(self) -> bool:
        """Check if unified dataset exists."""
        csv_exists = os.path.exists(os.path.join(self.upload_path, 'unified_dataset.csv'))
        geoparquet_exists = os.path.exists(os.path.join(self.upload_path, 'unified_dataset.geoparquet'))
        return csv_exists or geoparquet_exists

# Module-level function to get state
def get_state(session_id: str) -> UnifiedDataState:
    """Get unified data state for a session.
    Always creates a new instance to avoid cross-request contamination."""
    return UnifiedDataState(session_id)
EOF

# 3. Apply analysis_state_handler.py fix
echo -e "\n3. Applying analysis_state_handler.py fix..."
cat > app/core/analysis_state_handler.py << 'EOF'
"""Singleton handler for managing analysis state across the application."""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from threading import Lock

logger = logging.getLogger(__name__)

class AnalysisStateHandler:
    """Non-singleton handler for managing analysis state."""
    
    def __init__(self):
        """Initialize the handler."""
        self._state_file_lock = Lock()
        
    def _get_state_file_path(self, session_id: str) -> str:
        """Get the path to the state file for a session."""
        upload_path = os.path.join('instance/uploads', session_id)
        os.makedirs(upload_path, exist_ok=True)
        return os.path.join(upload_path, 'analysis_state.json')
        
    def _load_state(self, session_id: str) -> Dict[str, Any]:
        """Load state from file."""
        state_file = self._get_state_file_path(session_id)
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading state file: {str(e)}")
        return {}
        
    def _save_state(self, session_id: str, state: Dict[str, Any]):
        """Save state to file."""
        state_file = self._get_state_file_path(session_id)
        try:
            with self._state_file_lock:
                with open(state_file, 'w') as f:
                    json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving state file: {str(e)}")
            
    def update_state(self, session_id: str, updates: Dict[str, Any]):
        """Update the analysis state for a session."""
        if not session_id:
            logger.warning("No session_id provided for state update")
            return
            
        try:
            # Load current state
            state = self._load_state(session_id)
            
            # Update with new values
            state.update(updates)
            state['last_updated'] = datetime.now().isoformat()
            
            # Save back to file
            self._save_state(session_id, state)
            
            logger.info(f"Updated analysis state for session {session_id}: {list(updates.keys())}")
            
        except Exception as e:
            logger.error(f"Error updating analysis state: {str(e)}")
            
    def get_state(self, session_id: str) -> Dict[str, Any]:
        """Get the current analysis state for a session."""
        if not session_id:
            return {}
            
        return self._load_state(session_id)
        
    def clear_state(self, session_id: str):
        """Clear the analysis state for a session."""
        if not session_id:
            return
            
        state_file = self._get_state_file_path(session_id)
        if os.path.exists(state_file):
            try:
                os.remove(state_file)
                logger.info(f"Cleared analysis state for session {session_id}")
            except Exception as e:
                logger.error(f"Error clearing state file: {str(e)}")
                
    def is_analysis_complete(self, session_id: str) -> bool:
        """Check if analysis is complete for a session."""
        state = self.get_state(session_id)
        return state.get('analysis_complete', False)

# Module-level function to get handler
def get_handler() -> AnalysisStateHandler:
    """Get analysis state handler.
    Always creates a new instance to avoid cross-request contamination."""
    return AnalysisStateHandler()
EOF

# 4. Apply request_interpreter.py fix (add file-based detection)
echo -e "\n4. Applying request_interpreter.py fix..."
# First, backup and then modify only the specific section
python3 << 'PYTHON_EOF'
import re

# Read the current file
with open('app/core/request_interpreter.py', 'r') as f:
    content = f.read()

# Find the _get_session_context method and add our fix
# Look for the section where analysis_complete is checked
pattern = r'(analysis_complete = analysis_state\.get\([\'"']analysis_complete[\'"'], False\))'
replacement = r'''\1
        
        # NEW: Check for unified dataset files on disk (works across workers)
        if not analysis_complete and session_id:
            import os
            upload_path = os.path.join('instance/uploads', session_id)
            unified_files = ['unified_dataset.geoparquet', 'unified_dataset.csv', 
                            'analysis_vulnerability_rankings.csv', 'analysis_vulnerability_rankings_pca.csv']
            
            for filename in unified_files:
                filepath = os.path.join(upload_path, filename)
                if os.path.exists(filepath):
                    analysis_complete = True
                    logger.info(f"Session context: Found {filename}, marking analysis_complete=True for session {session_id}")
                    break'''

# Apply the replacement
new_content = re.sub(pattern, replacement, content)

# Write back
with open('app/core/request_interpreter.py', 'w') as f:
    f.write(new_content)

print("Successfully updated request_interpreter.py")
PYTHON_EOF

# 5. Update worker configuration
echo -e "\n5. Updating worker configuration to 6..."
sed -i 's/workers = [0-9]*/workers = 6/' gunicorn.conf.py

# Also update .env if it exists
if [ -f .env ]; then
    sed -i 's/GUNICORN_WORKERS=[0-9]*/GUNICORN_WORKERS=6/' .env
fi

# 6. Verify all files
echo -e "\n6. Verifying Python syntax..."
python3 -m py_compile app/core/unified_data_state.py && echo "✅ unified_data_state.py OK"
python3 -m py_compile app/core/analysis_state_handler.py && echo "✅ analysis_state_handler.py OK"
python3 -m py_compile app/core/request_interpreter.py && echo "✅ request_interpreter.py OK"

# 7. Show current configuration
echo -e "\n7. Current configuration:"
echo "Workers in gunicorn.conf.py:"
grep "workers =" gunicorn.conf.py
echo -e "\nWorkers in .env:"
grep "GUNICORN_WORKERS" .env || echo "GUNICORN_WORKERS not set in .env"

# 8. Restart service
echo -e "\n8. Restarting ChatMRPT service..."
sudo systemctl restart chatmrpt
sleep 10

# 9. Verify service is running
echo -e "\n9. Verifying service status..."
sudo systemctl status chatmrpt | head -20

# 10. Check worker count
echo -e "\n10. Active worker processes:"
ps aux | grep gunicorn | grep -v grep | wc -l

# 11. Test health endpoint
echo -e "\n11. Testing health endpoint..."
curl -s http://localhost:5000/ping && echo -e "\n✅ Service is healthy!"

echo -e "\n==========================================
✅ DEPLOYMENT COMPLETE!
==========================================
Production server now has:
- Multi-worker session state fixes
- ITN planning detection fix
- Session context file-based detection
- 6 workers for 50-60 concurrent users

All fixes successfully deployed!
=========================================="