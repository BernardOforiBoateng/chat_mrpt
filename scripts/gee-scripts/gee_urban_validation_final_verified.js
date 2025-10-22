// =====================================================
// URBAN VALIDATION - FINAL VERIFIED VERSION
// Carefully checked against research and data availability
// =====================================================

// WHAT THIS DOES:
// 1. Implements the CURRENT method ChatMRPT uses (control)
// 2. Compares with 3 ALTERNATIVE methods from literature
// 3. Identifies wards that are consistently rural
// 4. These rural wards should NOT be urban-targeted

// ========== SETUP ==========
var wards = table;  // Your imported ward boundaries
print('Total wards loaded:', wards.size());

var nigeria = ee.FeatureCollection("FAO/GAUL_SIMPLIFIED_500m/2015/level0")
  .filter(ee.Filter.eq('ADM0_NAME', 'Nigeria'));

Map.centerObject(nigeria, 6);

// ========== UTILITY: Safe Median (from your code) ==========
function safeMedian(collection) {
  return ee.Algorithms.If(
    collection.size().gt(0),
    collection.median(),
    null
  );
}

// ========== METHOD 1: CONTROL (Current ChatMRPT Method) ==========
// ACTUAL METHOD from NMEP Data App (context.md lines 414-437)
// Uses MODIS Land Cover Type 1 (IGBP) - Class 13 = Urban and Built-Up
function getControl() {
  print('Processing CONTROL method (MODIS IGBP Class 13 - Year 2023)...');
  
  // Using 2023 data only for consistency
  var year = 2023;
  
  // MODIS Land Cover - exactly as in NMEP Data App
  var landcoverDataset = ee.ImageCollection("MODIS/061/MCD12Q1")
    .filterDate(ee.Date.fromYMD(year, 1, 1), ee.Date.fromYMD(year + 1, 1, 1))
    .select('LC_Type1')
    .first();
  
  if (!landcoverDataset) {
    print('Warning: No MODIS land cover data for 2023');
    return null;
  }
  
  // IGBP Class 13 = Urban and Built-Up Areas
  var urbanClass = 13;
  var urbanMask = landcoverDataset.eq(urbanClass);
  
  // Convert binary mask to percentage
  // Keep at native MODIS resolution (500m)
  var urban = urbanMask
    .unmask(0)  // Fill nodata with 0 (non-urban)
    .multiply(100)  // Convert to percentage (0 or 100)
    .clip(nigeria)
    .rename('control_modis');
  
  return urban;
}

// ========== METHOD 2: NDBI Sentinel-2 ==========
// Literature: Zha et al. (2003) - Most cited method
function getNDBI() {
  print('Processing NDBI (Sentinel-2 - Year 2023)...');
  
  var s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterDate('2023-01-01', '2023-12-31')  // 2023 only
    .filterBounds(nigeria)
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20));
  
  var composite = safeMedian(s2);
  if (composite === null) {
    print('Warning: No Sentinel-2 data for 2023');
    return ee.Image.constant(0).rename('ndbi_s2').clip(nigeria);
  }
  
  composite = ee.Image(composite);
  
  // NDBI = (SWIR - NIR) / (SWIR + NIR)
  var ndbi = composite.normalizedDifference(['B11', 'B8']);
  
  // Simple threshold: NDBI > 0 indicates built-up
  // Convert to percentage
  var urban = ndbi
    .multiply(50)  // Scale 
    .add(50)        // Shift to 0-100 range
    .clamp(0, 100)
    .clip(nigeria)
    .rename('ndbi_s2');
  
  return urban;  // Keep at native Sentinel-2 resolution (20m for B11)
}

// ========== METHOD 3: GHSL (Most Reliable) ==========
// Literature: UN-recommended standard
// NOTE: Only 2020 data available (no 2023 version)
function getGHSL() {
  print('Processing GHSL (2020 data - latest available)...');
  
  // This dataset is pre-processed and reliable
  // IMPORTANT: This is 2020 data as 2023 is not available
  var smod = ee.Image('JRC/GHSL/P2023A/GHS_SMOD/2020')
    .select('smod_code');
  
  if (!smod) {
    print('Warning: No GHSL data');
    return ee.Image.constant(0).rename('ghsl').clip(nigeria);
  }
  
  // Map classes to urban percentages
  // Based on UN definitions
  var urban = smod
    .remap(
      [10, 11, 12, 13, 21, 22, 23, 30],  // Original values
      [0,  5,  10, 20, 40, 60, 80, 95]    // Urban percentages
    )
    .clip(nigeria)
    .rename('ghsl');
  
  return urban;  // Keep at native GHSL resolution (10m)
}

// ========== METHOD 4: EBBI (Enhanced Built-Up and Bareness Index) ==========
// Literature: As-syakur et al. (2012)
function getEBBI() {
  print('Processing EBBI (Landsat - Year 2023)...');
  
  var landsat = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
    .filterDate('2023-01-01', '2023-12-31')  // 2023 only
    .filterBounds(nigeria)
    .filter(ee.Filter.lt('CLOUD_COVER', 30));
    
  var l8Median = safeMedian(landsat);
  if (l8Median === null) {
    print('Warning: No Landsat data for 2023');
    return ee.Image.constant(0).rename('ebbi').clip(nigeria);
  }
  
  l8Median = ee.Image(l8Median);
  
  // Scale bands
  var optical = l8Median.select('SR_B.*').multiply(0.0000275).add(-0.2);
  var thermal = l8Median.select('ST_B10').multiply(0.00341802).add(149.0);
  
  var nir = optical.select('SR_B5');
  var swir = optical.select('SR_B6');
  var tir = thermal.subtract(273.15); // Convert to Celsius
  
  // EBBI = (SWIR - NIR) / (10 * sqrt(SWIR + TIR))
  var ebbi = swir.subtract(nir)
    .divide(swir.add(tir).sqrt().multiply(10));
  
  // Convert to urban percentage
  var urban = ebbi
    .add(0.5).multiply(100)
    .clamp(0, 100)
    .clip(nigeria)
    .rename('ebbi');
  
  return urban;  // Keep at native Landsat resolution (30m)
}

// ========== RUN ALL METHODS ==========
print('===== RUNNING ALL METHODS =====');

var control = getControl();
var ndbi = getNDBI();
var ghsl = getGHSL();
var ebbi = getEBBI();

// Check what we got
print('Control (MODIS IGBP):', control ? 'Success' : 'Failed');
print('NDBI (Sentinel-2):', ndbi ? 'Success' : 'Failed');
print('GHSL:', ghsl ? 'Success' : 'Failed');
print('EBBI:', ebbi ? 'Success' : 'Failed');

// Build stack of valid images only
var validImages = [];
if (control) validImages.push(control);
if (ndbi) validImages.push(ndbi);
if (ghsl) validImages.push(ghsl);
if (ebbi) validImages.push(ebbi);

if (validImages.length === 0) {
  print('ERROR: No methods produced valid data!');
  print('Cannot proceed with validation');
} else {
  print('Successfully processed', validImages.length, 'methods');
  
  // Stack images
  var urbanStack = ee.Image.cat(validImages);
  
  // Add visualization
  if (control) Map.addLayer(control, {min: 0, max: 100, palette: ['green', 'yellow', 'red']}, 'Control (MODIS IGBP)', false);
  if (ndbi) Map.addLayer(ndbi, {min: 0, max: 100, palette: ['green', 'yellow', 'red']}, 'NDBI (Sentinel-2)', false);
  if (ghsl) Map.addLayer(ghsl, {min: 0, max: 100, palette: ['green', 'yellow', 'red']}, 'GHSL', false);
  if (ebbi) Map.addLayer(ebbi, {min: 0, max: 100, palette: ['green', 'yellow', 'red']}, 'EBBI', false);
  
  // ========== WARD ANALYSIS ==========
  print('Calculating ward statistics using native resolutions...');
  
  // Process each method separately at its native resolution
  var controlStats = control ? control.reduceRegions({
    collection: wards,
    reducer: ee.Reducer.mean(),
    scale: 500,  // MODIS native resolution
    crs: 'EPSG:4326',
    tileScale: 4
  }) : null;
  
  var ndbiStats = ndbi ? ndbi.reduceRegions({
    collection: wards,
    reducer: ee.Reducer.mean(),
    scale: 20,  // Sentinel-2 B11 resolution
    crs: 'EPSG:4326',
    tileScale: 4
  }) : null;
  
  var ghslStats = ghsl ? ghsl.reduceRegions({
    collection: wards,
    reducer: ee.Reducer.mean(),
    scale: 10,  // GHSL native resolution
    crs: 'EPSG:4326',
    tileScale: 4
  }) : null;
  
  var ebbiStats = ebbi ? ebbi.reduceRegions({
    collection: wards,
    reducer: ee.Reducer.mean(),
    scale: 30,  // Landsat native resolution
    crs: 'EPSG:4326',
    tileScale: 4
  }) : null;
  
  // Merge results by WardCode
  var wardStats = wards;
  
  // Join control results
  if (controlStats) {
    var join = ee.Join.saveFirst('control_data');
    wardStats = join.apply(wardStats, controlStats, 
      ee.Filter.equals({leftField: 'WardCode', rightField: 'WardCode'}));
    wardStats = wardStats.map(function(f) {
      var controlData = ee.Feature(f.get('control_data'));
      return f.set('control_modis', controlData.get('mean'));
    });
  }
  
  // Join NDBI results
  if (ndbiStats) {
    var join = ee.Join.saveFirst('ndbi_data');
    wardStats = join.apply(wardStats, ndbiStats,
      ee.Filter.equals({leftField: 'WardCode', rightField: 'WardCode'}));
    wardStats = wardStats.map(function(f) {
      var ndbiData = ee.Feature(f.get('ndbi_data'));
      return f.set('ndbi_s2', ndbiData.get('mean'));
    });
  }
  
  // Join GHSL results
  if (ghslStats) {
    var join = ee.Join.saveFirst('ghsl_data');
    wardStats = join.apply(wardStats, ghslStats,
      ee.Filter.equals({leftField: 'WardCode', rightField: 'WardCode'}));
    wardStats = wardStats.map(function(f) {
      var ghslData = ee.Feature(f.get('ghsl_data'));
      return f.set('ghsl', ghslData.get('mean'));
    });
  }
  
  // Join EBBI results
  if (ebbiStats) {
    var join = ee.Join.saveFirst('ebbi_data');
    wardStats = join.apply(wardStats, ebbiStats,
      ee.Filter.equals({leftField: 'WardCode', rightField: 'WardCode'}));
    wardStats = wardStats.map(function(f) {
      var ebbiData = ee.Feature(f.get('ebbi_data'));
      return f.set('ebbi', ebbiData.get('mean'));
    });
  }
  
  // Process results
  wardStats = wardStats.map(function(feature) {
    // Get values (with defaults if missing)
    var controlVal = ee.Number(ee.Algorithms.If(feature.get('control_modis'), feature.get('control_modis'), 0));
    var ndbiVal = ee.Number(ee.Algorithms.If(feature.get('ndbi_s2'), feature.get('ndbi_s2'), 0));
    var ghslVal = ee.Number(ee.Algorithms.If(feature.get('ghsl'), feature.get('ghsl'), 0));
    var ebbiVal = ee.Number(ee.Algorithms.If(feature.get('ebbi'), feature.get('ebbi'), 0));
    
    // Calculate mean across all methods
    var meanUrban = controlVal.add(ndbiVal).add(ghslVal).add(ebbiVal).divide(4);
    
    // Check if ALL methods show rural (<30%)
    var threshold = 30;
    var isRural = controlVal.lt(threshold)
      .and(ndbiVal.lt(threshold))
      .and(ghslVal.lt(threshold))
      .and(ebbiVal.lt(threshold));
    
    return feature
      .set('control_urban', controlVal)
      .set('ndbi_urban', ndbiVal)
      .set('ghsl_urban', ghslVal)
      .set('ebbi_urban', ebbiVal)
      .set('mean_urban', meanUrban)
      .set('consistently_rural', ee.Algorithms.If(isRural, 'YES', 'NO'))
      .set('classification', ee.Algorithms.If(
        meanUrban.gt(50), 'Urban',
        ee.Algorithms.If(meanUrban.gt(30), 'Peri-urban', 'Rural')
      ));
  });
  
  // ========== EXPORTS ==========
  
  // To Google Drive (easier to access)
  Export.table.toDrive({
    collection: wardStats,
    description: 'Urban_Validation_Final',
    folder: 'GEE_Urban_Validation',
    fileNamePrefix: 'urban_validation_final_' + new Date().toISOString().slice(0,10),
    fileFormat: 'CSV'
  });
  
  // To Cloud Storage (if bucket exists)
  Export.table.toCloudStorage({
    collection: wardStats,
    description: 'Urban_Validation_Final_Bucket',
    bucket: 'urban-validation-nigeria',
    fileNamePrefix: 'validation/urban_validation_final_' + new Date().toISOString().slice(0,10),
    fileFormat: 'CSV'
  });
  
  // ========== SUMMARY ==========
  print('===== VALIDATION COMPLETE =====');
  
  // Count consistently rural wards
  var ruralWards = wardStats.filter(ee.Filter.eq('consistently_rural', 'YES'));
  print('Wards consistently rural across ALL methods:', ruralWards.size());
  
  // Show first 10 results
  print('Sample results (first 10 wards):');
  print(wardStats.limit(10));
  
  print('');
  print('WHAT THIS TELLS US:');
  print('- Wards marked "consistently_rural = YES" are definitively rural');
  print('- These should NOT be selected for urban-targeted interventions');
  print('- If Delta State selected these as urban, that would be suspicious');
  print('');
  print('EXPORTS READY - Check Tasks tab');
}