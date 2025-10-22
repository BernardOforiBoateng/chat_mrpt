# Raster Database Implementation Plan for ChatMRPT

## Overview
Plan for organizing and integrating raster files from the Urban Malaria Project into ChatMRPT's TPR module.

## Optimal Database Structure

### 1. File Organization Strategy

```
app/tpr_module/raster_database/
├── nigeria_base/                    # Static files (rarely change)
│   ├── elevation/
│   │   └── nigeria_elevation_90m.tif
│   ├── water_bodies/
│   │   └── distance_to_water_1km.tif
│   └── admin_boundaries/
│       └── nigeria_wards_2023.tif
│
├── environmental/                   # Time-varying environmental data
│   ├── rainfall/
│   │   ├── rainfall_2023_annual.tif
│   │   ├── rainfall_2023_q1.tif
│   │   ├── rainfall_2023_q2.tif
│   │   └── metadata.json
│   ├── temperature/
│   │   ├── temp_mean_2023_annual.tif
│   │   ├── temp_max_2023_annual.tif
│   │   └── metadata.json
│   ├── vegetation/
│   │   ├── evi_2023_annual.tif
│   │   ├── ndvi_2023_annual.tif
│   │   ├── ndmi_2023_annual.tif
│   │   └── metadata.json
│   └── soil/
│       ├── soil_moisture_2023.tif
│       └── metadata.json
│
├── socioeconomic/                   # Human-related indicators
│   ├── nighttime_lights/
│   │   └── viirs_ntl_2023.tif
│   ├── urban_extent/
│   │   └── urban_areas_2023.tif
│   └── housing_quality/
│       └── housing_index_2022.tif
│
└── index.json                       # Master index of all rasters
```

### 2. Raster Requirements by Geopolitical Zone

Based on our zone mapping, we need these rasters:

#### Core Variables (All Zones):
- Elevation (static)
- Distance to water bodies (static)

#### Zone-Specific Variables:
- **North_Central**: rainfall, temp, evi, ndmi, ndwi, soil_wetness, nighttime_lights
- **North_East**: housing_quality, evi, ndwi, soil_wetness
- **North_West**: housing_quality, elevation, evi, distance_to_waterbodies, soil_wetness
- **South_East**: rainfall, elevation, evi, nighttime_lights, soil_wetness, temp
- **South_South**: elevation, housing_quality, temp, evi, ndwi, ndmi
- **South_West**: rainfall, elevation, evi, nighttime_lights

### 3. Technical Specifications

#### Raster Properties:
- **Projection**: EPSG:4326 (WGS84) for consistency
- **Resolution**: 1km or finer (30m-90m preferred for accuracy)
- **Format**: GeoTIFF (.tif)
- **Compression**: LZW or DEFLATE to save space
- **NoData Value**: -9999 or similar (consistent across files)

#### Metadata Requirements (metadata.json):
```json
{
    "variable": "rainfall",
    "source": "CHIRPS/GPM/etc",
    "temporal_range": "2023-01-01 to 2023-12-31",
    "spatial_resolution": "1km",
    "units": "mm/year",
    "processing_date": "2024-01-15",
    "crs": "EPSG:4326",
    "bounds": {
        "north": 13.89,
        "south": 4.27,
        "east": 14.68,
        "west": 2.67
    }
}
```

## Implementation Steps

### Step 1: Inventory Existing Rasters
Please check your Dropbox folder for:
1. List all .tif/.tiff files
2. Note their naming convention
3. Check temporal coverage (years available)
4. Verify spatial extent (Nigeria-wide?)

### Step 2: Priority Rasters to Copy
Start with these essential rasters:
1. **Elevation** (static, one-time)
2. **EVI/NDVI** (latest annual average)
3. **Rainfall** (latest annual total)
4. **Temperature** (latest annual mean)
5. **Nighttime lights** (latest annual)

### Step 3: File Preparation
For each raster:
1. Ensure Nigeria-wide coverage
2. Convert to EPSG:4326 if needed
3. Compress with LZW
4. Generate pyramid overviews for fast reading

### Step 4: Copying Strategy
```bash
# Create a folder structure locally first
mkdir -p app/tpr_module/raster_database/{nigeria_base,environmental,socioeconomic}

# Copy files in batches (start with ~5-10 files)
# Rename to standardized format: {variable}_{year}_{temporal}.tif
```

## Recommended Approach

### Option 1: Selective Download (Recommended)
1. You identify and download only the required rasters (~15-20 files)
2. Organize them according to the structure above
3. Zip and share them with me (or commit to a data folder)
4. I'll create the extraction code

### Option 2: Full Inventory First
1. You provide a list of all available rasters
2. I'll identify exactly which ones we need
3. You download those specific files
4. We integrate them systematically

### Option 3: Cloud Storage
1. Upload rasters to a cloud service (Google Drive, S3)
2. Share read-only access
3. We can then programmatically access them

## File Size Considerations
- Estimate ~50-200MB per raster (1km resolution, Nigeria-wide)
- Total database size: ~2-4GB for all variables
- Consider using Cloud Optimized GeoTIFF (COG) format for better performance

## Questions for You:
1. What's the resolution of your current rasters?
2. Do they cover all of Nigeria or specific states?
3. What years are available?
4. Are they already in GeoTIFF format?
5. What's the typical file size?

## Next Steps:
1. Check what rasters you have available
2. Let me know the file list and sizes
3. We'll prioritize which ones to include
4. You download and organize them
5. I'll implement the extraction code