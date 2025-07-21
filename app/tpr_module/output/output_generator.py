"""
Output Generator for TPR Module.

This module generates the three output files required by the TPR analysis:
1. TPR Analysis CSV - Detailed TPR calculations
2. Main Analysis CSV - TPR + environmental variables
3. Shapefile - State boundaries with all data
"""

import os
import pandas as pd
import geopandas as gpd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime

from ..data.geopolitical_zones import STATE_TO_ZONE, ZONE_VARIABLES
from ..services.raster_extractor import RasterExtractor
from ..services.shapefile_extractor import ShapefileExtractor

logger = logging.getLogger(__name__)

class OutputGenerator:
    """Generate the three output files for TPR analysis."""
    
    def __init__(self, session_id: str, output_base_dir: str = None):
        """
        Initialize the output generator.
        
        Args:
            session_id: Session ID for output organization
            output_base_dir: Base directory for outputs
        """
        self.session_id = session_id
        
        if output_base_dir is None:
            # Default to instance/uploads/{session_id}
            output_base_dir = os.path.join('instance', 'uploads', session_id)
        
        self.output_dir = Path(output_base_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize services
        self.raster_extractor = RasterExtractor()
        self.shapefile_extractor = ShapefileExtractor()
        
        logger.info(f"OutputGenerator initialized for session {session_id}")
    
    def _merge_with_shapefile(self, tpr_data: pd.DataFrame, state_name: str) -> pd.DataFrame:
        """
        Merge TPR data with shapefile to get geometry and identifier columns.
        
        Args:
            tpr_data: TPR results DataFrame
            state_name: State name
            
        Returns:
            DataFrame with geometry and identifier columns added
        """
        try:
            # Load the master Nigerian shapefile
            if not self.shapefile_extractor.master_gdf is None:
                state_gdf = self.shapefile_extractor.master_gdf.copy()
            else:
                # Try to load shapefile
                shapefile_path = self.shapefile_extractor._find_shapefile_for_state(state_name)
                if not shapefile_path:
                    logger.warning("No shapefile found - returning data without geometry")
                    return tpr_data
                
                # Load shapefile
                state_gdf = gpd.read_file(shapefile_path)
            
            # Filter to state
            state_col = self.shapefile_extractor._identify_column('state', state_gdf)
            if state_col:
                # Clean state name for comparison
                clean_state_name = state_name.replace(' State', '').strip()
                state_gdf = state_gdf[state_gdf[state_col].str.contains(clean_state_name, case=False, na=False)]
                logger.info(f"Filtered shapefile to {len(state_gdf)} features for {state_name}")
            
            # Identify key columns
            identifier_cols = ['StateCode', 'WardCode', 'WardName', 'LGACode', 'LGAName', 'Urban', 'AMAPCODE']
            available_ids = [col for col in identifier_cols if col in state_gdf.columns]
            
            # Always include geometry and LGAName for proper merging
            merge_cols = available_ids + ['geometry'] if 'geometry' in state_gdf.columns else available_ids
            if 'LGAName' in state_gdf.columns and 'LGAName' not in merge_cols:
                merge_cols = merge_cols + ['LGAName']
            
            # Prepare for merge
            if 'WardName' in tpr_data.columns and 'WardName' in state_gdf.columns:
                # Debug logging
                logger.info(f"Merging on WardName. TPR has {len(tpr_data)} rows, shapefile has {len(state_gdf)} rows")
                logger.info(f"Available identifier columns from shapefile: {available_ids}")
                logger.info(f"Merge columns: {merge_cols}")
                
                # Check if we have LGA columns for more precise matching
                if 'LGA' in tpr_data.columns and 'LGAName' in state_gdf.columns:
                    # Merge on both WardName and LGA to avoid duplicates
                    logger.info("Merging on WardName AND LGA to ensure unique matches")
                    merged = tpr_data.merge(
                        state_gdf[merge_cols],
                        left_on=['WardName', 'LGA'],
                        right_on=['WardName', 'LGAName'],
                        how='left',
                        suffixes=('', '_shp')
                    )
                else:
                    # Fallback to WardName only merge
                    logger.warning("LGA columns not available for precise matching, using WardName only")
                    merged = tpr_data.merge(
                        state_gdf[merge_cols],
                        on='WardName',
                        how='left',
                        suffixes=('', '_shp')
                    )
            else:
                # Try to identify ward columns
                ward_col_tpr = self.shapefile_extractor._identify_column('ward', tpr_data)
                ward_col_shp = self.shapefile_extractor._identify_column('ward', state_gdf)
                
                if ward_col_tpr and ward_col_shp:
                    # Normalize names for matching
                    tpr_data['_ward_norm'] = tpr_data[ward_col_tpr].apply(
                        self.shapefile_extractor._normalize_name
                    )
                    state_gdf['_ward_norm'] = state_gdf[ward_col_shp].apply(
                        self.shapefile_extractor._normalize_name
                    )
                    
                    merged = tpr_data.merge(
                        state_gdf[merge_cols + ['_ward_norm']],
                        on='_ward_norm',
                        how='left',
                        suffixes=('', '_shp')
                    )
                    
                    # Clean up temp column
                    merged.drop('_ward_norm', axis=1, inplace=True)
                else:
                    logger.warning("Could not identify ward columns for merging")
                    return tpr_data
            
            # Clean up duplicate columns
            for col in merged.columns:
                if col.endswith('_shp'):
                    merged.drop(col, axis=1, inplace=True)
            
            # Log merge success
            if 'geometry' in merged.columns:
                matched = merged['geometry'].notna().sum()
                total = len(merged)
                logger.info(f"Merged shapefile data: {matched}/{total} wards matched ({matched/total*100:.1f}%)")
            
            # Check if identifier columns have data
            logger.info(f"Added identifier columns: {[col for col in available_ids if col in merged.columns]}")
            for col in available_ids:
                if col in merged.columns:
                    non_null = merged[col].notna().sum()
                    logger.info(f"  {col}: {non_null}/{len(merged)} non-null values")
            
            # Debug: Check sample data
            if 'WardCode' in merged.columns:
                sample = merged[['WardName', 'WardCode', 'StateCode']].head(3)
                logger.info(f"Sample merged data:\n{sample}")
            
            # Convert to GeoDataFrame if we have geometry
            if 'geometry' in merged.columns:
                merged = gpd.GeoDataFrame(merged, geometry='geometry')
            
            return merged
            
        except Exception as e:
            logger.error(f"Error merging with shapefile: {str(e)}")
            return tpr_data
    
    def generate_outputs(self, 
                        tpr_results: pd.DataFrame,
                        state_name: str,
                        metadata: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate all three output files.
        
        Args:
            tpr_results: DataFrame with TPR calculations
            state_name: Selected state name
            metadata: Analysis metadata (facility level, age group, etc.)
            
        Returns:
            Dictionary with paths to generated files
        """
        logger.info(f"Generating outputs for {state_name}")
        
        output_paths = {}
        
        try:
            # First, merge with shapefile to get geometry and identifier columns
            tpr_with_geo = self._merge_with_shapefile(tpr_results, state_name)
            
            # 1. Generate TPR Analysis CSV
            tpr_path = self._generate_tpr_csv(tpr_with_geo, state_name, metadata)
            output_paths['tpr_analysis'] = tpr_path
            
            # 2. Generate Main Analysis CSV with environmental variables
            main_path = self._generate_main_csv(tpr_with_geo, state_name)
            output_paths['main_analysis'] = main_path
            
            # 3. Generate Shapefile
            shapefile_path = self._generate_shapefile(tpr_with_geo, state_name)
            output_paths['shapefile'] = shapefile_path
            
            # 4. Generate summary report
            summary_path = self._generate_summary_report(
                tpr_with_geo, state_name, metadata, output_paths
            )
            output_paths['summary'] = summary_path
            
            logger.info(f"Successfully generated all outputs: {output_paths}")
            
        except Exception as e:
            logger.error(f"Error generating outputs: {str(e)}")
            raise
        
        return output_paths
    
    def _generate_tpr_csv(self, 
                         tpr_results: pd.DataFrame,
                         state_name: str,
                         metadata: Dict[str, Any]) -> str:
        """Generate detailed TPR analysis CSV."""
        # Create clean TPR dataframe
        tpr_df = tpr_results.copy()
        
        # Keep original ward names with disambiguation
        # DO NOT remove (WardCode) suffix as it ensures uniqueness
        
        # Add metadata columns
        tpr_df['State'] = state_name
        tpr_df['Analysis_Date'] = datetime.now().strftime('%Y-%m-%d')
        tpr_df['Facility_Level'] = metadata.get('facility_level', 'All')
        tpr_df['Age_Group'] = metadata.get('age_group', 'All Ages')
        tpr_df['TPR_Method'] = tpr_df.get('Method', 'standard')
        
        # Reorder columns for clarity
        column_order = [
            'State', 'LGA', 'WardName',
            'TPR', 'TPR_Method',
            'RDT_Tested', 'RDT_Positive', 
            'Microscopy_Tested', 'Microscopy_Positive',
            'Total_Tested', 'Total_Positive',
            'Facility_Count', 'Facility_Level', 'Age_Group',
            'Analysis_Date'
        ]
        
        # Add any additional columns
        for col in tpr_df.columns:
            if col not in column_order and col != 'geometry':
                column_order.append(col)
        
        # Select only columns that exist
        existing_columns = [col for col in column_order if col in tpr_df.columns]
        tpr_df = tpr_df[existing_columns]
        
        # Sort by LGA and WardName
        if 'LGA' in tpr_df.columns and 'WardName' in tpr_df.columns:
            tpr_df = tpr_df.sort_values(['LGA', 'WardName'])
        
        # Save to CSV
        filename = f"{state_name.replace(' ', '_')}_TPR_Analysis_{datetime.now().strftime('%Y%m%d')}.csv"
        output_path = self.output_dir / filename
        
        tpr_df.to_csv(output_path, index=False)
        logger.info(f"Saved TPR analysis to: {output_path}")
        
        return str(output_path)
    
    def _generate_main_csv(self, 
                          tpr_results: pd.DataFrame,
                          state_name: str) -> str:
        """Generate main analysis CSV with TPR and environmental variables."""
        # Start with TPR results
        main_df = tpr_results.copy()
        
        # Keep original ward names with disambiguation
        # DO NOT remove (WardCode) suffix as it ensures uniqueness
        
        # The data should already have geometry and identifiers from _merge_with_shapefile
        
        # Determine geopolitical zone
        zone = STATE_TO_ZONE.get(state_name)
        
        if not zone:
            # Try to match with normalization
            normalized_state = state_name.upper().replace(' STATE', '').strip()
            for state, state_zone in STATE_TO_ZONE.items():
                if state.upper() == normalized_state:
                    zone = state_zone
                    break
        
        if not zone:
            logger.warning(f"Unknown geopolitical zone for {state_name}, using North_Central defaults")
            zone = 'North_Central'
        
        logger.info(f"State {state_name} is in {zone} zone")
        
        # Get zone-specific variables
        zone_vars = ZONE_VARIABLES.get(zone, [])
        
        # Extract environmental variables
        if zone_vars and 'geometry' in main_df.columns:
            logger.info(f"Extracting {len(zone_vars)} environmental variables for {zone}")
            
            # Convert to GeoDataFrame if needed
            if not isinstance(main_df, gpd.GeoDataFrame):
                if 'geometry' in main_df.columns:
                    main_df = gpd.GeoDataFrame(main_df, geometry='geometry')
                else:
                    logger.warning("No geometry column found - cannot convert to GeoDataFrame")
                    zone_vars = []  # Skip extraction
            
            if zone_vars and isinstance(main_df, gpd.GeoDataFrame):
                # Extract variables
                main_df = self.raster_extractor.extract_zone_variables(
                    main_df, zone, ZONE_VARIABLES
                )
            
            # Validate extraction
            validation = self.raster_extractor.validate_extraction(main_df, zone_vars)
            
            for var, report in validation.items():
                if report['status'] == 'success':
                    logger.info(f"{var}: {report['coverage_percent']:.1f}% coverage")
                else:
                    logger.warning(f"{var}: {report['status']}")
        else:
            logger.warning("No geometry column or zone variables - skipping environmental extraction")
        
        # Define column order: WardName, Identifiers, TPR data, Environmental variables
        # 1. Ward Name first
        output_columns = ['WardName']
        
        # 2. Identifiers
        identifier_columns = ['WardCode', 'LGA', 'LGACode', 'State', 'StateCode', 'Urban', 'AMAPCODE']
        for col in identifier_columns:
            if col in main_df.columns:
                output_columns.append(col)
        
        # 3. TPR data (only TPR value as requested)
        if 'TPR' in main_df.columns:
            output_columns.append('TPR')
        
        # 4. Environmental variables last
        for var in zone_vars:
            if var in main_df.columns and var not in output_columns:
                output_columns.append(var)
        
        # Add any remaining relevant columns not already included
        other_columns = ['Population']
        for col in other_columns:
            if col in main_df.columns and col not in output_columns:
                output_columns.append(col)
        
        # Create output dataframe
        output_df = main_df[output_columns].copy()
        
        # Sort by LGA and WardName
        if 'LGA' in output_df.columns and 'WardName' in output_df.columns:
            output_df = output_df.sort_values(['LGA', 'WardName'])
        
        # Save to CSV with requested naming convention
        filename = f"{state_name.replace(' State', '').replace(' ', '_')}_plus.csv"
        output_path = self.output_dir / filename
        
        output_df.to_csv(output_path, index=False)
        logger.info(f"Saved main analysis to: {output_path}")
        
        return str(output_path)
    
    def _generate_shapefile(self, 
                           tpr_results: pd.DataFrame,
                           state_name: str) -> Optional[str]:
        """Generate shapefile with all data."""
        try:
            # Use shapefile extractor
            shapefile_path = self.shapefile_extractor.extract_state_shapefile(
                state_name,
                tpr_results,
                str(self.output_dir)
            )
            
            if shapefile_path:
                logger.info(f"Generated shapefile: {shapefile_path}")
                return shapefile_path
            else:
                logger.error("Failed to generate shapefile")
                return None
                
        except Exception as e:
            logger.error(f"Error generating shapefile: {str(e)}")
            return None
    
    def _generate_summary_report(self,
                               tpr_results: pd.DataFrame,
                               state_name: str,
                               metadata: Dict[str, Any],
                               output_paths: Dict[str, str]) -> str:
        """Generate a summary report of the analysis."""
        report = f"""# TPR Analysis Summary Report

**State**: {state_name}  
**Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**Session ID**: {self.session_id}

## Analysis Parameters
- **Facility Level**: {metadata.get('facility_level', 'All')}
- **Age Group**: {metadata.get('age_group', 'All Ages')}
- **Number of Wards**: {len(tpr_results)}
- **Geopolitical Zone**: {STATE_TO_ZONE.get(state_name, 'Unknown')}

## TPR Statistics
"""
        
        # Calculate statistics
        if 'TPR' in tpr_results.columns:
            tpr_values = tpr_results['TPR'].dropna()
            
            report += f"- **Mean TPR**: {tpr_values.mean():.2f}%\n"
            report += f"- **Median TPR**: {tpr_values.median():.2f}%\n"
            report += f"- **Min TPR**: {tpr_values.min():.2f}%\n"
            report += f"- **Max TPR**: {tpr_values.max():.2f}%\n"
            report += f"- **Std Dev**: {tpr_values.std():.2f}%\n"
            
            # High TPR wards
            high_tpr = tpr_results[tpr_results['TPR'] > 50]
            if not high_tpr.empty:
                report += f"\n### Wards with TPR > 50%\n"
                report += f"Total: {len(high_tpr)} wards\n\n"
                
                for _, ward in high_tpr.iterrows():
                    report += f"- {ward.get('WardName', 'Unknown')} ({ward.get('LGA', 'Unknown')} LGA): {ward['TPR']:.1f}%\n"
        
        # Method breakdown
        if 'Method' in tpr_results.columns:
            method_counts = tpr_results['Method'].value_counts()
            report += f"\n## Calculation Methods Used\n"
            for method, count in method_counts.items():
                report += f"- {method}: {count} wards ({count/len(tpr_results)*100:.1f}%)\n"
        
        # Environmental variables
        zone = STATE_TO_ZONE.get(state_name)
        if zone:
            zone_vars = ZONE_VARIABLES.get(zone, [])
            report += f"\n## Environmental Variables Extracted\n"
            report += f"Zone: {zone}\n"
            report += f"Variables: {', '.join(zone_vars)}\n"
            
            # Check coverage
            coverage_stats = []
            for var in zone_vars:
                if var in tpr_results.columns:
                    coverage = tpr_results[var].notna().sum() / len(tpr_results) * 100
                    coverage_stats.append(f"{var}: {coverage:.1f}%")
            
            if coverage_stats:
                report += "\nCoverage:\n"
                for stat in coverage_stats:
                    report += f"- {stat}\n"
        
        # Output files
        report += f"\n## Generated Files\n"
        for file_type, path in output_paths.items():
            if path:
                file_size = os.path.getsize(path) / 1024  # KB
                report += f"- **{file_type}**: {os.path.basename(path)} ({file_size:.1f} KB)\n"
        
        # Data quality notes
        report += f"\n## Data Quality Notes\n"
        
        if 'Total_Tested' in tpr_results.columns:
            zero_tested = (tpr_results['Total_Tested'] == 0).sum()
            if zero_tested > 0:
                report += f"- {zero_tested} wards had zero tested cases\n"
        
        missing_tpr = tpr_results['TPR'].isna().sum()
        if missing_tpr > 0:
            report += f"- {missing_tpr} wards have missing TPR values\n"
        
        # Save report
        report_path = self.output_dir / f"{state_name.replace(' ', '_')}_Summary_Report.md"
        with open(report_path, 'w') as f:
            f.write(report)
        
        logger.info(f"Saved summary report to: {report_path}")
        return str(report_path)
    
    def validate_outputs(self, output_paths: Dict[str, str]) -> Dict[str, Any]:
        """
        Validate all generated outputs.
        
        Args:
            output_paths: Dictionary of output file paths
            
        Returns:
            Validation report
        """
        validation = {
            'all_valid': True,
            'files': {}
        }
        
        for file_type, path in output_paths.items():
            if not path:
                validation['files'][file_type] = {
                    'exists': False,
                    'valid': False,
                    'message': 'Path is None'
                }
                validation['all_valid'] = False
                continue
            
            file_validation = {
                'exists': os.path.exists(path),
                'valid': False,
                'size_kb': 0
            }
            
            if file_validation['exists']:
                file_validation['size_kb'] = os.path.getsize(path) / 1024
                
                # Type-specific validation
                if file_type in ['tpr_analysis', 'main_analysis']:
                    # Validate CSV
                    try:
                        df = pd.read_csv(path)
                        file_validation['valid'] = len(df) > 0
                        file_validation['row_count'] = len(df)
                        file_validation['column_count'] = len(df.columns)
                    except Exception as e:
                        file_validation['message'] = str(e)
                
                elif file_type == 'shapefile':
                    # Use shapefile validator
                    shp_validation = self.shapefile_extractor.validate_shapefile(path)
                    file_validation.update(shp_validation)
                
                elif file_type == 'summary':
                    # Check if file is readable
                    try:
                        with open(path, 'r') as f:
                            content = f.read()
                            file_validation['valid'] = len(content) > 0
                    except Exception as e:
                        file_validation['message'] = str(e)
            else:
                validation['all_valid'] = False
                file_validation['message'] = 'File does not exist'
            
            validation['files'][file_type] = file_validation
        
        return validation


def test_output_generator():
    """Test the output generator functionality."""
    import pandas as pd
    from shapely.geometry import Point
    import geopandas as gpd
    
    # Create sample TPR results
    sample_data = pd.DataFrame({
        'Ward': ['Ward1', 'Ward2', 'Ward3'],
        'LGA': ['LGA1', 'LGA1', 'LGA2'],
        'TPR': [15.2, 22.5, 18.7],
        'RDT_Tested': [100, 150, 80],
        'RDT_Positive': [15, 34, 15],
        'Microscopy_Tested': [50, 75, 40],
        'Microscopy_Positive': [8, 17, 8],
        'Total_Tested': [100, 150, 80],
        'Total_Positive': [15, 34, 15],
        'Method': ['standard', 'standard', 'alternative'],
        'Facility_Count': [3, 5, 2],
        'lon': [7.5, 7.6, 7.7],
        'lat': [12.0, 12.1, 12.2]
    })
    
    # Add geometry
    geometry = [Point(lon, lat) for lon, lat in zip(sample_data.lon, sample_data.lat)]
    tpr_results = gpd.GeoDataFrame(sample_data, geometry=geometry, crs='EPSG:4326')
    
    # Create metadata
    metadata = {
        'facility_level': 'Primary',
        'age_group': 'Under 5',
        'source_file': 'test_nmep.xlsx'
    }
    
    # Initialize generator
    generator = OutputGenerator('test_session_123')
    
    # Generate outputs
    try:
        output_paths = generator.generate_outputs(
            tpr_results,
            'Kano',
            metadata
        )
        
        print("Generated outputs:")
        for file_type, path in output_paths.items():
            print(f"  {file_type}: {path}")
        
        # Validate
        validation = generator.validate_outputs(output_paths)
        print(f"\nValidation result: All valid = {validation['all_valid']}")
        
        # Clean up
        import shutil
        if os.path.exists(generator.output_dir):
            shutil.rmtree(generator.output_dir)
            
    except Exception as e:
        print(f"Error in test: {str(e)}")


if __name__ == "__main__":
    test_output_generator()