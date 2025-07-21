"""
Shapefile Extractor Service for TPR Module.

This service extracts state-specific shapefiles from the master Nigerian shapefile
and packages them for output with proper projections and ward name matching.
"""

import os
import shutil
import tempfile
import zipfile
import pandas as pd
import geopandas as gpd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
from difflib import get_close_matches
import json

logger = logging.getLogger(__name__)

class ShapefileExtractor:
    """Extract and package state-specific shapefiles."""
    
    def __init__(self, master_shapefile_path: str = None):
        """
        Initialize the shapefile extractor.
        
        Args:
            master_shapefile_path: Path to master Nigerian shapefile
        """
        if master_shapefile_path is None:
            # Look for Nigerian shapefile in common locations
            possible_paths = [
                'www/complete_names_wards/wards.shp',  # Extracted Nigerian shapefile
                'www/Nigeria_shapefile.zip',
                'www/ward_shape.shp',
                'instance/uploads/ward_shape.shp',
                'app/sample_data/nigeria_wards.shp'
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    master_shapefile_path = path
                    break
        
        self.master_shapefile_path = master_shapefile_path
        self.master_gdf = None
        
        # Load master shapefile if available
        if self.master_shapefile_path and os.path.exists(self.master_shapefile_path):
            try:
                # Handle ZIP files
                if self.master_shapefile_path.endswith('.zip'):
                    # Read shapefile directly from ZIP
                    self.master_gdf = gpd.read_file(f'zip://{self.master_shapefile_path}')
                else:
                    self.master_gdf = gpd.read_file(self.master_shapefile_path)
                logger.info(f"Loaded master shapefile with {len(self.master_gdf)} features")
            except Exception as e:
                logger.error(f"Error loading master shapefile: {str(e)}")
    
    def extract_state_shapefile(self, 
                              state_name: str,
                              tpr_data: pd.DataFrame,
                              output_dir: str) -> Optional[str]:
        """
        Extract state-specific shapefile with TPR data joined.
        
        Args:
            state_name: Name of the state
            tpr_data: TPR analysis results DataFrame
            output_dir: Directory to save the shapefile
            
        Returns:
            Path to created shapefile ZIP or None
        """
        if self.master_gdf is None:
            logger.error("No master shapefile loaded")
            return None
        
        # Extract state data
        state_gdf = self._filter_state_data(state_name)
        
        if state_gdf is None or state_gdf.empty:
            logger.error(f"No data found for state: {state_name}")
            return None
        
        # Match and join TPR data
        joined_gdf = self._join_tpr_data(state_gdf, tpr_data)
        
        # Package as shapefile
        shapefile_path = self._package_shapefile(joined_gdf, state_name, output_dir)
        
        return shapefile_path
    
    def _filter_state_data(self, state_name: str) -> Optional[gpd.GeoDataFrame]:
        """Filter master shapefile for specific state."""
        # Identify state column
        state_column = self._identify_column('state')
        
        if not state_column:
            logger.error("Could not identify state column")
            return None
        
        # Filter for state
        state_gdf = self.master_gdf[
            self.master_gdf[state_column].str.contains(
                state_name, case=False, na=False
            )
        ].copy()
        
        if state_gdf.empty:
            # Try normalized matching
            normalized_state = self._normalize_name(state_name)
            for idx, row in self.master_gdf.iterrows():
                if self._normalize_name(str(row[state_column])) == normalized_state:
                    if state_gdf.empty:
                        state_gdf = self.master_gdf.iloc[[idx]].copy()
                    else:
                        state_gdf = pd.concat([state_gdf, self.master_gdf.iloc[[idx]]])
        
        logger.info(f"Filtered {len(state_gdf)} features for {state_name}")
        return state_gdf
    
    def _join_tpr_data(self, 
                      state_gdf: gpd.GeoDataFrame, 
                      tpr_data: pd.DataFrame) -> gpd.GeoDataFrame:
        """Join TPR data to shapefile based on ward names."""
        # Ensure WardName column is present in state_gdf
        ward_col_shp = self._identify_column('ward', state_gdf)
        if ward_col_shp and ward_col_shp != 'WardName':
            state_gdf['WardName'] = state_gdf[ward_col_shp]
        
        # Ensure ward_code column is preserved if present
        ward_code_col = self._identify_column('ward_code', state_gdf)
        if ward_code_col:
            state_gdf['ward_code'] = state_gdf[ward_code_col]
        
        # Identify ward columns
        ward_col_shp = self._identify_column('ward', state_gdf)
        ward_col_tpr = self._identify_column('ward', tpr_data)
        
        if not ward_col_shp or not ward_col_tpr:
            logger.warning("Could not identify ward columns for joining")
            return state_gdf
        
        # Create normalized ward names for matching
        state_gdf['ward_norm'] = state_gdf[ward_col_shp].apply(self._normalize_name)
        tpr_data = tpr_data.copy()
        tpr_data['ward_norm'] = tpr_data[ward_col_tpr].apply(self._normalize_name)
        
        # Try direct join first
        joined = state_gdf.merge(
            tpr_data,
            on='ward_norm',
            how='left',
            suffixes=('', '_tpr')
        )
        
        # For unmatched wards, try fuzzy matching
        unmatched_mask = joined['TPR'].isna() if 'TPR' in joined.columns else joined[ward_col_tpr + '_tpr'].isna()
        unmatched_wards = joined[unmatched_mask]['ward_norm'].unique()
        
        if len(unmatched_wards) > 0:
            logger.info(f"Attempting fuzzy matching for {len(unmatched_wards)} unmatched wards")
            
            # Create mapping for fuzzy matches
            tpr_ward_list = tpr_data['ward_norm'].unique().tolist()
            fuzzy_matches = {}
            
            for ward in unmatched_wards:
                matches = get_close_matches(ward, tpr_ward_list, n=1, cutoff=0.7)
                if matches:
                    fuzzy_matches[ward] = matches[0]
            
            # Apply fuzzy matches
            for orig_ward, matched_ward in fuzzy_matches.items():
                mask = joined['ward_norm'] == orig_ward
                tpr_row = tpr_data[tpr_data['ward_norm'] == matched_ward].iloc[0]
                
                # Copy TPR columns
                for col in tpr_data.columns:
                    if col not in ['ward_norm', ward_col_tpr]:
                        joined.loc[mask, col] = tpr_row[col]
        
        # Clean up temporary columns
        columns_to_drop = ['ward_norm']
        # Remove duplicate columns from suffix
        for col in joined.columns:
            if col.endswith('_tpr'):
                columns_to_drop.append(col)
        
        joined = joined.drop(columns=columns_to_drop, errors='ignore')
        
        # Log matching statistics
        if 'TPR' in joined.columns:
            matched_count = joined['TPR'].notna().sum()
            total_count = len(joined)
            logger.info(f"Matched TPR data for {matched_count}/{total_count} wards ({matched_count/total_count*100:.1f}%)")
        
        return joined
    
    def _package_shapefile(self, 
                         gdf: gpd.GeoDataFrame, 
                         state_name: str,
                         output_dir: str) -> Optional[str]:
        """Package GeoDataFrame as shapefile ZIP."""
        try:
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Ensure proper CRS (WGS84)
                if gdf.crs is None:
                    gdf.set_crs('EPSG:4326', inplace=True)
                elif gdf.crs != 'EPSG:4326':
                    gdf = gdf.to_crs('EPSG:4326')
                
                # Clean column names (shapefile has 10 char limit)
                gdf = self._clean_column_names(gdf)
                
                # Save shapefile components
                shapefile_base = temp_path / f"{state_name.replace(' ', '_')}_wards"
                gdf.to_file(shapefile_base.with_suffix('.shp'))
                
                # Create ZIP file
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)
                
                zip_filename = f"{state_name.replace(' State', '').replace(' ', '_')}_state.zip"
                zip_path = output_path / zip_filename
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # Add all shapefile components
                    for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
                        file_path = shapefile_base.with_suffix(ext)
                        if file_path.exists():
                            zipf.write(file_path, file_path.name)
                    
                    # Add metadata JSON
                    metadata = {
                        'state': state_name,
                        'feature_count': len(gdf),
                        'crs': 'EPSG:4326',
                        'columns': list(gdf.columns),
                        'has_tpr_data': 'TPR' in gdf.columns
                    }
                    
                    metadata_path = temp_path / 'metadata.json'
                    with open(metadata_path, 'w') as f:
                        json.dump(metadata, f, indent=2)
                    
                    zipf.write(metadata_path, 'metadata.json')
                
                logger.info(f"Created shapefile package: {zip_path}")
                return str(zip_path)
                
        except Exception as e:
            logger.error(f"Error packaging shapefile: {str(e)}")
            return None
    
    def _identify_column(self, column_type: str, df=None) -> Optional[str]:
        """Identify column by type (state, ward, lga)."""
        if df is None:
            df = self.master_gdf
        
        if df is None:
            return None
        
        if column_type == 'state':
            possible_names = [
                'State', 'STATE', 'state', 'StateName', 'state_name',
                'Admin1', 'admin1', 'ADM1_EN', 'NAME_1'
            ]
        elif column_type == 'ward':
            possible_names = [
                'WardName', 'Ward', 'WARD', 'ward', 'ward_name', 
                'WARD_NAME', 'Admin3', 'admin3', 'NAME_3', 'adm3_02'
            ]
        elif column_type == 'ward_code':
            possible_names = [
                'WardCode', 'ward_code', 'Ward_Code', 'WARD_CODE', 
                'WARDCODE', 'Admin3Pcod', 'admin3pcod', 'ADM3_PCODE', 'Ward_ID'
            ]
        elif column_type == 'lga':
            possible_names = [
                'LGA', 'lga', 'LGAName', 'lga_name', 'LGA_NAME',
                'Admin2', 'admin2', 'ADM2_EN', 'NAME_2'
            ]
        else:
            return None
        
        for col in possible_names:
            if col in df.columns:
                return col
        
        return None
    
    def _normalize_name(self, name: str) -> str:
        """Normalize names for matching."""
        if pd.isna(name):
            return ""
        
        normalized = str(name).strip().upper()
        # Remove common words
        for word in ['WARD', 'LGA', 'STATE']:
            normalized = normalized.replace(word, '')
        
        # Remove extra spaces
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def _find_shapefile_for_state(self, state_name: str) -> Optional[str]:
        """Find the shapefile path containing data for a specific state."""
        if self.master_shapefile_path and os.path.exists(self.master_shapefile_path):
            return self.master_shapefile_path
        return None
    
    def _clean_column_names(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Clean column names for shapefile compatibility."""
        # Shapefile field names are limited to 10 characters
        rename_map = {}
        
        for col in gdf.columns:
            if col == 'geometry':
                continue
                
            new_name = col[:10]
            
            # Handle duplicates
            counter = 1
            while new_name in rename_map.values():
                new_name = col[:8] + str(counter).zfill(2)
                counter += 1
            
            if col != new_name:
                rename_map[col] = new_name
        
        if rename_map:
            logger.info(f"Renaming columns for shapefile compatibility: {rename_map}")
            gdf = gdf.rename(columns=rename_map)
        
        return gdf
    
    def validate_shapefile(self, shapefile_path: str) -> Dict[str, Any]:
        """
        Validate created shapefile.
        
        Args:
            shapefile_path: Path to shapefile ZIP
            
        Returns:
            Validation report
        """
        report = {
            'valid': False,
            'exists': os.path.exists(shapefile_path),
            'size_mb': 0,
            'components': [],
            'feature_count': 0,
            'has_tpr_data': False
        }
        
        if not report['exists']:
            report['message'] = "Shapefile does not exist"
            return report
        
        # Check file size
        report['size_mb'] = os.path.getsize(shapefile_path) / (1024 * 1024)
        
        try:
            # Check ZIP contents
            with zipfile.ZipFile(shapefile_path, 'r') as zipf:
                report['components'] = zipf.namelist()
                
                # Check for required components
                required_exts = ['.shp', '.shx', '.dbf']
                has_required = all(
                    any(f.endswith(ext) for f in report['components']) 
                    for ext in required_exts
                )
                
                if has_required:
                    # Extract and check shapefile
                    with tempfile.TemporaryDirectory() as temp_dir:
                        zipf.extractall(temp_dir)
                        
                        # Find .shp file
                        shp_file = None
                        for f in report['components']:
                            if f.endswith('.shp'):
                                shp_file = os.path.join(temp_dir, f)
                                break
                        
                        if shp_file:
                            # Read and validate
                            gdf = gpd.read_file(shp_file)
                            report['feature_count'] = len(gdf)
                            report['has_tpr_data'] = 'TPR' in gdf.columns
                            report['valid'] = True
                            report['message'] = "Shapefile is valid"
                else:
                    report['message'] = "Missing required shapefile components"
                    
        except Exception as e:
            report['message'] = f"Error validating shapefile: {str(e)}"
        
        return report


def test_shapefile_extractor():
    """Test the shapefile extractor functionality."""
    import pandas as pd
    
    # Initialize extractor
    extractor = ShapefileExtractor()
    
    if extractor.master_gdf is not None:
        print(f"Master shapefile loaded with {len(extractor.master_gdf)} features")
        
        # Create sample TPR data
        sample_tpr = pd.DataFrame({
            'Ward': ['Ward1', 'Ward2', 'Ward3'],
            'LGA': ['LGA1', 'LGA1', 'LGA2'],
            'TPR': [15.2, 22.5, 18.7],
            'Method': ['standard', 'standard', 'alternative']
        })
        
        # Test extraction
        output_dir = "test_output"
        shapefile_path = extractor.extract_state_shapefile(
            "Kano", 
            sample_tpr, 
            output_dir
        )
        
        if shapefile_path:
            print(f"Created shapefile: {shapefile_path}")
            
            # Validate
            validation = extractor.validate_shapefile(shapefile_path)
            print(f"Validation result: {validation}")
            
            # Clean up
            if os.path.exists(shapefile_path):
                os.remove(shapefile_path)
            if os.path.exists(output_dir):
                os.rmdir(output_dir)
    else:
        print("No master shapefile found - cannot test extraction")


if __name__ == "__main__":
    test_shapefile_extractor()