"""
Data Exploration Agent - MVP for Tool #19 integration.

Simple Python execution on session data.
Security hardening in Phase 2.
"""

import os
import logging
import glob
from typing import List, Dict, Any, Optional
import pandas as pd
import geopandas as gpd

from .agent import DataAnalysisAgent
from .encoding_handler import EncodingHandler

logger = logging.getLogger(__name__)


class DataExplorationAgent(DataAnalysisAgent):
    """
    MVP: Simple Python execution on user data.

    Called by RequestInterpreter's analyze_data_with_python tool.
    Phase 1: Basic functionality
    Phase 2: Add sandbox, limits, security
    """

    def __init__(self, session_id: str):
        super().__init__(session_id)
        logger.info(f"🔍 DataExplorationAgent initialized for {session_id}")

    def analyze_sync(self, query: str) -> Dict[str, Any]:
        """
        Synchronous wrapper for tool calling.

        Args:
            query: User's query/question

        Returns:
            Dict with message, visualizations, etc.
        """
        import asyncio

        # Create event loop for async analyze
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self.analyze(query))
            return result
        finally:
            loop.close()

    def _get_input_data(self) -> List[Dict[str, Any]]:
        """
        Load CSV + shapefile from session folder.

        Priority:
        1. unified_dataset.csv (post-risk)
        2. raw_data.csv (post-TPR or standard upload)
        3. uploaded_data.csv (fallback)
        """
        input_data_list = []
        session_folder = f"instance/uploads/{self.session_id}"

        # Load CSV
        csv_file = self._find_csv(session_folder)
        if csv_file and os.path.exists(csv_file):
            try:
                df = EncodingHandler.read_csv_with_encoding(csv_file)
                input_data_list.append({
                    'variable_name': 'df',
                    'data_description': f"Dataset with {len(df)} rows and {len(df.columns)} columns",
                    'data': df,
                    'columns': df.columns.tolist()
                })
                logger.info(f"✅ Loaded CSV: {os.path.basename(csv_file)} ({len(df)} rows)")
            except Exception as e:
                logger.error(f"Failed to load CSV {csv_file}: {e}")

        # Load shapefile if exists
        shapefile = self._find_shapefile(session_folder)
        if shapefile:
            try:
                gdf = gpd.read_file(shapefile)
                input_data_list.append({
                    'variable_name': 'gdf',
                    'data_description': f"Geospatial data with {len(gdf)} features",
                    'data': gdf,
                    'columns': gdf.columns.tolist(),
                    'is_spatial': True
                })
                logger.info(f"✅ Loaded shapefile: {len(gdf)} features")
            except Exception as e:
                logger.error(f"Failed to load shapefile {shapefile}: {e}")

        if not input_data_list:
            logger.warning(f"⚠️ No data loaded for session {self.session_id}")

        return input_data_list

    def _find_csv(self, session_folder: str) -> Optional[str]:
        """Find CSV file in priority order."""

        # Priority 1: unified_dataset.csv (post-risk analysis)
        unified = f"{session_folder}/unified_dataset.csv"
        if os.path.exists(unified):
            logger.info("📊 Using unified_dataset.csv (post-risk)")
            return unified

        # Priority 2: raw_data.csv (post-TPR or standard upload)
        raw_data = f"{session_folder}/raw_data.csv"
        if os.path.exists(raw_data):
            logger.info("📊 Using raw_data.csv")
            return raw_data

        # Priority 3: uploaded_data.csv (fallback)
        uploaded = f"{session_folder}/uploaded_data.csv"
        if os.path.exists(uploaded):
            logger.info("📊 Using uploaded_data.csv (fallback)")
            return uploaded

        return None

    def _find_shapefile(self, session_folder: str) -> Optional[str]:
        """Find shapefile in session folder."""

        # Try raw_shapefile.zip (created by TPR workflow)
        shapefile_zip = f"{session_folder}/raw_shapefile.zip"
        if os.path.exists(shapefile_zip):
            return shapefile_zip

        # Try shapefile directory
        shapefile_dir = f"{session_folder}/shapefile"
        if os.path.exists(shapefile_dir):
            shp_files = glob.glob(f"{shapefile_dir}/*.shp")
            if shp_files:
                return shp_files[0]

        return None
