import pandas as pd
import geopandas as gpd
from collections import Counter

# Load the TPR analysis CSV
tpr_csv_path = "/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/instance/uploads/6e90b139-5d30-40fd-91ad-4af66fec5f00/Adamawa_State_TPR_Analysis_20250719.csv"
tpr_df = pd.read_csv(tpr_csv_path)

# Load the shapefile
shapefile_path = "/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/instance/uploads/6e90b139-5d30-40fd-91ad-4af66fec5f00/shapefile/Adamawa_State_wards.shp"
gdf = gpd.read_file(shapefile_path)

print("=== TPR CSV Analysis ===")
print(f"Total rows in TPR CSV: {len(tpr_df)}")
print(f"Columns: {tpr_df.columns.tolist()}")

# Get unique wards from CSV
csv_wards = tpr_df['WardName'].unique()
print(f"\nUnique wards in CSV: {len(csv_wards)}")

# Check for duplicates in CSV
ward_counts = Counter(tpr_df['WardName'])
csv_duplicates = {ward: count for ward, count in ward_counts.items() if count > 1}
if csv_duplicates:
    print(f"\nDuplicate wards in CSV:")
    for ward, count in sorted(csv_duplicates.items()):
        print(f"  {ward}: {count} occurrences")

print("\n=== Shapefile Analysis ===")
print(f"Total features in shapefile: {len(gdf)}")
print(f"Columns: {gdf.columns.tolist()}")

# Get unique wards from shapefile - check different possible column names
ward_column = None
possible_ward_columns = ['Ward', 'WARD', 'ward', 'Ward_Name', 'WARD_NAME', 'Name', 'NAME']
for col in possible_ward_columns:
    if col in gdf.columns:
        ward_column = col
        break

if ward_column:
    shapefile_wards = gdf[ward_column].unique()
    print(f"\nUnique wards in shapefile (column '{ward_column}'): {len(shapefile_wards)}")
    
    # Check for duplicates in shapefile
    shape_ward_counts = Counter(gdf[ward_column])
    shape_duplicates = {ward: count for ward, count in shape_ward_counts.items() if count > 1}
    if shape_duplicates:
        print(f"\nDuplicate wards in shapefile:")
        for ward, count in sorted(shape_duplicates.items()):
            print(f"  {ward}: {count} occurrences")
else:
    print("\nCould not find ward column in shapefile")
    print(f"Available columns: {gdf.columns.tolist()}")
    
# Also check LGA information
if 'LGA' in tpr_df.columns:
    print(f"\n=== LGA Analysis from CSV ===")
    lga_counts = tpr_df['LGA'].value_counts()
    print(f"Number of LGAs: {len(lga_counts)}")
    print("\nWards per LGA:")
    for lga, count in lga_counts.items():
        print(f"  {lga}: {count} wards")

# Look at the first few rows of each dataset
print("\n=== Sample data from CSV ===")
print(tpr_df[['WardName', 'LGA', 'WardCode']].head(10))

if ward_column:
    print(f"\n=== Sample data from shapefile ===")
    relevant_cols = [col for col in gdf.columns if col != 'geometry']
    print(gdf[relevant_cols].head(10))