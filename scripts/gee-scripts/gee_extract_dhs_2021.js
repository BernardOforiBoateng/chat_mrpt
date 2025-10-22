// ----------------------------------------
// EXTRACT DHS VALUES FROM 2021 NDMI/NDWI FILES
// Using 2021 DHS cluster points (or 2021/2022 survey)
// ----------------------------------------

// Load 2021 DHS points - UPDATE THIS PATH to your 2021 DHS asset
var points = ee.FeatureCollection("projects/epidemiological-intelligence/assets/2021_DHS_cluster_points");

// Buffer each point by 2000 meters
var bufferedPoints = points.map(function(feature) {
  return feature.buffer(2000);
});

// Load Nigeria boundary
var nigeria = ee.FeatureCollection('FAO/GAUL/2015/level0')
                .filter(ee.Filter.eq('ADM0_NAME', 'Nigeria'));

Map.centerObject(nigeria, 6);
Map.addLayer(nigeria, {color: 'blue'}, 'Nigeria Boundary');
Map.addLayer(bufferedPoints, {color: 'purple'}, '2021 DHS Clusters (2km buffer)', false);

// ----------------------------------------
// CONFIGURATION FOR 2021
// ----------------------------------------
var BUCKET = 'ndmi_ndwi30m';
var year = 2021;
var months = [7, 8, 9, 10, 11, 12];  // July to December

// Tile suffixes for 2021 files
var tileSuffixes = [
  '-0000000000-0000000000',
  '-0000000000-0000032768',
  '-0000032768-0000000000',
  '-0000032768-0000032768'
];

// ----------------------------------------
// PROCESSING FUNCTIONS
// ----------------------------------------
function loadAndMosaicMonth(indexType, month) {
  var monthStr = (month < 10) ? '0' + month : '' + month;
  
  // Load all 4 tiles for this month
  var tiles = [];
  
  for (var i = 0; i < tileSuffixes.length; i++) {
    var filePath = 'gs://' + BUCKET + '/' + indexType + '_' + year + '_' + monthStr + tileSuffixes[i] + '.tif';
    try {
      var tile = ee.Image.loadGeoTIFF(filePath);
      tiles.push(tile);
    } catch (e) {
      print('Warning: Could not load ' + filePath);
    }
  }
  
  if (tiles.length === 4) {
    // Mosaic all tiles and clip to Nigeria
    return ee.ImageCollection(tiles).mosaic().clip(nigeria);
  } else {
    print('Error: Expected 4 tiles for ' + indexType + '_' + year + '_' + monthStr + ', got ' + tiles.length);
    return null;
  }
}

// ----------------------------------------
// MAIN PROCESSING
// ----------------------------------------
print('Processing 2021 data from Cloud Storage...');
print('Files in bucket: gs://' + BUCKET + '/');
print('Using 2021 DHS cluster points');

var exportCount = 0;

months.forEach(function(month) {
  var monthStr = (month < 10) ? '0' + month : '' + month;
  print('\nProcessing ' + year + '-' + monthStr + '...');
  
  // Load and mosaic NDMI
  var ndmiMosaic = loadAndMosaicMonth('NDMI', month);
  
  // Load and mosaic NDWI
  var ndwiMosaic = loadAndMosaicMonth('NDWI', month);
  
  if (ndmiMosaic !== null && ndwiMosaic !== null) {
    // Visualize first month to verify
    if (month === 7) {
      Map.addLayer(ndmiMosaic, 
        {min: -1, max: 1, palette: ['red', 'yellow', 'green', 'cyan', 'blue']}, 
        'NDMI July 2021', false);
      Map.addLayer(ndwiMosaic, 
        {min: -1, max: 1, palette: ['brown', 'white', 'blue', 'darkblue']}, 
        'NDWI July 2021', false);
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

// ----------------------------------------
// SUMMARY
// ----------------------------------------
print('\n' + '='.repeat(50));
print('SUMMARY FOR 2021');
print('='.repeat(50));
print('Export tasks created: ' + exportCount + ' (should be 12)');
print('Output folders:');
print('  - Google Drive/DHS_NDMI_Extracts/ (6 NDMI files)');
print('  - Google Drive/DHS_NDWI_Extracts/ (6 NDWI files)');
print('');
print('NEXT STEPS:');
print('1. Upload your 2021 DHS cluster points as Earth Engine asset');
print('2. Update line 7 with the correct asset path');
print('3. Go to Tasks tab');
print('4. Click RUN on all 12 tasks');
print('');
print('IMPORTANT:');
print('Make sure you have uploaded your 2021 DHS points CSV as an Earth Engine asset!');
print('The path should be something like:');
print('projects/epidemiological-intelligence/assets/2021_DHS_cluster_points');
print('');
print('Note: If the DHS survey was conducted in 2021-2022, you may need to');
print('check the exact survey year and name your asset accordingly.');