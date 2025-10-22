"""
Transfer 2018 and 2021 NDMI/NDWI files from Google Drive to Cloud Storage
Run this in Google Colab
"""

# Cell 1: Mount Drive and authenticate
from google.colab import drive, auth
drive.mount('/content/drive')
auth.authenticate_user()

# Cell 2: Configure settings
import os
import glob

PROJECT_ID = "turing-thought-468722-g6"  # Your Google Cloud Project ID
BUCKET_NAME = "ndmi_ndwi30m"  # Your bucket name

# Set project
!gcloud config set project {PROJECT_ID}

print(f"Project: {PROJECT_ID}")
print(f"Bucket: gs://{BUCKET_NAME}/")

# Cell 3: Check what's already in bucket
print("\nChecking current bucket contents...")
!gsutil ls gs://{BUCKET_NAME}/*.tif | wc -l > /tmp/bucket_count.txt

with open('/tmp/bucket_count.txt', 'r') as f:
    current_count = f.read().strip()
    print(f"Files currently in bucket: {current_count}")

# Cell 4: Transfer 2018 files
DRIVE_FOLDER = "/content/drive/MyDrive/Nigeria_NDMI_NDWI_HLS"

print("\n" + "="*60)
print("TRANSFERRING 2018 FILES")
print("="*60)

# Find all 2018 files
files_2018 = glob.glob(f"{DRIVE_FOLDER}/*_2018_*.tif")
print(f"Found {len(files_2018)} files for 2018")

if files_2018:
    print("\nSample 2018 files:")
    for f in files_2018[:3]:
        print(f"  - {os.path.basename(f)}")
    
    # Transfer 2018 files
    print("\nStarting transfer...")
    !gsutil -m cp {DRIVE_FOLDER}/*_2018_*.tif gs://{BUCKET_NAME}/
    print("✅ 2018 files transferred")
else:
    print("❌ No 2018 files found")

# Cell 5: Transfer 2021 files
print("\n" + "="*60)
print("TRANSFERRING 2021 FILES")
print("="*60)

# Find all 2021 files
files_2021 = glob.glob(f"{DRIVE_FOLDER}/*_2021_*.tif")
print(f"Found {len(files_2021)} files for 2021")

if files_2021:
    print("\nSample 2021 files:")
    for f in files_2021[:3]:
        print(f"  - {os.path.basename(f)}")
    
    # Transfer 2021 files
    print("\nStarting transfer...")
    !gsutil -m cp {DRIVE_FOLDER}/*_2021_*.tif gs://{BUCKET_NAME}/
    print("✅ 2021 files transferred")
else:
    print("❌ No 2021 files found")

# Cell 6: Verify uploads
print("\n" + "="*60)
print("VERIFICATION")
print("="*60)

# Count files by year
print("\nFiles in bucket by year:")
for year in [2015, 2018, 2021]:
    !echo -n "  {year}: " && gsutil ls gs://{BUCKET_NAME}/*_{year}_*.tif 2>/dev/null | wc -l

# Total size
print("\nTotal bucket size:")
!gsutil du -sh gs://{BUCKET_NAME}/

# Check specific months for completeness
print("\nChecking completeness (should be 4 tiles per index per month):")
for year in [2018, 2021]:
    for month in [7, 8, 9, 10, 11, 12]:
        month_str = f"{month:02d}"
        !echo -n "  NDMI_{year}_{month_str}: " && gsutil ls gs://{BUCKET_NAME}/NDMI_{year}_{month_str}*.tif 2>/dev/null | wc -l
        !echo -n "  NDWI_{year}_{month_str}: " && gsutil ls gs://{BUCKET_NAME}/NDWI_{year}_{month_str}*.tif 2>/dev/null | wc -l

# Cell 7: Optional - Transfer remaining years (2023, 2024)
print("\n" + "="*60)
print("OPTIONAL: Transfer 2023 and 2024 files")
print("="*60)

# Check if 2023/2024 files exist
files_2023 = glob.glob(f"{DRIVE_FOLDER}/*_2023_*.tif")
files_2024 = glob.glob(f"{DRIVE_FOLDER}/*_2024_*.tif")

print(f"Found {len(files_2023)} files for 2023")
print(f"Found {len(files_2024)} files for 2024")

if files_2023 or files_2024:
    transfer = input("\nTransfer 2023 and 2024 files too? (y/n): ")
    if transfer.lower() == 'y':
        if files_2023:
            print("\nTransferring 2023...")
            !gsutil -m cp {DRIVE_FOLDER}/*_2023_*.tif gs://{BUCKET_NAME}/
            print("✅ 2023 transferred")
        
        if files_2024:
            print("\nTransferring 2024...")
            !gsutil -m cp {DRIVE_FOLDER}/*_2024_*.tif gs://{BUCKET_NAME}/
            print("✅ 2024 transferred")

# Cell 8: Summary
print("\n" + "="*60)
print("FINAL SUMMARY")
print("="*60)

!echo -n "Total files in bucket: " && gsutil ls gs://{BUCKET_NAME}/*.tif | wc -l

print("\nExpected totals:")
print("  2015: 48 files (6 months × 2 indices × 4 tiles) ✓")
print("  2018: 48 files (6 months × 2 indices × 4 tiles)")
print("  2021: 48 files (6 months × 2 indices × 4 tiles)")
print("  2023: 48 files (6 months × 2 indices × 4 tiles)")
print("  2024: 48 files (6 months × 2 indices × 4 tiles)")
print("  TOTAL: 240 files")

print("\n✅ Ready for DHS extraction in Earth Engine!")