# Finding Your Earth Engine Exports

## Where Your Files Went

Your export script ran with two different folder configurations:

### 1. First Run (Already Completed)
- **Folder Name**: `Nigeria_Raster_Indices`
- **Status**: ~20+ files already exported here
- **Files Include**:
  - NDWI_2015_07_Nigeria.tif
  - NDMI_2015_07_Nigeria.tif
  - ... and more from 2015, 2018

### 2. Future Runs (After Update)
- **Folder Name**: `Rasters` 
- **Your Folder Link**: https://drive.google.com/drive/folders/1pjkF_04oAR0kLVXmCxjjX1ed3FElk7rr

## How to Find Your Completed Exports

### Option 1: Search in Google Drive
1. Go to https://drive.google.com
2. In the search bar, type: `Nigeria_Raster_Indices`
3. Or search for: `type:folder Nigeria`
4. Or search for specific files: `NDWI_2015`

### Option 2: Check Recent Activity
1. In Google Drive, click on "Recent" in the left sidebar
2. Look for .tif files created today
3. They should show the folder they're in

### Option 3: Search by File Type
1. In Google Drive search: `type:tiff` or `*.tif`
2. This will show all TIFF files in your Drive

## What To Do Next

### If you find the files in `Nigeria_Raster_Indices`:
1. Select all the files
2. Right-click → Move
3. Move them to your `Rasters` folder

### If you can't find the files:
1. They might be in a different Google account
2. Check which account you authenticated Earth Engine with
3. The exports might have failed (check Earth Engine task manager)

### To continue with remaining exports:
1. The script is now configured to use `Rasters` folder
2. Any new exports will go directly to your folder
3. You can re-run the script for any missing months/years

## Quick Check Commands

```python
# Check which account Earth Engine is using
import ee
ee.Initialize()
print(ee.data.getAssetRoots())
```

This will show which Google account is being used for Earth Engine.