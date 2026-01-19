# Raster Files Reorganization Summary

## Overview
This document summarizes the analysis and reorganization plan for raster files in the ChatMRPT TPR module.

## Key Findings

### 1. Variables Identified (12 types)

#### Environmental Variables
- **EVI (Enhanced Vegetation Index)**: 2010, 2013, 2015, 2018 (monthly)
- **Rainfall**: 2010, 2013, 2015, 2018, 2021 (monthly)
- **Temperature**: 2010, 2013, 2015, 2018, 2021 (monthly)
- **Surface Soil Wetness**: 2010, 2015, 2018 (monthly)
- **Elevation**: Static dataset (MERIT DEM)

#### Water-Related Variables
- **NDMI**: 2023 (annual)
- **NDWI**: 2023 (annual)
- **Distance to Water Bodies**: Static dataset
- **Flood Extent**: 2018, 2021 (monthly and yearly)

#### Human Activity Variables
- **Night Time Lights**: 2010-2024 (annual, DMSP → VIIRS transition)
- **Housing**: 2000, 2015 (annual)

#### Health Variables
- **Pf Parasite Rate**: 2000-2022 (complete annual series)

### 2. Critical Issues Found

1. **Naming Inconsistencies**
   - Mixed prefixes (X2013_, regular names)
   - Different conventions for same variable type
   - Typo in folder name: "night_timel_lights"

2. **Misplaced Files**
   - DMSP_2010_NTL_Nigeria.tif in EVI folder
   - Rainfall files in EVI folder

3. **Data Gaps**
   - Most environmental variables stop at 2021
   - No 2022-2024 data for EVI, rainfall, temperature, soil wetness

4. **Organizational Issues**
   - Duplicate files in pf_parasite_rate
   - Mixed file formats (.tif, .tiff)
   - Inconsistent subfolder structure

### 3. Reorganization Strategy

Since most environmental data lacks 2022-2024 coverage, the recommended approach is:

1. **Use 2021 as baseline year** for environmental analysis
2. **Supplement with 2023 data** where available (NDMI, NDWI)
3. **Include recent data** for other variables (2024 night lights, 2022 Pf rate)

### 4. Scripts Created

1. **`raster_analysis_report.md`** - Detailed analysis of all raster files
2. **`reorganize_rasters.py`** - Comprehensive reorganization for all years
3. **`reorganize_rasters_recent.py`** - Focused on most recent available data
4. **`reorganize_for_tpr.py`** - Aligned with existing TPR module structure

### 5. Target Directory Structure

```
app/tpr_module/raster_database/
├── elevation/          # Static elevation data
├── housing/            # Settlement/housing data
├── rainfall/           # Monthly rainfall (2021, 2018)
├── temperature/        # Monthly temperature (2021, 2018)
├── soil/              # Soil wetness (2018)
├── vegetation/        # EVI data (2018)
├── water_bodies/      # NDMI, NDWI, flood, distance to water
├── urban/             # Night lights (2024, 2021)
├── health/            # Pf parasite rate (2022, 2021, 2020)
└── metadata/          # Inventory and documentation
```

## Recommendations

1. **Immediate Action**: Run `python reorganize_for_tpr.py --execute` to organize existing data
2. **Data Acquisition**: Obtain 2022-2024 environmental data for complete coverage
3. **Standardization**: Implement consistent naming convention: `{variable}_{year}_{month}.tif`
4. **Quality Check**: Verify all reorganized files maintain proper georeferencing

## Next Steps

1. Execute the reorganization script
2. Update TPR module to use new raster database structure
3. Create data acquisition plan for missing 2022-2024 environmental data
4. Implement automated validation for raster file consistency

## Data Availability Matrix

| Variable | 2020 | 2021 | 2022 | 2023 | 2024 |
|----------|------|------|------|------|------|
| EVI | ❌ | ❌ | ❌ | ❌ | ❌ |
| Rainfall | ❌ | ✅* | ❌ | ❌ | ❌ |
| Temperature | ❌ | ✅* | ❌ | ❌ | ❌ |
| Soil Wetness | ❌ | ❌ | ❌ | ❌ | ❌ |
| NDMI | ❌ | ❌ | ❌ | ✅ | ❌ |
| NDWI | ❌ | ❌ | ❌ | ✅ | ❌ |
| Flood | ❌ | ✅ | ❌ | ❌ | ❌ |
| Night Lights | ❌ | ✅ | ❌ | ❌ | ✅ |
| Pf Rate | ✅ | ✅ | ✅ | ❌ | ❌ |

*Partial data (October-December only)