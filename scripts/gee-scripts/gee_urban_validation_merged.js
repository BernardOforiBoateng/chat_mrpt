// =====================================================
// URBAN PERCENTAGE VALIDATION - MERGED VERSION
// Combining robust error handling with ward-level analysis
// =====================================================

// ========== Time Range (2022-2023 for recent data) ==========
var startDate = '2022-01-01';
var endDate = '2023-12-31';

// ========== Define Nigeria AOI ==========
var nigeria = ee.FeatureCollection("FAO/GAUL_SIMPLIFIED_500m/2015/level0")
  .filter(ee.Filter.eq('ADM0_NAME', 'Nigeria'));

// ========== Use imported ward boundaries (from table variable) ==========
var wards = table;  // This uses your imported shapefile
print('Total wards loaded:', wards.size());
print('Sample ward properties:', wards.first());

Map.centerObject(nigeria, 6);

// ========== Utility: Safe Composite ==========
function safeMedian(collection) {
  return ee.Algorithms.If(
    collection.size().gt(0),
    collection.median(),
    null
  );
}

// ========== CONTROL METHOD: NASA HLS NDBI + MODIS ==========
function calculateControlMethod() {
  print('=== Processing Control Method ===');
  
  // NASA HLS
  var hlsCollection = ee.ImageCollection("NASA/HLS/HLSL30/v002")
    .filterDate(startDate, endDate)
    .filterBounds(nigeria)
    .filter(ee.Filter.lt('CLOUD_COVERAGE', 50));
  
  var hlsMedian = safeMedian(hlsCollection);
  var hlsUrban = null;
  
  if (hlsMedian !== null) {
    hlsMedian = ee.Image(hlsMedian);
    // Calculate NDBI for HLS
    var ndbi = hlsMedian.normalizedDifference(['B6', 'B5']).rename('NDBI_HLS');
    var ndvi = hlsMedian.normalizedDifference(['B5', 'B4']).rename('NDVI_HLS');
    var bui = ndbi.subtract(ndvi).rename('BUI_HLS');
    
    // Convert to urban percentage
    hlsUrban = bui
      .add(1).divide(2).multiply(100)
      .where(bui.lt(-0.2), 0)
      .where(bui.gt(0.3), 90)
      .clip(nigeria)
      .rename('control_hls_ndbi')
      .reproject({crs: 'EPSG:4326', scale: 100});
  }
  
  // MODIS Land Cover
  var modis = ee.ImageCollection('MODIS/006/MCD12Q1')
    .filterDate('2021-01-01', '2021-12-31')  // Use 2021 for MODIS (usually lags by 1-2 years)
    .first();
  
  var modisUrban = null;
  if (modis) {
    var urbanMask = modis.select('LC_Type1').eq(13);  // Urban class
    modisUrban = urbanMask
      .reduceNeighborhood({
        reducer: ee.Reducer.mean(),
        kernel: ee.Kernel.circle({radius: 500, units: 'meters'})
      })
      .multiply(100)
      .clip(nigeria)
      .rename('control_modis_igbp')
      .reproject({crs: 'EPSG:4326', scale: 100});
  }

  return {
    hls: hlsUrban,
    modis: modisUrban
  };
}

// ========== METHOD 1: NDBI using Sentinel-2 ==========
function calculateNDBIMethod() {
  print('=== Processing NDBI Sentinel-2 ===');
  
  var s2Collection = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterDate(startDate, endDate)
    .filterBounds(nigeria)
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30));
  
  var s2Median = safeMedian(s2Collection);
  if (s2Median === null) {
    print('Warning: No Sentinel-2 data available');
    return null;
  }

  s2Median = ee.Image(s2Median);
  
  // Cloud masking
  var qa = s2Median.select('QA60');
  var cloudBitMask = 1 << 10;
  var cirrusBitMask = 1 << 11;
  var mask = qa.bitwiseAnd(cloudBitMask).eq(0)
      .and(qa.bitwiseAnd(cirrusBitMask).eq(0));
  s2Median = s2Median.updateMask(mask);
  
  // Calculate NDBI
  var ndbi = s2Median.normalizedDifference(['B11', 'B8']).rename('NDBI');
  
  // Convert to urban percentage
  var urbanPercent = ndbi
    .where(ndbi.lt(-0.1), 0)
    .where(ndbi.gte(-0.1).and(ndbi.lt(0)), 10)
    .where(ndbi.gte(0).and(ndbi.lt(0.1)), 30)
    .where(ndbi.gte(0.1).and(ndbi.lt(0.2)), 50)
    .where(ndbi.gte(0.2).and(ndbi.lt(0.3)), 70)
    .where(ndbi.gte(0.3), 90)
    .clip(nigeria)
    .rename('ndbi_sentinel2')
    .reproject({crs: 'EPSG:4326', scale: 100});
  
  return urbanPercent;
}

// ========== METHOD 2: Africapolis ==========
function calculateAfricapolisMethod() {
  print('=== Processing Africapolis ===');
  
  // Get Sentinel-2 for built-up detection
  var s2Collection = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterDate(startDate, endDate)
    .filterBounds(nigeria)
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20));
  
  var s2Median = safeMedian(s2Collection);
  if (s2Median === null) {
    print('Warning: No Sentinel-2 data for Africapolis');
    return null;
  }
  
  s2Median = ee.Image(s2Median);
  var builtup = s2Median.normalizedDifference(['B11', 'B8']);
  var builtMask = builtup.gt(0);
  
  // Apply morphological operations for continuity
  var kernel = ee.Kernel.circle({radius: 200, units: 'meters'});
  var continuous = builtMask
    .focal_max({kernel: kernel, iterations: 1})
    .focal_min({kernel: kernel, iterations: 1});
  
  // Get population data
  var population = ee.ImageCollection('WorldPop/GP/100m/pop')
    .filterDate('2020-01-01', '2020-12-31')  // WorldPop 2020 is most recent complete year
    .filterBounds(nigeria);
  
  var popImage = safeMedian(population);
  if (popImage === null) {
    print('Warning: No WorldPop data available');
    return null;
  }
  
  popImage = ee.Image(popImage);
  
  // Calculate population density
  var popDensity = popImage
    .reduceNeighborhood({
      reducer: ee.Reducer.sum(),
      kernel: ee.Kernel.circle({radius: 1000, units: 'meters'})
    })
    .divide(3.14159);  // per km²
  
  // Apply Africapolis criteria
  var africanUrban = continuous
    .multiply(100)
    .where(popDensity.lt(100), 0)
    .where(popDensity.gte(100).and(popDensity.lt(300)), 20)
    .where(popDensity.gte(300).and(popDensity.lt(1000)), 50)
    .where(popDensity.gte(1000).and(popDensity.lt(5000)), 70)
    .where(popDensity.gte(5000), 90)
    .updateMask(continuous)
    .unmask(0)
    .clip(nigeria)
    .rename('africapolis')
    .reproject({crs: 'EPSG:4326', scale: 100});
  
  return africanUrban;
}

// ========== METHOD 3: GHSL ==========
function calculateGHSLMethod() {
  print('=== Processing GHSL ===');
  
  // GHSL SMOD - Use 2020 data from newer dataset
  var smod = ee.Image('JRC/GHSL/P2023A/GHS_SMOD/2020')
    .select('smod_code')
    .clip(nigeria);
  
  var ghslUrban = null;
  if (smod) {
    // Remap SMOD classes to urban percentage
    // New GHSL codes: 10=Water, 11-13=Rural, 21-23=Urban clusters, 30=Urban centres
    ghslUrban = smod
      .remap(
        [10, 11, 12, 13, 21, 22, 23, 30],
        [0,  0,  5,  10, 30, 50, 75, 95]
      )
      .rename('ghsl_degree')
      .reproject({crs: 'EPSG:4326', scale: 100});
  }
  
  // GHSL Built-up Surface (2020)
  var built = ee.Image('JRC/GHSL/P2023A/GHS_BUILT_S/2020')
    .select('built_surface')
    .clip(nigeria);
  
  var builtPercent = null;
  if (built) {
    // Already in percentage format (0-100)
    builtPercent = built
      .rename('ghsl_built_percent')
      .reproject({crs: 'EPSG:4326', scale: 100});
  }

  return {
    smod: ghslUrban,
    built: builtPercent
  };
}

// ========== METHOD 4: EBBI ==========
function calculateEBBIMethod() {
  print('=== Processing EBBI ===');
  
  var l8Collection = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
    .filterDate(startDate, endDate)
    .filterBounds(nigeria)
    .filter(ee.Filter.lt('CLOUD_COVER', 30));
  
  var l8Median = safeMedian(l8Collection);
  if (l8Median === null) {
    print('Warning: No Landsat 8 data available');
    return null;
  }

  l8Median = ee.Image(l8Median);
  
  // Scale bands
  var opticalBands = l8Median.select('SR_B.*').multiply(0.0000275).add(-0.2);
  var thermalBand = l8Median.select('ST_B10').multiply(0.00341802).add(149.0)
    .subtract(273.15);  // Convert to Celsius
  
  var nir = opticalBands.select('SR_B5');
  var swir = opticalBands.select('SR_B6');
  var tir = thermalBand;
  
  // EBBI calculation
  var ebbi = swir.subtract(nir)
    .divide(swir.add(tir).sqrt().multiply(10))
    .rename('EBBI');
  
  // Convert to urban percentage
  var ebbiUrban = ebbi
    .add(0.5).multiply(100)
    .clamp(0, 100)
    .clip(nigeria)
    .rename('ebbi')
    .reproject({crs: 'EPSG:4326', scale: 100});
  
  return ebbiUrban;
}

// ========== Run All Methods ==========
print('Processing all methods...');

var control = calculateControlMethod();
var ndbiMethod = calculateNDBIMethod();
var africapolisMethod = calculateAfricapolisMethod();
var ghslMethod = calculateGHSLMethod();
var ebbiMethod = calculateEBBIMethod();

// Debug prints
print('Control HLS:', control.hls);
print('Control MODIS:', control.modis);
print('NDBI:', ndbiMethod);
print('Africapolis:', africapolisMethod);
print('GHSL SMOD:', ghslMethod.smod);
print('GHSL Built:', ghslMethod.built);
print('EBBI:', ebbiMethod);

// ========== Visualization (add layers if not null) ==========
if (control.hls !== null) {
  Map.addLayer(control.hls, {min: 0, max: 100, palette: ['green', 'yellow', 'red']}, 
    'CONTROL: HLS NDBI', false);
}
if (control.modis !== null) {
  Map.addLayer(control.modis, {min: 0, max: 100, palette: ['green', 'yellow', 'red']}, 
    'CONTROL: MODIS IGBP', false);
}
if (ndbiMethod !== null) {
  Map.addLayer(ndbiMethod, {min: 0, max: 100, palette: ['green', 'yellow', 'orange', 'red']}, 
    'Method 1: NDBI Sentinel-2', false);
}
if (africapolisMethod !== null) {
  Map.addLayer(africapolisMethod, {min: 0, max: 100, palette: ['green', 'yellow', 'orange', 'red']}, 
    'Method 2: Africapolis', false);
}
if (ghslMethod.smod !== null) {
  Map.addLayer(ghslMethod.smod, {min: 0, max: 100, palette: ['green', 'yellow', 'orange', 'red']}, 
    'Method 3: GHSL SMOD', false);
}
if (ghslMethod.built !== null) {
  Map.addLayer(ghslMethod.built, {min: 0, max: 100, palette: ['green', 'yellow', 'orange', 'red']}, 
    'Method 3: GHSL Built', false);
}
if (ebbiMethod !== null) {
  Map.addLayer(ebbiMethod, {min: 0, max: 100, palette: ['green', 'yellow', 'orange', 'red']}, 
    'Method 4: EBBI', false);
}

// ========== Build Stack (only non-null images) ==========
var imagesToStack = [];

if (control && control.hls !== null) imagesToStack.push(control.hls);
if (control && control.modis !== null) imagesToStack.push(control.modis);
if (ndbiMethod !== null) imagesToStack.push(ndbiMethod);
if (africapolisMethod !== null) imagesToStack.push(africapolisMethod);
if (ghslMethod && ghslMethod.smod !== null) imagesToStack.push(ghslMethod.smod);
if (ghslMethod && ghslMethod.built !== null) imagesToStack.push(ghslMethod.built);
if (ebbiMethod !== null) imagesToStack.push(ebbiMethod);

// Check if we have any valid images
if (imagesToStack.length === 0) {
  print('ERROR: No valid urban percentage images were generated');
  print('Please check data availability for the study area and time period');
} else {
  print('Successfully stacked ' + imagesToStack.length + ' urban percentage layers');
  
  var urbanStack = ee.Image.cat(imagesToStack);
  print('Urban Stack bands:', urbanStack.bandNames());
  
  // ========== WARD-LEVEL ANALYSIS ==========
  print('Calculating ward-level statistics...');
  
  // Calculate mean urban percentage for each ward
  var wardStats = urbanStack.reduceRegions({
    collection: wards,
    reducer: ee.Reducer.mean(),
    scale: 100,
    crs: 'EPSG:4326',
    tileScale: 4  // Helps with memory for large operations
  });
  
  // Add comparison with existing Urban field from shapefile
  wardStats = wardStats.map(function(feature) {
    // Get existing urban classification
    var existingUrban = feature.get('Urban');
    
    // Calculate mean across all methods (if available)
    var values = [];
    if (control && control.hls !== null) values.push(feature.get('control_hls_ndbi'));
    if (control && control.modis !== null) values.push(feature.get('control_modis_igbp'));
    if (ndbiMethod !== null) values.push(feature.get('ndbi_sentinel2'));
    if (africapolisMethod !== null) values.push(feature.get('africapolis'));
    if (ghslMethod && ghslMethod.smod !== null) values.push(feature.get('ghsl_degree'));
    if (ghslMethod && ghslMethod.built !== null) values.push(feature.get('ghsl_built_percent'));
    if (ebbiMethod !== null) values.push(feature.get('ebbi'));
    
    // Calculate mean (handling nulls)
    var meanUrban = ee.List(values).reduce(ee.Reducer.mean());
    
    return feature
      .set('existing_urban_class', existingUrban)
      .set('calculated_mean_urban', meanUrban)
      .set('methods_count', values.length);
  });
  
  // ========== EXPORTS ==========
  
  // Export 1: Ward-level comparison
  Export.table.toCloudStorage({
    collection: wardStats,
    description: 'Urban_Validation_Ward_Comparison',
    bucket: 'urban-validation-nigeria',
    fileNamePrefix: 'ward_comparison/urban_validation_all_wards_2022_2023',
    fileFormat: 'CSV'
  });
  
  // Alternative: Export to Drive
  Export.table.toDrive({
    collection: wardStats,
    description: 'Urban_Validation_Ward_Comparison_Drive',
    folder: 'GEE_Urban_Validation',
    fileNamePrefix: 'urban_validation_all_wards_2022_2023',
    fileFormat: 'CSV'
  });
  
  // Export 2: Statistical correlation points
  var gridPoints = ee.FeatureCollection.randomPoints({
    region: nigeria.geometry(),
    points: 1000,
    seed: 42
  });
  
  var sampledPoints = urbanStack.sampleRegions({
    collection: gridPoints,
    scale: 100,
    geometries: false,
    tileScale: 4
  });
  
  Export.table.toCloudStorage({
    collection: sampledPoints,
    description: 'Urban_Methods_Correlation',
    bucket: 'urban-validation-nigeria',
    fileNamePrefix: 'correlation_analysis/methods_correlation_2022_2023',
    fileFormat: 'CSV'
  });
  
  // Export 3: Full image stack (optional)
  Export.image.toCloudStorage({
    image: urbanStack,
    description: 'Urban_Stack_Image',
    bucket: 'urban-validation-nigeria',
    fileNamePrefix: 'images/urban_stack_2022_2023',
    region: nigeria.geometry(),
    scale: 100,
    maxPixels: 1e13,
    fileFormat: 'GeoTIFF'
  });
  
  print('=== EXPORTS READY ===');
  print('1. Ward Comparison CSV - Compare calculated vs existing urban classification');
  print('2. Correlation Points CSV - For statistical analysis');
  print('3. Urban Stack Image - Full raster data');
  
  // ========== SAMPLE RESULTS ==========
  print('Sample ward results (first 5):');
  print(wardStats.limit(5));
  
  // Find discrepancies
  var discrepantWards = wardStats.filter(ee.Filter.and(
    ee.Filter.eq('Urban', 'Yes'),  // Marked as urban in shapefile
    ee.Filter.lt('calculated_mean_urban', 30)  // But calculated as rural
  ));
  
  print('Potentially misclassified wards (marked Urban but calculated <30%):');
  print(discrepantWards.size());
}

print('=== Script Complete ===');
print('Check Tasks tab for exports');
print('Results will help identify potentially swapped urban/rural wards for Thursday meeting');