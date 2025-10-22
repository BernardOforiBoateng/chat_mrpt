"""
Test shapefile matching to debug why identifiers aren't populated.
"""

import pandas as pd
import geopandas as gpd

# Load shapefile
print("Loading Nigerian shapefile...")
gdf = gpd.read_file('www/complete_names_wards/wards.shp')
adamawa_shp = gdf[gdf['StateName'].str.contains('Adamawa', case=False, na=False)]
print(f"Adamawa wards in shapefile: {len(adamawa_shp)}")

# Load recent TPR output
print("\nLoading TPR output...")
tpr_df = pd.read_csv('instance/uploads/test_user_session_001/Adamawa_State_Main_Analysis_20250718.csv')
print(f"Wards in TPR output: {len(tpr_df)}")

# Compare ward names
print("\nWard name comparison:")
print("First 10 TPR ward names:", list(tpr_df['WardName'].head(10)))
print("First 10 Shapefile ward names:", list(adamawa_shp['WardName'].head(10)))

# Check exact matches
tpr_wards = set(tpr_df['WardName'].dropna())
shp_wards = set(adamawa_shp['WardName'].dropna())
matches = tpr_wards.intersection(shp_wards)
print(f"\nExact matches: {len(matches)} out of {len(tpr_wards)} TPR wards")

# Show some matches
if matches:
    print("Sample matches:", list(matches)[:5])
else:
    # Try fuzzy matching
    print("\nNo exact matches! Checking for close matches...")
    from difflib import get_close_matches
    
    sample_tpr = list(tpr_wards)[:5]
    for ward in sample_tpr:
        close = get_close_matches(ward, list(shp_wards), n=1, cutoff=0.8)
        if close:
            print(f"  TPR: '{ward}' -> Shapefile: '{close[0]}'")
        else:
            print(f"  TPR: '{ward}' -> No close match")

# Check LGA names too
print("\nLGA comparison:")
tpr_lgas = set(tpr_df['LGA'].dropna())
shp_lgas = set(adamawa_shp['LGAName'].dropna())
print(f"Sample TPR LGAs: {list(tpr_lgas)[:3]}")
print(f"Sample Shapefile LGAs: {list(shp_lgas)[:3]}")