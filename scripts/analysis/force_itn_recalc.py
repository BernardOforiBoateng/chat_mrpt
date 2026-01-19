#!/usr/bin/env python3
"""
Force ITN recalculation with all data available
"""

import sys
import os
import json

# Set environment
os.environ['FLASK_APP'] = 'run.py'
sys.path.insert(0, '/home/ec2-user/ChatMRPT')

def force_recalc(session_id):
    """Force recalculation of ITN distribution"""
    
    # Create Flask app context
    from app import create_app
    app = create_app()
    
    with app.app_context():
        from app.analysis.itn_pipeline import calculate_itn_distribution
        from app.data import DataHandler
        
        session_folder = f'instance/uploads/{session_id}'
        print(f"Session: {session_id}")
        
        # Initialize data handler
        data_handler = DataHandler(session_folder)
        
        # Force reload all data
        data_handler._attempt_data_reload()
        
        # Load shapefile if exists
        import geopandas as gpd
        shp_dir = os.path.join(session_folder, 'shapefile')
        if os.path.exists(shp_dir):
            shp_files = [f for f in os.listdir(shp_dir) if f.endswith('.shp')]
            if shp_files:
                data_handler.shapefile_data = gpd.read_file(os.path.join(shp_dir, shp_files[0]))
                print(f"Shapefile loaded: {len(data_handler.shapefile_data)} features")
        
        # Load rankings
        import pandas as pd
        rankings_path = os.path.join(session_folder, 'analysis_vulnerability_rankings.csv')
        if os.path.exists(rankings_path):
            data_handler.vulnerability_rankings = pd.read_csv(rankings_path)
            print(f"Rankings loaded: {len(data_handler.vulnerability_rankings)} wards")
        
        # Load unified dataset
        unified_path = os.path.join(session_folder, 'unified_dataset.csv')
        if os.path.exists(unified_path):
            data_handler.unified_dataset = pd.read_csv(unified_path)
            print(f"Unified dataset: {len(data_handler.unified_dataset)} rows")
            
            # Check for urban_percentage
            if 'urban_percentage' in data_handler.unified_dataset.columns:
                print(f"✅ Urban percentage in unified dataset")
            else:
                print(f"❌ No urban percentage in unified dataset")
        
        print("\nCalculating ITN distribution...")
        
        # Force recalculation
        result = calculate_itn_distribution(
            data_handler,
            session_id=session_id,
            total_nets=2000000,
            avg_household_size=5.0,
            urban_threshold=30.0,
            method='composite'
        )
        
        print(f"Status: {result['status']}")
        
        if result['status'] == 'success':
            # Check results
            results_path = os.path.join(session_folder, 'itn_distribution_results.json')
            with open(results_path, 'r') as f:
                dist = json.load(f)
            
            print(f"\n=== SUCCESS ===")
            print(f"Wards: {len(dist.get('distribution', []))}")
            print(f"Allocated: {dist.get('total_allocated', 0):,} nets")
            print(f"Coverage: {dist.get('coverage_percentage', 0):.1f}%")
            
            # Check first ward
            if dist.get('distribution'):
                ward = dist['distribution'][0]
                print(f"\nFirst ward: {ward.get('ward_name')}")
                print(f"  Population: {ward.get('population', 0):,}")
                print(f"  Nets: {ward.get('nets_allocated', 0):,}")
        else:
            print(f"Error: {result.get('message')}")
        
        return result['status'] == 'success'

if __name__ == "__main__":
    session_id = '4e21ce78-66e6-4ef4-b13e-23e994846de8'
    success = force_recalc(session_id)
    
    if success:
        print("\n✅ ITN RECALCULATION SUCCESSFUL!")
    else:
        print("\n❌ ITN RECALCULATION FAILED")