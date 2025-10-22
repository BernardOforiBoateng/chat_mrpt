// ----------------------------------------
// EXTRACT DHS VALUES FROM 2015 NDMI/NDWI FILES
// For months 1-6 (single files, no tiles)
// ----------------------------------------

// Load 2015 DHS points
var points = ee.FeatureCollection("projects/epidemiological-intelligence/assets/2015_DHS_cluster_points");

// Buffer each point by 2000 meters
var bufferedPoints = points.map(function(feature) {
  return feature.buffer(2000);
});

// Load Nigeria boundary
var nigeria = ee.FeatureCollection('FAO/GAUL/2015/level0')
                .filter(ee.Filter.eq('ADM0_NAME', 'Nigeria'));

Map.centerObject(nigeria, 6);
Map.addLayer(nigeria, {color: 'blue'}, 'Nigeria Boundary');
Map.addLayer(bufferedPoints, {color: 'green'}, '2015 DHS Clusters (2km buffer)', false);

// ----------------------------------------
// CONFIGURATION FOR 2015 MONTHS 1-6
// ----------------------------------------
var BUCKET = 'ndmi_ndwi30m';
var year = 2015;
var months = [1, 2, 3, 4, 5, 6];  // January to June

// ----------------------------------------
// PROCESSING FUNCTIONS
// ----------------------------------------
function loadMonth(indexType, month) {
  var monthStr = (month < 10) ? '0' + month : '' + month;
  
  // Load single file (no tiles for months 1-6)
  var filePath = 'gs://' + BUCKET + '/' + indexType + '_' + year + '_' + monthStr + '.tif';
  
  try {
    return ee.Image.loadGeoTIFF(filePath).clip(nigeria);
  } catch (e) {
    print('Warning: Could not load ' + filePath);
    return null;
  }
}

// ----------------------------------------
// CREATE MONTHLY COMPOSITES
// ----------------------------------------
print('Creating monthly composites for 2015 months 1-6...');

// Create lists to hold monthly images
var ndmiImages = [];
var ndwiImages = [];

months.forEach(function(month) {
  var monthStr = (month < 10) ? '0' + month : '' + month;
  
  // Load NDMI
  var ndmi = loadMonth('NDMI', month);
  if (ndmi) {
    ndmiImages.push(ndmi.rename('NDMI_' + monthStr));
    print('✓ Loaded NDMI for month ' + monthStr);
  } else {
    print('✗ Missing NDMI for month ' + monthStr);
  }
  
  // Load NDWI
  var ndwi = loadMonth('NDWI', month);
  if (ndwi) {
    ndwiImages.push(ndwi.rename('NDWI_' + monthStr));
    print('✓ Loaded NDWI for month ' + monthStr);
  } else {
    print('✗ Missing NDWI for month ' + monthStr);
  }
});

// Stack all months
var ndmiStack = ee.Image(ndmiImages);
var ndwiStack = ee.Image(ndwiImages);

// Add visualization for the first month
Map.addLayer(ndmiImages[0], 
  {min: -1, max: 1, palette: ['red', 'yellow', 'green', 'cyan', 'blue']}, 
  'NDMI January 2015', false);
Map.addLayer(ndwiImages[0], 
  {min: -1, max: 1, palette: ['brown', 'white', 'blue', 'darkblue']}, 
  'NDWI January 2015', false);

// ----------------------------------------
// EXTRACT VALUES AT DHS POINTS
// ----------------------------------------
print('Extracting values at DHS points...');

// Extract NDMI values
var ndmiSamples = ndmiStack.reduceRegions({
  collection: bufferedPoints,
  reducer: ee.Reducer.mean(),
  scale: 30,
  tileScale: 4
});

// Extract NDWI values
var ndwiSamples = ndwiStack.reduceRegions({
  collection: bufferedPoints,
  reducer: ee.Reducer.mean(),
  scale: 30,
  tileScale: 4
});

// ----------------------------------------
// EXPORT RESULTS
// ----------------------------------------
// Export NDMI values
Export.table.toDrive({
  collection: ndmiSamples,
  description: 'DHS_2015_NDMI_months_1_6',
  folder: 'DHS_Extracts',
  fileNamePrefix: '2015_NDMI_months_1_6',
  fileFormat: 'CSV'
});

// Export NDWI values
Export.table.toDrive({
  collection: ndwiSamples,
  description: 'DHS_2015_NDWI_months_1_6',
  folder: 'DHS_Extracts',
  fileNamePrefix: '2015_NDWI_months_1_6',
  fileFormat: 'CSV'
});

// ----------------------------------------
// SUMMARY
// ----------------------------------------
print('\n' + '='.repeat(60));
print('DHS 2015 EXTRACTION SUMMARY (Months 1-6)');
print('='.repeat(60));
print('');
print('Processing:');
print('  - Year: 2015');
print('  - Months: January to June (1-6)');
print('  - DHS cluster points with 2km buffers');
print('  - Source: gs://' + BUCKET + '/');
print('');
print('Outputs:');
print('  - 2015_NDMI_months_1_6.csv');
print('  - 2015_NDWI_months_1_6.csv');
print('  - Export folder: Google Drive/DHS_Extracts/');
print('');
print('Each CSV will contain:');
print('  - Original DHS cluster attributes');
print('  - NDMI_01 through NDMI_06 (mean values)');
print('  - NDWI_01 through NDWI_06 (mean values)');
print('');
print('NEXT STEPS:');
print('1. Click RUN on both export tasks in the Tasks tab');
print('2. Files will export to Google Drive/DHS_Extracts/');
print('3. Combine with months 7-12 data for complete 2015 analysis');