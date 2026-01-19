#!/usr/bin/env python3
"""
Test ITN distribution with detailed debugging
"""

import sys
import os
import json
import warnings
warnings.filterwarnings('ignore')

# Set environment
os.environ['FLASK_APP'] = 'run.py'
sys.path.insert(0, '/home/ec2-user/ChatMRPT')

def test_itn_detailed(session_id):
    """Test ITN with detailed output"""
    
    from app import create_app
    app = create_app()
    
    with app.app_context():
        from app.analysis.itn_pipeline import calculate_itn_distribution
        from app.data import DataHandler
        import pandas as pd
        import geopandas as gpd
        
        session_folder = f'instance/uploads/{session_id}'
        print(f"Session: {session_id}")
        
        # Initialize data handler
        data_handler = DataHandler(session_folder)
        
        # Load data
        data_handler._attempt_data_reload()
        data_handler.load_session_state()
        
        # Load shapefile
        shp_dir = os.path.join(session_folder, 'shapefile')
        if os.path.exists(shp_dir):
            shp_files = [f for f in os.listdir(shp_dir) if f.endswith('.shp')]
            if shp_files:
                data_handler.shapefile_data = gpd.read_file(os.path.join(shp_dir, shp_files[0]))
                print(f"✅ Shapefile loaded: {len(data_handler.shapefile_data)} features")
        
        # Load rankings
        rankings_path = os.path.join(session_folder, 'analysis_vulnerability_rankings.csv')
        if os.path.exists(rankings_path):
            data_handler.vulnerability_rankings = pd.read_csv(rankings_path)
            print(f"✅ Rankings loaded: {len(data_handler.vulnerability_rankings)} wards")
        
        # Load unified dataset
        unified_path = os.path.join(session_folder, 'unified_dataset.csv')
        if os.path.exists(unified_path):
            data_handler.unified_dataset = pd.read_csv(unified_path)
            print(f"✅ Unified dataset: {len(data_handler.unified_dataset)} rows")
            
            # Check for urban_percentage
            urban_cols = [col for col in data_handler.unified_dataset.columns if 'urban' in col.lower()]
            print(f"   Urban columns: {urban_cols}")
            
            if 'urban_percentage' in data_handler.unified_dataset.columns:
                non_null = data_handler.unified_dataset['urban_percentage'].notna().sum()
                print(f"   urban_percentage: {non_null}/{len(data_handler.unified_dataset)} non-null")
        
        print("\n=== Running ITN Distribution ===")
        
        # Run with debug output
        result = calculate_itn_distribution(
            data_handler,
            session_id=session_id,
            total_nets=2000000,
            avg_household_size=5.0,
            urban_threshold=30.0,
            method='composite'
        )
        
        print(f"\nStatus: {result['status']}")
        
        if result['status'] == 'success':
            # Check the results file directly
            results_path = os.path.join(session_folder, 'itn_distribution_results.json')
            if os.path.exists(results_path):
                with open(results_path, 'r') as f:
                    dist = json.load(f)
                
                print(f"\n=== ITN Results ===")
                print(f"Total nets: {dist.get('total_nets', 0):,}")
                print(f"Allocated: {dist.get('stats', {}).get('allocated', 0):,}")
                print(f"Coverage: {dist.get('stats', {}).get('coverage_percent', 0):.1f}%")
                
                # Check prioritized wards
                prioritized = dist.get('prioritized', [])
                print(f"\nPrioritized wards: {len(prioritized)}")
                if prioritized:
                    # Show first ward
                    ward = prioritized[0]
                    print(f"\nFirst ward details:")
                    print(f"  Name: {ward.get('WardName', 'Unknown')}")
                    print(f"  Population: {ward.get('Population', 0):,}")
                    print(f"  Nets allocated: {ward.get('nets_allocated', 0):,}")
                    print(f"  Urban %: {ward.get('urbanPercentage', ward.get('urban_percentage', 'N/A'))}")
                else:
                    print("⚠️ No prioritized wards in results!")
                
                # Check distribution
                distribution = dist.get('distribution')
                if distribution:
                    print(f"\nDistribution array: {len(distribution)} wards")
                else:
                    print("⚠️ No distribution array in results!")
        else:
            print(f"Error: {result.get('message', 'Unknown error')}")
        
        return result['status'] == 'success'

if __name__ == "__main__":
    session_id = '4e21ce78-66e6-4ef4-b13e-23e994846de8'
    success = test_itn_detailed(session_id)
    
    print("\n" + "="*50)
    if success:
        print("✅ ITN WORKING!")
    else:
        print("❌ ITN FAILED")