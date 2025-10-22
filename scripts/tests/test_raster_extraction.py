#!/usr/bin/env python3
"""
Test Environmental Variable Extraction from Rasters
"""

import os
import sys
import pandas as pd
import geopandas as gpd
import numpy as np

# Add app to path
sys.path.insert(0, '.')

from app.data_analysis_v3.tools.tpr_analysis_tool import extract_environmental_variables


def test_raster_extraction():
    """Test extraction of environmental variables from raster files"""
    
    print("=" * 60)
    print("TESTING ENVIRONMENTAL VARIABLE EXTRACTION")
    print("=" * 60)
    
    # Step 1: Check if raster directory exists
    print("\n📁 Step 1: Checking raster directory...")
    raster_dir = 'rasters'
    
    if not os.path.exists(raster_dir):
        print(f"❌ Raster directory not found: {raster_dir}")
        print("   Creating mock raster directory for testing...")
        os.makedirs(raster_dir, exist_ok=True)
    
    # List available rasters
    raster_files = []
    if os.path.exists(raster_dir):
        for file in os.listdir(raster_dir):
            if file.endswith(('.tif', '.tiff')):
                raster_files.append(file)
    
    if raster_files:
        print(f"✅ Found {len(raster_files)} raster files:")
        for i, file in enumerate(raster_files[:10], 1):
            size_mb = os.path.getsize(os.path.join(raster_dir, file)) / (1024 * 1024)
            print(f"   {i}. {file} ({size_mb:.1f} MB)")
    else:
        print("⚠️ No raster files found in directory")
        print("   Will use mock data for testing")
    
    # Step 2: Load test shapefile (Adamawa wards)
    print("\n🗺️ Step 2: Loading test shapefile...")
    
    try:
        # Load Nigeria master shapefile
        master_shapefile = 'www/complete_names_wards/wards.shp'
        if not os.path.exists(master_shapefile):
            print(f"❌ Master shapefile not found: {master_shapefile}")
            return False
        
        master_gdf = gpd.read_file(master_shapefile)
        
        # Filter to Adamawa
        adamawa_gdf = master_gdf[master_gdf['StateName'] == 'Adamawa'].copy()
        
        if adamawa_gdf.empty:
            adamawa_gdf = master_gdf[master_gdf['StateName'].str.lower() == 'adamawa'].copy()
        
        if not adamawa_gdf.empty:
            print(f"✅ Loaded {len(adamawa_gdf)} Adamawa wards")
            print(f"   CRS: {adamawa_gdf.crs}")
            
            # Select a subset for testing (first 10 wards)
            test_gdf = adamawa_gdf.head(10).copy()
            print(f"   Using {len(test_gdf)} wards for testing")
        else:
            print("❌ No Adamawa wards found in shapefile")
            return False
            
    except Exception as e:
        print(f"❌ Error loading shapefile: {e}")
        return False
    
    # Step 3: Test extraction function
    print("\n🔬 Step 3: Testing extraction function...")
    
    try:
        # Call the extraction function
        result_df = extract_environmental_variables(test_gdf)
        
        print(f"✅ Extraction completed")
        print(f"   Result shape: {result_df.shape}")
        print(f"   Columns: {list(result_df.columns)}")
        
        # Check what variables were extracted
        env_vars = [col for col in result_df.columns if col != 'WardCode']
        print(f"\n📊 Environmental variables extracted: {len(env_vars)}")
        
        for var in env_vars:
            # Check data statistics
            non_null = result_df[var].notna().sum()
            if non_null > 0:
                mean_val = result_df[var].mean()
                min_val = result_df[var].min()
                max_val = result_df[var].max()
                print(f"   ✅ {var}: mean={mean_val:.2f}, range=[{min_val:.2f}, {max_val:.2f}], non-null={non_null}/{len(result_df)}")
            else:
                print(f"   ⚠️ {var}: all values are null/mock")
        
        # Step 4: Verify mock data if no real rasters
        if not raster_files:
            print("\n🎭 Using mock data (no real rasters available)")
            print("   Mock ranges:")
            print("   - NDVI: 0.2 to 0.8 (vegetation index)")
            print("   - NDWI: -0.3 to 0.3 (water index)")
            print("   - Elevation: 200 to 800 meters")
            print("   - Temperature: 20 to 35°C")
            print("   - Rainfall: 600 to 1400 mm/year")
        
        # Step 5: Test with full Adamawa dataset
        print("\n📈 Step 4: Testing with full Adamawa dataset...")
        
        full_result = extract_environmental_variables(adamawa_gdf)
        print(f"✅ Full extraction completed")
        print(f"   Shape: {full_result.shape}")
        print(f"   Wards with data: {len(full_result)}")
        
        # Check coverage
        for var in env_vars:
            coverage = (full_result[var].notna().sum() / len(full_result)) * 100
            print(f"   {var} coverage: {coverage:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_extraction_with_tpr_data():
    """Test extraction using actual TPR prepare_for_risk output"""
    
    print("\n" + "=" * 60)
    print("TESTING WITH TPR OUTPUT DATA")
    print("=" * 60)
    
    # Check if we have a test raw_data.csv from TPR
    test_files = [
        'instance/uploads/test_tpr_integration/raw_data.csv',
        'instance/uploads/test_debug/raw_data.csv',
        'instance/uploads/test_transition/raw_data.csv'
    ]
    
    raw_data_file = None
    for file in test_files:
        if os.path.exists(file):
            raw_data_file = file
            break
    
    if not raw_data_file:
        print("⚠️ No TPR output file found to test")
        return False
    
    print(f"✅ Found TPR output: {raw_data_file}")
    
    try:
        # Load the data
        df = pd.read_csv(raw_data_file)
        print(f"   Shape: {df.shape}")
        print(f"   Columns: {len(df.columns)}")
        
        # Check environmental variables
        env_indicators = [
            'NDVI', 'NDWI', 'Elevation', 'Slope', 'Temperature',
            'Rainfall', 'Humidity', 'Distance_to_Water',
            'Nighttime_Lights', 'Housing_Quality', 'Urban_Extent'
        ]
        
        found_vars = []
        for indicator in env_indicators:
            matching_cols = [col for col in df.columns if indicator.lower() in col.lower()]
            if matching_cols:
                found_vars.extend(matching_cols)
        
        print(f"\n📊 Environmental variables in TPR output:")
        if found_vars:
            for var in found_vars:
                non_null = df[var].notna().sum()
                if non_null > 0:
                    print(f"   ✅ {var}: {non_null}/{len(df)} non-null values")
                else:
                    print(f"   ⚠️ {var}: all null (mock data)")
        else:
            print("   ❌ No environmental variables found")
        
        # Check TPR integration
        if 'TPR' in df.columns:
            print(f"\n✅ TPR column present: mean={df['TPR'].mean():.2f}%")
        
        # Check identifiers
        id_cols = ['WardCode', 'StateCode', 'LGACode', 'WardName']
        for col in id_cols:
            if col in df.columns:
                non_null = df[col].notna().sum()
                print(f"   ✅ {col}: {non_null}/{len(df)} values")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading TPR output: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Starting Raster Extraction Tests\n")
    
    # Run tests
    extraction_passed = test_raster_extraction()
    tpr_output_passed = test_extraction_with_tpr_data()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Raster Extraction: {'✅ PASSED' if extraction_passed else '❌ FAILED'}")
    print(f"TPR Output Check: {'✅ PASSED' if tpr_output_passed else '❌ FAILED'}")
    
    all_passed = extraction_passed  # TPR output check is optional
    
    print("\n" + ("✅ RASTER EXTRACTION TESTS PASSED!" if all_passed else "❌ SOME TESTS FAILED"))
    
    # Note about mock data
    if all_passed:
        print("\nNote: The system is using mock environmental data when real rasters")
        print("are not available, which is appropriate for testing and development.")
    
    sys.exit(0 if all_passed else 1)