import pandas as pd
import geopandas as gpd
from collections import Counter

# Load the TPR analysis CSV
tpr_csv_path = "/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/instance/uploads/6e90b139-5d30-40fd-91ad-4af66fec5f00/Adamawa_State_TPR_Analysis_20250719.csv"
tpr_df = pd.read_csv(tpr_csv_path)

# Load the shapefile
shapefile_path = "/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/instance/uploads/6e90b139-5d30-40fd-91ad-4af66fec5f00/shapefile/Adamawa_State_wards.shp"
gdf = gpd.read_file(shapefile_path)

print("=== SUMMARY ===")
print(f"CSV rows: {len(tpr_df)}")
print(f"CSV unique wards: {len(tpr_df['WardName'].unique())}")
print(f"Shapefile features: {len(gdf)}")
print(f"Shapefile unique wards: {len(gdf['WardName'].unique())}")

# Get ward lists
csv_wards = set(tpr_df['WardName'].unique())
shapefile_wards = set(gdf['WardName'].unique())

# Find differences
csv_only = csv_wards - shapefile_wards
shapefile_only = shapefile_wards - csv_wards

print(f"\n=== WARD DIFFERENCES ===")
print(f"Wards in CSV but NOT in shapefile: {len(csv_only)}")
if csv_only:
    for ward in sorted(csv_only):
        # Find LGA for this ward
        lga = tpr_df[tpr_df['WardName'] == ward]['LGA'].iloc[0]
        ward_code = tpr_df[tpr_df['WardName'] == ward]['WardCode'].iloc[0]
        print(f"  - {ward} (LGA: {lga}, Code: {ward_code})")

print(f"\nWards in shapefile but NOT in CSV: {len(shapefile_only)}")
if shapefile_only:
    for ward in sorted(shapefile_only):
        # Find LGA for this ward
        lga = gdf[gdf['WardName'] == ward]['LGA'].iloc[0]
        ward_code = gdf[gdf['WardName'] == ward]['WardCode'].iloc[0]
        print(f"  - {ward} (LGA: {lga}, Code: {ward_code})")

# Check duplicates in CSV
print(f"\n=== DUPLICATES IN CSV ===")
ward_counts = Counter(tpr_df['WardName'])
csv_duplicates = {ward: count for ward, count in ward_counts.items() if count > 1}
if csv_duplicates:
    for ward, count in sorted(csv_duplicates.items()):
        # Get info about the duplicates
        dup_rows = tpr_df[tpr_df['WardName'] == ward][['WardName', 'LGA', 'WardCode']]
        print(f"\n{ward}: {count} occurrences")
        print(dup_rows.to_string(index=False))

# Check duplicates in shapefile
print(f"\n=== DUPLICATES IN SHAPEFILE ===")
shape_ward_counts = Counter(gdf['WardName'])
shape_duplicates = {ward: count for ward, count in shape_ward_counts.items() if count > 1}
if shape_duplicates:
    for ward, count in sorted(shape_duplicates.items()):
        # Get info about the duplicates
        dup_rows = gdf[gdf['WardName'] == ward][['WardName', 'LGA', 'WardCode']]
        print(f"\n{ward}: {count} occurrences")
        print(dup_rows.to_string(index=False))

# Analyze by LGA
print(f"\n=== LGA COMPARISON ===")
csv_lga_counts = tpr_df.groupby('LGA').size()
shape_lga_counts = gdf.groupby('LGA').size()

# Find LGAs with different ward counts
all_lgas = set(csv_lga_counts.index) | set(shape_lga_counts.index)
for lga in sorted(all_lgas):
    csv_count = csv_lga_counts.get(lga, 0)
    shape_count = shape_lga_counts.get(lga, 0)
    if csv_count != shape_count:
        print(f"\n{lga}:")
        print(f"  CSV: {csv_count} wards")
        print(f"  Shapefile: {shape_count} wards")
        print(f"  Difference: {csv_count - shape_count}")
        
        # Show which wards are different
        csv_lga_wards = set(tpr_df[tpr_df['LGA'] == lga]['WardName'])
        shape_lga_wards = set(gdf[gdf['LGA'] == lga]['WardName'])
        
        csv_only_lga = csv_lga_wards - shape_lga_wards
        if csv_only_lga:
            print(f"  In CSV only: {', '.join(sorted(csv_only_lga))}")
        
        shape_only_lga = shape_lga_wards - csv_lga_wards
        if shape_only_lga:
            print(f"  In shapefile only: {', '.join(sorted(shape_only_lga))}")

# Check ward codes
print(f"\n=== WARD CODE ANALYSIS ===")
csv_ward_codes = set(tpr_df['WardCode'].unique())
shape_ward_codes = set(gdf['WardCode'].unique())

codes_csv_only = csv_ward_codes - shape_ward_codes
codes_shape_only = shape_ward_codes - csv_ward_codes

if codes_csv_only:
    print(f"\nWard codes in CSV but not in shapefile: {len(codes_csv_only)}")
    for code in sorted(codes_csv_only):
        ward_info = tpr_df[tpr_df['WardCode'] == code][['WardName', 'LGA']].iloc[0]
        print(f"  {code}: {ward_info['WardName']} ({ward_info['LGA']})")

if codes_shape_only:
    print(f"\nWard codes in shapefile but not in CSV: {len(codes_shape_only)}")
    for code in sorted(codes_shape_only):
        ward_info = gdf[gdf['WardCode'] == code][['WardName', 'LGA']].iloc[0]
        print(f"  {code}: {ward_info['WardName']} ({ward_info['LGA']})")