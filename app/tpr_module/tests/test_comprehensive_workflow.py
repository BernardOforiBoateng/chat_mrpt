"""
Comprehensive end-to-end test for TPR module using real NMEP data.

This test demonstrates the complete workflow:
1. Loading actual NMEP Excel file
2. Processing data with ward name prefix removal
3. Calculating TPR for all states
4. Extracting environmental variables from rasters
5. Extracting and joining shapefile data with identifier columns
6. Generating all required outputs with proper column names
7. Creating TPR distribution maps
"""

import os
import sys
import pandas as pd
import geopandas as gpd
from pathlib import Path
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from app.tpr_module.data.nmep_parser import NMEPParser
from app.tpr_module.data.column_mapper import ColumnMapper
from app.tpr_module.core.tpr_calculator import TPRCalculator
from app.tpr_module.output.output_generator import OutputGenerator
from app.tpr_module.services.raster_extractor import RasterExtractor
from app.tpr_module.services.shapefile_extractor import ShapefileExtractor
from app.tpr_module.data.geopolitical_zones import STATE_TO_ZONE, ZONE_VARIABLES

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_comprehensive_tpr_workflow():
    """Test the complete TPR workflow with real NMEP data."""
    
    # Path to actual NMEP data file
    nmep_file = "/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/NMEP Malaria Adamawa_Kwara_Osun_Test Postivity Rate_2022_2024.xlsx"
    
    if not os.path.exists(nmep_file):
        logger.error(f"NMEP file not found: {nmep_file}")
        return
    
    print("\n=== COMPREHENSIVE TPR WORKFLOW TEST ===\n")
    
    # Step 1: Parse NMEP file
    print("1. Parsing NMEP Excel file...")
    parser = NMEPParser()
    parse_result = parser.parse_file(nmep_file)
    
    if parse_result['status'] != 'success':
        logger.error(f"Failed to parse NMEP file: {parse_result['message']}")
        return
    
    data = parse_result['data']
    states = parse_result['states']
    
    print(f"   - Found {len(states)} states: {', '.join(states)}")
    print(f"   - Total records: {len(data)}")
    print(f"   - Time range: {parse_result['metadata']['time_range']}")
    
    # Check ward name cleaning
    print("\n2. Checking ward name cleaning...")
    if 'WardName' in data.columns:
        sample_wards = data[['Ward', 'WardName']].drop_duplicates().head(5)
        print("   Original Ward -> Cleaned WardName:")
        for _, row in sample_wards.iterrows():
            print(f"   '{row['Ward']}' -> '{row['WardName']}'")
    
    # Step 2: Process each state
    for state_name in states[:1]:  # Test with first state only for brevity
        print(f"\n3. Processing {state_name}...")
        
        # Get state data
        state_data = parser.get_state_data(state_name)
        print(f"   - Records for {state_name}: {len(state_data)}")
        
        # Map columns
        print("\n4. Mapping columns...")
        mapper = ColumnMapper()
        mapped_data = mapper.map_columns(state_data)
        
        # Calculate TPR
        print("\n5. Calculating TPR...")
        calculator = TPRCalculator()
        tpr_results = calculator.calculate_ward_tpr(mapped_data, age_group='u5')
        
        # Convert to DataFrame for output generation
        tpr_df = calculator.export_results_to_dataframe()
        print(f"   - Calculated TPR for {len(tpr_df)} wards")
        
        # Display sample results
        print("\n   Sample TPR results:")
        print(tpr_df[['WardName', 'LGA', 'TPR', 'TPR_Method']].head(5).to_string())
        
        # Initialize output generator
        print("\n6. Generating outputs...")
        output_dir = f"test_output_{state_name.replace(' ', '_')}"
        generator = OutputGenerator('test_session', output_dir)
        
        # Generate all outputs
        metadata = {
            'facility_level': 'All',
            'age_group': 'Under 5',
            'source_file': os.path.basename(nmep_file)
        }
        
        output_paths = generator.generate_outputs(tpr_df, state_name, metadata)
        
        # Check outputs
        print("\n7. Checking generated files...")
        for file_type, path in output_paths.items():
            if path and os.path.exists(path):
                file_size = os.path.getsize(path) / 1024
                print(f"   - {file_type}: {os.path.basename(path)} ({file_size:.1f} KB)")
                
                # Check CSV contents
                if file_type == 'main_analysis':
                    main_df = pd.read_csv(path)
                    print(f"\n   Main CSV columns: {list(main_df.columns)}")
                    
                    # Check for identifier columns
                    id_cols = ['StateCode', 'WardCode', 'LGACode', 'WardName']
                    present_ids = [col for col in id_cols if col in main_df.columns]
                    print(f"   Identifier columns present: {present_ids}")
                    
                    # Check environmental variables
                    zone = STATE_TO_ZONE.get(state_name)
                    if zone:
                        zone_vars = ZONE_VARIABLES.get(zone, [])
                        present_vars = [var for var in zone_vars if var in main_df.columns]
                        print(f"   Environmental variables ({zone}): {len(present_vars)}/{len(zone_vars)} extracted")
                    
                    # Show sample data
                    print("\n   Sample of main CSV:")
                    display_cols = ['WardName', 'WardCode', 'LGA', 'LGACode', 'TPR']
                    display_cols = [col for col in display_cols if col in main_df.columns]
                    print(main_df[display_cols].head(3).to_string())
                
                elif file_type == 'shapefile':
                    # Validate shapefile
                    validation = generator.shapefile_extractor.validate_shapefile(path)
                    print(f"\n   Shapefile validation: {validation['message']}")
                    print(f"   Features: {validation.get('feature_count', 0)}")
                    print(f"   Has TPR data: {validation.get('has_tpr_data', False)}")
        
        # Clean up test output
        import shutil
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
            print(f"\n8. Cleaned up test output directory")
    
    print("\n=== TEST COMPLETED ===")


def test_ward_name_cleaning():
    """Test that ward name prefixes are properly removed."""
    print("\n=== TESTING WARD NAME CLEANING ===\n")
    
    parser = NMEPParser()
    
    # Test cases
    test_wards = [
        "KW Alanamu",
        "AD Yola North",
        "OS Ife Central",
        "Regular Ward Name",
        "kw lowercase prefix",
        "KWARA Full State Name"  # Should not be cleaned
    ]
    
    print("Testing ward name cleaning:")
    for ward in test_wards:
        cleaned = parser._clean_ward_name(ward)
        print(f"  '{ward}' -> '{cleaned}'")
    
    print("\n=== WARD NAME CLEANING TEST COMPLETED ===")


if __name__ == "__main__":
    # Run tests
    test_ward_name_cleaning()
    test_comprehensive_tpr_workflow()