#!/usr/bin/env python3
"""Complete test of ITN distribution planning with proper state detection."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import geopandas as gpd
from app.analysis.itn_pipeline import calculate_itn_distribution
from app.models.data_handler import DataHandler

def test_complete_itn():
    """Test ITN distribution with complete setup."""
    
    session_id = "59b18890-638c-4c1e-862b-82a900cea3e9"
    
    print("Complete ITN Distribution Planning Test")
    print("=" * 60)
    
    # Create a proper DataHandler with all necessary data
    print("\n1. Setting up DataHandler with Adamawa data...")
    data_handler = DataHandler(session_id)
    
    # Load the data files
    try:
        # Load CSV data
        csv_path = f"instance/uploads/{session_id}/raw_data.csv"
        if os.path.exists(csv_path):
            data_handler.csv_data = pd.read_csv(csv_path)
            print(f"   ✓ Loaded CSV data: {len(data_handler.csv_data)} rows")
        
        # Load shapefile data
        shp_path = f"instance/uploads/{session_id}/shapefile"
        if os.path.exists(shp_path):
            shp_file = os.path.join(shp_path, "raw.shp")
            if os.path.exists(shp_file):
                data_handler.shapefile_data = gpd.read_file(shp_file)
                print(f"   ✓ Loaded shapefile data: {len(data_handler.shapefile_data)} features")
                
                # Check for state code in shapefile
                if 'ADM0_CODE' in data_handler.shapefile_data.columns:
                    state_code = data_handler.shapefile_data['ADM0_CODE'].iloc[0]
                    print(f"   ✓ Detected state code: {state_code}")
        
        # Load unified dataset
        unified_path = f"instance/uploads/{session_id}/unified_dataset.csv"
        if os.path.exists(unified_path):
            data_handler.unified_dataset = pd.read_csv(unified_path)
            print(f"   ✓ Loaded unified dataset: {len(data_handler.unified_dataset)} rows")
            print(f"   Columns: {list(data_handler.unified_dataset.columns)[:10]}...")
        
        # Load vulnerability rankings
        rankings_path = f"instance/uploads/{session_id}/analysis_vulnerability_rankings.csv"
        if os.path.exists(rankings_path):
            data_handler.vulnerability_rankings = pd.read_csv(rankings_path)
            print(f"   ✓ Loaded vulnerability rankings: {len(data_handler.vulnerability_rankings)} wards")
            
    except Exception as e:
        print(f"   ✗ Error loading data: {str(e)}")
        return
    
    # Test ITN distribution
    print("\n2. Running ITN distribution calculation...")
    try:
        result = calculate_itn_distribution(
            data_handler=data_handler,
            session_id=session_id,
            total_nets=10000,
            avg_household_size=5.0,
            urban_threshold=30.0,
            method='composite'
        )
        
        if result['status'] == 'success':
            print("   ✓ ITN distribution calculation successful!")
            stats = result['stats']
            print(f"\n   Distribution Summary:")
            print(f"   - Total nets available: {stats['total_nets']:,}")
            print(f"   - Nets allocated: {stats['allocated']:,}")
            print(f"   - Remaining nets: {stats['remaining']:,}")
            print(f"   - Population covered: {stats['covered_population']:,}")
            print(f"   - Coverage percentage: {stats['coverage_percent']}%")
            print(f"   - Prioritized rural wards: {stats['prioritized_wards']}")
            print(f"   - Additional urban wards: {stats['reprioritized_wards']}")
            
            # Check if map was generated
            if 'map_path' in result and result['map_path']:
                print(f"\n   ✓ Map generated: {result['map_path']}")
            
            # Show top priority wards
            if 'prioritized' in result and result['prioritized'] is not None:
                print(f"\n   Top 5 Priority Wards:")
                top_wards = result['prioritized'].nlargest(5, 'nets_allocated')[['WardName', 'nets_allocated', 'Population']]
                for idx, (_, ward) in enumerate(top_wards.iterrows(), 1):
                    coverage = (ward['nets_allocated'] * 1.8 / ward['Population'] * 100) if ward['Population'] > 0 else 0
                    print(f"   {idx}. {ward['WardName']} - {ward['nets_allocated']} nets ({coverage:.1f}% coverage)")
                    
        else:
            print(f"   ✗ ITN calculation failed: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ✗ Error during ITN calculation: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_complete_itn()