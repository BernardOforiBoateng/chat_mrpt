import pandas as pd
import geopandas as gpd

# Load the data
tpr_csv_path = "/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/instance/uploads/6e90b139-5d30-40fd-91ad-4af66fec5f00/Adamawa_State_TPR_Analysis_20250719.csv"
tpr_df = pd.read_csv(tpr_csv_path)

shapefile_path = "/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/instance/uploads/6e90b139-5d30-40fd-91ad-4af66fec5f00/shapefile/Adamawa_State_wards.shp"
gdf = gpd.read_file(shapefile_path)

print("=== THE 3 EXTRA WARDS IN CSV ===")
print("\nThese are the duplicate ward entries that cause the count to be 229 instead of 226:\n")

# Find duplicates in CSV
duplicated_wards = tpr_df[tpr_df.duplicated(subset=['WardName'], keep=False)].sort_values(['WardName', 'WardCode'])

for ward in duplicated_wards['WardName'].unique():
    ward_data = duplicated_wards[duplicated_wards['WardName'] == ward]
    print(f"\n{ward} (appears {len(ward_data)} times):")
    print(ward_data[['WardName', 'LGA', 'WardCode', 'TPR', 'Tested', 'Positive']].to_string(index=False))

print("\n\n=== VERIFICATION ===")
print(f"Total CSV rows: {len(tpr_df)}")
print(f"Unique wards in CSV: {len(tpr_df['WardName'].unique())}")
print(f"Number of duplicate rows: {len(duplicated_wards)}")
print(f"Expected if we remove duplicates: {len(tpr_df) - len(duplicated_wards)/2} rows")

# Check if these wards exist in shapefile
print("\n\n=== CHECKING SHAPEFILE FOR THESE WARDS ===")
for ward in ['Nassarawo', 'Ribadu', 'Yelwa']:
    shape_matches = gdf[gdf['WardName'] == ward]
    print(f"\n{ward} in shapefile: {len(shape_matches)} occurrences")
    if len(shape_matches) > 0:
        print(shape_matches[['WardName', 'LGA', 'WardCode']].drop_duplicates().to_string(index=False))

# Let's also check the ward codes
print("\n\n=== WARD CODE ANALYSIS FOR DUPLICATES ===")
for ward in ['Nassarawo', 'Ribadu', 'Yelwa']:
    csv_codes = tpr_df[tpr_df['WardName'] == ward]['WardCode'].unique()
    print(f"\n{ward} WardCodes in CSV: {csv_codes}")
    
    shape_ward = gdf[gdf['WardName'] == ward]
    if len(shape_ward) > 0:
        shape_codes = shape_ward['WardCode'].unique()
        print(f"{ward} WardCodes in shapefile: {shape_codes}")

# Final summary
print("\n\n=== FINAL ANSWER ===")
print("The 3 extra wards in the CSV (making it 229 instead of 226) are:")
print("\n1. Nassarawo (duplicate entry with codes ADSGYL09 and ADSYLN09)")
print("2. Ribadu (duplicate entry with codes ADSFUR08 and ADSMWA10)")  
print("3. Yelwa (duplicate entry with codes ADSMUB11 and ADSYLN11)")
print("\nThese appear to be data quality issues where the same ward was entered twice with different ward codes.")