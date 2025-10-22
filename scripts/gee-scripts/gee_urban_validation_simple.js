// =====================================================
// SIMPLIFIED URBAN VALIDATION - FOCUS ON WORKING METHODS
// =====================================================

// Import ward boundaries (already imported as 'table')
var wards = table;
print('Total wards loaded:', wards.size());

// Nigeria boundary
var nigeria = ee.FeatureCollection("FAO/GAUL_SIMPLIFIED_500m/2015/level0")
  .filter(ee.Filter.eq('ADM0_NAME', 'Nigeria'));

Map.centerObject(nigeria, 6);

// ========== METHOD 1: Simple NDBI from Sentinel-2 ==========
function getNDBI() {
  // Get Sentinel-2 without complex cloud masking
  var s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterDate('2022-01-01', '2023-12-31')
    .filterBounds(nigeria)
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
    .select(['B11', 'B8', 'B4'])  // Only bands we need
    .median();
  
  // Simple NDBI calculation
  var ndbi = s2.normalizedDifference(['B11', 'B8']);
  
  // Convert to urban percentage (simple thresholds)
  var urban = ndbi
    .multiply(100)  // Scale to percentage
    .add(50)        // Shift from -100 to 100 range to 0-100
    .clamp(0, 100)
    .rename('ndbi_urban_percent');
  
  return urban.reproject({crs: 'EPSG:4326', scale: 100});
}

// ========== METHOD 2: GHSL (Most Reliable) ==========
function getGHSL() {
  // GHSL SMOD 2020 - this should definitely work
  var smod = ee.Image('JRC/GHSL/P2023A/GHS_SMOD/2020')
    .select('smod_code')
    .clip(nigeria);
  
  // Simple remapping
  var urban = smod.remap(
    [10, 11, 12, 13, 21, 22, 23, 30],  // Input values
    [0,  5,  10, 20, 40, 60, 80, 95]   // Urban percentages
  ).rename('ghsl_urban_percent');
  
  return urban.reproject({crs: 'EPSG:4326', scale: 100});
}

// ========== METHOD 3: MODIS Urban Mask ==========
function getMODIS() {
  // MODIS Land Cover - Urban class
  var modis = ee.ImageCollection('MODIS/006/MCD12Q1')
    .filterDate('2021-01-01', '2021-12-31')
    .first()
    .select('LC_Type1')
    .clip(nigeria);
  
  // Binary urban mask (class 13 = urban)
  var urban = modis.eq(13)
    .multiply(100)  // Convert to percentage (0 or 100)
    .rename('modis_urban_percent');
  
  return urban.reproject({crs: 'EPSG:4326', scale: 100});
}

// ========== METHOD 4: Night Lights as Urban Proxy ==========
function getNightLights() {
  // VIIRS Night lights
  var viirs = ee.ImageCollection('NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG')
    .filterDate('2022-01-01', '2023-12-31')
    .select('avg_rad')
    .median()
    .clip(nigeria);
  
  // Convert to urban percentage based on light intensity
  var urban = viirs
    .where(viirs.lt(1), 0)      // No lights = 0% urban
    .where(viirs.gte(1).and(viirs.lt(5)), 30)   // Low lights
    .where(viirs.gte(5).and(viirs.lt(15)), 60)  // Medium lights  
    .where(viirs.gte(15), 90)   // Bright lights = highly urban
    .rename('nightlights_urban_percent');
  
  return urban.reproject({crs: 'EPSG:4326', scale: 100});
}

// ========== Run Methods ==========
print('Getting urban layers...');

var ndbi = getNDBI();
var ghsl = getGHSL();
var modis = getMODIS();
var nightlights = getNightLights();

// Add to map
Map.addLayer(ndbi, {min: 0, max: 100, palette: ['green', 'yellow', 'red']}, 'NDBI Urban %', false);
Map.addLayer(ghsl, {min: 0, max: 100, palette: ['green', 'yellow', 'red']}, 'GHSL Urban %', false);
Map.addLayer(modis, {min: 0, max: 100, palette: ['green', 'yellow', 'red']}, 'MODIS Urban %', false);
Map.addLayer(nightlights, {min: 0, max: 100, palette: ['green', 'yellow', 'red']}, 'Night Lights Urban %', false);

// ========== Stack Images ==========
var urbanStack = ee.Image.cat([ndbi, ghsl, modis, nightlights]);
print('Stacked bands:', urbanStack.bandNames());

// ========== Calculate Ward Statistics ==========
print('Calculating ward statistics...');

var wardStats = urbanStack.reduceRegions({
  collection: wards,
  reducer: ee.Reducer.mean(),
  scale: 100,
  crs: 'EPSG:4326'
});

// Add mean and classification
wardStats = wardStats.map(function(feature) {
  // Get values
  var ndbiVal = ee.Number(feature.get('ndbi_urban_percent'));
  var ghslVal = ee.Number(feature.get('ghsl_urban_percent'));
  var modisVal = ee.Number(feature.get('modis_urban_percent'));
  var nightVal = ee.Number(feature.get('nightlights_urban_percent'));
  
  // Calculate mean
  var meanUrban = ndbiVal.add(ghslVal).add(modisVal).add(nightVal).divide(4);
  
  // Classify based on mean of all methods
  var classification = ee.Algorithms.If(meanUrban.gt(50), 'Urban', 
    ee.Algorithms.If(meanUrban.gt(30), 'Peri-urban', 'Rural'));
  
  // Check consistency across methods
  var allLow = ee.Algorithms.And(
    ee.Algorithms.And(ndbiVal.lt(30), ghslVal.lt(30)),
    ee.Algorithms.And(modisVal.lt(30), nightVal.lt(30))
  );
  
  var consistentlyRural = ee.Algorithms.If(allLow, 'YES', 'NO');
  
  return feature
    .set('mean_urban_percent', meanUrban)
    .set('classification', classification)
    .set('consistently_rural', consistentlyRural)
    .set('ndbi_percent', ndbiVal)
    .set('ghsl_percent', ghslVal)
    .set('modis_percent', modisVal)
    .set('nightlights_percent', nightVal);
});

// ========== EXPORTS ==========

// Export to Cloud Storage
Export.table.toCloudStorage({
  collection: wardStats,
  description: 'Urban_Validation_Simple',
  bucket: 'urban-validation-nigeria',
  fileNamePrefix: 'validation/urban_validation_simple_2022_2023',
  fileFormat: 'CSV'
});

// Also export to Drive for easy access
Export.table.toDrive({
  collection: wardStats,
  description: 'Urban_Validation_Simple_Drive',
  folder: 'GEE_Urban_Validation',
  fileNamePrefix: 'urban_validation_simple_2022_2023',
  fileFormat: 'CSV'
});

// ========== Print Summary ==========
print('Sample results (first 10 wards):');
print(wardStats.limit(10));

// Count consistently rural wards
var ruralCount = wardStats
  .filter(ee.Filter.eq('consistently_rural', 'YES'))
  .size();

print('Consistently rural wards (across all methods):', ruralCount);

// Also show classification distribution
var urbanCount = wardStats.filter(ee.Filter.eq('classification', 'Urban')).size();
var periUrbanCount = wardStats.filter(ee.Filter.eq('classification', 'Peri-urban')).size();
var ruralClassCount = wardStats.filter(ee.Filter.eq('classification', 'Rural')).size();

print('Classification distribution:');
print('Urban wards:', urbanCount);
print('Peri-urban wards:', periUrbanCount);  
print('Rural wards:', ruralClassCount);

print('=== COMPLETE ===');
print('Exports ready in Tasks tab');
print('This compares multiple urban detection methods to find consistently rural wards');