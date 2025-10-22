#!/usr/bin/env python3
"""
Script to add debug logging to visualization tools
This will help us see what's actually happening when tools execute
"""

import os

def add_debug_logging():
    """Add debug logging to key files"""
    
    # 1. Add debug logging to get_unified_dataset.py
    unified_dataset_file = '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/app/services/tools/get_unified_dataset.py'
    
    new_content = '''import os
import pandas as pd
from log import logger

def _get_unified_dataset(session_id: str) -> pd.DataFrame:
    """Get unified dataset with debug logging."""
    try:
        logger.info(f"🔍 DEBUG: _get_unified_dataset called for session {session_id}")
        
        # Check what files exist in session directory
        session_dir = f'instance/uploads/{session_id}'
        if os.path.exists(session_dir):
            files = os.listdir(session_dir)
            logger.info(f"🔍 DEBUG: Files in session directory: {files[:10]}")
        else:
            logger.error(f"🔍 DEBUG: Session directory does not exist: {session_dir}")
        
        # Check for unified dataset
        unified_path = f'instance/uploads/{session_id}/unified_dataset.csv'
        logger.info(f"🔍 DEBUG: Looking for unified dataset at: {unified_path}")
        
        if not os.path.exists(unified_path):
            # Check for raw_data.csv as fallback
            raw_path = f'instance/uploads/{session_id}/raw_data.csv'
            logger.warning(f"🔍 DEBUG: Unified dataset not found, checking for raw_data at: {raw_path}")
            
            if os.path.exists(raw_path):
                logger.info(f"🔍 DEBUG: Found raw_data.csv, using as fallback")
                raw_df = pd.read_csv(raw_path)
                logger.info(f"🔍 DEBUG: Raw data loaded: {len(raw_df)} rows, {len(raw_df.columns)} columns")
                
                # Check for shapefile to create GeoDataFrame if needed
                shapefile_path = f'instance/uploads/{session_id}/raw_shapefile.zip'
                if os.path.exists(shapefile_path):
                    logger.info(f"🔍 DEBUG: Found shapefile, attempting to create GeoDataFrame")
                    try:
                        import geopandas as gpd
                        import zipfile
                        
                        # Extract shapefile
                        shapefile_dir = f'instance/uploads/{session_id}/shapefile'
                        os.makedirs(shapefile_dir, exist_ok=True)
                        
                        with zipfile.ZipFile(shapefile_path, 'r') as zip_ref:
                            zip_ref.extractall(shapefile_dir)
                        
                        # Find .shp file
                        shp_files = [f for f in os.listdir(shapefile_dir) if f.endswith('.shp')]
                        if shp_files:
                            shp_path = os.path.join(shapefile_dir, shp_files[0])
                            gdf = gpd.read_file(shp_path)
                            logger.info(f"🔍 DEBUG: Loaded shapefile with {len(gdf)} features")
                            
                            # Merge with CSV data
                            # Try different join columns
                            for join_col in ['WardName', 'WardCode', 'ward_name', 'ward_code']:
                                if join_col in raw_df.columns and join_col in gdf.columns:
                                    merged = gdf.merge(raw_df, on=join_col, how='left')
                                    logger.info(f"🔍 DEBUG: Merged data on {join_col}: {len(merged)} rows")
                                    return merged
                            
                            logger.warning(f"🔍 DEBUG: Could not find common join column")
                            return raw_df
                    except Exception as e:
                        logger.error(f"🔍 DEBUG: Error creating GeoDataFrame: {e}")
                        return raw_df
                
                return raw_df
            
            raise FileNotFoundError(f"❌ UNIFIED DATASET NOT FOUND: {unified_path} (and no raw_data.csv fallback)")
        
        unified_df = pd.read_csv(unified_path)
        
        if unified_df.empty:
            raise ValueError(f"❌ UNIFIED DATASET IS EMPTY: {unified_path}")
        
        logger.info(f"✅ Unified dataset loaded: {len(unified_df)} rows, {len(unified_df.columns)} columns")
        return unified_df
        
    except Exception as e:
        logger.error(f"❌ Unified dataset loading failed: {e}")
        raise
'''
    
    with open(unified_dataset_file, 'w') as f:
        f.write(new_content)
    print(f"✅ Updated {unified_dataset_file} with debug logging and fallback")
    
    # 2. Add debug logging to variable_distribution.py at key points
    var_dist_file = '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/app/tools/variable_distribution.py'
    
    # Read current content and add debug logs
    with open(var_dist_file, 'r') as f:
        content = f.read()
    
    # Add debug logging at the execute method
    if 'def execute(self, session_id: str)' in content:
        # Add debug at start of execute
        content = content.replace(
            'def execute(self, session_id: str) -> ToolExecutionResult:',
            '''def execute(self, session_id: str) -> ToolExecutionResult:
        """Execute variable distribution visualization with debug logging"""
        logger.info(f"🔍 DEBUG: VariableDistribution.execute called for variable '{self.variable_name}' in session {session_id}")'''
        )
        
        # Add debug in _create_spatial_distribution_map
        content = content.replace(
            'def _create_spatial_distribution_map(self, csv_data: pd.DataFrame, shapefile: gpd.GeoDataFrame, variable: str, session_id: str)',
            '''def _create_spatial_distribution_map(self, csv_data: pd.DataFrame, shapefile: gpd.GeoDataFrame, variable: str, session_id: str)'''
        )
        
        # Find the line with "Could not merge CSV and shapefile data" and add more debug
        content = content.replace(
            'logger.error("Could not merge CSV and shapefile data")',
            '''logger.error(f"🔍 DEBUG: Could not merge CSV and shapefile data")
                logger.error(f"🔍 DEBUG: CSV columns: {list(csv_data.columns)}")
                logger.error(f"🔍 DEBUG: Shapefile columns: {list(shapefile.columns)}")
                logger.error(f"🔍 DEBUG: Attempted join columns: {join_columns}")'''
        )
    
    with open(var_dist_file, 'w') as f:
        f.write(content)
    print(f"✅ Updated {var_dist_file} with debug logging")
    
    # 3. Add debug to visualization_maps_tools.py
    viz_maps_file = '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/app/tools/visualization_maps_tools.py'
    
    with open(viz_maps_file, 'r') as f:
        content = f.read()
    
    # Add debug at execute method
    content = content.replace(
        'def execute(self, session_id: str)',
        '''def execute(self, session_id: str)'''
    )
    
    # Add debug logging after getting unified dataset
    if '_get_unified_dataset' in content:
        content = content.replace(
            'gdf = _get_unified_dataset(session_id)',
            '''logger.info(f"🔍 DEBUG: CreateVulnerabilityMap attempting to get unified dataset for {session_id}")
            gdf = _get_unified_dataset(session_id)
            logger.info(f"🔍 DEBUG: Got dataset with {len(gdf)} rows, type: {type(gdf)}")'''
        )
    
    with open(viz_maps_file, 'w') as f:
        f.write(content)
    print(f"✅ Updated {viz_maps_file} with debug logging")

if __name__ == "__main__":
    add_debug_logging()
    print("\n✅ Debug logging added to all visualization files")
    print("\nNow deploy these changes to see what's happening:")
    print("1. Deploy the updated files to AWS")
    print("2. Run the visualization commands again")
    print("3. Check the logs to see the debug output")