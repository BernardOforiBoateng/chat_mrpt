// ----------------------------------------
// EXTRACT DHS VALUES FROM 2018 AND 2021 NDMI/NDWI FILES
// ----------------------------------------

// Load DHS points
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
Map.addLayer(bufferedPoints, {color: 'red'}, 'DHS Clusters (2km buffer)', false);

// ----------------------------------------
// CONFIGURATION
// ----------------------------------------
var BUCKET = 'ndmi_ndwi30m';
var years = [2018, 2021];  // Process both years
var months = [7, 8, 9, 10, 11, 12];  // July to December

// Note: 2018 and 2021 files use different tile suffixes
// 2018: uses -0000032768 pattern
// 2021: uses -0000032768 pattern
var tileSuffixes = [
  '-0000000000-0000000000',
  '-0000000000-0000032768',
  '-0000032768-0000000000',
  '-0000032768-0000032768'
];

// ----------------------------------------
// PROCESSING FUNCTIONS
// ----------------------------------------
function loadAndMosaicMonth(indexType, year, month) {
  var monthStr = (month < 10) ? '0' + month : '' + month;
  
  // Load all 4 tiles for this month
  var tiles = [];
  
  for (var i = 0; i < tileSuffixes.length; i++) {
    var filePath = 'gs://' + BUCKET + '/' + indexType + '_' + year + '_' + monthStr + tileSuffixes[i] + '.tif';
    var tile = ee.Image.loadGeoTIFF(filePath);
    tiles.push(tile);
  }
  
  // Mosaic all tiles and clip to Nigeria
  return ee.ImageCollection(tiles).mosaic().clip(nigeria);
}

// ----------------------------------------
// MAIN PROCESSING
// ----------------------------------------
print('Processing 2018 and 2021 data from Cloud Storage...');
print('Files in bucket: gs://' + BUCKET + '/');

var exportCount = 0;

// Process each year
years.forEach(function(year) {
  print('\n' + '='.repeat(40));
  print('Processing Year: ' + year);
  print('='.repeat(40));
  
  months.forEach(function(month) {
    var monthStr = (month < 10) ? '0' + month : '' + month;
    print('\nProcessing ' + year + '-' + monthStr + '...');
    
    // Load and mosaic NDMI
    var ndmiMosaic = loadAndMosaicMonth('NDMI', year, month);
    
    // Load and mosaic NDWI
    var ndwiMosaic = loadAndMosaicMonth('NDWI', year, month);
    
    if (ndmiMosaic !== null && ndwiMosaic !== null) {
      // Visualize first month of each year to verify
      if (month === 7) {
        Map.addLayer(ndmiMosaic, 
          {min: -1, max: 1, palette: ['red', 'yellow', 'green', 'cyan', 'blue']}, 
          'NDMI July ' + year, false);
        Map.addLayer(ndwiMosaic, 
          {min: -1, max: 1, palette: ['brown', 'white', 'blue', 'darkblue']}, 
          'NDWI July ' + year, false);
      }
      
      // Extract NDMI values at DHS clusters
      var ndmiSamples = ndmiMosaic.rename('NDMI').reduceRegions({
        collection: bufferedPoints,
        reducer: ee.Reducer.mean(),
        scale: 30,
        tileScale: 4
      });
      
      // Add metadata to NDMI samples
      ndmiSamples = ndmiSamples.map(function(feature) {
        return feature.set({
          'year': year,
          'month': month,
          'year_month': year + '_' + monthStr
        });
      });
      
      // Export NDMI to Drive
      Export.table.toDrive({
        collection: ndmiSamples,
        description: 'DHS_NDMI_' + year + '_' + monthStr,
        folder: 'DHS_NDMI_Extracts',
        fileFormat: 'CSV'
      });
      
      // Extract NDWI values at DHS clusters
      var ndwiSamples = ndwiMosaic.rename('NDWI').reduceRegions({
        collection: bufferedPoints,
        reducer: ee.Reducer.mean(),
        scale: 30,
        tileScale: 4
      });
      
      // Add metadata to NDWI samples
      ndwiSamples = ndwiSamples.map(function(feature) {
        return feature.set({
          'year': year,
          'month': month,
          'year_month': year + '_' + monthStr
        });
      });
      
      // Export NDWI to Drive
      Export.table.toDrive({
        collection: ndwiSamples,
        description: 'DHS_NDWI_' + year + '_' + monthStr,
        folder: 'DHS_NDWI_Extracts',
        fileFormat: 'CSV'
      });
      
      exportCount += 2;  // 2 exports per month
      print('✓ Created NDMI export for ' + year + '-' + monthStr);
      print('✓ Created NDWI export for ' + year + '-' + monthStr);
    } else {
      print('✗ Skipped ' + year + '-' + monthStr + ' - missing data');
    }
  });
});

// ----------------------------------------
// SUMMARY
// ----------------------------------------
print('\n' + '='.repeat(50));
print('SUMMARY FOR 2018 AND 2021');
print('='.repeat(50));
print('Export tasks created: ' + exportCount + ' (should be 24)');
print('  - 2018: 12 tasks (6 NDMI + 6 NDWI)');
print('  - 2021: 12 tasks (6 NDMI + 6 NDWI)');
print('');
print('Output folders:');
print('  - Google Drive/DHS_NDMI_Extracts/');
print('  - Google Drive/DHS_NDWI_Extracts/');
print('');
print('NEXT STEPS:');
print('1. Go to Tasks tab');
print('2. Click RUN on all 24 tasks');
print('3. Files will be saved as:');
print('   - DHS_NDMI_2018_07.csv through DHS_NDMI_2018_12.csv');
print('   - DHS_NDWI_2018_07.csv through DHS_NDWI_2018_12.csv');
print('   - DHS_NDMI_2021_07.csv through DHS_NDMI_2021_12.csv');
print('   - DHS_NDWI_2021_07.csv through DHS_NDWI_2021_12.csv');
print('');
print('Once complete, you will have DHS extracts for:');
print('  - 2015 (if already run)');
print('  - 2018 (from this script)');
print('  - 2021 (from this script)');
print('');
print('Still need 2023 and 2024 data to be uploaded to Cloud Storage.');