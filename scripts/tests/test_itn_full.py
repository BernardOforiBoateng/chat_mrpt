#!/usr/bin/env python3
"""
Test ITN distribution calculation directly
"""

import sys
import os
import json
import warnings
warnings.filterwarnings('ignore')

def test_itn_calculation(session_id):
    """Test ITN calculation with all fixes"""
    
    session_folder = f'/home/ec2-user/ChatMRPT/instance/uploads/{session_id}'
    print(f"Testing ITN for session: {session_id}")
    print(f"Session folder: {session_folder}")
    
    # Change to ChatMRPT directory
    os.chdir('/home/ec2-user/ChatMRPT')
    sys.path.insert(0, '/home/ec2-user/ChatMRPT')
    
    # Import after setting path
    import pandas as pd
    import geopandas as gpd
    from pathlib import Path
    
    print("\n=== Step 1: Checking Data Files ===")
    
    # Check for required files
    files_to_check = [
        'raw_data.csv',
        'analysis_vulnerability_rankings.csv',
        'unified_dataset.csv',
        'itn_distribution_results.json'
    ]
    
    for file in files_to_check:
        file_path = os.path.join(session_folder, file)
        exists = os.path.exists(file_path)
        print(f"{file}: {'✅ exists' if exists else '❌ missing'}")
    
    # Check for urban_percentage in raw data
    raw_data_path = os.path.join(session_folder, 'raw_data.csv')
    if os.path.exists(raw_data_path):
        df = pd.read_csv(raw_data_path)
        has_urban = 'urban_percentage' in df.columns or 'urban_extent' in df.columns
        print(f"Urban percentage column: {'✅ present' if has_urban else '❌ missing'}")
        if has_urban:
            col_name = 'urban_percentage' if 'urban_percentage' in df.columns else 'urban_extent'
            non_null = df[col_name].notna().sum()
            print(f"  - Non-null urban values: {non_null}/{len(df)}")
    
    print("\n=== Step 2: Testing Population Data Loading ===")
    
    # Test population loader
    from app.data.population_data.itn_population_loader import get_population_loader
    loader = get_population_loader()
    
    # Try to load Adamawa population
    pop_data = loader.load_state_population('Adamawa')
    if pop_data is not None:
        print(f"✅ Population data loaded: {len(pop_data)} wards, {pop_data['Population'].sum():,.0f} total population")
    else:
        print("❌ Failed to load population data")
    
    print("\n=== Step 3: Simulating ITN Calculation ===")
    
    # Import ITN pipeline
    from app.analysis.itn_pipeline import calculate_itn_distribution, detect_state, load_population_data
    
    # Create a mock data handler
    class MockDataHandler:
        def __init__(self, session_folder):
            self.session_folder = session_folder
            
            # Load CSV data
            csv_path = os.path.join(session_folder, 'raw_data.csv')
            self.csv_data = pd.read_csv(csv_path) if os.path.exists(csv_path) else None
            
            # Load shapefile
            shp_dir = os.path.join(session_folder, 'shapefile')
            if os.path.exists(shp_dir):
                shp_files = [f for f in os.listdir(shp_dir) if f.endswith('.shp')]
                if shp_files:
                    self.shapefile_data = gpd.read_file(os.path.join(shp_dir, shp_files[0]))
                else:
                    self.shapefile_data = None
            else:
                self.shapefile_data = None
            
            # Load vulnerability rankings
            rankings_path = os.path.join(session_folder, 'analysis_vulnerability_rankings.csv')
            self.vulnerability_rankings = pd.read_csv(rankings_path) if os.path.exists(rankings_path) else None
            
            # Load unified dataset
            unified_path = os.path.join(session_folder, 'unified_dataset.csv')
            self.unified_dataset = pd.read_csv(unified_path) if os.path.exists(unified_path) else None
    
    # Create data handler
    data_handler = MockDataHandler(session_folder)
    
    # Test state detection
    state = detect_state(data_handler)
    print(f"Detected state: {state}")
    
    # Test population loading
    pop_data = load_population_data(state) if state else None
    if pop_data is not None:
        print(f"✅ Population data for {state}: {len(pop_data)} wards")
    else:
        print(f"❌ No population data for {state}")
    
    # Run ITN calculation
    print("\n=== Step 4: Running ITN Distribution ===")
    
    result = calculate_itn_distribution(
        data_handler,
        session_id=session_id,
        total_nets=2000000,
        avg_household_size=5.0,
        urban_threshold=30.0,
        method='composite'
    )
    
    print(f"Result status: {result['status']}")
    
    if result['status'] == 'success':
        print("✅ ITN calculation successful!")
        
        # Load and check results
        results_path = os.path.join(session_folder, 'itn_distribution_results.json')
        if os.path.exists(results_path):
            with open(results_path, 'r') as f:
                dist_results = json.load(f)
            
            print("\n=== Distribution Results ===")
            print(f"Total nets: {dist_results.get('total_nets', 0):,}")
            print(f"Total allocated: {dist_results.get('total_allocated', 0):,}")
            print(f"Coverage: {dist_results.get('coverage_percentage', 0):.1f}%")
            
            distribution = dist_results.get('distribution', [])
            print(f"Wards in distribution: {len(distribution)}")
            
            if distribution:
                allocated = sum(1 for w in distribution if w.get('nets_allocated', 0) > 0)
                has_pop = sum(1 for w in distribution if w.get('population', 0) > 0)
                has_urban = sum(1 for w in distribution if 'urban_percentage' in w)
                
                print(f"  - Wards with nets: {allocated}")
                print(f"  - Wards with population: {has_pop}")
                print(f"  - Wards with urban data: {has_urban}")
                
                # Sample first ward
                if distribution:
                    ward = distribution[0]
                    print(f"\nSample ward: {ward.get('ward_name', 'Unknown')}")
                    print(f"  - Population: {ward.get('population', 0):,}")
                    print(f"  - Nets allocated: {ward.get('nets_allocated', 0):,}")
                    print(f"  - Urban %: {ward.get('urban_percentage', 'N/A')}")
            else:
                print("⚠️ Distribution is empty!")
    else:
        print(f"❌ ITN calculation failed: {result.get('message', 'Unknown error')}")
    
    return result['status'] == 'success'

if __name__ == "__main__":
    session_id = sys.argv[1] if len(sys.argv) > 1 else '4e21ce78-66e6-4ef4-b13e-23e994846de8'
    success = test_itn_calculation(session_id)
    
    print("\n" + "="*50)
    if success:
        print("✅ ALL TESTS PASSED - ITN DISTRIBUTION WORKING!")
    else:
        print("❌ ITN DISTRIBUTION STILL HAS ISSUES")