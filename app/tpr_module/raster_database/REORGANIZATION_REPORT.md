
# TPR Raster Reorganization Summary

Generated: 2025-07-18 14:01:28

## Overview
- Total operations: 40
- Source directory: /mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/rasters
- Target directory: /mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/app/tpr_module/raster_database

## Variables Processed

### elevation
Files: 1

- elevation_static.tif: Elevation (static)

### flood
Files: 2

- flood_extent_2021_annual.tif: Flood extent 2021 annual
- flood_extent_2018_annual.tif: Flood extent 2018 annual

### health
Files: 3

- pfpr_2022.tif: Pf parasite rate 2022
- pfpr_2021.tif: Pf parasite rate 2021
- pfpr_2020.tif: Pf parasite rate 2020

### housing
Files: 1

- housing_quality_2015.tif: Housing quality 2015

### rainfall
Files: 8

- rainfall_2021_10.tif: Rainfall rainfall_2021_10.tif
- rainfall_2021_11.tif: Rainfall rainfall_2021_11.tif
- rainfall_2021_12.tif: Rainfall rainfall_2021_12.tif
- rainfall_2018_08.tif: Rainfall rainfall_2018_08.tif
- rainfall_2018_09.tif: Rainfall rainfall_2018_09.tif
- rainfall_2018_10.tif: Rainfall rainfall_2018_10.tif
- rainfall_2018_11.tif: Rainfall rainfall_2018_11.tif
- rainfall_2018_12.tif: Rainfall rainfall_2018_12.tif

### soil
Files: 5

- soil_wetness_2018_08.tif: Soil wetness soil_wetness_2018_08.tif
- soil_wetness_2018_09.tif: Soil wetness soil_wetness_2018_09.tif
- soil_wetness_2018_10.tif: Soil wetness soil_wetness_2018_10.tif
- soil_wetness_2018_11.tif: Soil wetness soil_wetness_2018_11.tif
- soil_wetness_2018_12.tif: Soil wetness soil_wetness_2018_12.tif

### temperature
Files: 8

- temperature_2021_10.tif: Temperature temperature_2021_10.tif
- temperature_2021_11.tif: Temperature temperature_2021_11.tif
- temperature_2021_12.tif: Temperature temperature_2021_12.tif
- temperature_2018_08.tif: Temperature temperature_2018_08.tif
- temperature_2018_09.tif: Temperature temperature_2018_09.tif
- temperature_2018_10.tif: Temperature temperature_2018_10.tif
- temperature_2018_11.tif: Temperature temperature_2018_11.tif
- temperature_2018_12.tif: Temperature temperature_2018_12.tif

### urban
Files: 3

- nighttime_lights_2024.tif: Nighttime lights 2024
- nighttime_lights_2021.tif: Nighttime lights 2021
- nighttime_lights_2018.tif: Nighttime lights 2018

### vegetation
Files: 8

- evi_2018_08.tif: EVI 2018 monthly data
- evi_2018_09.tif: EVI 2018 monthly data
- evi_2018_10.tif: EVI 2018 monthly data
- evi_2018_11.tif: EVI 2018 monthly data
- evi_2018_12.tif: EVI 2018 monthly data
- evi_2015_12.tif: EVI 2015 December
- ndmi_2023_annual.tif: NDMI 2023 annual
- ndwi_2023_annual.tif: NDWI 2023 annual

### water_bodies
Files: 1

- distance_to_water_static.tif: Distance to water bodies (static)

## Metadata Summary

### evi
```json
{
  "years_available": [
    2018,
    2015,
    2013,
    2010
  ],
  "selected_years": [
    2018,
    2015,
    2013
  ],
  "note": "Monthly data available, annual averages need to be computed"
}
```

### ndmi
```json
{
  "years_available": [
    2023
  ],
  "selected_years": [
    2023
  ]
}
```

### ndwi
```json
{
  "years_available": [
    2023
  ],
  "selected_years": [
    2023
  ]
}
```

### elevation
```json
{
  "type": "static",
  "source": "MERIT DEM"
}
```

### distance_to_water
```json
{
  "type": "static"
}
```

### flood
```json
{
  "years_available": [
    2021,
    2018
  ],
  "selected_years": [
    2021,
    2018
  ]
}
```

### housing
```json
{
  "years_available": [
    2015,
    2000
  ],
  "selected_years": [
    2015
  ],
  "note": "Most recent available"
}
```

### nighttime_lights
```json
{
  "years_available": [
    2024,
    2021,
    2018,
    2015,
    2010
  ],
  "selected_years": [
    2024,
    2021,
    2018
  ]
}
```

### pfpr
```json
{
  "years_available": [
    2000,
    2001,
    2002,
    2003,
    2004,
    2005,
    2006,
    2007,
    2008,
    2009,
    2010,
    2011,
    2012,
    2013,
    2014,
    2015,
    2016,
    2017,
    2018,
    2019,
    2020,
    2021,
    2022
  ],
  "selected_years": [
    2022,
    2021,
    2020
  ]
}
```

### rainfall
```json
{
  "years_available": [
    2021,
    2018,
    2015,
    2013,
    2010
  ],
  "selected_years": [
    2021,
    2018
  ],
  "note": "Monthly data, annual totals need to be computed"
}
```

### temperature
```json
{
  "years_available": [
    2021,
    2018,
    2015,
    2013,
    2010
  ],
  "selected_years": [
    2021,
    2018
  ],
  "note": "Monthly data, annual means need to be computed"
}
```

### soil_wetness
```json
{
  "years_available": [
    2018,
    2015,
    2010
  ],
  "selected_years": [
    2018
  ],
  "source": "NASA GIOVANNI"
}
```

