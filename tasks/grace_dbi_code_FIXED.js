// =====================================================
// FIXED: DBI CALCULATION WITH WARD-LEVEL AGGREGATION
// Based on Grace's original + Bernard's aggregation method
// Date: October 8, 2025
// =====================================================

// CRITICAL FIX:
// Grace's original code exported pixel-level binary rasters (0 or 1)
// This version adds ward-level aggregation to produce percentages (0-100%)
// comparable to Bernard's Delta State validation results

// =====================================================
// CONFIGURATION
// =====================================================

// Load ward boundaries - REPLACE THIS PATH WITH YOUR ACTUAL WARD BOUNDARIES
// Bernard used Nigerian ward boundaries from INEC/GRID3
var wards = ee.FeatureCollection('users/YOUR_USERNAME/nigeria_wards');
// Alternative: Use FAO GAUL or other admin boundaries
// var wards = ee.FeatureCollection("FAO/GAUL_SIMPLIFIED_500m/2015/level2");

// Filter to Delta State for validation test
var deltaWards = wards.filter(ee.Filter.eq('StateName', 'Delta'));
// OR if your data uses different column names:
// var deltaWards = wards.filter(ee.Filter.eq('ADM1_NAME', 'Delta'));

print('Total Delta State wards:', deltaWards.size());
print('First 5 wards:', deltaWards.limit(5));

// Analysis year
var year = 2018;

// =====================================================
// HELPER: CALCULATE URBAN PERCENTAGE
// From Bernard's research-backed methodology
// =====================================================

function calculateUrbanPercentage(binaryMask, wardGeometry, scale) {
  // Ensure mask is binary (0 or 1)
  binaryMask = binaryMask.unmask(0).clamp(0, 1);

  // Calculate total urban area in square meters
  // Method: Sum of (urban pixels × pixel area)
  var urbanArea = binaryMask.multiply(ee.Image.pixelArea())
    .reduceRegion({
      reducer: ee.Reducer.sum(),
      geometry: wardGeometry,
      scale: scale,
      maxPixels: 1e13,
      tileScale: 2  // Reduces memory usage for large wards
    });

  // Get the urban area value
  var areaValue = ee.Number(urbanArea.values().get(0));

  // Calculate total ward area
  var totalArea = wardGeometry.area();

  // Calculate percentage with 100% cap (mathematical constraint)
  var percentage = ee.Algorithms.If(
    totalArea.gt(0),
    areaValue.divide(totalArea).multiply(100).min(100),
    0
  );

  return ee.Number(percentage);
}

// =====================================================
// DBI CALCULATION (Rasul et al. 2018)
// =====================================================

print('===== Processing Delta State (' + year + ') =====');

var startDate = ee.Date.fromYMD(year, 1, 1);
var endDate = ee.Date.fromYMD(year, 12, 31);

var geometry = deltaWards.geometry();

// Sentinel-2 SR Harmonized
var s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
  .filterDate(startDate, endDate)
  .filterBounds(geometry)
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20));

var nImages = s2.size();
print('Number of Sentinel-2 images found:', nImages);

// Create median composite
var composite = s2.median();

// Compute indices
var ndbi = composite.normalizedDifference(['B11', 'B8']).rename('NDBI');  // SWIR vs NIR
var ndvi = composite.normalizedDifference(['B8', 'B4']).rename('NDVI');   // NIR vs Red

// DBI = NDBI - NDVI (Rasul et al. 2018)
var dbi = ndbi.subtract(ndvi).rename('DBI');

// Built-up mask (DBI > 0)
var builtUpMask = dbi.gt(0).selfMask().rename('dbi_urban');

// Visualizations
Map.addLayer(dbi.clip(geometry),
  {min: -1, max: 1, palette: ['#006400', '#f5deb3', '#b22222']},
  'Delta State DBI (' + year + ')');
Map.addLayer(builtUpMask,
  {palette: ['#d3d3d3', '#ff0000']},
  'Delta State Built-up Mask (' + year + ')');
Map.addLayer(deltaWards, {color: 'black', fillColor: '00000000'}, 'Ward Boundaries');

Map.centerObject(geometry, 8);

// =====================================================
// WARD-LEVEL AGGREGATION (NEW - This is what was missing!)
// =====================================================

print('');
print('===== Calculating Ward-Level Urban Percentages =====');
print('Processing', deltaWards.size().getInfo(), 'wards...');

// Process each ward
var wardStats = deltaWards.map(function(ward) {
  var wardGeom = ward.geometry();
  var wardArea = wardGeom.area();

  // Calculate DBI urban percentage
  var dbiPercent = calculateUrbanPercentage(
    builtUpMask.unmask(0),
    wardGeom,
    30  // 30m resolution for Sentinel-2
  );

  // Set attributes
  return ward.set({
    'dbi_urban_percent': dbiPercent,
    'ward_area_km2': wardArea.divide(1e6)
  });
});

// =====================================================
// VALIDATION CHECKS
// =====================================================

print('');
print('===== Validation Sample (First 5 Wards) =====');
var sampleWards = wardStats.limit(5);
print(sampleWards);

// Calculate basic statistics
var dbiStats = wardStats.aggregate_stats('dbi_urban_percent');
print('');
print('===== DBI Statistics =====');
print('Mean DBI:', dbiStats.get('mean'));
print('Min DBI:', dbiStats.get('min'));
print('Max DBI:', dbiStats.get('max'));
print('Std Dev:', dbiStats.get('stdDev'));

// EXPECTED VALUES (from Bernard's Delta State validation):
// Mean: ~5.4%
// Min: 0%
// Max: ~48%
// If you see 0-1 values, the aggregation isn't working

// =====================================================
// EXPORT
// =====================================================

print('');
print('===== Preparing Export =====');

// Export ward-level CSV (comparable to Bernard's results)
Export.table.toDrive({
  collection: wardStats,
  description: 'Delta_State_DBI_Ward_Percentages_' + year,
  folder: 'DBI_exports',
  fileNamePrefix: 'delta_dbi_validation_' + year,
  fileFormat: 'CSV'
});

// Optional: Also export raster for visualization
Export.image.toDrive({
  image: builtUpMask.clip(geometry),
  description: 'Delta_State_DBI_Raster_' + year,
  folder: 'DBI_exports',
  scale: 30,
  region: geometry,
  maxPixels: 1e13
});

print('');
print('===== COMPLETE =====');
print('✅ Check Tasks tab to run exports');
print('✅ CSV output will have dbi_urban_percent column (0-100%)');
print('✅ Compare with Bernard\'s results at:');
print('   urban_validation_outputs/DELTA_STATE_Urbanicity_Validation_Report/');
print('');
print('NEXT STEPS:');
print('1. Run this script for Delta State');
print('2. Download CSV from Google Drive');
print('3. Compare with Bernard\'s validation_delta_state_urban_validation_2025-09-04.csv');
print('4. Differences should be <5% due to year difference (2018 vs 2023)');
print('5. If results match, expand to other states');

// =====================================================
// DEBUGGING TIPS
// =====================================================

// If you get errors:
// 1. "wards is not defined" → Replace line 15 with your ward boundaries path
// 2. "StateName not found" → Check your ward attribute names with: print(wards.first())
// 3. Mean DBI is 0-1 instead of 0-100 → Check calculateUrbanPercentage() multiply(100) on line 66
// 4. All wards show 0% → Check if builtUpMask has any data: print(builtUpMask.reduceRegion({reducer: ee.Reducer.sum(), geometry: geometry, scale: 1000}))
// 5. Timeout error → Reduce ward count or use .limit(50) for testing

// =====================================================
// DIFFERENCES FROM GRACE'S ORIGINAL CODE
// =====================================================

// ADDED:
// 1. Ward boundary loading (line 15)
// 2. calculateUrbanPercentage() function (lines 28-67)
// 3. Ward-level mapping loop (lines 106-120)
// 4. CSV export of ward percentages (lines 146-152)
// 5. Statistics calculation (lines 128-140)

// REMOVED:
// - Multi-country loop (Grace had 15 countries, we focus on Delta State for validation)
// - Direct raster export as primary output (now secondary/optional)

// KEY FIX:
// Original: Export.image.toDrive(builtUpMask) → 0/1 per pixel
// Fixed: Export.table.toDrive(wardStats) → 0-100% per ward

// =====================================================
// COMPARISON TEST SCRIPT
// =====================================================

// After running this and downloading CSV, use this Python script to compare:
/*
import pandas as pd

# Load both files
grace_data = pd.read_csv('delta_dbi_validation_2018.csv')
bernard_data = pd.read_csv('validation_delta_state_urban_validation_2025-09-04.csv')

# Merge on ward identifier (adjust column name as needed)
merged = grace_data.merge(bernard_data, on='WardCode', suffixes=('_grace', '_bernard'))

# Calculate differences
merged['dbi_diff'] = merged['dbi_urban_percent_grace'] - merged['dbi_urban_percent_bernard']
merged['abs_diff'] = merged['dbi_diff'].abs()

# Statistics
print("DBI Comparison Statistics:")
print(f"Mean absolute difference: {merged['abs_diff'].mean():.2f}%")
print(f"Max difference: {merged['abs_diff'].max():.2f}%")
print(f"Wards with >10% difference: {(merged['abs_diff'] > 10).sum()}")

# Expected: Mean difference <5% (due to 2018 vs 2023 imagery)
# If mean difference >10%, something is wrong with the calculation
*/
