# Multi-Method Urban Percentage Calculation Documentation

## Overview
This Google Earth Engine script implements three scientifically-validated methods to measure urban percentage for Nigerian wards, providing multiple independent validation approaches to verify whether areas are truly rural or urban.

## Methods Implemented

### 1. NDBI (Normalized Difference Built-up Index)
- **Formula**: NDBI = (SWIR - NIR) / (SWIR + NIR)
- **Data Source**: Sentinel-2 imagery
- **Bands Used**: B11 (SWIR) and B8 (NIR)
- **Threshold**: NDBI > 0 indicates urban/built-up areas
- **Advantages**: Direct spectral signature of built-up areas
- **Limitations**: May confuse bare soil with built-up areas

### 2. Africapolis Methodology
- **Criteria**: 
  - Continuous built-up area (< 200m between buildings)
  - Minimum 10,000 population threshold
- **Data Sources**: 
  - Sentinel-2 for built-up detection
  - WorldPop for population data
- **Advantages**: Combines physical and demographic criteria
- **Limitations**: Requires accurate population data

### 3. GHSL Degree of Urbanization
- **Classification Levels**:
  - Urban centre: ≥1,500 inhabitants/km² + ≥50,000 total population
  - Urban cluster: ≥300 inhabitants/km² + ≥5,000 total population
  - Rural: Everything else
- **Data Source**: JRC Global Human Settlement Layer
- **Advantages**: UN-recommended standard, pre-processed data
- **Resolution**: 1000m grid cells

### 4. EBBI (Bonus Method)
- **Formula**: EBBI = (NIR - TIR) / (NIR + TIR)
- **Data Source**: Landsat 8 (includes thermal band)
- **Advantages**: Better discrimination using thermal signature
- **Use Case**: When NDBI shows ambiguous results

## How to Use the Script

### Step 1: Import Ward Boundaries
```javascript
// Option A: Upload shapefile to GEE Assets
var wards = ee.FeatureCollection('users/your_username/delta_state_wards');

// Option B: Import from Google Fusion Tables
var wards = ee.FeatureCollection('ft:your_fusion_table_id');

// Option C: Load from existing GEE dataset
var wards = ee.FeatureCollection('projects/your_project/assets/wards');
```

### Step 2: Update Study Area
```javascript
// Replace the nigeria variable with your state boundaries
var deltaState = ee.Geometry.Rectangle([5.0, 5.0, 6.5, 6.5]); // Example coordinates
```

### Step 3: Adjust Time Period
```javascript
var startDate = '2023-01-01';  // Use recent imagery
var endDate = '2023-12-31';
```

### Step 4: Run the Script
1. Copy the script to Google Earth Engine Code Editor
2. Replace sample wards with your actual ward boundaries
3. Click "Run"
4. Wait for processing (may take several minutes)
5. Check the Console for results
6. Approve exports in the Tasks tab

## Interpreting Results

### Urban Percentage Thresholds
- **> 50%**: Clearly urban
- **30-50%**: Mixed/peri-urban
- **10-30%**: Rural with some development
- **< 10%**: Clearly rural

### Consistency Check
If a ward shows:
- Low urban % across ALL methods → Confidently rural
- High urban % across ALL methods → Confidently urban
- Mixed results → Requires further investigation

### Expected Output Files

1. **CSV File**: `Urban_Percentage_Multi_Methods.csv`
   - Columns: ward_name, NDBI_urban_percent, Africapolis_urban_percent, GHSL_urban_percent, EBBI_urban_percent

2. **Raster Files**:
   - `NDBI_Raster.tif`: Raw NDBI values (-1 to 1)
   - `GHSL_Raster.tif`: Settlement classification codes

## Troubleshooting

### Common Issues

1. **"wards is not defined"**
   - Solution: Import your ward boundaries shapefile

2. **"Too many pixels"**
   - Solution: Process smaller regions or increase scale parameter

3. **"No imagery found"**
   - Solution: Check date range and cloud cover threshold

4. **Export taking too long**
   - Solution: Reduce region size or increase scale

### Data Requirements

- Ward boundaries shapefile with:
  - Unique identifier field (e.g., 'ward_name', 'ward_id')
  - Proper geometry (polygons)
  - CRS: WGS84 (EPSG:4326) recommended

## Validation Strategy

### For Thursday Meeting:
1. Run script for Delta State wards
2. Export results to CSV
3. Create comparison table showing:
   - Ward names
   - Urban % from each method
   - Average urban %
   - Classification (Urban/Rural)
4. Highlight wards with consistent rural classification across methods
5. Flag any discrepancies for discussion

## Quick Start Example

```javascript
// 1. Define your state
var deltaState = ee.Geometry.Rectangle([5.05, 4.95, 6.7, 6.4]);

// 2. Load your wards (example for Delta State)
var wards = ee.FeatureCollection('users/your_username/delta_wards_2023');

// 3. Run just NDBI for quick test
var sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(deltaState)
  .filterDate('2023-01-01', '2023-12-31')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30));

var ndbi = sentinel2.median().normalizedDifference(['B11', 'B8']);
Map.addLayer(ndbi, {min: -1, max: 1, palette: ['blue', 'white', 'red']}, 'NDBI');
```

## References

1. **NDBI**: Zha, Y., Gao, J., & Ni, S. (2003). Use of normalized difference built-up index in automatically mapping urban areas from TM imagery.

2. **Africapolis**: OECD/SWAC (2020). Africa's Urbanisation Dynamics 2020: Africapolis, Mapping a New Urban Geography.

3. **GHSL**: Pesaresi, M., et al. (2016). Operating procedure for the production of the Global Human Settlement Layer from Landsat data of the epochs 1975, 1990, 2000, and 2014.

4. **EBBI**: As-syakur, A. R., et al. (2012). Enhanced built-up and bareness index (EBBI) for mapping built-up and bare land in an urban area.

## Contact & Support
For questions about implementation or interpretation of results, please refer to the meeting notes from the supervisor discussion regarding urban percentage validation for Delta State ward prioritization.