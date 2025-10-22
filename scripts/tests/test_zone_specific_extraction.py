#!/usr/bin/env python3
"""
Test Zone-Specific Environmental Variable Extraction
"""

import os
import sys
import pandas as pd
import geopandas as gpd
import shutil

# Add app to path
sys.path.insert(0, '.')

from app.data_analysis_v3.tools.tpr_analysis_tool import extract_environmental_variables, analyze_tpr_data
from app.core.tpr_utils import get_geopolitical_zone


def test_zone_specific_extraction():
    """Test that different zones get different variables"""
    
    print("=" * 60)
    print("TESTING ZONE-SPECIFIC VARIABLE EXTRACTION")
    print("=" * 60)
    
    # Test states from different zones
    test_states = [
        ('Adamawa', 'North-East', ['pfpr', 'housing_quality', 'evi', 'ndwi', 'soil_wetness']),
        ('Kano', 'North-West', ['pfpr', 'housing_quality', 'elevation', 'evi', 'distance_to_waterbodies', 'soil_wetness']),
        ('Kwara', 'North-Central', ['pfpr', 'nighttime_lights', 'evi', 'ndmi', 'ndwi', 'soil_wetness', 'rainfall', 'temp']),
        ('Lagos', 'South-West', ['pfpr', 'rainfall', 'elevation', 'evi', 'nighttime_lights'])
    ]
    
    # Load Nigeria shapefile
    master_shapefile = 'www/complete_names_wards/wards.shp'
    if not os.path.exists(master_shapefile):
        print(f"❌ Master shapefile not found: {master_shapefile}")
        return False
    
    master_gdf = gpd.read_file(master_shapefile)
    
    print("\n📊 Testing variable extraction for different zones:\n")
    
    all_passed = True
    
    for state_name, expected_zone, expected_vars in test_states:
        print(f"🌍 Testing {state_name} ({expected_zone}):")
        
        # Verify zone detection
        detected_zone = get_geopolitical_zone(state_name)
        if detected_zone == expected_zone:
            print(f"   ✅ Zone correctly detected: {detected_zone}")
        else:
            print(f"   ❌ Zone detection failed: Expected {expected_zone}, got {detected_zone}")
            all_passed = False
            continue
        
        # Filter to state
        state_gdf = master_gdf[master_gdf['StateName'] == state_name].copy()
        if state_gdf.empty:
            state_gdf = master_gdf[master_gdf['StateName'].str.lower() == state_name.lower()].copy()
        
        if state_gdf.empty:
            print(f"   ⚠️ No wards found for {state_name}")
            continue
        
        # Use first 5 wards for testing
        test_gdf = state_gdf.head(5).copy()
        
        # Extract variables
        env_data = extract_environmental_variables(test_gdf, state_name)
        
        # Check which variables were extracted
        extracted_cols = [col for col in env_data.columns if col != 'WardCode']
        
        print(f"   Expected {len(expected_vars)} variables: {expected_vars}")
        print(f"   Extracted {len(extracted_cols)} columns: {extracted_cols}")
        
        # Verify correct variables were extracted
        # Note: Column names might be title-cased or modified
        expected_normalized = [v.lower().replace('_', '') for v in expected_vars]
        extracted_normalized = [c.lower().replace('_', '') for c in extracted_cols]
        
        missing = []
        for exp_var in expected_normalized:
            if not any(exp_var in ext_var or ext_var in exp_var for ext_var in extracted_normalized):
                missing.append(exp_var)
        
        extra = []
        for ext_var in extracted_normalized:
            if not any(ext_var in exp_var or exp_var in ext_var for exp_var in expected_normalized):
                extra.append(ext_var)
        
        if missing:
            print(f"   ⚠️ Missing expected variables: {missing}")
        if extra:
            print(f"   ⚠️ Extra unexpected variables: {extra}")
        
        if not missing and not extra:
            print(f"   ✅ All zone-specific variables correctly extracted")
        else:
            all_passed = False
        
        print()
    
    return all_passed


def test_tpr_prepare_with_zones():
    """Test that prepare_for_risk uses zone-specific variables"""
    
    print("=" * 60)
    print("TESTING TPR PREPARE_FOR_RISK WITH ZONE VARIABLES")
    print("=" * 60)
    
    # Test with Adamawa (North-East)
    session_id = "test_zone_adamawa"
    session_folder = f"instance/uploads/{session_id}"
    
    # Clean and setup
    if os.path.exists(session_folder):
        shutil.rmtree(session_folder)
    os.makedirs(session_folder, exist_ok=True)
    
    # Copy Adamawa TPR file
    source = "www/tpr_data_by_state/ad_Adamawa_State_TPR_LLIN_2024.xlsx"
    dest = os.path.join(session_folder, "test.xlsx")
    shutil.copy(source, dest)
    
    print("\n📊 Running prepare_for_risk for Adamawa (North-East)...")
    
    # Run prepare_for_risk
    graph_state = {'session_id': session_id}
    result = analyze_tpr_data.invoke({
        "thought": "Testing zone-specific extraction",
        "action": "prepare_for_risk",
        "options": "{}",
        "graph_state": graph_state
    })
    
    # Check the output file
    raw_data_path = os.path.join(session_folder, "raw_data.csv")
    if os.path.exists(raw_data_path):
        df = pd.read_csv(raw_data_path)
        print(f"✅ Output file created with {len(df)} rows, {len(df.columns)} columns")
        
        # Check for North-East specific variables
        expected_ne_vars = ['pfpr', 'housing', 'evi', 'ndwi', 'soil']  # Partial matches
        found_vars = []
        
        for col in df.columns:
            col_lower = col.lower()
            for var in expected_ne_vars:
                if var in col_lower:
                    found_vars.append(col)
                    break
        
        print(f"\n   North-East specific variables found:")
        for var in found_vars:
            non_null = df[var].notna().sum()
            print(f"   ✅ {var}: {non_null}/{len(df)} values")
        
        # Check that North-West specific variables are NOT present
        nw_specific = ['distance_to_water', 'distancetowater']
        unwanted = []
        for col in df.columns:
            col_lower = col.lower().replace('_', '')
            if any(nw.lower().replace('_', '') in col_lower for nw in nw_specific):
                unwanted.append(col)
        
        if unwanted:
            print(f"\n   ⚠️ Found North-West variables that shouldn't be here: {unwanted}")
            return False
        else:
            print(f"\n   ✅ Correctly excluded North-West specific variables")
        
        return True
    else:
        print("❌ Output file not created")
        return False


if __name__ == "__main__":
    print("🚀 Starting Zone-Specific Extraction Tests\n")
    
    # Run tests
    zone_test_passed = test_zone_specific_extraction()
    tpr_test_passed = test_tpr_prepare_with_zones()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Zone-Specific Extraction: {'✅ PASSED' if zone_test_passed else '❌ FAILED'}")
    print(f"TPR Prepare with Zones: {'✅ PASSED' if tpr_test_passed else '❌ FAILED'}")
    
    all_passed = zone_test_passed and tpr_test_passed
    
    print("\n" + ("✅ ALL ZONE-SPECIFIC TESTS PASSED!" if all_passed else "❌ SOME TESTS FAILED"))
    
    if all_passed:
        print("\nThe system correctly selects different environmental variables")
        print("based on the geopolitical zone, ensuring scientifically-validated")
        print("analysis for each region of Nigeria.")
    
    sys.exit(0 if all_passed else 1)