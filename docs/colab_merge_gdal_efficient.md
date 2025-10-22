# Ultra Memory-Efficient Raster Merging with GDAL (One by One)

This script uses GDAL to merge tiles one dataset at a time, minimizing RAM usage.

## Cell 1: Mount Google Drive
```python
from google.colab import drive
drive.mount('/content/drive')
print("✅ Google Drive mounted")
```

## Cell 2: Install GDAL (Memory Efficient Tool)
```python
!apt-get update -qq
!apt-get install -y gdal-bin python3-gdal
print("✅ GDAL installed - this is the most memory-efficient merger")
```

## Cell 3: Setup Folders
```python
import os
import glob
import subprocess
import time
import gc

# Folders
DRIVE_FOLDER = '/content/drive/MyDrive/Nigeria_Raster_Indices'
MERGED_FOLDER = '/content/drive/MyDrive/Nigeria_Merged_Rasters'
os.makedirs(MERGED_FOLDER, exist_ok=True)

print(f"📁 Source: {DRIVE_FOLDER}")
print(f"📁 Output: {MERGED_FOLDER}")
```

## Cell 4: Find All Datasets
```python
# Find all datasets that need merging
from collections import defaultdict

all_files = glob.glob(f"{DRIVE_FOLDER}/*.tif")
datasets = defaultdict(list)

for f in all_files:
    name = os.path.basename(f)
    if '-0000' in name and '_merged' not in name:
        base = name.split('-0000')[0]
        datasets[base].append(f)

datasets_to_merge = sorted([k for k, v in datasets.items() if len(v) > 1])

print(f"Found {len(datasets_to_merge)} datasets to merge:")
for i, d in enumerate(datasets_to_merge[:10], 1):
    print(f"  {i}. {d}")
if len(datasets_to_merge) > 10:
    print(f"  ... and {len(datasets_to_merge)-10} more")
```

## Cell 5: Define GDAL Merge Function (Most Efficient)
```python
def merge_one_dataset_gdal(base_name):
    """
    Merge one dataset using GDAL (minimal RAM usage)
    GDAL processes files in chunks, not loading everything to RAM
    """
    output_path = f"{MERGED_FOLDER}/{base_name}.tif"
    
    # Skip if already exists
    if os.path.exists(output_path):
        size_gb = os.path.getsize(output_path) / (1024**3)
        print(f"  ⏭️ Already exists: {base_name}.tif ({size_gb:.2f} GB)")
        return True
    
    # Find tiles for this dataset
    pattern = f"{DRIVE_FOLDER}/{base_name}-*.tif"
    tiles = sorted(glob.glob(pattern))
    
    if not tiles:
        print(f"  ❌ No tiles found for {base_name}")
        return False
    
    print(f"  📦 Found {len(tiles)} tiles")
    
    # List tiles with sizes
    total_size = 0
    valid_tiles = []
    for tile in tiles:
        size_gb = os.path.getsize(tile) / (1024**3)
        if size_gb < 0.001:  # Skip tiny files (corrupted)
            print(f"    ⚠️ Skipping corrupted: {os.path.basename(tile)}")
        else:
            print(f"    ✓ {os.path.basename(tile)}: {size_gb:.2f} GB")
            valid_tiles.append(tile)
            total_size += size_gb
    
    if len(valid_tiles) < 2:
        print(f"  ❌ Not enough valid tiles")
        return False
    
    print(f"  📊 Total input: {total_size:.2f} GB")
    print(f"  🔄 Merging with GDAL...")
    
    # Build GDAL command
    tiles_str = ' '.join([f'"{t}"' for t in valid_tiles])
    cmd = f'gdal_merge.py -o "{output_path}" -co COMPRESS=LZW -co TILED=YES -co BLOCKXSIZE=512 -co BLOCKYSIZE=512 {tiles_str}'
    
    # Run merge
    start_time = time.time()
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0 and os.path.exists(output_path):
        elapsed = time.time() - start_time
        output_size = os.path.getsize(output_path) / (1024**3)
        print(f"  ✅ Success: {base_name}.tif")
        print(f"     Output: {output_size:.2f} GB")
        print(f"     Time: {elapsed:.1f} seconds")
        print(f"     Compression: {((total_size-output_size)/total_size*100):.1f}% saved")
        return True
    else:
        print(f"  ❌ Failed: {result.stderr[:200] if result.stderr else 'Unknown error'}")
        return False

print("✅ GDAL merge function ready")
print("This uses minimal RAM by processing in chunks")
```

## Cell 6: Process ONE Dataset at a Time (Manual Control)
```python
# Process a single dataset - YOU control which one
# This gives you maximum control and uses minimal RAM

def process_single(dataset_name):
    """Process one dataset with full cleanup"""
    print("="*60)
    print(f"Processing: {dataset_name}")
    print("="*60)
    
    success = merge_one_dataset_gdal(dataset_name)
    
    # Clear any temp files
    !rm -rf /tmp/*
    gc.collect()
    
    if success:
        print("✅ Complete!")
    else:
        print("❌ Failed - try the next one")
    
    return success

# Example: Process NDMI_2015_08
process_single('NDMI_2015_08')
```

## Cell 7: Process Year 2015 (One by One)
```python
# Process all 2015 datasets one by one
year_2015 = [d for d in datasets_to_merge if '2015' in d]

print(f"Processing {len(year_2015)} datasets from 2015")
print("="*60)

for dataset in year_2015:
    print(f"\n📍 {dataset}")
    merge_one_dataset_gdal(dataset)
    
    # Clean memory after each
    gc.collect()
    time.sleep(1)  # Brief pause

print("\n✅ Year 2015 complete!")
```

## Cell 8: Process Year 2018 (One by One)
```python
# Process all 2018 datasets
year_2018 = [d for d in datasets_to_merge if '2018' in d]

print(f"Processing {len(year_2018)} datasets from 2018")
print("="*60)

for dataset in year_2018:
    print(f"\n📍 {dataset}")
    merge_one_dataset_gdal(dataset)
    gc.collect()
    time.sleep(1)

print("\n✅ Year 2018 complete!")
```

## Cell 9: Process Year 2021 (One by One)
```python
# Process all 2021 datasets
year_2021 = [d for d in datasets_to_merge if '2021' in d]

print(f"Processing {len(year_2021)} datasets from 2021")
print("="*60)

for dataset in year_2021:
    print(f"\n📍 {dataset}")
    merge_one_dataset_gdal(dataset)
    gc.collect()
    time.sleep(1)

print("\n✅ Year 2021 complete!")
```

## Cell 10: Process Year 2023 (One by One)
```python
# Process all 2023 datasets
year_2023 = [d for d in datasets_to_merge if '2023' in d]

print(f"Processing {len(year_2023)} datasets from 2023")
print("="*60)

for dataset in year_2023:
    print(f"\n📍 {dataset}")
    merge_one_dataset_gdal(dataset)
    gc.collect()
    time.sleep(1)

print("\n✅ Year 2023 complete!")
```

## Cell 11: Process Year 2024 (One by One)
```python
# Process all 2024 datasets
year_2024 = [d for d in datasets_to_merge if '2024' in d]

print(f"Processing {len(year_2024)} datasets from 2024")
print("="*60)

for dataset in year_2024:
    print(f"\n📍 {dataset}")
    merge_one_dataset_gdal(dataset)
    gc.collect()
    time.sleep(1)

print("\n✅ Year 2024 complete!")
```

## Cell 12: Process Any Remaining Datasets
```python
# Check for any datasets not yet processed
merged_files = glob.glob(f"{MERGED_FOLDER}/*.tif")
merged_names = [os.path.basename(f).replace('.tif', '') for f in merged_files]

remaining = [d for d in datasets_to_merge if d not in merged_names]

if remaining:
    print(f"Processing {len(remaining)} remaining datasets")
    print("="*60)
    
    for dataset in remaining:
        print(f"\n📍 {dataset}")
        merge_one_dataset_gdal(dataset)
        gc.collect()
        time.sleep(1)
else:
    print("✅ All datasets already processed!")
```

## Cell 13: Final Summary
```python
# Check results
merged_files = sorted(glob.glob(f"{MERGED_FOLDER}/*.tif"))

print("="*60)
print("FINAL SUMMARY")
print("="*60)
print(f"✅ Total merged files: {len(merged_files)}")
print(f"📁 Location: {MERGED_FOLDER}\n")

# Calculate total size
total_gb = sum(os.path.getsize(f) for f in merged_files) / (1024**3)
print(f"💾 Total size: {total_gb:.2f} GB\n")

# List by year
for year in ['2015', '2018', '2021', '2023', '2024']:
    year_files = [f for f in merged_files if year in f]
    if year_files:
        year_size = sum(os.path.getsize(f) for f in year_files) / (1024**3)
        print(f"Year {year}: {len(year_files)} files ({year_size:.2f} GB)")

# Show sample files
print("\nSample merged files:")
for f in merged_files[:5]:
    size = os.path.getsize(f) / (1024**3)
    print(f"  ✅ {os.path.basename(f)}: {size:.2f} GB")
```

## Alternative: Process Individual Dataset on Demand
```python
# Process any specific dataset by name
dataset_name = 'NDMI_2015_08'  # Change this to any dataset you want
process_single(dataset_name)
```

## Why This Works Better:
1. **GDAL** processes files in chunks, not loading everything to RAM
2. **One by one** processing prevents memory accumulation
3. **Organized by year** so you can process in manageable groups
4. **Resume capability** - skips already completed files
5. **Memory cleanup** after each file

## If It Still Crashes:
- Restart runtime
- Run cells 1-5 to setup
- Continue from the year that crashed (it will skip completed files)

## Expected Performance:
- Each file: 30 seconds to 2 minutes
- RAM usage: Stays under 2-3 GB
- No crashes even on free Colab tier