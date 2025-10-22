// ----------------------------------------
// EXTRACT DHS VALUES FROM 2018 NDMI/NDWI FILES (MONTHS 1-6)
// FIXED VERSION - Using correct tile naming from bucket
// ----------------------------------------

// Load 2018 DHS points
var points = ee.FeatureCollection("projects/epidemiological-intelligence/assets/2018_DHS_cluster_points");

// Buffer each point by 2000 meters
var bufferedPoints = points.map(function(feature) {
  return feature.buffer(2000);
});

// Load Nigeria boundary
var nigeria = ee.FeatureCollection('FAO/GAUL/2015/level0')
                .filter(ee.Filter.eq('ADM0_NAME', 'Nigeria'));

Map.centerObject(nigeria, 6);
Map.addLayer(nigeria, {color: 'blue'}, 'Nigeria Boundary');
Map.addLayer(bufferedPoints, {color: 'green'}, '2018 DHS Clusters (2km buffer)', false);

// ----------------------------------------
// CONFIGURATION FOR 2018 MONTHS 1-6
// ----------------------------------------
var BUCKET = 'ndmi_ndwi30m';
var year = 2018;
var months = [1, 2, 3, 4, 5, 6];  // January to June

// CORRECT tile suffixes based on what's actually in the bucket
// For months 1-6, the pattern is: 0000000000/0000023296 (not 0000032768)
var tileSuffixes = [
  '0000000000-0000000000',
  '0000000000-0000023296',
  '0000023296-0000000000',
  '0000023296-0000023296'
];

// ----------------------------------------
// PROCESSING FUNCTIONS
// ----------------------------------------
function loadAndMosaicMonth(indexType, month) {
  var monthStr = (month < 10) ? '0' + month : '' + month;
  
  print('Loading ' + indexType + ' for ' + year + '-' + monthStr);
  
  // Load all 4 tiles for this month
  var tiles = [];
  var successCount = 0;
  
  for (var i = 0; i < tileSuffixes.length; i++) {
    // Build the exact file path as it appears in the bucket
    var filePath = 'gs://' + BUCKET + '/' + indexType + '_' + year + '_' + monthStr + tileSuffixes[i] + '.tif';
    
    try {
      var tile = ee.Image.loadGeoTIFF(filePath);
      tiles.push(tile);
      successCount++;
      print('  ✓ Loaded tile ' + (i+1) + ': ' + tileSuffixes[i]);
    } catch (e) {
      print('  ✗ Failed to load: ' + filePath);
    }
  }
  
  if (successCount === 4) {
    print('  Success: All 4 tiles loaded for ' + indexType + ' ' + monthStr);
    // Mosaic all tiles and clip to Nigeria
    return ee.ImageCollection(tiles).mosaic().clip(nigeria);
  } else {
    print('  ERROR: Only ' + successCount + '/4 tiles loaded for ' + indexType + ' ' + monthStr);
    return null;
  }
}

// ----------------------------------------
// EXTRACT VALUES FOR EACH MONTH
// ----------------------------------------
var exportCount = 0;

months.forEach(function(month) {
  var monthStr = (month < 10) ? '0' + month : '' + month;
  
  print('\n========================================');
  print('Processing ' + year + '-' + monthStr);
  print('========================================');
  
  // Load and process NDMI
  var ndmi = loadAndMosaicMonth('NDMI', month);
  if (ndmi) {
    // Extract values at buffered points
    var ndmiSamples = ndmi.rename('NDMI').reduceRegions({
      collection: bufferedPoints,
      reducer: ee.Reducer.mean(),
      scale: 30,
      tileScale: 16
    });
    
    // Add month metadata
    ndmiSamples = ndmiSamples.map(function(feature) {
      return feature.set({
        'year': year,
        'month': month,
        'year_month': year + '_' + monthStr
      });
    });
    
    // Export NDMI for this month separately
    Export.table.toDrive({
      collection: ndmiSamples,
      description: 'DHS_2018_NDMI_' + monthStr,
      folder: 'DHS_Extracts',
      fileNamePrefix: 'DHS_2018_NDMI_' + monthStr,
      fileFormat: 'CSV'
    });
    
    exportCount++;
    print('✓ Created NDMI export for month ' + monthStr);
    
    // Add to map (first month only for visualization)
    if (month === 1) {
      Map.addLayer(ndmi, {min: -1, max: 1, palette: ['red', 'yellow', 'green', 'cyan', 'blue']}, 
                   'NDMI ' + year + '-' + monthStr, false);
    }
  } else {
    print('✗ Skipped NDMI export for month ' + monthStr + ' - data not available');
  }
  
  // Load and process NDWI
  var ndwi = loadAndMosaicMonth('NDWI', month);
  if (ndwi) {
    // Extract values at buffered points
    var ndwiSamples = ndwi.rename('NDWI').reduceRegions({
      collection: bufferedPoints,
      reducer: ee.Reducer.mean(),
      scale: 30,
      tileScale: 16
    });
    
    // Add month metadata
    ndwiSamples = ndwiSamples.map(function(feature) {
      return feature.set({
        'year': year,
        'month': month,
        'year_month': year + '_' + monthStr
      });
    });
    
    // Export NDWI for this month separately
    Export.table.toDrive({
      collection: ndwiSamples,
      description: 'DHS_2018_NDWI_' + monthStr,
      folder: 'DHS_Extracts',
      fileNamePrefix: 'DHS_2018_NDWI_' + monthStr,
      fileFormat: 'CSV'
    });
    
    exportCount++;
    print('✓ Created NDWI export for month ' + monthStr);
    
    // Add to map (first month only for visualization)
    if (month === 1) {
      Map.addLayer(ndwi, {min: -1, max: 1, palette: ['brown', 'white', 'blue', 'darkblue']}, 
                   'NDWI ' + year + '-' + monthStr, false);
    }
  } else {
    print('✗ Skipped NDWI export for month ' + monthStr + ' - data not available');
  }
});

// ----------------------------------------
// SUMMARY
// ----------------------------------------
print('\n============================================================');
print('EXTRACTION COMPLETE FOR 2018 MONTHS 1-6');
print('============================================================');
print('');
print('Export tasks created: ' + exportCount);
print('Expected: Up to 12 tasks (6 months × 2 indices)');
print('');
print('Files are using the pattern:');
print('  NDMI_2018_010000000000-0000000000.tif (not 01-0000032768)');
print('  4 tiles per month with coordinates: 0000000000/0000023296');
print('');
print('NEXT STEPS:');
print('1. Go to Tasks tab');
print('2. Click RUN on all export tasks');
print('3. Files will be saved to Google Drive/DHS_Extracts/');
print('');
print('The exports will create separate files for each month:');
print('  - DHS_2018_NDMI_01.csv');
print('  - DHS_2018_NDMI_02.csv');
print('  - ... (6 NDMI files total)');
print('  - DHS_2018_NDWI_01.csv');
print('  - DHS_2018_NDWI_02.csv');
print('  - ... (6 NDWI files total)');