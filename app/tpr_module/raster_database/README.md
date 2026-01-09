# Raster Database Structure

This directory contains pre-downloaded raster files for environmental variables used in TPR analysis.

## Directory Structure

```
raster_database/
├── rainfall/          # Precipitation data (CHIRPS)
├── temperature/       # Temperature data (ERA5)
├── vegetation/        # EVI, NDVI, NDMI indices
├── elevation/         # Digital elevation model
├── water_bodies/      # Distance to water bodies
├── urban/            # Nighttime lights, urban extent
├── soil/             # Soil wetness indices
└── housing/          # Housing quality index
```

## File Naming Convention

- `{variable}_{year}_annual.tif` - Annual average
- `{variable}_{year}_{month}.tif` - Monthly data
- `{variable}_static.tif` - Static variables (e.g., elevation)

## Metadata Format

Each directory should contain a `metadata.json` file following the template in `metadata_template.json`.

## Variables by Geopolitical Zone

Based on `app/analysis/region_aware_selection.py`:

- **North_Central**: rainfall, temp, evi, ndmi, ndwi, soil_wetness, nighttime_lights
- **North_East**: housing_quality, evi, ndwi, soil_wetness
- **North_West**: housing_quality, elevation, evi, distance_to_waterbodies, soil_wetness
- **South_East**: rainfall, elevation, evi, nighttime_lights, soil_wetness, temp
- **South_South**: elevation, housing_quality, temp, evi, ndwi, ndmi
- **South_West**: rainfall, elevation, evi, nighttime_lights

## Placeholder Files

This is a placeholder structure. Actual TIFF files will be added when available.