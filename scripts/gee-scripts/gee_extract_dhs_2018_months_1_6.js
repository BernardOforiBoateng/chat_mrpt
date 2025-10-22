// ----------------------------------------
// EXTRACT DHS VALUES FROM 2018 NDMI/NDWI FILES (MONTHS 1-6)
// Using 2018 DHS cluster points
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

// Different tile naming patterns
var tileSuffixPatterns = [
  // Pattern 1: Original format for months 7-12
  ['-0000000000-0000000000', '-0000000000-0000032768', '-0000032768-0000000000', '-0000032768-0000032768'],
  // Pattern 2: Alternative format that might be used for months 1-6
  ['-0000032768-0000000000', '-0000032768-0000032768', '-0000065536-0000000000', '-0000065536-0000032768'],
  // Pattern 3: Simple numbered tiles
  ['_tile_0', '_tile_1', '_tile_2', '_tile_3'],
  // Pattern 4: No suffix (single file)
  ['']
];

// ----------------------------------------
// PROCESSING FUNCTIONS
// ----------------------------------------
function loadAndMosaicMonth(indexType, month) {
  var monthStr = (month < 10) ? '0' + month : '' + month;
  
  print('Attempting to load ' + indexType + ' for ' + year + '-' + monthStr);
  
  // Try different tile patterns
  for (var p = 0; p < tileSuffixPatterns.length; p++) {
    var pattern = tileSuffixPatterns[p];
    var tiles = [];
    
    for (var i = 0; i < pattern.length; i++) {
      var filePath = 'gs://' + BUCKET + '/' + indexType + '_' + year + '_' + monthStr + pattern[i] + '.tif';
      
      try {
        var tile = ee.Image.loadGeoTIFF(filePath);
        tiles.push(tile);
        print('✓ Loaded: ' + filePath);
      } catch (e) {
        // Silent fail - try next pattern
      }
    }
    
    // If we successfully loaded tiles with this pattern
    if (tiles.length > 0) {
      print('Successfully loaded ' + tiles.length + ' tiles using pattern ' + p);
      
      if (tiles.length === 1) {
        // Single file - just clip to Nigeria
        return tiles[0].clip(nigeria);
      } else {
        // Multiple tiles - mosaic and clip
        return ee.ImageCollection(tiles).mosaic().clip(nigeria);
      }
    }
  }
  
  // If no pattern worked, return null
  print('ERROR: Could not load any tiles for ' + indexType + ' ' + year + '-' + monthStr);
  return null;
}

// ----------------------------------------
// EXTRACT VALUES FOR EACH MONTH
// ----------------------------------------
var ndmiCollections = [];
var ndwiCollections = [];

months.forEach(function(month) {
  var monthStr = (month < 10) ? '0' + month : '' + month;
  
  print('\n========== Processing ' + year + '-' + monthStr + ' ==========');
  
  // Load NDMI
  var ndmi = loadAndMosaicMonth('NDMI', month);
  if (ndmi) {
    print('Processing NDMI extraction for ' + monthStr);
    
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
    
    ndmiCollections.push(ndmiSamples);
    
    // Add to map (first month only for visualization)
    if (month === months[0]) {
      Map.addLayer(ndmi, {min: -1, max: 1, palette: ['red', 'yellow', 'green', 'cyan', 'blue']}, 
                   'NDMI ' + year + '-' + monthStr, false);
    }
  }
  
  // Load NDWI
  var ndwi = loadAndMosaicMonth('NDWI', month);
  if (ndwi) {
    print('Processing NDWI extraction for ' + monthStr);
    
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
    
    ndwiCollections.push(ndwiSamples);
    
    // Add to map (first month only for visualization)
    if (month === months[0]) {
      Map.addLayer(ndwi, {min: -1, max: 1, palette: ['brown', 'white', 'blue', 'darkblue']}, 
                   'NDWI ' + year + '-' + monthStr, false);
    }
  }
});

// ----------------------------------------
// MERGE AND EXPORT
// ----------------------------------------
print('\n========== Creating exports ==========');

// Merge all NDMI collections
if (ndmiCollections.length > 0) {
  var allNDMI = ee.FeatureCollection(ndmiCollections).flatten();
  
  print('NDMI samples ready for export');
  print('Total NDMI collections: ' + ndmiCollections.length);
  
  // Export NDMI
  Export.table.toDrive({
    collection: allNDMI,
    description: 'DHS_2018_NDMI_months_1_6',
    folder: 'DHS_Extracts',
    fileNamePrefix: 'DHS_2018_NDMI_months_1_6',
    fileFormat: 'CSV'
  });
} else {
  print('WARNING: No NDMI data to export');
}

// Merge all NDWI collections
if (ndwiCollections.length > 0) {
  var allNDWI = ee.FeatureCollection(ndwiCollections).flatten();
  
  print('NDWI samples ready for export');
  print('Total NDWI collections: ' + ndwiCollections.length);
  
  // Export NDWI
  Export.table.toDrive({
    collection: allNDWI,
    description: 'DHS_2018_NDWI_months_1_6',
    folder: 'DHS_Extracts',
    fileNamePrefix: 'DHS_2018_NDWI_months_1_6',
    fileFormat: 'CSV'
  });
} else {
  print('WARNING: No NDWI data to export');
}

print('\n========================================');
print('EXPORT SETUP COMPLETE FOR 2018 MONTHS 1-6');
print('========================================');
print('');
print('Files in bucket should be named like:');
print('  - NDMI_2018_01.tif (single file), OR');
print('  - NDMI_2018_01-0000000000-0000000000.tif (tiled), OR');
print('  - NDMI_2018_01_tile_0.tif (numbered tiles)');
print('');
print('The script will automatically detect the correct naming pattern.');
print('');
print('NEXT STEPS:');
print('1. Check the console above to see which files were successfully loaded');
print('2. Go to Tasks tab and run the exports');
print('3. Files will be saved to Google Drive in DHS_Extracts folder');
print('');
print('If files are not loading, check the exact naming in your bucket:');
print('  gsutil ls gs://ndmi_ndwi30m/NDMI_2018_01*');
print('  gsutil ls gs://ndmi_ndwi30m/NDWI_2018_01*');