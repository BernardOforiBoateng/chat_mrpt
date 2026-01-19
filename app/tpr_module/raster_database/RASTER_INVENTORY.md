# TPR Module Raster Database Inventory

## Current Status
The raster files have been collected but need reorganization for the TPR module.

## Available Variables and Years

### 1. **Vegetation Indices**
- **EVI**: 2018, 2015, 2013, 2010 (monthly data)
- **NDMI**: 2023 (annual) ✅
- **NDWI**: 2023 (annual) ✅

### 2. **Climate Variables**
- **Rainfall**: 2021, 2018, 2015, 2013, 2010 (monthly)
- **Temperature**: 2021, 2018, 2015, 2013, 2010 (monthly)
- **Soil Wetness**: 2018, 2015, 2010 (monthly GIOVANNI data)

### 3. **Static Variables**
- **Elevation**: MERIT DEM 1km (static) ✅
- **Distance to Water**: Available (static) ✅

### 4. **Socioeconomic Indicators**
- **Nighttime Lights**: 2024 ✅, 2021, 2018, 2015, 2010
- **Housing Quality**: 2015, 2000

### 5. **Health/Environmental**
- **Pf Parasite Rate**: 2000-2022 (complete series!)
- **Flood Extent**: 2021, 2018 (annual and monthly)

## Reorganization Plan

### Directory Structure
```
app/tpr_module/raster_database/
├── vegetation/
│   ├── evi_2018_annual.tif (to be computed from monthly)
│   ├── ndmi_2023_annual.tif
│   └── ndwi_2023_annual.tif
├── rainfall/
│   ├── rainfall_2021_annual.tif (to be computed)
│   └── rainfall_2018_annual.tif (to be computed)
├── temperature/
│   ├── temperature_2021_mean.tif (to be computed)
│   └── temperature_2018_mean.tif (to be computed)
├── elevation/
│   └── elevation_static.tif
├── water_bodies/
│   └── distance_to_water_static.tif
├── urban/
│   ├── nighttime_lights_2024.tif
│   ├── nighttime_lights_2021.tif
│   └── nighttime_lights_2018.tif
├── housing/
│   └── housing_quality_2015.tif
├── soil/
│   └── soil_wetness_2018_annual.tif (to be computed)
└── health/
    ├── pfpr_2022.tif
    ├── pfpr_2021.tif
    └── pfpr_2020.tif
```

## Key Issues to Address

### 1. **Missing Recent Environmental Data**
- No EVI data after 2018
- No rainfall/temperature after 2021
- Consider using 2018 as baseline year for complete analysis

### 2. **Monthly to Annual Conversion Needed**
- EVI: Compute annual mean from monthly data
- Rainfall: Compute annual total from monthly data
- Temperature: Compute annual mean from monthly data
- Soil wetness: Compute annual mean from monthly data

### 3. **Naming Convention Standardization**
Current: Mixed formats (X2021_rainfall_year_2021_month_10.tif, EVI_v6.2018.08.mean.1km.tif)
Target: {variable}_{year}_{temporal}.tif (e.g., rainfall_2021_annual.tif)

### 4. **Misplaced Files**
- DMSP_2010_NTL_Nigeria.tif in EVI folder (should be nighttime lights)
- X2015_rainfall files in EVI folder

## Recommendations

### For Immediate Use:
1. **2021 as Primary Year**: Most complete recent data across variables
2. **Static Variables**: Ready to use (elevation, distance to water)
3. **2023 Vegetation Indices**: NDMI and NDWI are current

### Data Gaps to Fill:
1. **2022-2024 Environmental Data**: Consider downloading from:
   - CHIRPS for rainfall
   - ERA5 for temperature
   - MODIS for EVI/NDVI

2. **Annual Aggregations**: Need script to compute annual values from monthly data

### Next Steps:
1. Run `reorganize_rasters_for_tpr.py --execute` to clean up structure
2. Create annual aggregation script for monthly data
3. Document each variable's source and processing method
4. Create extraction script for ward-level values