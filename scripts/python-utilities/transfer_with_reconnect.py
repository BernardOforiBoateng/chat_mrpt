"""
Transfer files with automatic Drive reconnection
Handles the "Transport endpoint is not connected" error
"""

# Cell 1: Initial setup
from google.colab import drive, auth
import os
import glob
import time

# Mount Drive
drive.mount('/content/drive', force_remount=True)
auth.authenticate_user()

# Cell 2: Configuration
PROJECT_ID = "turing-thought-468722-g6"
BUCKET_NAME = "ndmi_ndwi30m"

# The CORRECT folder where your files are
DRIVE_FOLDER = "/content/drive/MyDrive/Nigeria_Raster_Indices"

!gcloud config set project {PROJECT_ID}
print(f"Project: {PROJECT_ID}")
print(f"Bucket: gs://{BUCKET_NAME}/")

# Cell 3: Function to remount Drive when disconnected
def ensure_drive_mounted():
    """Check if Drive is mounted, remount if needed"""
    if not os.path.exists('/content/drive/MyDrive'):
        print("Drive disconnected, remounting...")
        drive.mount('/content/drive', force_remount=True)
        time.sleep(2)
        print("Drive remounted successfully")
    return True

# Cell 4: Transfer files in smaller batches
def transfer_batch(files, batch_size=5):
    """Transfer files in small batches to avoid disconnection"""
    total = len(files)
    transferred = 0
    failed = []
    
    for i in range(0, total, batch_size):
        batch = files[i:i+batch_size]
        
        # Ensure Drive is connected
        ensure_drive_mounted()
        
        print(f"\nBatch {i//batch_size + 1}: Transferring {len(batch)} files...")
        
        for file_path in batch:
            filename = os.path.basename(file_path)
            try:
                # Transfer single file
                !gsutil cp "{file_path}" gs://{BUCKET_NAME}/ 2>/dev/null
                transferred += 1
                print(f"  ✓ {filename}")
            except Exception as e:
                print(f"  ✗ {filename}: {str(e)[:50]}")
                failed.append(filename)
                # Try to remount if error
                ensure_drive_mounted()
        
        # Small pause between batches
        time.sleep(1)
    
    return transferred, failed

# Cell 5: Check what's already in bucket
print("\nChecking bucket contents...")
!gsutil ls gs://{BUCKET_NAME}/*.tif 2>/dev/null | wc -l > /tmp/count.txt
with open('/tmp/count.txt', 'r') as f:
    already_uploaded = int(f.read().strip())
print(f"Files already in bucket: {already_uploaded}")

# Cell 6: Get list of files to transfer
ensure_drive_mounted()

# Get all files
all_files = glob.glob(f"{DRIVE_FOLDER}/*.tif")
print(f"\nTotal files in Drive folder: {len(all_files)}")

# Get what's already uploaded
!gsutil ls gs://{BUCKET_NAME}/*.tif 2>/dev/null > /tmp/uploaded.txt
with open('/tmp/uploaded.txt', 'r') as f:
    uploaded_names = [os.path.basename(line.strip()) for line in f if line.strip()]

print(f"Files already in bucket: {len(uploaded_names)}")

# Show what's already uploaded by year
for year in [2015, 2018, 2021, 2023, 2024]:
    year_uploaded = [f for f in uploaded_names if f"_{year}_" in f]
    if year_uploaded:
        print(f"  {year}: {len(year_uploaded)} files already uploaded")

# Filter out already uploaded files
files_to_upload = [f for f in all_files if os.path.basename(f) not in uploaded_names]
print(f"\nFiles still to upload: {len(files_to_upload)}")

# Cell 7: Transfer by year
for year in [2018, 2021, 2023, 2024]:
    year_files = [f for f in files_to_upload if f"_{year}_" in f]
    
    if year_files:
        print(f"\n{'='*60}")
        print(f"TRANSFERRING {year} FILES ({len(year_files)} files)")
        print(f"{'='*60}")
        
        transferred, failed = transfer_batch(year_files, batch_size=4)
        
        print(f"\nYear {year} summary:")
        print(f"  Transferred: {transferred}")
        print(f"  Failed: {len(failed)}")
        
        if failed:
            print(f"  Failed files: {failed[:5]}...")

# Cell 8: Final verification
print("\n" + "="*60)
print("FINAL VERIFICATION")
print("="*60)

!echo -n "Total files in bucket: " && gsutil ls gs://{BUCKET_NAME}/*.tif 2>/dev/null | wc -l

print("\nFiles by year:")
for year in [2015, 2018, 2021, 2023, 2024]:
    !echo -n "  {year}: " && gsutil ls gs://{BUCKET_NAME}/*_{year}_*.tif 2>/dev/null | wc -l

print("\nBucket size:")
!gsutil du -sh gs://{BUCKET_NAME}/

# Cell 9: Retry failed files if any
print("\n" + "="*60)
print("RETRY FAILED TRANSFERS")
print("="*60)

# Check for missing files
ensure_drive_mounted()
all_files = glob.glob(f"{DRIVE_FOLDER}/*.tif")

!gsutil ls gs://{BUCKET_NAME}/*.tif 2>/dev/null > /tmp/final_uploaded.txt
with open('/tmp/final_uploaded.txt', 'r') as f:
    final_uploaded = [os.path.basename(line.strip()) for line in f if line.strip()]

still_missing = [f for f in all_files if os.path.basename(f) not in final_uploaded]

if still_missing:
    print(f"Still missing {len(still_missing)} files. Retrying...")
    transferred, failed = transfer_batch(still_missing, batch_size=2)
    print(f"Retry complete: {transferred} transferred, {len(failed)} failed")
else:
    print("✅ All files successfully transferred!")

print("\n✅ Transfer complete! Ready for DHS extraction.")