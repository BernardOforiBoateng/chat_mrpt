# Ultra Memory-Efficient Raster Tile Merging using GDAL VRT

This method uses GDAL's Virtual Raster format to merge without loading data into RAM.

## Cell 1: Mount Google Drive
```python
from google.colab import drive
drive.mount('/content/drive')
```

## Cell 2: Install GDAL
```python
!apt-get update -qq
!apt-get install -qq gdal-bin python3-gdal
!pip install rasterio -q
```

## Cell 3: Setup and Check
```python
import os
import glob
import subprocess

# Your folder paths
DRIVE_FOLDER = '/content/drive/MyDrive/Nigeria_NDMI_NDWI_HLS'
MERGED_FOLDER = '/content/drive/MyDrive/Nigeria_Merged_Rasters'

# Create output folder
os.makedirs(MERGED_FOLDER, exist_ok=True)

# Check GDAL is working
result = subprocess.run(['gdalinfo', '--version'], capture_output=True, text=True)
print(f"GDAL Version: {result.stdout}")

print(f"✅ Setup complete")
print(f"📁 Input folder: {DRIVE_FOLDER}")
print(f"📁 Output folder: {MERGED_FOLDER}")
```

## Cell 4: Find All Datasets
```python
# Find all unique dataset names
all_files = glob.glob(f"{DRIVE_FOLDER}/*.tif")
dataset_names = set()

for file in all_files:
    filename = os.path.basename(file)
    # Extract base name (everything before the dash and number)
    if '-' in filename:
        base_name = filename.rsplit('-', 1)[0]
        dataset_names.add(base_name)

dataset_names = sorted(list(dataset_names))
print(f"📊 Found {len(dataset_names)} datasets to merge")

# Show first few
for i, name in enumerate(dataset_names[:5], 1):
    tiles = glob.glob(f"{DRIVE_FOLDER}/{name}-*.tif")
    print(f"{i}. {name} ({len(tiles)} tiles)")
print(f"... and {len(dataset_names)-5} more")
```

## Cell 5: Ultra Efficient Merge Function Using GDAL
```python
def merge_with_gdal_vrt(base_name):
    """Use GDAL VRT to merge without loading into memory"""
    try:
        # Find all tiles
        pattern = f"{DRIVE_FOLDER}/{base_name}-*.tif"
        tiles = sorted(glob.glob(pattern))
        
        if not tiles:
            print(f"❌ No tiles found for {base_name}")
            return False
        
        print(f"\n📍 Processing: {base_name}")
        print(f"   Found {len(tiles)} tiles:")
        for tile in tiles:
            # Check tile size
            size_mb = os.path.getsize(tile) / (1024**2)
            print(f"     - {os.path.basename(tile)}: {size_mb:.1f} MB")
        
        # Output paths
        output_tif = f"{MERGED_FOLDER}/{base_name}.tif"
        temp_vrt = f"/tmp/{base_name}.vrt"
        
        # Check if already exists
        if os.path.exists(output_tif):
            size_gb = os.path.getsize(output_tif) / (1024**3)
            print(f"   ✅ Already merged ({size_gb:.2f} GB), skipping")
            return True
        
        # Step 1: Create VRT (virtual raster) - this doesn't load data
        print(f"   Creating virtual raster...")
        vrt_cmd = ['gdalbuildvrt', temp_vrt] + tiles
        result = subprocess.run(vrt_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"   ❌ VRT creation failed: {result.stderr}")
            return False
        
        # Step 2: Convert VRT to GeoTIFF with compression
        print(f"   Writing compressed GeoTIFF...")
        translate_cmd = [
            'gdal_translate',
            '-co', 'COMPRESS=LZW',
            '-co', 'TILED=YES',
            '-co', 'BIGTIFF=YES',  # Support files >4GB
            temp_vrt,
            output_tif
        ]
        
        result = subprocess.run(translate_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"   ❌ Merge failed: {result.stderr}")
            # Clean up failed output
            if os.path.exists(output_tif):
                os.remove(output_tif)
            return False
        
        # Clean up VRT
        if os.path.exists(temp_vrt):
            os.remove(temp_vrt)
        
        # Check output
        if os.path.exists(output_tif):
            size_gb = os.path.getsize(output_tif) / (1024**3)
            print(f"   ✅ Success! Created {size_gb:.2f} GB file")
            return True
        else:
            print(f"   ❌ Output file not created")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False
```

## Cell 6: Process ONE Dataset at a Time
```python
# Let's start with just ONE dataset to test
test_dataset = dataset_names[0]  # First dataset
print(f"Testing with: {test_dataset}")

if merge_with_gdal_vrt(test_dataset):
    print("✅ Test successful! Ready to process all.")
else:
    print("❌ Test failed. Check the error above.")
```

## Cell 7: Process All One by One (Run ONLY if Cell 6 succeeds)
```python
# Process each dataset ONE AT A TIME
successful = []
failed = []

for i, dataset in enumerate(dataset_names, 1):
    print(f"\n{'='*50}")
    print(f"Dataset {i}/{len(dataset_names)}")
    
    try:
        if merge_with_gdal_vrt(dataset):
            successful.append(dataset)
        else:
            failed.append(dataset)
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        failed.append(dataset)
    
    # Show progress
    print(f"\nProgress: {i}/{len(dataset_names)} processed")
    print(f"✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")
    
    # Optional: Stop after every 10 to check memory
    if i % 10 == 0:
        print("\n⏸️  Processed 10 datasets. Check memory usage.")
        print("If memory is high, restart runtime and continue from here.")

# Final summary
print(f"\n{'='*50}")
print(f"FINAL SUMMARY")
print(f"{'='*50}")
print(f"✅ Successfully merged: {len(successful)} datasets")
print(f"❌ Failed: {len(failed)} datasets")

if failed:
    print(f"\nFailed datasets:")
    for name in failed:
        print(f"  - {name}")
```

## Cell 8: Verify Results
```python
# Check merged files
merged_files = sorted(glob.glob(f"{MERGED_FOLDER}/*.tif"))
print(f"📁 Created {len(merged_files)} merged files\n")

total_size = 0
for file in merged_files[:10]:
    size_gb = os.path.getsize(file) / (1024**3)
    total_size += size_gb
    name = os.path.basename(file)
    print(f"  {name}: {size_gb:.2f} GB")

if len(merged_files) > 10:
    print(f"  ... and {len(merged_files)-10} more")

print(f"\nTotal size (first 10): {total_size:.2f} GB")
```

## If Memory Still Crashes - Manual Batch Processing:

Run this instead of Cell 7 to process in smaller batches:

```python
# Process in VERY SMALL batches
BATCH_SIZE = 3  # Process only 3 at a time

for batch_start in range(0, len(dataset_names), BATCH_SIZE):
    batch_end = min(batch_start + BATCH_SIZE, len(dataset_names))
    batch = dataset_names[batch_start:batch_end]
    
    print(f"\n{'='*60}")
    print(f"BATCH: Processing datasets {batch_start+1} to {batch_end}")
    print(f"{'='*60}")
    
    for dataset in batch:
        print(f"\nProcessing: {dataset}")
        merge_with_gdal_vrt(dataset)
    
    print(f"\n✅ Batch complete. Datasets {batch_start+1}-{batch_end} processed.")
    print("⚠️  If memory is high, you can restart runtime now and continue with next batch")
    
    # Add a pause to let you check
    input("Press Enter to continue to next batch...")
```

## Why This is Ultra Efficient:
1. **GDAL VRT** creates a virtual raster without loading data into RAM
2. **gdal_translate** streams data directly to disk
3. **LZW compression** reduces output file size
4. **BIGTIFF** supports files larger than 4GB
5. **No Python memory usage** - all processing done by GDAL C++ libraries

## Important Notes:
- This method uses almost NO RAM because it streams data
- The VRT is just a small XML file pointing to the tiles
- GDAL handles all the heavy lifting at the C++ level
- If it still crashes, use the manual batch processing in the last cell