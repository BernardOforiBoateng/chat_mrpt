"""
Export Tools for ChatMRPT - Modular Export System

This module provides export functionality for analysis results without
modifying any existing tools or pipelines. Completely standalone.
"""

import os
import json
import logging
import zipfile
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import pandas as pd
import geopandas as gpd
from pydantic import Field

from .base import BaseTool, ToolCategory, ToolExecutionResult, get_session_unified_dataset
from ..data.unified_dataset_builder import load_unified_dataset

logger = logging.getLogger(__name__)


class ExportITNResults(BaseTool):
    """
    Export ITN distribution results as a comprehensive take-home package.
    
    This tool creates a professional export package including:
    - Interactive dashboard (HTML)
    - Detailed results (CSV)
    - Maps and visualizations
    
    Completely modular - doesn't affect existing functionality.
    """
    
    include_dashboard: bool = Field(
        True,
        description="Include interactive HTML dashboard"
    )
    
    include_csv: bool = Field(
        True,
        description="Include detailed CSV with all rankings and allocations"
    )
    
    include_maps: bool = Field(
        True,
        description="Include standalone map files"
    )
    
    @classmethod
    def get_tool_name(cls) -> str:
        return "export_itn_results"
    
    @classmethod
    def get_category(cls) -> ToolCategory:
        return ToolCategory.REPORT_GENERATION
    
    @classmethod
    def get_description(cls) -> str:
        return "Export comprehensive ITN distribution results package for stakeholder presentation"
    
    @classmethod
    def get_examples(cls) -> List[str]:
        return [
            "Export ITN distribution results",
            "Create take-home package for ITN analysis",
            "Generate ITN distribution report",
            "Export analysis results for presentation"
        ]
    
    def execute(self, session_id: str) -> ToolExecutionResult:
        """Execute ITN results export"""
        try:
            logger.info(f"Starting ITN results export for session {session_id}")
            
            # Create export directory
            export_dir = self._create_export_directory(session_id)
            
            # Gather all necessary data
            export_data = self._gather_export_data(session_id)
            if not export_data:
                return self._create_error_result(
                    "No ITN distribution results found. Please run ITN distribution planning first."
                )
            
            exported_files = []
            
            # 1. Export CSV if requested
            if self.include_csv:
                csv_path = self._export_csv(export_data, export_dir)
                if csv_path:
                    exported_files.append(csv_path)
                    logger.info(f"Exported CSV: {csv_path}")
            
            # 2. Generate dashboard if requested
            if self.include_dashboard:
                dashboard_path = self._generate_dashboard(export_data, export_dir, session_id)
                if dashboard_path:
                    exported_files.append(dashboard_path)
                    logger.info(f"Generated dashboard: {dashboard_path}")
            
            # 3. Copy maps if requested
            if self.include_maps:
                map_files = self._copy_maps(export_data, export_dir, session_id)
                exported_files.extend(map_files)
                logger.info(f"Copied {len(map_files)} map files")
            
            # 4. Create metadata file
            metadata_path = self._create_metadata(export_data, export_dir)
            if metadata_path:
                exported_files.append(metadata_path)
            
            # 5. Create ZIP package
            zip_path = self._create_zip_package(exported_files, export_dir, session_id)
            
            # Calculate package size
            package_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
            
            # Prepare success message
            message = self._format_export_summary(export_data, len(exported_files), package_size_mb)
            
            # Create web path for download
            web_path = f"/download/{session_id}/{os.path.basename(zip_path)}"
            
            result_data = {
                'export_path': zip_path,
                'web_path': web_path,
                'files_included': len(exported_files),
                'package_size_mb': round(package_size_mb, 2),
                'export_type': 'itn_distribution',
                'timestamp': datetime.now().isoformat()
            }
            
            return self._create_success_result(
                message=message,
                data=result_data,
                web_path=web_path
            )
            
        except Exception as e:
            logger.error(f"Error exporting ITN results: {e}", exc_info=True)
            return self._create_error_result(f"Export failed: {str(e)}")
    
    def _create_export_directory(self, session_id: str) -> Path:
        """Create directory for export files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = Path(f"instance/exports/{session_id}/itn_export_{timestamp}")
        export_dir.mkdir(parents=True, exist_ok=True)
        return export_dir
    
    def _gather_export_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Gather all data needed for export"""
        try:
            # Load unified dataset with geometry
            gdf = load_unified_dataset(session_id, require_geometry=True)
            if gdf is None:
                logger.error("No unified dataset found")
                return None
            
            # Check for ITN distribution results
            itn_results_path = f"instance/uploads/{session_id}/itn_distribution_results.json"
            if not os.path.exists(itn_results_path):
                logger.error("No ITN distribution results found")
                return None
            
            with open(itn_results_path, 'r') as f:
                itn_results = json.load(f)
            
            # Gather visualization paths
            viz_dir = Path(f"instance/uploads/{session_id}")
            vulnerability_maps = list(viz_dir.glob("*vulnerability*map*.html"))
            itn_maps = list(viz_dir.glob("*itn*map*.html"))
            
            export_data = {
                'unified_dataset': gdf,
                'itn_results': itn_results,
                'vulnerability_maps': vulnerability_maps,
                'itn_maps': itn_maps,
                'session_id': session_id,
                'export_date': datetime.now(),
                'total_wards': len(gdf),
                'analysis_method': itn_results.get('method', 'composite')
            }
            
            # Add summary statistics
            if 'stats' in itn_results:
                export_data['summary_stats'] = itn_results['stats']
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error gathering export data: {e}")
            return None
    
    def _export_csv(self, export_data: Dict[str, Any], export_dir: Path) -> Optional[Path]:
        """Export detailed CSV with all rankings and ITN allocations"""
        try:
            gdf = export_data['unified_dataset']
            itn_results = export_data['itn_results']
            
            # Select relevant columns for export
            export_columns = [
                'ward_name', 'lga_name', 'state',
                'composite_score', 'composite_rank', 'composite_category',
                'population', 'urbanPercentage',
                'nets_allocated', 'nets_needed', 'coverage_percent',
                'allocation_phase'
            ]
            
            # Filter to existing columns
            available_columns = [col for col in export_columns if col in gdf.columns]
            
            # Create export dataframe
            export_df = gdf[available_columns].copy()
            
            # Add ITN allocation data if available
            if 'prioritized' in itn_results and 'reprioritized' in itn_results:
                # This would merge the ITN allocation results
                # For now, we'll use what's in the unified dataset
                pass
            
            # Sort by composite rank
            if 'composite_rank' in export_df.columns:
                export_df = export_df.sort_values('composite_rank')
            
            # Save CSV
            csv_path = export_dir / 'itn_distribution_results.csv'
            export_df.to_csv(csv_path, index=False)
            
            return csv_path
            
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            return None
    
    def _generate_dashboard(self, export_data: Dict[str, Any], export_dir: Path, session_id: str) -> Optional[Path]:
        """Generate interactive HTML dashboard"""
        try:
            # For now, create a placeholder dashboard
            # In the next step, we'll create the actual template
            dashboard_html = self._create_dashboard_html(export_data)
            
            dashboard_path = export_dir / 'itn_distribution_dashboard.html'
            with open(dashboard_path, 'w', encoding='utf-8') as f:
                f.write(dashboard_html)
            
            return dashboard_path
            
        except Exception as e:
            logger.error(f"Error generating dashboard: {e}")
            return None
    
    def _create_dashboard_html(self, export_data: Dict[str, Any]) -> str:
        """Create dashboard HTML content"""
        # Placeholder for now - will be replaced with actual template
        stats = export_data.get('summary_stats', {})
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ITN Distribution Analysis - {export_data.get('session_id', 'Results')}</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
                .summary {{ margin: 20px 0; }}
                .card {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>ITN Distribution Analysis Results</h1>
                <p>Generated: {export_data['export_date'].strftime('%Y-%m-%d %H:%M')}</p>
            </div>
            
            <div class="summary">
                <h2>Summary Statistics</h2>
                <div class="card">
                    <h3>Distribution Overview</h3>
                    <ul>
                        <li>Total Nets Available: {stats.get('total_nets', 'N/A'):,}</li>
                        <li>Nets Allocated: {stats.get('allocated', 'N/A'):,}</li>
                        <li>Population Coverage: {stats.get('coverage_percent', 'N/A')}%</li>
                        <li>Prioritized Wards: {stats.get('prioritized_wards', 'N/A')}</li>
                    </ul>
                </div>
            </div>
            
            <div class="note">
                <p><em>Full dashboard with interactive maps will be available in the next update.</em></p>
            </div>
        </body>
        </html>
        """
        return html
    
    def _copy_maps(self, export_data: Dict[str, Any], export_dir: Path, session_id: str) -> List[Path]:
        """Copy relevant map files to export directory"""
        copied_files = []
        
        try:
            # Copy vulnerability maps
            for map_file in export_data.get('vulnerability_maps', []):
                if map_file.exists():
                    dest = export_dir / f"vulnerability_{map_file.name}"
                    import shutil
                    shutil.copy2(map_file, dest)
                    copied_files.append(dest)
            
            # Copy ITN maps
            for map_file in export_data.get('itn_maps', []):
                if map_file.exists():
                    dest = export_dir / f"itn_{map_file.name}"
                    import shutil
                    shutil.copy2(map_file, dest)
                    copied_files.append(dest)
            
        except Exception as e:
            logger.error(f"Error copying maps: {e}")
        
        return copied_files
    
    def _create_metadata(self, export_data: Dict[str, Any], export_dir: Path) -> Optional[Path]:
        """Create metadata file with export information"""
        try:
            metadata = {
                'export_type': 'itn_distribution',
                'export_date': export_data['export_date'].isoformat(),
                'session_id': export_data['session_id'],
                'analysis_method': export_data['analysis_method'],
                'total_wards': export_data['total_wards'],
                'files_included': {
                    'dashboard': 'itn_distribution_dashboard.html',
                    'csv': 'itn_distribution_results.csv',
                    'maps': [f.name for f in export_dir.glob('*.html')]
                },
                'summary_stats': export_data.get('summary_stats', {})
            }
            
            metadata_path = export_dir / 'export_metadata.json'
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return metadata_path
            
        except Exception as e:
            logger.error(f"Error creating metadata: {e}")
            return None
    
    def _create_zip_package(self, files: List[Path], export_dir: Path, session_id: str) -> Path:
        """Create ZIP file with all export components"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_name = f"ITN_Distribution_Export_{timestamp}.zip"
        zip_path = export_dir.parent / zip_name
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in files:
                if file_path.exists():
                    arcname = file_path.relative_to(export_dir)
                    zipf.write(file_path, arcname)
        
        return zip_path
    
    def _format_export_summary(self, export_data: Dict[str, Any], file_count: int, size_mb: float) -> str:
        """Format export summary message"""
        stats = export_data.get('summary_stats', {})
        
        message = f"""**ITN Distribution Export Package Created Successfully!**

**Package Contents:**
- Interactive Dashboard (HTML)
- Detailed Results (CSV) with {export_data['total_wards']} wards
- Visualization Maps

**Key Statistics:**
- Total Nets: {stats.get('total_nets', 'N/A'):,}
- Population Coverage: {stats.get('coverage_percent', 'N/A')}%
- Prioritized Wards: {stats.get('prioritized_wards', 'N/A')}

**Package Details:**
- Files Included: {file_count}
- Package Size: {size_mb:.1f} MB
- Export Date: {export_data['export_date'].strftime('%Y-%m-%d %H:%M')}

Click the download button below to get your complete ITN distribution analysis package."""
        
        return message