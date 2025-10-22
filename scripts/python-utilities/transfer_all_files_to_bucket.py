"""
Transfer ALL NDMI/NDWI files from Google Drive to Cloud Storage
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

# Cell 3: Check what's left to transfer
DRIVE_FOLDER = "/content/drive/MyDrive/Nigeria_NDMI_NDWI_HLS"

# Get all TIFF files
all_tif_files = glob.glob(f"{DRIVE_FOLDER}/*.tif")
print(f"\nTotal TIFF files in Drive: {len(all_tif_files)}")

# Check what's already in bucket
print("\nChecking what's already uploaded...")
!gsutil ls gs://{BUCKET_NAME}/*.tif > /tmp/bucket_files.txt

with open('/tmp/bucket_files.txt', 'r') as f:
    bucket_files = f.read().strip().split('\n')
    bucket_files = [os.path.basename(f) for f in bucket_files if f]

print(f"Files already in bucket: {len(bucket_files)}")

# Find files not yet uploaded
drive_basenames = [os.path.basename(f) for f in all_tif_files]
files_to_upload = [f for f in all_tif_files if os.path.basename(f) not in bucket_files]

print(f"Files left to upload: {len(files_to_upload)}")

if files_to_upload:
    total_size_gb = sum(os.path.getsize(f) for f in files_to_upload) / (1024**3)
    print(f"Total size to upload: {total_size_gb:.2f} GB")
    print("\nSample files to upload:")
    for f in files_to_upload[:5]:
        print(f"  - {os.path.basename(f)}")

# Cell 4: Transfer remaining files
if len(files_to_upload) > 0:
    print("\n" + "="*60)
    print(f"TRANSFERRING {len(files_to_upload)} REMAINING FILES")
    print("This will take time - let it run!")
    print("="*60 + "\n")
    
    # Create a temporary file list for gsutil
    with open('/tmp/files_to_upload.txt', 'w') as f:
        for file_path in files_to_upload:
            f.write(file_path + '\n')
    
    # Use gsutil with file list for better control
    !cat /tmp/files_to_upload.txt | gsutil -m cp -I gs://{BUCKET_NAME}/
    
else:
    print("\n✅ All files already uploaded!")

# Cell 5: Final verification
print("\n" + "="*60)
print("FINAL VERIFICATION")
print("="*60 + "\n")

# Count total files in bucket
!echo -n "Total files in bucket: " && gsutil ls gs://{BUCKET_NAME}/*.tif | wc -l

# Check total size
print("\nTotal size in bucket:")
!gsutil du -sh gs://{BUCKET_NAME}/

# Show breakdown by year
print("\nFiles by pattern:")
for year in [2015, 2018, 2021, 2023, 2024]:
    for index in ['NDMI', 'NDWI']:
        !echo -n "{index}_{year}_*: " && gsutil ls gs://{BUCKET_NAME}/{index}_{year}_*.tif 2>/dev/null | wc -l

# Cell 6: Test Earth Engine access
print("\n" + "="*60)
print("TEST EARTH ENGINE ACCESS")
print("="*60 + "\n")

print("Use this code in Earth Engine to test:")
print("""
// Test loading from your bucket
var testImage = ee.Image.loadGeoTIFF('gs://ndmi_ndwi30m/NDMI_2015_07-0000000000-0000000000.tif');
Map.addLayer(testImage, {min: -1, max: 1, palette: ['red', 'yellow', 'green']}, 'Test NDMI');
print('Successfully loaded from Cloud Storage!');
""")

# Cell 7: Monitor transfer progress (optional - run in a separate cell)
import time
import IPython.display as display

def monitor_upload():
    while True:
        # Count files in bucket
        !gsutil ls gs://{BUCKET_NAME}/*.tif 2>/dev/null | wc -l > /tmp/count.txt
        with open('/tmp/count.txt', 'r') as f:
            count = f.read().strip()
        
        # Get size
        !gsutil du -sh gs://{BUCKET_NAME}/ 2>/dev/null > /tmp/size.txt
        with open('/tmp/size.txt', 'r') as f:
            size = f.read().strip()
        
        display.clear_output(wait=True)
        print(f"Upload Progress:")
        print(f"Files uploaded: {count}/233")
        print(f"Total size: {size}")
        print(f"Time: {time.strftime('%H:%M:%S')}")
        
        if int(count) >= 233:
            print("\n✅ Upload complete!")
            break
        
        time.sleep(30)  # Check every 30 seconds

# Uncomment to run monitoring:
# monitor_upload()