# Simple One-by-One Raster Tile Merging for Google Colab

Copy this entire code into a Google Colab notebook and run each cell in order.

## Cell 1: Mount Google Drive
```python
from google.colab import drive
drive.mount('/content/drive')
```

## Cell 2: Install Required Libraries
```python
!pip install rasterio -q
```

## Cell 3: Import and Setup
```python
import os
import glob
import rasterio
from rasterio.merge import merge
import gc
import warnings
warnings.filterwarnings('ignore')

# Your folder paths
DRIVE_FOLDER = '/content/drive/MyDrive/Nigeria_NDMI_NDWI_HLS'
MERGED_FOLDER = '/content/drive/MyDrive/Nigeria_Merged_Rasters'

# Create output folder if it doesn't exist
os.makedirs(MERGED_FOLDER, exist_ok=True)
print(f"✅ Setup complete")
print(f"📁 Input folder: {DRIVE_FOLDER}")
print(f"📁 Output folder: {MERGED_FOLDER}")
```

## Cell 4: Get All Datasets
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
print("\nDatasets to process:")
for i, name in enumerate(dataset_names, 1):
    print(f"{i}. {name}")
```

## Cell 5: Simple Merge Function
```python
def merge_one_dataset(base_name):
    """Merge tiles for one dataset"""
    try:
        # Find all tiles for this dataset
        pattern = f"{DRIVE_FOLDER}/{base_name}-*.tif"
        tiles = sorted(glob.glob(pattern))
        
        if not tiles:
            print(f"❌ No tiles found for {base_name}")
            return False
        
        print(f"\n📍 Processing: {base_name}")
        print(f"   Found {len(tiles)} tiles")
        
        # Output path (no _merged suffix)
        output_path = f"{MERGED_FOLDER}/{base_name}.tif"
        
        # Check if already exists
        if os.path.exists(output_path):
            print(f"   ✅ Already merged, skipping")
            return True
        
        # Open all tiles
        src_files = []
        for tile in tiles:
            try:
                src = rasterio.open(tile)
                src_files.append(src)
            except Exception as e:
                print(f"   ⚠️ Cannot open tile: {os.path.basename(tile)}")
                print(f"      Error: {str(e)}")
                # Close any opened files
                for s in src_files:
                    s.close()
                return False
        
        if not src_files:
            print(f"   ❌ No valid tiles to merge")
            return False
        
        # Merge tiles
        print(f"   Merging {len(src_files)} tiles...")
        mosaic, out_trans = merge(src_files)
        
        # Copy metadata from first tile
        out_meta = src_files[0].meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": out_trans,
            "compress": "lzw"
        })
        
        # Write merged file
        print(f"   Writing merged file...")
        with rasterio.open(output_path, "w", **out_meta) as dest:
            dest.write(mosaic)
        
        # Close all source files
        for src in src_files:
            src.close()
        
        # Check file size
        file_size = os.path.getsize(output_path) / (1024**3)  # GB
        print(f"   ✅ Success! Saved {file_size:.2f} GB")
        
        # Clean up memory
        del mosaic
        gc.collect()
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False
```

## Cell 6: Process All Datasets One by One
```python
# Process each dataset
successful = []
failed = []

for i, dataset in enumerate(dataset_names, 1):
    print(f"\n{'='*50}")
    print(f"Dataset {i}/{len(dataset_names)}")
    
    if merge_one_dataset(dataset):
        successful.append(dataset)
    else:
        failed.append(dataset)
    
    # Clear memory after each merge
    gc.collect()
    
    # Show progress
    print(f"\nProgress: {i}/{len(dataset_names)} completed")
    print(f"✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")

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

## Cell 7: Verify Results
```python
# Check what we created
merged_files = glob.glob(f"{MERGED_FOLDER}/*.tif")
print(f"\n📁 Files in output folder: {len(merged_files)}")
print("\nMerged files:")
for file in sorted(merged_files)[:10]:  # Show first 10
    size = os.path.getsize(file) / (1024**3)  # GB
    name = os.path.basename(file)
    print(f"  {name}: {size:.2f} GB")

if len(merged_files) > 10:
    print(f"  ... and {len(merged_files) - 10} more files")
```

## Instructions:
1. Open Google Colab
2. Create a new notebook
3. Copy each cell above into separate code cells
4. Run each cell in order (1 through 7)
5. The script will process each dataset one at a time
6. If it fails on any dataset, it will continue with the next one
7. You'll get a summary at the end showing which succeeded and which failed

## What this does:
- Processes ONE dataset at a time to avoid memory issues
- Automatically skips already merged files
- Handles errors gracefully and continues
- Shows clear progress for each dataset
- Saves to Nigeria_Merged_Rasters folder without "_merged" suffix
- Cleans up memory after each merge