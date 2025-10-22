"""
Transfer NDMI/NDWI files from Google Drive to Cloud Storage Bucket
Run this in Google Colab
"""

# Cell 1: Mount Drive and authenticate
from google.colab import drive, auth
drive.mount('/content/drive')
auth.authenticate_user()

# Cell 2: Configure your settings
import os
import glob

PROJECT_ID = "turing-thought-468722-g6"  # Your Google Cloud Project ID
BUCKET_NAME = "ndmi_ndwi30m"  # Your bucket name

# Set project
!gcloud config set project {PROJECT_ID}

print(f"Project: {PROJECT_ID}")
print(f"Bucket: gs://{BUCKET_NAME}/")

# Cell 3: Check Drive files
DRIVE_FOLDER = "/content/drive/MyDrive/Nigeria_NDMI_NDWI_HLS"

print("\nChecking Drive folder contents...")
!ls -lh {DRIVE_FOLDER}/*.tif 2>/dev/null | head -5

# Count total files
tif_files = glob.glob(f"{DRIVE_FOLDER}/*.tif")
print(f"\nFound {len(tif_files)} TIFF files")

# Calculate total size
total_size = sum(os.path.getsize(f) for f in tif_files) / (1024**3)
print(f"Total size: {total_size:.2f} GB")

# Show some filenames to verify
print("\nSample files:")
for f in tif_files[:5]:
    print(f"  - {os.path.basename(f)}")

# Cell 4: Transfer files to Cloud Storage
print("\n" + "="*60)
print("STARTING TRANSFER TO CLOUD STORAGE")
print("This will take time for 322GB - you can let it run!")
print("="*60 + "\n")

# Use gsutil with parallel transfers (-m flag)
!gsutil -m cp {DRIVE_FOLDER}/*.tif gs://{BUCKET_NAME}/

# Cell 5: Verify upload
print("\n" + "="*60)
print("VERIFYING UPLOAD")
print("="*60 + "\n")

# List first 10 files in bucket
print("First 10 files in bucket:")
!gsutil ls gs://{BUCKET_NAME}/ | head -10

# Count files in bucket
!echo -n "Total files in bucket: " && gsutil ls gs://{BUCKET_NAME}/*.tif | wc -l

# Check total size in bucket
print("\nTotal size in bucket:")
!gsutil du -sh gs://{BUCKET_NAME}/