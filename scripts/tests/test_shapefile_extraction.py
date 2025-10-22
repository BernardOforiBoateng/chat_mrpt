#!/usr/bin/env python3
"""
Test Shapefile Extraction from Nigeria Master File
"""

import os
import sys
import geopandas as gpd

# Add app to path
sys.path.insert(0, '.')

def test_nigeria_shapefile():
    """Test loading and filtering Nigeria master shapefile"""
    
    print("=" * 60)
    print("TESTING NIGERIA SHAPEFILE EXTRACTION")
    print("=" * 60)
    
    shapefile_path = 'www/complete_names_wards/wards.shp'
    
    # Check if file exists
    if not os.path.exists(shapefile_path):
        print(f"❌ Shapefile not found at: {shapefile_path}")
        return False
    
    print(f"✅ Found shapefile: {shapefile_path}")
    
    try:
        # Load shapefile
        print("\n📊 Loading Nigeria master shapefile...")
        master_gdf = gpd.read_file(shapefile_path)
        
        print(f"✅ Loaded {len(master_gdf)} wards")
        print(f"   CRS: {master_gdf.crs}")
        print(f"   Columns: {list(master_gdf.columns)}")
        
        # Check unique states
        states = master_gdf['StateName'].unique()
        print(f"\n🌍 Found {len(states)} unique states")
        print(f"   Sample states: {list(states[:10])}")
        
        # Test filtering for Adamawa
        print("\n🔍 Testing state filtering for Adamawa...")
        adamawa_gdf = master_gdf[master_gdf['StateName'] == 'Adamawa']
        
        if adamawa_gdf.empty:
            # Try case variations
            adamawa_gdf = master_gdf[master_gdf['StateName'].str.lower() == 'adamawa']
        
        if not adamawa_gdf.empty:
            print(f"✅ Found {len(adamawa_gdf)} wards in Adamawa")
            
            # Check ward names
            ward_names = adamawa_gdf['WardName'].head(10).tolist()
            print(f"   Sample ward names: {ward_names}")
            
            # Check codes
            if 'WardCode' in adamawa_gdf.columns:
                print(f"   ✅ WardCode column exists")
                sample_codes = adamawa_gdf['WardCode'].head(3).tolist()
                print(f"      Sample codes: {sample_codes}")
            else:
                print(f"   ⚠️ WardCode column not found")
            
            if 'StateCode' in adamawa_gdf.columns:
                state_codes = adamawa_gdf['StateCode'].unique()
                print(f"   ✅ StateCode: {state_codes}")
            
            # Check LGAs
            lgas = adamawa_gdf['LGAName'].unique() if 'LGAName' in adamawa_gdf.columns else []
            print(f"   Found {len(lgas)} LGAs in Adamawa")
            if lgas.any():
                print(f"      Sample LGAs: {list(lgas[:5])}")
        else:
            print(f"❌ No wards found for Adamawa")
            print(f"   Available state names: {list(states[:20])}")
            return False
        
        # Test Kwara
        print("\n🔍 Testing state filtering for Kwara...")
        kwara_gdf = master_gdf[master_gdf['StateName'] == 'Kwara']
        if not kwara_gdf.empty:
            print(f"✅ Found {len(kwara_gdf)} wards in Kwara")
        else:
            print(f"⚠️ No wards found for Kwara")
        
        # Test Osun
        print("\n🔍 Testing state filtering for Osun...")
        osun_gdf = master_gdf[master_gdf['StateName'] == 'Osun']
        if not osun_gdf.empty:
            print(f"✅ Found {len(osun_gdf)} wards in Osun")
        else:
            print(f"⚠️ No wards found for Osun")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading shapefile: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ward_matching():
    """Test ward name matching between TPR and shapefile"""
    
    print("\n" + "=" * 60)
    print("TESTING WARD NAME MATCHING")
    print("=" * 60)
    
    # Load TPR data
    import pandas as pd
    from app.core.tpr_utils import normalize_ward_name
    
    tpr_file = 'www/tpr_data_by_state/ad_Adamawa_State_TPR_LLIN_2024.xlsx'
    
    try:
        # Load TPR data
        tpr_df = pd.read_excel(tpr_file)
        tpr_wards = tpr_df['WardName'].unique()
        print(f"✅ Loaded {len(tpr_wards)} unique wards from TPR data")
        
        # Normalize TPR ward names
        tpr_normalized = {normalize_ward_name(w) for w in tpr_wards}
        print(f"   Sample TPR wards (normalized): {list(tpr_normalized)[:5]}")
        
        # Load shapefile
        shapefile_path = 'www/complete_names_wards/wards.shp'
        master_gdf = gpd.read_file(shapefile_path)
        adamawa_gdf = master_gdf[master_gdf['StateName'] == 'Adamawa']
        
        if not adamawa_gdf.empty:
            shapefile_wards = adamawa_gdf['WardName'].unique()
            print(f"✅ Found {len(shapefile_wards)} wards in Adamawa shapefile")
            
            # Normalize shapefile ward names
            shapefile_normalized = {normalize_ward_name(w) for w in shapefile_wards}
            print(f"   Sample shapefile wards (normalized): {list(shapefile_normalized)[:5]}")
            
            # Find matches
            matches = tpr_normalized.intersection(shapefile_normalized)
            print(f"\n📊 Matching Results:")
            print(f"   Matched: {len(matches)}/{len(tpr_normalized)} ({len(matches)/len(tpr_normalized)*100:.1f}%)")
            
            # Find unmatched
            unmatched_tpr = tpr_normalized - shapefile_normalized
            if unmatched_tpr:
                print(f"   Unmatched TPR wards: {list(unmatched_tpr)[:5]}")
            
            # Try fuzzy matching for unmatched
            if unmatched_tpr:
                from difflib import get_close_matches
                print("\n🔍 Trying fuzzy matching for unmatched wards...")
                
                fuzzy_matched = 0
                for ward in list(unmatched_tpr)[:5]:  # Test first 5
                    close_matches = get_close_matches(ward, shapefile_normalized, n=1, cutoff=0.8)
                    if close_matches:
                        print(f"   '{ward}' → '{close_matches[0]}'")
                        fuzzy_matched += 1
                
                print(f"   Fuzzy matched: {fuzzy_matched} additional wards")
            
            return len(matches) > 0
        else:
            print("❌ No Adamawa wards in shapefile")
            return False
            
    except Exception as e:
        print(f"❌ Error in ward matching: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Starting Shapefile Tests\n")
    
    # Run tests
    shapefile_passed = test_nigeria_shapefile()
    matching_passed = test_ward_matching()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Nigeria Shapefile: {'✅ PASSED' if shapefile_passed else '❌ FAILED'}")
    print(f"Ward Matching: {'✅ PASSED' if matching_passed else '❌ FAILED'}")
    
    all_passed = shapefile_passed and matching_passed
    
    print("\n" + ("✅ ALL TESTS PASSED!" if all_passed else "❌ SOME TESTS FAILED"))
    
    sys.exit(0 if all_passed else 1)