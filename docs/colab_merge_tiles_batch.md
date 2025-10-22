# Google Colab Script to Merge Raster Tiles (Memory-Efficient Batch Processing)

This script merges large raster tiles in batches to avoid memory issues in Google Colab.

## Cell 1: Mount Google Drive
```python
from google.colab import drive
drive.mount('/content/drive')
print("✅ Google Drive mounted")
```

## Cell 2: Install Required Packages
```python
!pip install -q rasterio
print("✅ Rasterio installed")
```

## Cell 3: Setup Folders and Imports
```python
import os
import gc
import glob
import time
import rasterio
from rasterio.merge import merge
from collections import defaultdict

# Source folder with your tiles
DRIVE_FOLDER = '/content/drive/MyDrive/Nigeria_Raster_Indices'

# Output folder for merged files
MERGED_FOLDER = '/content/drive/MyDrive/Nigeria_Merged_Rasters'
os.makedirs(MERGED_FOLDER, exist_ok=True)

print(f"📁 Source folder: {DRIVE_FOLDER}")
print(f"📁 Output folder: {MERGED_FOLDER}")
print("✅ Folders configured")
```

## Cell 4: Scan Available Datasets
```python
# Find all files and group by dataset
all_files = glob.glob(f"{DRIVE_FOLDER}/*.tif")
datasets = defaultdict(list)

for f in all_files:
    name = os.path.basename(f)
    if '-0000' in name and '_merged' not in name:
        base = name.split('-0000')[0]
        datasets[base].append(name)

datasets_to_merge = sorted([k for k, v in datasets.items() if len(v) > 1])

print(f"Found {len(datasets_to_merge)} datasets to merge:")
print("-" * 50)

# Group by index type and year for batch processing
ndmi_datasets = [d for d in datasets_to_merge if 'NDMI' in d]
ndwi_datasets = [d for d in datasets_to_merge if 'NDWI' in d]

print(f"📊 NDMI datasets: {len(ndmi_datasets)}")
print(f"📊 NDWI datasets: {len(ndwi_datasets)}")
print(f"📊 Total: {len(datasets_to_merge)} datasets")
```

## Cell 5: Define Memory-Efficient Merge Function
```python
def merge_tiles_memory_efficient(base_name):
    """
    Merge tiles with memory management
    """
    try:
        # Find tiles
        pattern = f"{DRIVE_FOLDER}/{base_name}-*.tif"
        tiles = sorted(glob.glob(pattern))
        
        if not tiles:
            print(f"  ❌ No tiles found for {base_name}")
            return False
        
        print(f"  📦 Found {len(tiles)} tiles")
        
        # Check if already merged
        output_path = f"{MERGED_FOLDER}/{base_name}.tif"
        if os.path.exists(output_path):
            print(f"  ⏭️ Already exists, skipping")
            return True
        
        # Open tiles with error handling
        src_files = []
        for tile in tiles:
            try:
                # Check file size
                size_gb = os.path.getsize(tile) / (1024**3)
                if size_gb < 0.001:  # Skip if less than 1MB (likely corrupted)
                    print(f"    ⚠️ Skipping tiny/corrupted tile: {os.path.basename(tile)}")
                    continue
                src = rasterio.open(tile)
                src_files.append(src)
            except Exception as e:
                print(f"    ⚠️ Skipping problematic tile: {os.path.basename(tile)}")
                continue
        
        if not src_files:
            print(f"  ❌ No valid tiles to merge")
            return False
        
        # Merge
        print(f"  🔄 Merging {len(src_files)} valid tiles...")
        mosaic, out_trans = merge(src_files, method='first')
        
        # Setup output metadata
        out_meta = src_files[0].meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": out_trans,
            "compress": "lzw",
            "tiled": True,
            "blockxsize": 512,
            "blockysize": 512
        })
        
        # Write output
        with rasterio.open(output_path, "w", **out_meta) as dest:
            dest.write(mosaic)
        
        # Close all source files
        for src in src_files:
            src.close()
        
        # Clear the mosaic from memory
        del mosaic
        del out_trans
        
        # Check output size
        output_size_gb = os.path.getsize(output_path) / (1024**3)
        print(f"  ✅ Saved: {base_name}.tif ({output_size_gb:.2f} GB)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False
    finally:
        # Force garbage collection
        gc.collect()

print("✅ Memory-efficient merge function ready")
```

## Cell 6: Process NDMI Datasets (Batch 1)
```python
# Process NDMI datasets in batches
print("="*60)
print("PROCESSING NDMI DATASETS")
print("="*60)

successful = []
failed = []
batch_size = 5  # Process 5 at a time

for i in range(0, len(ndmi_datasets), batch_size):
    batch = ndmi_datasets[i:i+batch_size]
    print(f"\nBatch {i//batch_size + 1}/{(len(ndmi_datasets)-1)//batch_size + 1}")
    print("-"*40)
    
    for dataset in batch:
        print(f"\n🔄 Processing: {dataset}")
        if merge_tiles_memory_efficient(dataset):
            successful.append(dataset)
        else:
            failed.append(dataset)
    
    # Clear memory after each batch
    print("\n🧹 Clearing memory...")
    gc.collect()
    time.sleep(2)  # Give system time to clear

print(f"\n✅ NDMI Complete: {len(successful)}/{len(ndmi_datasets)} successful")
if failed:
    print(f"❌ Failed: {failed}")
```

## Cell 7: Process NDWI Datasets (Batch 2)
```python
# Process NDWI datasets in batches
print("="*60)
print("PROCESSING NDWI DATASETS")
print("="*60)

successful_ndwi = []
failed_ndwi = []
batch_size = 5  # Process 5 at a time

for i in range(0, len(ndwi_datasets), batch_size):
    batch = ndwi_datasets[i:i+batch_size]
    print(f"\nBatch {i//batch_size + 1}/{(len(ndwi_datasets)-1)//batch_size + 1}")
    print("-"*40)
    
    for dataset in batch:
        print(f"\n🔄 Processing: {dataset}")
        if merge_tiles_memory_efficient(dataset):
            successful_ndwi.append(dataset)
        else:
            failed_ndwi.append(dataset)
    
    # Clear memory after each batch
    print("\n🧹 Clearing memory...")
    gc.collect()
    time.sleep(2)  # Give system time to clear

print(f"\n✅ NDWI Complete: {len(successful_ndwi)}/{len(ndwi_datasets)} successful")
if failed_ndwi:
    print(f"❌ Failed: {failed_ndwi}")
```

## Cell 8: Process Any Failed Datasets Individually
```python
# Retry failed datasets one by one
all_failed = failed + failed_ndwi if 'failed' in locals() else []

if all_failed:
    print("="*60)
    print("RETRYING FAILED DATASETS")
    print("="*60)
    
    retry_success = []
    still_failed = []
    
    for dataset in all_failed:
        print(f"\n🔄 Retrying: {dataset}")
        
        # Extra memory cleanup before retry
        gc.collect()
        !rm -rf /tmp/*  # Clear temp files
        time.sleep(3)
        
        if merge_tiles_memory_efficient(dataset):
            retry_success.append(dataset)
        else:
            still_failed.append(dataset)
    
    print(f"\n✅ Retry successful: {len(retry_success)}")
    if still_failed:
        print(f"❌ Still failed: {still_failed}")
else:
    print("✅ No failed datasets to retry!")
```

## Cell 9: Verify Final Results
```python
# Check what was successfully created
merged_files = glob.glob(f"{MERGED_FOLDER}/*.tif")

print("="*60)
print("FINAL RESULTS")
print("="*60)
print(f"📁 Output folder: {MERGED_FOLDER}")
print(f"✅ Successfully merged: {len(merged_files)} files\n")

# List files by type
ndmi_merged = sorted([f for f in merged_files if 'NDMI' in f])
ndwi_merged = sorted([f for f in merged_files if 'NDWI' in f])

print(f"NDMI files ({len(ndmi_merged)}):")
for f in ndmi_merged[:5]:
    size_gb = os.path.getsize(f) / (1024**3)
    print(f"  ✅ {os.path.basename(f)}: {size_gb:.2f} GB")
if len(ndmi_merged) > 5:
    print(f"  ... and {len(ndmi_merged)-5} more")

print(f"\nNDWI files ({len(ndwi_merged)}):")
for f in ndwi_merged[:5]:
    size_gb = os.path.getsize(f) / (1024**3)
    print(f"  ✅ {os.path.basename(f)}: {size_gb:.2f} GB")
if len(ndwi_merged) > 5:
    print(f"  ... and {len(ndwi_merged)-5} more")

# Calculate total size
total_size = sum(os.path.getsize(f) for f in merged_files) / (1024**3)
print(f"\n📊 Total size of merged files: {total_size:.2f} GB")
```

## Cell 10: Optional - Process Specific Years Only
```python
# If memory issues persist, process just one year at a time
def process_single_year(year):
    """Process all datasets for a specific year"""
    year_datasets = [d for d in datasets_to_merge if str(year) in d]
    
    print(f"Processing {len(year_datasets)} datasets for year {year}")
    
    for dataset in year_datasets:
        print(f"\n🔄 {dataset}")
        merge_tiles_memory_efficient(dataset)
        gc.collect()  # Clear memory after each
        time.sleep(2)

# Process year by year if needed
# process_single_year(2024)
# process_single_year(2023)
# process_single_year(2021)
# process_single_year(2018)
# process_single_year(2015)
```

## Notes:
- **Batch size**: Set to 5 datasets at a time to avoid memory issues
- **Memory cleanup**: Automatic garbage collection after each batch
- **Error handling**: Skips corrupted tiles automatically
- **Resume capability**: Checks if file already exists before processing
- **Output**: Clean filenames in separate folder (e.g., `NDMI_2015_08.tif`)

## If Runtime Crashes:
1. Runtime → Restart runtime
2. Re-run Cells 1-3 (mount drive, install packages, setup)
3. Re-run Cell 4 to scan datasets
4. Continue from Cell 6/7 (it will skip already merged files)

## Expected Processing Time:
- Each dataset: 1-3 minutes
- Total time: ~2-3 hours for all 58 datasets
- Can be interrupted and resumed anytime