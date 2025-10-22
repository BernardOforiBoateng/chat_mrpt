// =====================================================
// GRACE'S CODE - MODIFIED FOR DELTA STATE ONLY
// Purpose: Test if Grace's method produces same results as Bernard's
// Date: October 8, 2025
// =====================================================

// MODIFICATIONS FROM ORIGINAL:
// 1. Only process Delta State (not all 15 countries)
// 2. Add statistics to verify results
// 3. Optional: Add ward-level aggregation for direct comparison

// =====================================================
// SETUP
// =====================================================

// Load country boundaries
var gadm = ee.FeatureCollection('FAO/GAUL_SIMPLIFIED_500m/2015/level0');

// Get Nigeria geometry
var nigeria = gadm.filter(ee.Filter.eq('ADM0_NAME', 'Nigeria'));

// Get Delta State geometry (admin level 1)
var deltaState = ee.FeatureCollection('FAO/GAUL_SIMPLIFIED_500m/2015/level1')
  .filter(ee.Filter.and(
    ee.Filter.eq('ADM0_NAME', 'Nigeria'),
    ee.Filter.eq('ADM1_NAME', 'Delta')
  ));

var deltaGeometry = deltaState.geometry();

print('Delta State loaded:', deltaState.size(), 'feature(s)');
Map.centerObject(deltaGeometry, 8);

// Analysis year (matching Grace's original)
var year = 2018;

// =====================================================
// GRACE'S ORIGINAL DBI CALCULATION
// (Copied exactly from her code)
// =====================================================

function calculateDBI(geometry, regionName, year) {
  var startDate = ee.Date.fromYMD(year, 1, 1);
  var endDate = ee.Date.fromYMD(year, 12, 31);

  print('===== Processing: ' + regionName + ' (' + year + ') =====');

  // Sentinel-2 SR Harmonized
  var s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterDate(startDate, endDate)
    .filterBounds(geometry)
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20));

  var nImages = s2.size();
  print('Number of Sentinel-2 images found for', regionName, year + ':', nImages);

  // Stop early if no imagery found
  var composite = ee.Algorithms.If(nImages.gt(0), s2.median(), null);
  if (composite === null) {
    print('⚠️ Warning: No Sentinel-2 data for ' + regionName + ' (' + year + ')');
    return null;
  }

  composite = ee.Image(composite);

  // Compute indices
  var ndbi = composite.normalizedDifference(['B11', 'B8']).rename('NDBI');  // SWIR vs NIR
  var ndvi = composite.normalizedDifference(['B8', 'B4']).rename('NDVI');   // NIR vs Red

  // DBI = NDBI - NDVI
  var dbi = ndbi.subtract(ndvi).rename('DBI');

  // Built-up mask (DBI > 0)
  var builtUpMask = dbi.gt(0).selfMask().rename('dbi_urban');

  // Visualizations
  Map.addLayer(dbi.clip(geometry),
    {min: -1, max: 1, palette: ['#006400', '#f5deb3', '#b22222']},
    regionName + ' DBI (' + year + ')');
  Map.addLayer(builtUpMask,
    {palette: ['#d3d3d3', '#ff0000']},
    regionName + ' Built-up Mask (' + year + ')');

  // Clip and rename
  builtUpMask = builtUpMask.clip(geometry)
    .rename(regionName.replace(/\s+/g, '_') + '_dbi_' + year);

  return builtUpMask;
}

// =====================================================
// RUN GRACE'S METHOD FOR DELTA STATE
// =====================================================

var dbiImage = calculateDBI(deltaGeometry, 'Delta_State', year);

// =====================================================
// VALIDATION CHECKS (NEW - NOT IN GRACE'S ORIGINAL)
// =====================================================

if (dbiImage !== null) {
  print('');
  print('===== VALIDATION CHECKS =====');

  // Check 1: What are the actual pixel values?
  var pixelStats = dbiImage.reduceRegion({
    reducer: ee.Reducer.mean().combine({
      reducer2: ee.Reducer.minMax(),
      sharedInputs: true
    }),
    geometry: deltaGeometry,
    scale: 30,
    maxPixels: 1e13,
    tileScale: 4
  });

  print('Pixel Statistics (Binary Mask):');
  print('  Mean (fraction urban):', pixelStats.get('Delta_State_dbi_2018_mean'));
  print('  Min:', pixelStats.get('Delta_State_dbi_2018_min'));
  print('  Max:', pixelStats.get('Delta_State_dbi_2018_max'));
  print('');
  print('INTERPRETATION:');
  print('  - Mean should be ~0.05-0.10 (5-10% of pixels are urban)');
  print('  - Min should be 1 (masked values only)');
  print('  - Max should be 1 (binary mask)');
  print('');

  // Check 2: How much total urban area?
  var totalUrbanArea = dbiImage.multiply(ee.Image.pixelArea())
    .reduceRegion({
      reducer: ee.Reducer.sum(),
      geometry: deltaGeometry,
      scale: 30,
      maxPixels: 1e13,
      tileScale: 4
    });

  var stateArea = deltaGeometry.area();
  print('Area Statistics:');
  print('  Total Delta State area (km²):', ee.Number(stateArea).divide(1e6));
  print('  Total urban area (km²):', ee.Number(totalUrbanArea.get('Delta_State_dbi_2018')).divide(1e6));
  print('  Urban percentage:',
    ee.Number(totalUrbanArea.get('Delta_State_dbi_2018'))
      .divide(stateArea)
      .multiply(100));
  print('');
  print('EXPECTED (from Bernard\'s original):');
  print('  Urban percentage should be ~5-6% for whole state');
  print('');

  // =====================================================
  // EXPORT RASTER (GRACE'S ORIGINAL METHOD)
  // =====================================================

  Export.image.toDrive({
    image: dbiImage,
    description: 'Delta_State_DBI_2018_Grace_Method',
    folder: 'DBI_exports',
    scale: 30,
    region: deltaGeometry,
    maxPixels: 1e13
  });

  print('✅ Raster export task created: Delta_State_DBI_2018_Grace_Method');
  print('   Check Tasks tab to run export');
  print('');
}

// =====================================================
// OPTIONAL: WARD-LEVEL COMPARISON
// (Uncomment this section if you have ward boundaries)
// =====================================================

// INSTRUCTIONS TO ENABLE WARD-LEVEL COMPARISON:
// 1. Replace 'YOUR_ASSET_PATH' below with your actual ward boundaries asset
// 2. Uncomment all code in this section
// 3. Run the script

/*
print('');
print('===== WARD-LEVEL AGGREGATION (FOR DIRECT COMPARISON) =====');

// Load ward boundaries - REPLACE THIS WITH YOUR ACTUAL PATH
var wards = ee.FeatureCollection('users/YOUR_USERNAME/nigeria_wards');
// OR if you uploaded as asset: var wards = ee.FeatureCollection('projects/your-project/assets/nigeria_wards');

// Filter to Delta State
var deltaWards = wards.filter(ee.Filter.eq('StateName', 'Delta'));
// OR if different column name: var deltaWards = wards.filter(ee.Filter.eq('ADM1_NAME', 'Delta'));

print('Delta State wards loaded:', deltaWards.size());

// Bernard's calculateUrbanPercentage function
function calculateUrbanPercentage(binaryMask, wardGeometry, scale) {
  binaryMask = binaryMask.unmask(0).clamp(0, 1);

  var urbanArea = binaryMask.multiply(ee.Image.pixelArea())
    .reduceRegion({
      reducer: ee.Reducer.sum(),
      geometry: wardGeometry,
      scale: scale,
      maxPixels: 1e13,
      tileScale: 2
    });

  var areaValue = ee.Number(urbanArea.values().get(0));
  var totalArea = wardGeometry.area();

  var percentage = ee.Algorithms.If(
    totalArea.gt(0),
    areaValue.divide(totalArea).multiply(100).min(100),
    0
  );

  return ee.Number(percentage);
}

// Calculate DBI percentage for each ward
var wardStats = deltaWards.map(function(ward) {
  var wardGeom = ward.geometry();

  var dbiPercent = calculateUrbanPercentage(
    dbiImage.unmask(0),
    wardGeom,
    30
  );

  return ward.set('dbi_grace_method', dbiPercent);
});

// Calculate statistics
var dbiStats = wardStats.aggregate_stats('dbi_grace_method');
print('');
print('Ward-Level Statistics (Grace\'s Method):');
print('  Mean DBI:', dbiStats.get('mean'), '%');
print('  Min DBI:', dbiStats.get('min'), '%');
print('  Max DBI:', dbiStats.get('max'), '%');
print('');
print('COMPARE TO BERNARD\'S ORIGINAL:');
print('  Bernard\'s Mean: 5.44%');
print('  Bernard\'s Min: 0.00%');
print('  Bernard\'s Max: 47.96%');
print('');
print('If values match within 5%, methods are equivalent!');
print('');

// Export ward-level comparison CSV
Export.table.toDrive({
  collection: wardStats,
  description: 'Delta_Ward_Comparison_Grace_Method',
  folder: 'DBI_exports',
  fileFormat: 'CSV'
});

print('✅ Ward-level CSV export task created');
*/

// =====================================================
// SUMMARY
// =====================================================

print('');
print('===== NEXT STEPS =====');
print('1. Check console output above for validation statistics');
print('2. Go to Tasks tab and run the export');
print('3. Download the raster from Google Drive');
print('4. If ward boundaries available, uncomment ward comparison section');
print('5. Compare results to Bernard\'s original Delta State analysis');
print('');
print('EXPECTED OUTCOMES:');
print('A. If pixel mean ~0.05-0.10 → Raster is correct (5-10% urban)');
print('B. If ward-level mean ~5.4% → Matches Bernard\'s original ✅');
print('C. If results differ significantly → Investigate differences');
print('');
print('TO INVESTIGATE GRACE\'S 0-1 VALUES:');
print('Need to see her SECOND script that calculates buffer percentages');
print('(Line 7 in contxt.md: "I used THIS CODE to calculate percentages')
print(' urban within 2km buffer of each cluster point")');
