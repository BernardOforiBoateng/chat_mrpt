# Universal Raster Tile Merger

## Quick Start

### Windows Users:
1. **Double-click** `merge_tiles_windows.bat`
2. **Enter or drag** your folder containing tiles when prompted
3. Find merged files in the `merged` subfolder

### Mac/Linux Users:
```bash
chmod +x merge_tiles_unix.sh
./merge_tiles_unix.sh
```

### Python Direct Usage:
```bash
python merge_raster_tiles.py /path/to/your/tiles/folder
```

## What This Does

Automatically merges GEE tile exports like:
- `NDMI_2023_7-0000000000-0000000000.tif` → `NDMI_2023_7_merged.tif`
- `NDWI_2023_7-0000000000-0000000000.tif` → `NDWI_2023_7_merged.tif`

## Installation Requirements

### Option 1: pip (Recommended)
```bash
pip install rasterio
```

### Option 2: conda
```bash
conda install -c conda-forge rasterio
```

## Advanced Usage

### Merge to specific output folder:
```bash
python merge_raster_tiles.py input_folder -o output_folder
```

### Merge and delete original tiles:
```bash
python merge_raster_tiles.py input_folder --cleanup
```

### Process multiple folders:
```bash
for folder in folder1 folder2 folder3; do
    python merge_raster_tiles.py "$folder"
done
```

## Features

✅ **Universal** - Works on Windows, Mac, Linux  
✅ **Automatic** - Detects and groups tiles automatically  
✅ **Batch Processing** - Merges all tile groups in folder  
✅ **Safe** - Preserves original files (unless --cleanup used)  
✅ **Compressed** - Output files use LZW compression  

## Troubleshooting

### "rasterio not installed"
```bash
# Windows
pip install rasterio

# Mac/Linux
pip3 install rasterio

# Conda
conda install -c conda-forge rasterio
```

### "Python not found"
- Windows: Download from https://www.python.org/
- Mac: `brew install python3`
- Linux: `sudo apt install python3 python3-pip`

### Tiles not merging?
Check that your tiles follow these patterns:
- `name-0000000000-0000000000.tif` (GEE standard)
- `name_1.tif, name_2.tif, name_3.tif`
- `name-00000001.tif, name-00000002.tif`

## Example Output

```
Scanning directory: /Users/you/Downloads/tiles
Found 2 tile groups to merge:

Processing: NDMI_2023_7 (4 tiles)
  - Adding tile: NDMI_2023_7-0000000000-0000000000.tif
  - Adding tile: NDMI_2023_7-0000000000-0000001024.tif
  - Adding tile: NDMI_2023_7-0000001024-0000000000.tif
  - Adding tile: NDMI_2023_7-0000001024-0000001024.tif
✓ Merged successfully!
  Input: 45.23 MB (4 files)
  Output: 44.89 MB

Processing: NDWI_2023_7 (4 tiles)
...
```