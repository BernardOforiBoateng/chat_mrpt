#!/usr/bin/env python3
"""Check which wards are missing in the vulnerability map."""

import pandas as pd
import geopandas as gpd
import os

session_path = "instance/uploads/59b18890-638c-4c1e-862b-82a900cea3e9"

# Load the data
print("Loading data...")
tpr_df = pd.read_csv(os.path.join(session_path, "Adamawa_State_TPR_Analysis_20250724.csv"))
rankings_df = pd.read_csv(os.path.join(session_path, "analysis_vulnerability_rankings.csv"))
shp_gdf = gpd.read_file(os.path.join(session_path, "shapefile/raw.shp"))

# Get unique ward names from each dataset
tpr_wards = set(tpr_df['WardName'].unique())
ranking_wards = set(rankings_df['WardName'].unique())
shp_wards = set(shp_gdf['WardName'].unique())

print(f"\nWard counts:")
print(f"TPR wards: {len(tpr_wards)}")
print(f"Ranking wards: {len(ranking_wards)}")
print(f"Shapefile wards: {len(shp_wards)}")

# Find differences
print("\n=== Wards in TPR but not in rankings ===")
tpr_not_rankings = tpr_wards - ranking_wards
for ward in sorted(list(tpr_not_rankings))[:10]:
    print(f"  {ward}")
if len(tpr_not_rankings) > 10:
    print(f"  ... and {len(tpr_not_rankings) - 10} more")

print("\n=== Wards in rankings but not in shapefile ===")
rankings_not_shp = ranking_wards - shp_wards
for ward in sorted(list(rankings_not_shp))[:10]:
    print(f"  {ward}")
if len(rankings_not_shp) > 10:
    print(f"  ... and {len(rankings_not_shp) - 10} more")

print("\n=== Wards in shapefile but not in rankings ===")
shp_not_rankings = shp_wards - ranking_wards  
for ward in sorted(list(shp_not_rankings))[:10]:
    print(f"  {ward}")
if len(shp_not_rankings) > 10:
    print(f"  ... and {len(shp_not_rankings) - 10} more")

# Check for case sensitivity issues
print("\n=== Checking for case sensitivity issues ===")
rankings_lower = {w.lower(): w for w in ranking_wards}
shp_lower = {w.lower(): w for w in shp_wards}

case_mismatches = []
for ward_lower, ward_rankings in rankings_lower.items():
    if ward_lower in shp_lower and shp_lower[ward_lower] != ward_rankings:
        case_mismatches.append((ward_rankings, shp_lower[ward_lower]))

if case_mismatches:
    print(f"Found {len(case_mismatches)} case mismatches:")
    for r, s in case_mismatches[:5]:
        print(f"  Rankings: '{r}' vs Shapefile: '{s}'")
else:
    print("No case sensitivity issues found")

# Check which wards might be missing geometry
print("\n=== Checking for missing geometries ===")
null_geom = shp_gdf[shp_gdf.geometry.isnull()]
if len(null_geom) > 0:
    print(f"Found {len(null_geom)} wards with null geometry:")
    for _, row in null_geom.head().iterrows():
        print(f"  {row['WardName']}")
else:
    print("All wards have valid geometries")