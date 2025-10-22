# Google Colab Script to Merge Raster Tiles

Copy each code block into separate cells in Google Colab.

## Cell 1: Mount Google Drive
```python
from google.colab import drive
drive.mount('/content/drive')
```

## Cell 2: Install Required Packages
```python
!pip install -q rasterio
```

## Cell 3: Setup and Explore Your Folder
```python
import os
import glob
import rasterio
from rasterio.merge import merge

# Your specific folder from the link
DRIVE_FOLDER = '/content/drive/MyDrive/Nigeria_Raster_Indices'

print(f"Checking folder: {DRIVE_FOLDER}")
print("\nFiles in your folder:")
!ls -lh "/content/drive/MyDrive/Nigeria_Raster_Indices/" | head -20
```

## Cell 4: Define Merge Function (REQUIRED - RUN THIS FIRST!)
```python
def merge_tiles_in_drive(base_name):
    """
    Merge tiles for a specific dataset
    Example: base_name = 'NDMI_2021_10'
    """
    # Find tiles
    pattern = f"{DRIVE_FOLDER}/{base_name}-*.tif"
    tiles = sorted(glob.glob(pattern))
    
    if not tiles:
        print(f"No tiles found for {base_name}")
        return
    
    print(f"Found {len(tiles)} tiles for {base_name}:")
    for t in tiles:
        size_gb = os.path.getsize(t) / (1024**3)
        print(f"  - {os.path.basename(t)}: {size_gb:.2f} GB")
    
    # Open all tiles
    src_files = [rasterio.open(t) for t in tiles]
    
    # Merge
    print("\nMerging...")
    mosaic, out_trans = merge(src_files)
    
    # Setup output
    out_meta = src_files[0].meta.copy()
    out_meta.update({
        "driver": "GTiff",
        "height": mosaic.shape[1],
        "width": mosaic.shape[2],
        "transform": out_trans,
        "compress": "lzw"
    })
    
    # Write merged file (saves in same folder with _merged suffix)
    output = f"{DRIVE_FOLDER}/{base_name}_merged.tif"
    with rasterio.open(output, "w", **out_meta) as dest:
        dest.write(mosaic)
    
    # Close sources
    for src in src_files:
        src.close()
    
    print(f"✅ Saved: {base_name}_merged.tif")
    print(f"Size: {os.path.getsize(output) / (1024**3):.2f} GB")

print("✅ Merge function defined successfully!")
print("Now you can run Cell 7 to merge all datasets")
```

## Cell 5: Merge Specific Dataset
```python
# Merge your NDMI October 2021 tiles
merge_tiles_in_drive('NDMI_2021_10')
```

## Cell 6: Scan All Datasets
```python
# Quick scan of all files
from collections import defaultdict

# Get all files
all_files = glob.glob(f"{DRIVE_FOLDER}/*.tif")

# Group by base name
datasets = defaultdict(list)
for f in all_files:
    name = os.path.basename(f)
    if '-0000' in name:
        # It's a tile
        base = name.split('-0000')[0]
        datasets[base].append(name)
    else:
        # It's a single file
        datasets[name].append(name)

# Display summary
print(f"Total files: {len(all_files)}")
print(f"Total datasets: {len(datasets)}\n")

print("Datasets found (with tile count):")
print("-" * 50)
for base_name in sorted(datasets.keys()):
    tile_count = len(datasets[base_name])
    if tile_count > 1:
        print(f"📦 {base_name}: {tile_count} tiles")
    else:
        print(f"📄 {base_name}: single file")

# Show which ones need merging
print("\n" + "=" * 50)
print("Datasets that need merging:")
datasets_to_merge = []
for base_name in sorted(datasets.keys()):
    if len(datasets[base_name]) > 1:
        print(f"  - {base_name}")
        datasets_to_merge.append(base_name)
```

## Cell 7: Merge ALL Datasets Automatically
```python
import time

print(f"Will merge {len(datasets_to_merge)} datasets\n")

# Track progress
successful = []
failed = []

# Merge each dataset
for i, dataset in enumerate(datasets_to_merge, 1):
    print(f"\n{'='*60}")
    print(f"[{i}/{len(datasets_to_merge)}] Processing {dataset}")
    print('='*60)
    
    try:
        start_time = time.time()
        merge_tiles_in_drive(dataset)
        elapsed = time.time() - start_time
        print(f"⏱️ Completed in {elapsed:.1f} seconds")
        successful.append(dataset)
    except Exception as e:
        print(f"❌ Failed: {e}")
        failed.append(dataset)

# Summary
print("\n" + "="*60)
print("MERGE COMPLETE!")
print("="*60)
print(f"✅ Successful: {len(successful)}/{len(datasets_to_merge)}")
if failed:
    print(f"❌ Failed: {failed}")
```

## Cell 8: Create New Folder and Setup Clean Merge Function
```python
# Create new folder for merged files
MERGED_FOLDER = '/content/drive/MyDrive/Nigeria_Merged_Rasters'
os.makedirs(MERGED_FOLDER, exist_ok=True)
print(f"✅ Created folder: {MERGED_FOLDER}")
```

## Cell 9: Define Clean Merge Function (Saves to New Folder)
```python
# Updated merge function - saves to new folder without _merged suffix
def merge_tiles_clean(base_name):
    """
    Merge tiles and save to separate folder with clean names
    """
    # Find tiles
    pattern = f"{DRIVE_FOLDER}/{base_name}-*.tif"
    tiles = sorted(glob.glob(pattern))
    
    if not tiles:
        print(f"No tiles found for {base_name}")
        return False
    
    print(f"Found {len(tiles)} tiles for {base_name}")
    
    # Open all tiles
    src_files = []
    for t in tiles:
        try:
            src = rasterio.open(t)
            src_files.append(src)
        except:
            print(f"  ⚠️ Skipping corrupted tile: {os.path.basename(t)}")
    
    if not src_files:
        print(f"  ❌ No valid tiles to merge")
        return False
    
    # Merge
    print("  Merging...")
    mosaic, out_trans = merge(src_files)
    
    # Setup output
    out_meta = src_files[0].meta.copy()
    out_meta.update({
        "driver": "GTiff",
        "height": mosaic.shape[1],
        "width": mosaic.shape[2],
        "transform": out_trans,
        "compress": "lzw"
    })
    
    # Save to NEW folder with CLEAN name (no _merged)
    output = f"{MERGED_FOLDER}/{base_name}.tif"
    with rasterio.open(output, "w", **out_meta) as dest:
        dest.write(mosaic)
    
    # Close sources
    for src in src_files:
        src.close()
    
    size_gb = os.path.getsize(output) / (1024**3)
    print(f"  ✅ Saved: {base_name}.tif ({size_gb:.2f} GB)")
    return True

print("✅ Clean merge function defined!")
```

## Cell 10: Merge All Datasets to New Folder
```python
# Re-run merge for all datasets to new folder
import time
from collections import defaultdict

# Find all datasets to merge again
all_files = glob.glob(f"{DRIVE_FOLDER}/*.tif")
datasets = defaultdict(list)

for f in all_files:
    name = os.path.basename(f)
    if '-0000' in name and '_merged' not in name:
        base = name.split('-0000')[0]
        datasets[base].append(name)

datasets_to_merge = [k for k, v in datasets.items() if len(v) > 1]

print(f"Will merge {len(datasets_to_merge)} datasets to new folder\n")
print(f"Output folder: {MERGED_FOLDER}\n")

successful = []
failed = []

# Merge each dataset
for i, dataset in enumerate(sorted(datasets_to_merge), 1):
    print(f"\n[{i}/{len(datasets_to_merge)}] Processing {dataset}")
    print("-" * 40)
    
    try:
        if merge_tiles_clean(dataset):
            successful.append(dataset)
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        failed.append(dataset)

# Summary
print("\n" + "="*60)
print("MERGE COMPLETE!")
print("="*60)
print(f"✅ Successful: {len(successful)}/{len(datasets_to_merge)}")
print(f"📁 Output folder: {MERGED_FOLDER}")
print(f"\nFiles saved as:")
print(f"  - NDMI_2015_08.tif (not NDMI_2015_08_merged.tif)")
print(f"  - NDWI_2021_07.tif (not NDWI_2021_07_merged.tif)")
print(f"  - etc.")

if failed:
    print(f"\n❌ Failed: {failed}")
```

## Cell 11: Verify Output
```python
# Check what was created in the new folder
merged_files = glob.glob(f"{MERGED_FOLDER}/*.tif")
print(f"Successfully created {len(merged_files)} merged files in:")
print(f"📁 {MERGED_FOLDER}\n")

print("Files created:")
for f in sorted(merged_files)[:10]:
    size_gb = os.path.getsize(f) / (1024**3)
    print(f"  ✅ {os.path.basename(f)}: {size_gb:.2f} GB")

if len(merged_files) > 10:
    print(f"  ... and {len(merged_files) - 10} more files")
```

## Alternative: Using GDAL (Faster for Large Files)

## Cell 7: Install GDAL
```python
!apt-get install -qq gdal-bin python3-gdal
```

## Cell 8: Merge with GDAL
```python
import subprocess

def gdal_merge_tiles(base_name):
    """Use GDAL to merge tiles (often faster for large files)"""
    pattern = f"{DRIVE_FOLDER}/{base_name}-*.tif"
    output = f"{DRIVE_FOLDER}/{base_name}_merged_gdal.tif"
    
    # Build command
    cmd = f'gdal_merge.py -o "{output}" -co COMPRESS=LZW {pattern}'
    
    print(f"Merging {base_name} with GDAL...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Success: {base_name}_merged_gdal.tif")
    else:
        print(f"❌ Error: {result.stderr}")

# Use GDAL for all tile groups
for base_name in tile_groups:
    gdal_merge_tiles(base_name)
```

## Cell 9: Check Results
```python
# List all merged files
print("Merged files created:")
merged_files = glob.glob(f"{DRIVE_FOLDER}/*_merged*.tif")
for f in merged_files:
    size_gb = os.path.getsize(f) / (1024**3)
    print(f"  {os.path.basename(f)}: {size_gb:.2f} GB")
```

## Instructions:
1. Open [Google Colab](https://colab.research.google.com)
2. Create a new notebook
3. Copy each code block into a separate cell
4. Run cells in order (Shift+Enter)
5. Authorize Google Drive access when prompted
6. Merged files will appear in your Drive folder

## Notes:
- The script handles files in "Nigeria HLS analysis" folder
- Automatically finds all tile groups (files with -0000 pattern)
- Creates merged files with "_merged.tif" suffix
- Uses LZW compression to reduce file size
- GDAL method (Cell 7-8) is often faster for very large files