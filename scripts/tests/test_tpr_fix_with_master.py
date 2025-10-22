#!/usr/bin/env python
"""Test the TPR join fix with the master shapefile."""

import pandas as pd
import geopandas as gpd
import sys
import os

# Add app to path
sys.path.insert(0, '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT')

from app.tpr_module.services.shapefile_extractor import ShapefileExtractor

def test_with_master():
    """Test the TPR join with master shapefile."""
    
    # Load TPR data
    tpr_data = pd.read_csv('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/TPR_analysis/Adamawa_plus.csv')
    print(f"TPR data: {len(tpr_data)} rows")
    print(f"TPR unique wards: {tpr_data['WardName'].nunique()}")
    print(f"TPR unique LGAs: {tpr_data['LGA'].nunique()}")
    
    # Load master shapefile to verify it has 226 for Adamawa
    master_path = 'www/complete_names_wards/wards.shp'
    master_gdf = gpd.read_file(master_path)
    print(f"\nMaster shapefile: {len(master_gdf)} total features")
    
    # Check Adamawa in master
    adamawa_master = master_gdf[master_gdf['StateName'].str.contains('Adamawa', case=False, na=False)]
    print(f"Adamawa in master: {len(adamawa_master)} features")
    
    # Check unique LGA+Ward combinations
    unique_master = adamawa_master[['LGAName', 'WardName']].drop_duplicates()
    print(f"Unique LGA+Ward in master: {len(unique_master)}")
    
    # Now test the extractor with our fix
    print("\n=== Testing ShapefileExtractor with fix ===")
    extractor = ShapefileExtractor(master_path)
    
    # Extract with TPR data
    output_dir = '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/test_output'
    os.makedirs(output_dir, exist_ok=True)
    
    result_path = extractor.extract_state_shapefile(
        state_name='Adamawa State',
        tpr_data=tpr_data,
        output_dir=output_dir
    )
    
    if result_path:
        # Load the result
        result_gdf = gpd.read_file(result_path)
        print(f"\n=== RESULT ===")
        print(f"Output shapefile: {len(result_gdf)} features")
        
        # Check unique LGA+Ward
        unique_result = result_gdf[['LGAName', 'WardName']].drop_duplicates()
        print(f"Unique LGA+Ward combinations: {len(unique_result)}")
        
        # Check for duplicates
        ward_counts = result_gdf.groupby(['LGAName', 'WardName']).size()
        duplicates = ward_counts[ward_counts > 1]
        
        if not duplicates.empty:
            print(f"\n⚠️ Duplicate wards found:")
            print(duplicates)
        else:
            print(f"\n✓ No duplicates found!")
            
        if len(result_gdf) == 226:
            print(f"\n✅ SUCCESS: Got exactly 226 features!")
        else:
            print(f"\n❌ ISSUE: Got {len(result_gdf)} features instead of 226")
            
    else:
        print("\n❌ FAILED: No result returned")

if __name__ == '__main__':
    test_with_master()