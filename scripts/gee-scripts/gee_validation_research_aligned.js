// =====================================================
// URBAN VALIDATION - ALIGNED WITH LITERATURE RESEARCH
// Implementing methods from our literature review
// =====================================================

// Import ward boundaries (already imported as 'table')
var wards = table;
print('Total wards loaded:', wards.size());

// Nigeria boundary
var nigeria = ee.FeatureCollection("FAO/GAUL_SIMPLIFIED_500m/2015/level0")
  .filter(ee.Filter.eq('ADM0_NAME', 'Nigeria'));

Map.centerObject(nigeria, 6);

// =====================================================
// CONTROL METHOD: What ChatMRPT Currently Uses
// From our research: NASA HLS NDBI + MODIS IGBP
// =====================================================
function getControlMethod() {
  print('=== CONTROL: Current ChatMRPT Method ===');
  
  // Part 1: NASA HLS NDBI (as found in gee_urban_percentage_nigeria.js)
  var hls = ee.ImageCollection("NASA/HLS/HLSL30/v002")
    .filterDate('2022-01-01', '2023-12-31')
    .filterBounds(nigeria)
    .filter(ee.Filter.lt('CLOUD_COVERAGE', 30))
    .median();
  
  var hlsNDBI = null;
  if (hls) {
    // BUI = NDBI - NDVI (as per existing implementation)
    var ndbi = hls.normalizedDifference(['B6', 'B5']);
    var ndvi = hls.normalizedDifference(['B5', 'B4']);
    var bui = ndbi.subtract(ndvi);
    
    hlsNDBI = bui
      .add(1).divide(2).multiply(100)  // Scale to 0-100%
      .clamp(0, 100)
      .rename('control_hls_urban_percent');
  }
  
  // Part 2: MODIS IGBP Urban Class
  var modis = ee.ImageCollection('MODIS/006/MCD12Q1')
    .filterDate('2021-01-01', '2021-12-31')
    .first()
    .select('LC_Type1')
    .clip(nigeria);
  
  var modisUrban = modis.eq(13)  // Class 13 = Urban
    .focal_mean({radius: 500, units: 'meters'})
    .multiply(100)
    .rename('control_modis_urban_percent');
  
  // Average the two control methods
  var control = ee.ImageCollection([hlsNDBI, modisUrban]).mean()
    .rename('control_mean_urban_percent');
  
  return control.reproject({crs: 'EPSG:4326', scale: 100});
}

// =====================================================
// METHOD 1: NDBI using Sentinel-2
// From literature: Zha et al. (2003)
// =====================================================
function getNDBI_Sentinel2() {
  print('=== Method 1: NDBI (Sentinel-2) ===');
  
  var s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterDate('2022-01-01', '2023-12-31')
    .filterBounds(nigeria)
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
    .median();
  
  // NDBI = (SWIR - NIR) / (SWIR + NIR)
  // Sentinel-2: B11 (SWIR) and B8 (NIR)
  var ndbi = s2.normalizedDifference(['B11', 'B8']);
  
  // Convert to urban percentage based on literature thresholds
  var urban = ndbi
    .where(ndbi.lt(0), 0)           // Negative = not urban
    .where(ndbi.gte(0).and(ndbi.lt(0.1)), 30)   // Low built-up
    .where(ndbi.gte(0.1).and(ndbi.lt(0.2)), 60) // Medium built-up
    .where(ndbi.gte(0.2), 90)       // High built-up
    .rename('ndbi_urban_percent');
  
  return urban.reproject({crs: 'EPSG:4326', scale: 100});
}

// =====================================================
// METHOD 2: Africapolis Methodology
// From literature: OECD/SWAC (2020)
// 10,000 population + 200m building continuity
// =====================================================
function getAfricapolis() {
  print('=== Method 2: Africapolis ===');
  
  // Built-up detection from Sentinel-2
  var s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterDate('2022-01-01', '2023-12-31')
    .filterBounds(nigeria)
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
    .median();
  
  var builtup = s2.normalizedDifference(['B11', 'B8']).gt(0);
  
  // Apply 200m continuity criterion
  var kernel = ee.Kernel.circle({radius: 200, units: 'meters'});
  var continuous = builtup.focal_max({kernel: kernel});
  
  // Population density from WorldPop
  var population = ee.ImageCollection('WorldPop/GP/100m/pop')
    .filterDate('2020-01-01', '2020-12-31')
    .first()
    .clip(nigeria);
  
  // Population density per km²
  var popDensity = population.reduceNeighborhood({
    reducer: ee.Reducer.sum(),
    kernel: ee.Kernel.circle({radius: 1000, units: 'meters'})
  }).divide(3.14159);
  
  // Africapolis criteria: continuous built + population thresholds
  var urban = continuous.multiply(100)
    .where(popDensity.lt(100), 0)    // <100 people/km² = rural
    .where(popDensity.gte(100).and(popDensity.lt(500)), 30)   // Low urban
    .where(popDensity.gte(500).and(popDensity.lt(1500)), 60)  // Medium urban
    .where(popDensity.gte(1500), 90) // High urban
    .updateMask(continuous)
    .unmask(0)
    .rename('africapolis_urban_percent');
  
  return urban.reproject({crs: 'EPSG:4326', scale: 100});
}

// =====================================================
// METHOD 3: GHSL Degree of Urbanization
// From literature: Pesaresi et al. (2016), UN standard
// =====================================================
function getGHSL() {
  print('=== Method 3: GHSL Degree of Urbanization ===');
  
  var smod = ee.Image('JRC/GHSL/P2023A/GHS_SMOD/2020')
    .select('smod_code')
    .clip(nigeria);
  
  // GHSL classification codes to urban percentage
  var urban = smod.remap(
    [10, 11, 12, 13, 21, 22, 23, 30],
    [0,  0,  5,  10, 30, 50, 75, 95]  // Based on UN definitions
  ).rename('ghsl_urban_percent');
  
  return urban.reproject({crs: 'EPSG:4326', scale: 100});
}

// =====================================================
// METHOD 4: EBBI (Bonus Method)
// From literature: As-syakur et al. (2012)
// Enhanced Built-Up and Bareness Index
// =====================================================
function getEBBI() {
  print('=== Method 4: EBBI (Bonus) ===');
  
  var landsat = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
    .filterDate('2022-01-01', '2023-12-31')
    .filterBounds(nigeria)
    .filter(ee.Filter.lt('CLOUD_COVER', 30))
    .median();
  
  // Scale optical and thermal bands
  var optical = landsat.select('SR_B.*').multiply(0.0000275).add(-0.2);
  var thermal = landsat.select('ST_B10').multiply(0.00341802).add(149.0);
  
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
    .rename('ebbi_urban_percent');
  
  return urban.reproject({crs: 'EPSG:4326', scale: 100});
}

// =====================================================
// RUN ALL METHODS
// =====================================================
print('Processing all methods from literature...');

var control = getControlMethod();
var ndbi = getNDBI_Sentinel2();
var africapolis = getAfricapolis();
var ghsl = getGHSL();
var ebbi = getEBBI();

// Add to map for visualization
Map.addLayer(control, {min: 0, max: 100, palette: ['green', 'yellow', 'red']}, 'CONTROL (Current Method)', false);
Map.addLayer(ndbi, {min: 0, max: 100, palette: ['green', 'yellow', 'red']}, 'Method 1: NDBI', false);
Map.addLayer(africapolis, {min: 0, max: 100, palette: ['green', 'yellow', 'red']}, 'Method 2: Africapolis', false);
Map.addLayer(ghsl, {min: 0, max: 100, palette: ['green', 'yellow', 'red']}, 'Method 3: GHSL', false);
Map.addLayer(ebbi, {min: 0, max: 100, palette: ['green', 'yellow', 'red']}, 'Method 4: EBBI', false);

// =====================================================
// STACK AND ANALYZE
// =====================================================
var urbanStack = ee.Image.cat([control, ndbi, africapolis, ghsl, ebbi]);
print('Stacked bands:', urbanStack.bandNames());

// Calculate ward statistics
var wardStats = urbanStack.reduceRegions({
  collection: wards,
  reducer: ee.Reducer.mean(),
  scale: 100,
  crs: 'EPSG:4326'
});

// Process results
wardStats = wardStats.map(function(feature) {
  var controlVal = ee.Number(feature.get('control_mean_urban_percent'));
  var ndbiVal = ee.Number(feature.get('ndbi_urban_percent'));
  var africaVal = ee.Number(feature.get('africapolis_urban_percent'));
  var ghslVal = ee.Number(feature.get('ghsl_urban_percent'));
  var ebbiVal = ee.Number(feature.get('ebbi_urban_percent'));
  
  // Mean across all alternative methods (excluding control)
  var altMean = ndbiVal.add(africaVal).add(ghslVal).add(ebbiVal).divide(4);
  
  // Check if consistently rural across ALL methods
  var allRural = controlVal.lt(30)
    .and(ndbiVal.lt(30))
    .and(africaVal.lt(30))
    .and(ghslVal.lt(30))
    .and(ebbiVal.lt(30));
  
  return feature
    .set('control_percent', controlVal)
    .set('alternatives_mean', altMean)
    .set('consistently_rural', ee.Algorithms.If(allRural, 'YES', 'NO'))
    .set('classification', ee.Algorithms.If(altMean.gt(50), 'Urban',
      ee.Algorithms.If(altMean.gt(30), 'Peri-urban', 'Rural')));
});

// =====================================================
// EXPORTS
// =====================================================
Export.table.toCloudStorage({
  collection: wardStats,
  description: 'Urban_Validation_Research_Based',
  bucket: 'urban-validation-nigeria',
  fileNamePrefix: 'validation/research_based_validation_2022_2023',
  fileFormat: 'CSV'
});

Export.table.toDrive({
  collection: wardStats,
  description: 'Urban_Validation_Research_Based_Drive',
  folder: 'GEE_Urban_Validation',
  fileNamePrefix: 'research_based_validation_2022_2023',
  fileFormat: 'CSV'
});

// =====================================================
// SUMMARY
// =====================================================
print('=== VALIDATION SUMMARY ===');
print('Control Method: NASA HLS NDBI + MODIS IGBP (current ChatMRPT method)');
print('Alternative Methods:');
print('1. NDBI (Sentinel-2) - Zha et al. 2003');
print('2. Africapolis - OECD/SWAC 2020');
print('3. GHSL Degree of Urbanization - UN standard');
print('4. EBBI - As-syakur et al. 2012');

var ruralWards = wardStats.filter(ee.Filter.eq('consistently_rural', 'YES'));
print('Consistently rural wards across ALL methods:', ruralWards.size());

print('=== EXPORTS READY ===');
print('Results will show which wards are consistently rural');
print('These should NOT be selected for urban-targeted interventions');