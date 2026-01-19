# Raster Files Analysis Report

## 1. Unique Variables Found

### Environmental Variables
1. **EVI (Enhanced Vegetation Index)**
   - Years: 2010, 2013, 2015, 2018
   - Monthly data available
   - File formats: .tif

2. **Rainfall**
   - Years: 2010, 2013, 2015, 2018, 2021
   - Monthly data available
   - File formats: .tif with some .aux.xml metadata files

3. **Temperature**
   - Years: 2010, 2013, 2015, 2018, 2021
   - Monthly data available
   - File formats: .tif with some .aux.xml metadata files

4. **Surface Soil Wetness (GWETTOP)**
   - Years: 2010, 2015, 2018
   - Monthly data available
   - File formats: GIOVANNI-sourced .tif files

5. **Elevation**
   - Static dataset (no year)
   - File formats: .tif with PDF and XML documentation

### Water-Related Variables
6. **NDMI (Normalized Difference Moisture Index)**
   - Years: 2023
   - Annual data
   - File formats: .tif

7. **NDWI (Normalized Difference Water Index)**
   - Years: 2023
   - Annual data
   - File formats: .tif

8. **Distance to Water Bodies**
   - Static dataset (no year)
   - File formats: .tif

9. **Flood Extent**
   - Years: 2018, 2021
   - Monthly and yearly aggregations
   - File formats: .tif

### Human Activity Variables
10. **Night Time Lights**
    - Years: 2010 (DMSP), 2015, 2018, 2021, 2024 (VIIRS)
    - Annual data
    - File formats: .tif

11. **Housing**
    - Years: 2000, 2015
    - Annual data
    - File formats: .tiff

### Health Variables
12. **Pf Parasite Rate (Plasmodium falciparum)**
    - Years: 2000-2022 (complete series)
    - Annual data
    - File formats: .tiff

## 2. Issues Identified

### Naming Inconsistencies
1. **Prefix inconsistencies**: Some files have "X" prefix (e.g., X2013_rainfall_year_2013_month_02.tif)
2. **Mixed naming conventions**:
   - EVI: `EVI_v6.YYYY.MM.mean.1km.tif` vs `evi_nigeria_YYYY_month_M.tif`
   - Rainfall: `rainfall_year_YYYY_month_MM.tif` vs `XYYYY_rainfall_year_YYYY_month_MM.tif`
3. **Misplaced files**:
   - DMSP_2010_NTL_Nigeria.tif in EVI folder (should be in night_time_lights)
   - X2015_rainfall files in EVI folder
4. **Typo in folder name**: "night_timel_lights" should be "night_time_lights"

### Data Coverage Gaps
1. **Missing recent data** for most environmental variables (2022-2024)
2. **Incomplete monthly coverage** - many years only have partial months
3. **Inconsistent temporal resolution** - some variables have more frequent updates than others

### File Organization Issues
1. **Duplicate files** in pf_parasite_rate folder
2. **Mixed file types** (.tif, .tiff, .aux.xml, .pdf, .xml, .rtf, .zip)
3. **Inconsistent subfolder structure** (some have year folders, others don't)

## 3. Reorganization Plan

### Target Structure
```
app/tpr_module/raster_database/
├── environmental/
│   ├── evi/
│   │   ├── 2021/  # If available from other sources
│   │   ├── 2022/  # If available from other sources
│   │   └── 2023/  # If available from other sources
│   ├── rainfall/
│   │   ├── 2021/
│   │   ├── 2022/  # If available from other sources
│   │   └── 2023/  # If available from other sources
│   ├── temperature/
│   │   ├── 2021/
│   │   ├── 2022/  # If available from other sources
│   │   └── 2023/  # If available from other sources
│   └── soil_wetness/
│       ├── 2021/  # If available from other sources
│       ├── 2022/  # If available from other sources
│       └── 2023/  # If available from other sources
├── water/
│   ├── ndmi/
│   │   └── 2023/
│   ├── ndwi/
│   │   └── 2023/
│   ├── flood_extent/
│   │   ├── 2021/
│   │   ├── 2022/  # If available from other sources
│   │   └── 2023/  # If available from other sources
│   └── static/
│       └── distance_to_water.tif
├── human_activity/
│   ├── night_lights/
│   │   ├── 2021/
│   │   ├── 2022/  # If available from other sources
│   │   ├── 2023/  # If available from other sources
│   │   └── 2024/
│   └── housing/
│       └── 2015/  # Most recent available
├── health/
│   └── pf_parasite_rate/
│       ├── 2020/
│       ├── 2021/
│       └── 2022/
├── static/
│   └── elevation/
│       └── MERIT_Elevation.max.1km.tif
└── metadata/
    └── file_inventory.json
```

### Naming Convention
```
{variable}_{year}_{month}.tif
```
Examples:
- evi_2023_01.tif
- rainfall_2023_12.tif
- temperature_2023_06.tif
- pf_parasite_rate_2022.tif (annual data)
- ndwi_2023.tif (annual data)

## 4. Data Availability Summary

### Most Recent 3 Years Coverage (2022-2024)
- **Complete**: Pf Parasite Rate (2022), Night Lights (2024)
- **Partial**: NDMI (2023), NDWI (2023), Flood Extent (2021)
- **Missing**: EVI, Rainfall, Temperature, Soil Wetness (all stop at 2021 or earlier)

### Recommendation
Since most environmental variables lack recent data (2022-2024), we should:
1. Use 2021 as the primary year for environmental data
2. Supplement with 2023 NDMI/NDWI data
3. Include 2022 Pf Parasite Rate and 2024 Night Lights
4. Consider data acquisition for missing 2022-2024 environmental variables