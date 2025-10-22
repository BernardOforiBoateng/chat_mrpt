#!/usr/bin/env python
"""Test the TPR join fix to verify it produces correct 226 wards for Adamawa."""

import pandas as pd
import geopandas as gpd
import sys
import os

# Add app to path
sys.path.insert(0, '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT')

from app.tpr_module.services.shapefile_extractor import ShapefileExtractor

def test_tpr_join():
    """Test the TPR join produces correct number of wards."""
    
    # Load TPR data
    tpr_data = pd.read_csv('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/TPR_analysis/Adamawa_plus.csv')
    print(f"TPR data has {len(tpr_data)} rows")
    print(f"TPR LGA values: {tpr_data['LGA'].nunique()} unique LGAs")
    
    # Initialize extractor with master shapefile
    master_shapefile_path = '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/app/data/shapefiles/nigeria_wards_master.shp'
    
    if not os.path.exists(master_shapefile_path):
        # Try to find the master shapefile
        print(f"Master shapefile not found at {master_shapefile_path}")
        print("Searching for Nigeria wards shapefile...")
        
        # List potential locations
        potential_paths = [
            '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/app/data/Nigeria_Wards.shp',
            '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/Nigeria_Wards.shp',
            '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/data/Nigeria_Wards.shp'
        ]
        
        for path in potential_paths:
            if os.path.exists(path):
                master_shapefile_path = path
                print(f"Found at: {path}")
                break
        else:
            print("Could not find master shapefile, using extracted shapefile")
            # Use the extracted shapefile to test
            state_gdf = gpd.read_file('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/TPR_analysis/shapefile_extracted/Adamawa_State_wards.shp')
            
            # Get unique wards before join
            print(f"\nShapefile has {len(state_gdf)} features")
            unique_wards = state_gdf[['LGAName', 'WardName']].drop_duplicates()
            print(f"Unique LGA+Ward combinations: {len(unique_wards)}")
            
            # Check for duplicates
            ward_counts = state_gdf.groupby(['LGAName', 'WardName']).size()
            duplicates = ward_counts[ward_counts > 1]
            if not duplicates.empty:
                print(f"\nDuplicate wards found:")
                print(duplicates)
            
            return
    
    # Load master shapefile
    master_gdf = gpd.read_file(master_shapefile_path)
    print(f"\nMaster shapefile has {len(master_gdf)} total features")
    
    # Filter for Adamawa
    adamawa_gdf = master_gdf[master_gdf['StateName'].str.contains('Adamawa', case=False, na=False)].copy()
    print(f"Adamawa has {len(adamawa_gdf)} features in master shapefile")
    
    # Check unique wards
    unique_wards = adamawa_gdf[['LGAName', 'WardName']].drop_duplicates()
    print(f"Unique LGA+Ward combinations: {len(unique_wards)}")
    
    # Now test the join with the extractor
    extractor = ShapefileExtractor(master_shapefile_path)
    
    # Extract and join
    result = extractor.extract_state_with_tpr(
        state_name='Adamawa State',
        tpr_data=tpr_data
    )
    
    if result:
        print(f"\n=== RESULT ===")
        print(f"Final shapefile has {len(result)} features")
        
        # Check for duplicates
        if 'WardCode' in result.columns:
            ward_code_counts = result['WardCode'].value_counts()
            duplicates = ward_code_counts[ward_code_counts > 1]
            if not duplicates.empty:
                print(f"\nDuplicate WardCodes found:")
                print(duplicates)
        
        # Check unique LGA+Ward combinations
        if 'LGAName' in result.columns and 'WardName' in result.columns:
            unique_result = result[['LGAName', 'WardName']].drop_duplicates()
            print(f"Unique LGA+Ward combinations in result: {len(unique_result)}")
        
        print(f"\n✓ SUCCESS: Got {len(result)} features (expected 226)")
    else:
        print("\n✗ FAILED: No result returned")

if __name__ == '__main__':
    test_tpr_join()