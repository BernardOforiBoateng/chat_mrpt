#!/usr/bin/env python
"""
Test the enhanced ward matcher with Adamawa data to verify it fixes the 46 ward issue.
"""

import sys
import pandas as pd
import geopandas as gpd
from app.tpr_module.services.enhanced_ward_matcher import EnhancedWardMatcher

def test_enhanced_matcher():
    """Test the enhanced ward matcher with real Adamawa data."""
    
    print("="*70)
    print("TESTING ENHANCED WARD MATCHER")
    print("="*70)
    
    # Load the data
    print("\n1. Loading data...")
    
    # Load TPR data (has problematic ward names)
    tpr_path = 'instance/uploads/9000f9df-451d-4dd9-a4d1-2040becdf902/Adamawa_plus.csv'
    try:
        tpr_df = pd.read_csv(tpr_path)
        print(f"✓ Loaded TPR data: {len(tpr_df)} wards")
    except FileNotFoundError:
        print(f"✗ TPR file not found at {tpr_path}")
        print("Looking for alternative TPR files...")
        import glob
        tpr_files = glob.glob('instance/uploads/*/Adamawa_plus.csv')
        if tpr_files:
            tpr_path = tpr_files[0]
            tpr_df = pd.read_csv(tpr_path)
            print(f"✓ Found and loaded TPR data: {len(tpr_df)} wards from {tpr_path}")
        else:
            print("✗ No Adamawa TPR data found")
            return
    
    # Load shapefile (has correct ward names and WardCodes)
    shp_path = 'www/complete_names_wards/wards.shp'
    shp_gdf = gpd.read_file(shp_path)
    adamawa_shp = shp_gdf[shp_gdf['StateCode'] == 'AD'].copy()
    print(f"✓ Loaded shapefile: {len(adamawa_shp)} Adamawa wards")
    
    # Check initial state
    print("\n2. Initial data state:")
    print(f"   TPR wards with WardCode: {tpr_df['WardCode'].notna().sum()}/{len(tpr_df)}")
    print(f"   Shapefile wards with WardCode: {adamawa_shp['WardCode'].notna().sum()}/{len(adamawa_shp)}")
    
    # The problematic wards we identified
    problem_wards = [
        'Hosheri-Zum', 'Wagga', 'Mafarang', 'Futudou/Futuless', 
        'Garta/Ghumchi', 'Bolki', 'Mayo-Ine', 'Uki-Tuki', 
        'Wuro-Bokki', 'Girei I', 'Girei II', "Ga'anda", 'Gabun'
    ]
    
    print(f"\n3. Testing {len(problem_wards)} known problematic wards:")
    print("-"*50)
    
    # Initialize matcher
    matcher = EnhancedWardMatcher()
    
    # Test individual problematic wards
    for ward in problem_wards:
        # Check if this ward exists in TPR data
        tpr_matches = tpr_df[tpr_df['WardName'].str.contains(ward.replace("'", "").split('/')[0], case=False, na=False)]
        
        if len(tpr_matches) > 0:
            tpr_ward = tpr_matches.iloc[0]['WardName']
            lga = tpr_matches.iloc[0].get('LGA', None)
            
            # Try to match with shapefile
            shp_candidates = adamawa_shp['WardName'].dropna().unique().tolist()
            match = matcher.find_best_match(tpr_ward, shp_candidates, lga)
            
            if match:
                # Find the WardCode for the matched ward
                ward_code = adamawa_shp[adamawa_shp['WardName'] == match[0]]['WardCode'].iloc[0]
                print(f"✓ '{tpr_ward}' → '{match[0]}' (score: {match[1]:.2f}, WardCode: {ward_code})")
            else:
                print(f"✗ '{tpr_ward}' → NO MATCH FOUND")
        else:
            print(f"? '{ward}' not found in TPR data")
    
    print("\n4. Testing batch matching with full dataset:")
    print("-"*50)
    
    # Test batch matching
    mapping = matcher.match_wards_batch(
        tpr_wards=tpr_df,
        shapefile_wards=adamawa_shp,
        ward_col_tpr='WardName',
        ward_col_shp='WardName',
        lga_col='LGA' if 'LGA' in tpr_df.columns else 'LGAName'
    )
    
    print(f"Matched {len(mapping)}/{len(tpr_df)} wards ({len(mapping)/len(tpr_df)*100:.1f}%)")
    
    # Check how many of the problematic wards were matched
    matched_problems = 0
    for ward in problem_wards:
        variants = matcher.generate_variants(ward)
        for variant in variants:
            if variant in mapping or any(variant in k for k in mapping.keys()):
                matched_problems += 1
                break
    
    print(f"Matched {matched_problems}/{len(problem_wards)} known problematic wards")
    
    # Show statistics
    stats = matcher.get_statistics()
    print(f"\n5. Matcher statistics:")
    print(f"   Cache entries: {stats['cache_entries']}")
    print(f"   Failed matches: {stats['failed_matches']}")
    print(f"   Pattern rules: {stats['pattern_rules']}")
    
    if stats['examples_failed']:
        print(f"   Examples of failed matches: {stats['examples_failed']}")
    
    # Test if WardCodes would be preserved
    print("\n6. Testing WardCode preservation:")
    print("-"*50)
    
    # Apply the mapping to TPR data
    tpr_mapped = tpr_df.copy()
    tpr_mapped['original_ward'] = tpr_mapped['WardName']
    tpr_mapped['mapped_ward'] = tpr_mapped['WardName'].map(lambda x: mapping.get(x, x))
    
    # Merge with shapefile to get WardCodes
    merged = tpr_mapped.merge(
        adamawa_shp[['WardName', 'WardCode']],
        left_on='mapped_ward',
        right_on='WardName',
        how='left',
        suffixes=('_tpr', '_shp')
    )
    
    # Check how many got WardCodes
    if 'WardCode' in merged.columns:
        has_wardcode = merged['WardCode'].notna().sum()
    elif 'WardCode_shp' in merged.columns:
        has_wardcode = merged['WardCode_shp'].notna().sum()
        merged['WardCode'] = merged['WardCode_shp']  # Use the shapefile WardCode
    else:
        print("Warning: WardCode column not found in merged data")
        print(f"Available columns: {list(merged.columns)}")
        has_wardcode = 0
    
    print(f"After mapping and merging:")
    print(f"   Wards with WardCode: {has_wardcode}/{len(merged)} ({has_wardcode/len(merged)*100:.1f}%)")
    
    # Show which wards still don't have WardCodes
    missing_wardcode = merged[merged['WardCode'].isna()]
    if len(missing_wardcode) > 0:
        print(f"\n   Wards still missing WardCode ({len(missing_wardcode)}):")
        for idx, row in missing_wardcode.head(10).iterrows():
            print(f"      - {row['original_ward']} → {row['mapped_ward']}")
    
    print("\n" + "="*70)
    if has_wardcode >= len(merged) - 5:  # Allow for up to 5 unmatched
        print("SUCCESS: Enhanced matcher significantly improves ward matching!")
    else:
        print(f"NEEDS IMPROVEMENT: Still {len(merged) - has_wardcode} wards without WardCodes")
    print("="*70)

if __name__ == "__main__":
    test_enhanced_matcher()