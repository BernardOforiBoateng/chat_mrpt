// ----------------------------------------
// EXTRACT DHS VALUES FROM 2015 NDMI/NDWI FILES IN CLOUD STORAGE
// Start with 2015 while other years are still uploading
// ----------------------------------------

// Load DHS points - UPDATE THIS PATH to your Earth Engine asset
// First upload your DHS CSV: Assets → NEW → Table upload → CSV
var points = ee.FeatureCollection("projects/ee-epidemiological-intelligence/assets/2015_DHS_cluster_points");

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
// CONFIGURATION FOR 2015 ONLY
// ----------------------------------------
var BUCKET = 'ndmi_ndwi30m';
var year = 2015;
var months = [7, 8, 9, 10, 11, 12];  // July to December

// Tile suffixes based on your files
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
print('Processing 2015 data from Cloud Storage...');
print('Files in bucket: gs://' + BUCKET + '/');

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
        'NDMI July 2015', false);
      Map.addLayer(ndwiMosaic, 
        {min: -1, max: 1, palette: ['brown', 'white', 'blue', 'darkblue']}, 
        'NDWI July 2015', false);
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
    
    exportCount += 2;  // Now creating 2 exports per month
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
print('SUMMARY FOR 2015');
print('='.repeat(50));
print('Export tasks created: ' + exportCount + ' (should be 12)');
print('Output folders:');
print('  - Google Drive/DHS_NDMI_Extracts/ (6 NDMI files)');
print('  - Google Drive/DHS_NDWI_Extracts/ (6 NDWI files)');
print('');
print('NEXT STEPS:');
print('1. Go to Tasks tab');
print('2. Click RUN on all 12 tasks');
print('3. NDMI CSVs will contain:');
print('   - DHS cluster IDs and coordinates');
print('   - Mean NDMI value (2km buffer)');
print('4. NDWI CSVs will contain:');
print('   - DHS cluster IDs and coordinates');
print('   - Mean NDWI value (2km buffer)');
print('   - Year and month metadata');
print('');
print('IMPORTANT:');
print('Make sure you have uploaded your DHS points CSV as an Earth Engine asset!');
print('Update line 8 with your actual DHS points asset path.');
print('');
print('Once 2018-2024 finish uploading, run similar scripts for those years.');