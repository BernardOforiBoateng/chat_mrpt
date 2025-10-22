#!/usr/bin/env python3
"""
Test ITN recalculation with fixed population data
"""

import sys
import os
import json

def test_itn_recalculation(session_id):
    """Force ITN recalculation with population data"""
    
    # Add app to path
    sys.path.insert(0, '/home/ec2-user/ChatMRPT')
    
    from app.analysis.itn_pipeline import calculate_itn_distribution
    from app.data import DataHandler
    
    # Set up session folder
    session_folder = f'/home/ec2-user/ChatMRPT/instance/uploads/{session_id}'
    
    print(f"Testing ITN recalculation for session: {session_id}")
    print(f"Session folder: {session_folder}")
    
    # Initialize DataHandler
    data_handler = DataHandler(session_folder)
    
    # Load data
    data_handler._attempt_data_reload()
    data_handler.load_session_state()
    
    # Check if data loaded
    if data_handler.csv_data is None:
        print("ERROR: No CSV data loaded")
        return False
    
    print(f"CSV data loaded: {len(data_handler.csv_data)} rows")
    
    # Check for shapefile
    shapefile_path = os.path.join(session_folder, 'shapefile')
    if os.path.exists(shapefile_path):
        import geopandas as gpd
        shp_files = [f for f in os.listdir(shapefile_path) if f.endswith('.shp')]
        if shp_files:
            shp_file = os.path.join(shapefile_path, shp_files[0])
            data_handler.shapefile_data = gpd.read_file(shp_file)
            print(f"Shapefile loaded: {len(data_handler.shapefile_data)} features")
    
    # Load vulnerability rankings
    rankings_path = os.path.join(session_folder, 'analysis_vulnerability_rankings.csv')
    if os.path.exists(rankings_path):
        import pandas as pd
        data_handler.vulnerability_rankings = pd.read_csv(rankings_path)
        print(f"Rankings loaded: {len(data_handler.vulnerability_rankings)} wards")
    
    # Load unified dataset
    unified_path = os.path.join(session_folder, 'unified_dataset.csv')
    if os.path.exists(unified_path):
        import pandas as pd
        data_handler.unified_dataset = pd.read_csv(unified_path)
        print(f"Unified dataset loaded: {len(data_handler.unified_dataset)} rows")
    
    print("\nRunning ITN distribution calculation...")
    
    # Calculate ITN distribution with default parameters
    result = calculate_itn_distribution(
        data_handler,
        session_id=session_id,
        total_nets=2000000,  # 2 million nets
        avg_household_size=5.0,
        urban_threshold=30.0,
        method='composite'
    )
    
    print(f"\nResult status: {result['status']}")
    
    if result['status'] == 'success':
        print(f"Map created: {result.get('map_path', 'No path')}")
        
        # Check the distribution results
        results_path = os.path.join(session_folder, 'itn_distribution_results.json')
        if os.path.exists(results_path):
            with open(results_path, 'r') as f:
                dist_results = json.load(f)
            
            print("\n=== ITN Distribution Summary ===")
            print(f"Total nets: {dist_results.get('total_nets', 0):,}")
            print(f"Total allocated: {dist_results.get('total_allocated', 0):,}")
            print(f"Coverage: {dist_results.get('coverage_percentage', 0):.1f}%")
            
            distribution = dist_results.get('distribution', [])
            print(f"Wards in distribution: {len(distribution)}")
            
            allocated = sum(1 for w in distribution if w.get('nets_allocated', 0) > 0)
            print(f"Wards with nets: {allocated}")
            
            # Check for population data
            has_pop = sum(1 for w in distribution if w.get('population', 0) > 0)
            print(f"Wards with population data: {has_pop}")
            
            return len(distribution) > 0
    else:
        print(f"Error: {result.get('message', 'Unknown error')}")
        return False

if __name__ == "__main__":
    session_id = '0b7e3bbc-284a-421c-ab89-b53ea56b1dc3'
    success = test_itn_recalculation(session_id)
    
    if success:
        print("\n✅ ITN recalculation successful!")
    else:
        print("\n❌ ITN recalculation failed")