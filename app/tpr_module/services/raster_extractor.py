"""
Raster Extractor Service for TPR Module.

This service extracts environmental variable values from local raster files
for ward centroids based on geopolitical zone requirements.
"""

import os
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.sample import sample_gen
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
from shapely.geometry import Point

# Suppress rasterio warnings
warnings.filterwarnings('ignore', category=rasterio.errors.NotGeoreferencedWarning)

logger = logging.getLogger(__name__)

class RasterExtractor:
    """Extract values from raster files for ward centroids."""
    
    def __init__(self, raster_base_dir: str = None):
        """
        Initialize the raster extractor.
        
        Args:
            raster_base_dir: Base directory containing organized raster files
        """
        if raster_base_dir is None:
            # Default to TPR module raster database
            raster_base_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'raster_database'
            )
        
        self.raster_base_dir = Path(raster_base_dir)
        self.raster_cache = {}  # Cache opened rasters for efficiency
        
        # Load Nigerian master shapefile for better coordinate extraction
        self.shapefile_path = Path('www/complete_names_wards/wards.shp')
        self.master_gdf = None
        
        if self.shapefile_path.exists():
            try:
                self.master_gdf = gpd.read_file(self.shapefile_path)
                logger.info(f"Loaded Nigerian shapefile with {len(self.master_gdf)} wards")
            except Exception as e:
                logger.error(f"Failed to load Nigerian shapefile: {e}")
        
        # Variable to directory mapping
        self.variable_directories = {
            'evi': 'vegetation',
            'ndmi': 'vegetation',
            'ndwi': 'vegetation',
            'rainfall': 'rainfall',
            'temp': 'temperature',
            'temperature': 'temperature',
            'soil_wetness': 'soil',
            'elevation': 'elevation',
            'distance_to_water': 'water_bodies',
            'nighttime_lights': 'urban',
            'housing_quality': 'housing',
            'flood': 'flood',
            'pfpr': 'health'
        }
        
        logger.info(f"RasterExtractor initialized with base directory: {self.raster_base_dir}")
    
    def extract_values_for_wards(self, 
                                ward_data: pd.DataFrame,
                                variables: List[str],
                                year: int = None) -> pd.DataFrame:
        """
        Extract raster values for wards using Nigerian shapefile geometry.
        
        Args:
            ward_data: DataFrame with ward information (must have WardName)
            variables: List of variables to extract
            year: Year for temporal variables (optional)
            
        Returns:
            DataFrame with extracted values added as columns
        """
        logger.info(f"Extracting {len(variables)} variables for {len(ward_data)} wards")
        
        # We MUST use the Nigerian shapefile - no fallbacks
        if self.master_gdf is None:
            raise ValueError("Nigerian master shapefile not loaded. Cannot extract raster values without official ward geometry.")
        
        if 'WardName' not in ward_data.columns:
            raise ValueError("Ward data must have 'WardName' column to match with Nigerian shapefile")
        
        # Get geometry from Nigerian shapefile ONLY
        logger.info("Using Nigerian shapefile for ward geometry")
        ward_gdf = self._get_wards_from_master_shapefile(ward_data)
        
        # Extract values for each variable
        extracted_data = ward_data.copy()
        
        # Use parallel processing for efficiency
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_var = {}
            
            for variable in variables:
                future = executor.submit(
                    self._extract_single_variable,
                    ward_gdf,
                    variable,
                    year
                )
                future_to_var[future] = variable
            
            # Collect results
            for future in as_completed(future_to_var):
                variable = future_to_var[future]
                try:
                    values = future.result()
                    extracted_data[variable] = values
                    logger.info(f"Successfully extracted {variable}")
                except Exception as e:
                    logger.error(f"Failed to extract {variable}: {str(e)}")
                    extracted_data[variable] = np.nan
        
        return extracted_data
    
    def _extract_single_variable(self,
                               ward_gdf: gpd.GeoDataFrame,
                               variable: str,
                               year: Optional[int]) -> List[float]:
        """
        Extract values for a single variable using ward geometries.
        
        Args:
            ward_gdf: GeoDataFrame with ward geometries from Nigerian shapefile
            variable: Variable name
            year: Year for temporal variables
            
        Returns:
            List of extracted values
        """
        # Find raster file
        raster_path = self._find_raster_file(variable, year)
        
        if raster_path is None:
            logger.warning(f"No raster file found for {variable} (year: {year})")
            # Log available files for debugging
            var_dir = self.raster_base_dir / self.variable_directories.get(variable, '')
            if var_dir.exists():
                available_files = list(var_dir.glob("*.tif"))
                logger.info(f"Available files in {var_dir}: {[f.name for f in available_files]}")
            return [np.nan] * len(ward_gdf)
        
        # Extract values using ward geometries
        try:
            with rasterio.open(raster_path) as src:
                # Convert ward geometries to raster CRS if needed
                if ward_gdf.crs != src.crs:
                    ward_gdf_transformed = ward_gdf.to_crs(src.crs)
                else:
                    ward_gdf_transformed = ward_gdf
                
                # Extract values using ward centroids from official shapefile
                values = []
                for idx, ward in ward_gdf_transformed.iterrows():
                    if ward.geometry is not None and ward.geometry.is_valid:
                        # Get centroid from the official geometry
                        centroid = ward.geometry.centroid
                        # Sample value at centroid
                        val = list(sample_gen(src, [(centroid.x, centroid.y)]))[0]
                        values.append(val[0] if val[0] is not None else np.nan)
                    else:
                        values.append(np.nan)
                
                # Ensure we return exactly the right number of values
                if len(values) != len(ward_gdf):
                    logger.error(f"Value count mismatch: extracted {len(values)}, expected {len(ward_gdf)}")
                    # Pad or truncate to match
                    if len(values) < len(ward_gdf):
                        values.extend([np.nan] * (len(ward_gdf) - len(values)))
                    else:
                        values = values[:len(ward_gdf)]
                
                logger.debug(f"Extracted {len(values)} values from {raster_path.name}")
                return values
                
        except Exception as e:
            logger.error(f"Error reading raster {raster_path}: {str(e)}")
            return [np.nan] * len(ward_gdf)
    
    def _find_raster_file(self, variable: str, year: Optional[int]) -> Optional[Path]:
        """
        Find the appropriate raster file for a variable and year.
        
        Args:
            variable: Variable name
            year: Year (optional for static variables)
            
        Returns:
            Path to raster file or None if not found
        """
        # Get directory for variable
        if variable not in self.variable_directories:
            logger.warning(f"Unknown variable: {variable}")
            return None
        
        var_dir = self.raster_base_dir / self.variable_directories[variable]
        
        if not var_dir.exists():
            logger.warning(f"Directory not found: {var_dir}")
            return None
        
        # Static variables
        if variable in ['elevation', 'distance_to_water']:
            # Look for static file
            patterns = [f"{variable}_static.tif", f"{variable}.tif"]
            for pattern in patterns:
                file_path = var_dir / pattern
                if file_path.exists():
                    return file_path
        
        # Temporal variables
        else:
            # First try the requested year
            if year:
                # Try different patterns for the requested year
                patterns = [
                    f"{variable}_{year}_annual.tif",
                    f"{variable}_{year}.tif",
                    f"{variable}_{year}_mean.tif",
                    f"{variable}_{year}_total.tif"
                ]
                
                for pattern in patterns:
                    file_path = var_dir / pattern
                    if file_path.exists():
                        logger.info(f"Found {variable} file for requested year {year}: {file_path.name}")
                        return file_path
                
                # Check for monthly data (use December as representative)
                monthly_pattern = f"{variable}_{year}_12.tif"
                file_path = var_dir / monthly_pattern
                if file_path.exists():
                    logger.info(f"Using December data for {variable} {year}")
                    return file_path
            
            # If requested year not found or not provided, use most recent available
            most_recent_year = self._find_most_recent_year(var_dir, variable)
            if most_recent_year:
                logger.info(f"Requested year {year} not found for {variable}, using most recent: {most_recent_year}")
                # Try patterns with most recent year
                patterns = [
                    f"{variable}_{most_recent_year}_annual.tif",
                    f"{variable}_{most_recent_year}.tif",
                    f"{variable}_{most_recent_year}_mean.tif",
                    f"{variable}_{most_recent_year}_total.tif"
                ]
                
                for pattern in patterns:
                    file_path = var_dir / pattern
                    if file_path.exists():
                        logger.info(f"Using {file_path.name} as fallback")
                        return file_path
                
                # Check for monthly data
                monthly_pattern = f"{variable}_{most_recent_year}_12.tif"
                file_path = var_dir / monthly_pattern
                if file_path.exists():
                    logger.info(f"Using December {most_recent_year} data for {variable}")
                    return file_path
        
        return None
    
    def _find_most_recent_year(self, var_dir: Path, variable: str) -> Optional[int]:
        """
        Find the most recent year available for a variable.
        
        Args:
            var_dir: Variable directory
            variable: Variable name
            
        Returns:
            Most recent year or None
        """
        years = []
        
        # Look for year patterns in filenames that contain the variable name
        for file in var_dir.glob(f"{variable}*.tif"):
            # Extract year from filename
            import re
            year_match = re.search(r'(\d{4})', file.stem)
            if year_match:
                year = int(year_match.group(1))
                if 2000 <= year <= 2030:  # Reasonable year range
                    years.append(year)
        
        if years:
            most_recent = max(years)
            logger.info(f"Most recent year for {variable}: {most_recent}")
            return most_recent
        
        return None
    
    def get_available_variables(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about available variables and years.
        
        Returns:
            Dictionary with variable information
        """
        available = {}
        
        for variable, directory in self.variable_directories.items():
            var_dir = self.raster_base_dir / directory
            
            if not var_dir.exists():
                continue
            
            # Find available years
            years = set()
            files = []
            
            for file in var_dir.glob("*.tif"):
                files.append(file.name)
                
                # Extract year if present
                import re
                year_match = re.search(r'(\d{4})', file.stem)
                if year_match:
                    year = int(year_match.group(1))
                    if 2000 <= year <= 2030:
                        years.append(year)
            
            if files:
                available[variable] = {
                    'directory': directory,
                    'years': sorted(list(years)) if years else ['static'],
                    'files': sorted(files),
                    'is_static': variable in ['elevation', 'distance_to_water']
                }
        
        return available
    
    def extract_zone_variables(self,
                             ward_data: pd.DataFrame,
                             zone: str,
                             zone_variables: Dict[str, List[str]],
                             year: Optional[int] = None) -> pd.DataFrame:
        """
        Extract zone-specific variables for wards.
        
        Args:
            ward_data: DataFrame with ward information
            zone: Geopolitical zone name
            zone_variables: Dictionary mapping zones to variables
            year: Year for temporal variables
            
        Returns:
            DataFrame with zone-specific variables extracted
        """
        if zone not in zone_variables:
            logger.warning(f"Unknown zone: {zone}")
            return ward_data
        
        variables = zone_variables[zone]
        logger.info(f"Extracting {len(variables)} variables for {zone}")
        
        return self.extract_values_for_wards(ward_data, variables, year)
    
    def validate_extraction(self, extracted_data: pd.DataFrame, 
                          variables: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Validate extracted data quality.
        
        Args:
            extracted_data: DataFrame with extracted values
            variables: List of variables to validate
            
        Returns:
            Validation report
        """
        report = {}
        
        for variable in variables:
            if variable not in extracted_data.columns:
                report[variable] = {
                    'status': 'missing',
                    'message': 'Variable not found in data'
                }
                continue
            
            values = extracted_data[variable]
            non_nan = values.notna()
            
            report[variable] = {
                'status': 'success' if non_nan.sum() > 0 else 'failed',
                'total_wards': len(values),
                'valid_values': non_nan.sum(),
                'missing_values': (~non_nan).sum(),
                'coverage_percent': (non_nan.sum() / len(values)) * 100,
                'min': values[non_nan].min() if non_nan.any() else None,
                'max': values[non_nan].max() if non_nan.any() else None,
                'mean': values[non_nan].mean() if non_nan.any() else None
            }
        
        return report
    
    def _get_wards_from_master_shapefile(self, ward_data: pd.DataFrame) -> gpd.GeoDataFrame:
        """
        Get ward geometries from the Nigerian master shapefile.
        
        Args:
            ward_data: DataFrame with WardName column
            
        Returns:
            GeoDataFrame with matched ward geometries from master shapefile
        """
        # Clean ward names for matching
        ward_data_clean = ward_data.copy()
        ward_data_clean['ward_clean'] = ward_data['WardName'].str.strip().str.lower()
        # Add index to preserve original order
        ward_data_clean['original_index'] = ward_data_clean.index
        
        # Also clean master shapefile ward names
        master_clean = self.master_gdf.copy()
        master_clean['ward_clean'] = master_clean['WardName'].str.strip().str.lower()
        
        # Get state from ward data if available to filter master shapefile
        if 'StateName' in ward_data.columns and len(ward_data) > 0:
            state_name = ward_data['StateName'].iloc[0]
            # Filter master shapefile by state for faster matching
            master_clean = master_clean[
                master_clean['StateName'].str.lower() == state_name.lower()
            ]
            logger.info(f"Filtered to {len(master_clean)} wards in {state_name}")
        
        # Add LGA info if available to improve matching
        if 'LGA' in ward_data_clean.columns:
            ward_data_clean['lga_clean'] = ward_data_clean['LGA'].str.strip().str.lower()
            master_clean['lga_clean'] = master_clean['LGAName'].str.strip().str.lower()
            
            # First try to match on both ward and LGA
            result = ward_data_clean.merge(
                master_clean[['ward_clean', 'lga_clean', 'geometry', 'WardCode', 'LGAName', 'StateName']],
                on=['ward_clean', 'lga_clean'],
                how='left',
                suffixes=('', '_master')
            )
            
            # For unmatched rows, try matching on ward name only
            unmatched = result[result['geometry'].isna()]
            if len(unmatched) > 0:
                ward_only_match = unmatched[['original_index', 'ward_clean']].merge(
                    master_clean[['ward_clean', 'geometry', 'WardCode', 'LGAName', 'StateName']].drop_duplicates('ward_clean'),
                    on='ward_clean',
                    how='left',
                    suffixes=('', '_ward_only')
                )
                # Update the unmatched rows with ward-only matches
                for idx, row in ward_only_match.iterrows():
                    if pd.notna(row['geometry']):
                        orig_idx = row['original_index']
                        result.loc[result['original_index'] == orig_idx, 'geometry'] = row['geometry']
                        result.loc[result['original_index'] == orig_idx, 'WardCode'] = row['WardCode']
                        result.loc[result['original_index'] == orig_idx, 'LGAName_master'] = row['LGAName']
                        result.loc[result['original_index'] == orig_idx, 'StateName_master'] = row['StateName']
        else:
            # Merge on ward name only, but take first match to avoid duplicates
            master_dedup = master_clean.drop_duplicates('ward_clean', keep='first')
            result = ward_data_clean.merge(
                master_dedup[['ward_clean', 'geometry', 'WardCode', 'LGAName', 'StateName']],
                on='ward_clean',
                how='left',
                suffixes=('', '_master')
            )
        
        # Sort by original index to maintain order
        result = result.sort_values('original_index').reset_index(drop=True)
        
        # Count matches
        matched = result['geometry'].notna().sum()
        logger.info(f"Matched {matched}/{len(ward_data)} wards with master shapefile")
        
        # If we have duplicates due to merge, log warning
        if len(result) != len(ward_data):
            logger.warning(f"Row count changed after merge: {len(ward_data)} -> {len(result)}")
            # Keep only first match per original index
            result = result.drop_duplicates('original_index', keep='first')
            logger.info(f"After deduplication: {len(result)} rows")
        
        # Convert to GeoDataFrame
        result_gdf = gpd.GeoDataFrame(result, geometry='geometry', crs=self.master_gdf.crs)
        
        return result_gdf
    
    def close(self):
        """Close any cached raster files."""
        self.raster_cache.clear()


def test_raster_extractor():
    """Test the raster extractor with sample data."""
    import geopandas as gpd
    from shapely.geometry import Point
    
    # Create sample ward data
    sample_wards = pd.DataFrame({
        'WardName': ['Ward1', 'Ward2', 'Ward3'],
        'LGA': ['LGA1', 'LGA1', 'LGA2'],
        'lon': [7.5, 7.6, 7.7],
        'lat': [12.0, 12.1, 12.2]
    })
    
    # Create geometry
    geometry = [Point(lon, lat) for lon, lat in zip(sample_wards.lon, sample_wards.lat)]
    ward_gdf = gpd.GeoDataFrame(sample_wards, geometry=geometry, crs='EPSG:4326')
    
    # Initialize extractor
    extractor = RasterExtractor()
    
    # Get available variables
    print("Available variables:")
    available = extractor.get_available_variables()
    for var, info in available.items():
        print(f"  {var}: {info['years']}")
    
    # Test extraction
    if available:
        test_vars = list(available.keys())[:3]  # Test first 3 variables
        print(f"\nTesting extraction for: {test_vars}")
        
        result = extractor.extract_values_for_wards(ward_gdf, test_vars)
        print("\nExtracted values:")
        print(result[['WardName'] + test_vars])
        
        # Validate
        validation = extractor.validate_extraction(result, test_vars)
        print("\nValidation report:")
        for var, report in validation.items():
            print(f"  {var}: {report['coverage_percent']:.1f}% coverage")


if __name__ == "__main__":
    test_raster_extractor()