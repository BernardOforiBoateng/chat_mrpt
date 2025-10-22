// ----------------------------------------
// EXTRACT DHS VALUES FROM 2018 NDMI/NDWI FILES
// FIXED VERSION - Only 2018
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
// CONFIGURATION FOR 2018 ONLY
// ----------------------------------------
var BUCKET = 'ndmi_ndwi30m';
var year = 2018;

// ----------------------------------------
// PROCESSING FUNCTION
// ----------------------------------------
function loadAndMosaicTiles(indexType, month) {
  var monthStr = (month < 10) ? '0' + month : '' + month;
  
  // Load all 4 tiles
  var tile1 = ee.Image.loadGeoTIFF('gs://' + BUCKET + '/' + indexType + '_' + year + '_' + monthStr + '-0000000000-0000000000.tif');
  var tile2 = ee.Image.loadGeoTIFF('gs://' + BUCKET + '/' + indexType + '_' + year + '_' + monthStr + '-0000000000-0000032768.tif');
  var tile3 = ee.Image.loadGeoTIFF('gs://' + BUCKET + '/' + indexType + '_' + year + '_' + monthStr + '-0000032768-0000000000.tif');
  var tile4 = ee.Image.loadGeoTIFF('gs://' + BUCKET + '/' + indexType + '_' + year + '_' + monthStr + '-0000032768-0000032768.tif');
  
  // Mosaic and clip
  return ee.ImageCollection([tile1, tile2, tile3, tile4]).mosaic().clip(nigeria);
}

// ----------------------------------------
// CREATE EXPORTS FOR 2018
// ----------------------------------------
print('Creating exports for 2018...');

// July 2018
var ndmi_07 = loadAndMosaicTiles('NDMI', 7);
var ndwi_07 = loadAndMosaicTiles('NDWI', 7);

Export.table.toDrive({
  collection: ndmi_07.rename('NDMI').reduceRegions({
    collection: bufferedPoints,
    reducer: ee.Reducer.mean(),
    scale: 30,
    tileScale: 4
  }).map(function(f) { return f.set({'year': 2018, 'month': 7, 'year_month': '2018_07'}); }),
  description: 'DHS_NDMI_2018_07',
  folder: 'DHS_NDMI_Extracts',
  fileFormat: 'CSV'
});

Export.table.toDrive({
  collection: ndwi_07.rename('NDWI').reduceRegions({
    collection: bufferedPoints,
    reducer: ee.Reducer.mean(),
    scale: 30,
    tileScale: 4
  }).map(function(f) { return f.set({'year': 2018, 'month': 7, 'year_month': '2018_07'}); }),
  description: 'DHS_NDWI_2018_07',
  folder: 'DHS_NDWI_Extracts',
  fileFormat: 'CSV'
});

// August 2018
var ndmi_08 = loadAndMosaicTiles('NDMI', 8);
var ndwi_08 = loadAndMosaicTiles('NDWI', 8);

Export.table.toDrive({
  collection: ndmi_08.rename('NDMI').reduceRegions({
    collection: bufferedPoints,
    reducer: ee.Reducer.mean(),
    scale: 30,
    tileScale: 4
  }).map(function(f) { return f.set({'year': 2018, 'month': 8, 'year_month': '2018_08'}); }),
  description: 'DHS_NDMI_2018_08',
  folder: 'DHS_NDMI_Extracts',
  fileFormat: 'CSV'
});

Export.table.toDrive({
  collection: ndwi_08.rename('NDWI').reduceRegions({
    collection: bufferedPoints,
    reducer: ee.Reducer.mean(),
    scale: 30,
    tileScale: 4
  }).map(function(f) { return f.set({'year': 2018, 'month': 8, 'year_month': '2018_08'}); }),
  description: 'DHS_NDWI_2018_08',
  folder: 'DHS_NDWI_Extracts',
  fileFormat: 'CSV'
});

// September 2018
var ndmi_09 = loadAndMosaicTiles('NDMI', 9);
var ndwi_09 = loadAndMosaicTiles('NDWI', 9);

Export.table.toDrive({
  collection: ndmi_09.rename('NDMI').reduceRegions({
    collection: bufferedPoints,
    reducer: ee.Reducer.mean(),
    scale: 30,
    tileScale: 4
  }).map(function(f) { return f.set({'year': 2018, 'month': 9, 'year_month': '2018_09'}); }),
  description: 'DHS_NDMI_2018_09',
  folder: 'DHS_NDMI_Extracts',
  fileFormat: 'CSV'
});

Export.table.toDrive({
  collection: ndwi_09.rename('NDWI').reduceRegions({
    collection: bufferedPoints,
    reducer: ee.Reducer.mean(),
    scale: 30,
    tileScale: 4
  }).map(function(f) { return f.set({'year': 2018, 'month': 9, 'year_month': '2018_09'}); }),
  description: 'DHS_NDWI_2018_09',
  folder: 'DHS_NDWI_Extracts',
  fileFormat: 'CSV'
});

// October 2018
var ndmi_10 = loadAndMosaicTiles('NDMI', 10);
var ndwi_10 = loadAndMosaicTiles('NDWI', 10);

Export.table.toDrive({
  collection: ndmi_10.rename('NDMI').reduceRegions({
    collection: bufferedPoints,
    reducer: ee.Reducer.mean(),
    scale: 30,
    tileScale: 4
  }).map(function(f) { return f.set({'year': 2018, 'month': 10, 'year_month': '2018_10'}); }),
  description: 'DHS_NDMI_2018_10',
  folder: 'DHS_NDMI_Extracts',
  fileFormat: 'CSV'
});

Export.table.toDrive({
  collection: ndwi_10.rename('NDWI').reduceRegions({
    collection: bufferedPoints,
    reducer: ee.Reducer.mean(),
    scale: 30,
    tileScale: 4
  }).map(function(f) { return f.set({'year': 2018, 'month': 10, 'year_month': '2018_10'}); }),
  description: 'DHS_NDWI_2018_10',
  folder: 'DHS_NDWI_Extracts',
  fileFormat: 'CSV'
});

// November 2018
var ndmi_11 = loadAndMosaicTiles('NDMI', 11);
var ndwi_11 = loadAndMosaicTiles('NDWI', 11);

Export.table.toDrive({
  collection: ndmi_11.rename('NDMI').reduceRegions({
    collection: bufferedPoints,
    reducer: ee.Reducer.mean(),
    scale: 30,
    tileScale: 4
  }).map(function(f) { return f.set({'year': 2018, 'month': 11, 'year_month': '2018_11'}); }),
  description: 'DHS_NDMI_2018_11',
  folder: 'DHS_NDMI_Extracts',
  fileFormat: 'CSV'
});

Export.table.toDrive({
  collection: ndwi_11.rename('NDWI').reduceRegions({
    collection: bufferedPoints,
    reducer: ee.Reducer.mean(),
    scale: 30,
    tileScale: 4
  }).map(function(f) { return f.set({'year': 2018, 'month': 11, 'year_month': '2018_11'}); }),
  description: 'DHS_NDWI_2018_11',
  folder: 'DHS_NDWI_Extracts',
  fileFormat: 'CSV'
});

// December 2018
var ndmi_12 = loadAndMosaicTiles('NDMI', 12);
var ndwi_12 = loadAndMosaicTiles('NDWI', 12);

Export.table.toDrive({
  collection: ndmi_12.rename('NDMI').reduceRegions({
    collection: bufferedPoints,
    reducer: ee.Reducer.mean(),
    scale: 30,
    tileScale: 4
  }).map(function(f) { return f.set({'year': 2018, 'month': 12, 'year_month': '2018_12'}); }),
  description: 'DHS_NDMI_2018_12',
  folder: 'DHS_NDMI_Extracts',
  fileFormat: 'CSV'
});

Export.table.toDrive({
  collection: ndwi_12.rename('NDWI').reduceRegions({
    collection: bufferedPoints,
    reducer: ee.Reducer.mean(),
    scale: 30,
    tileScale: 4
  }).map(function(f) { return f.set({'year': 2018, 'month': 12, 'year_month': '2018_12'}); }),
  description: 'DHS_NDWI_2018_12',
  folder: 'DHS_NDWI_Extracts',
  fileFormat: 'CSV'
});

// Add visualization for verification
Map.addLayer(ndmi_07, {min: -1, max: 1, palette: ['red', 'yellow', 'green', 'cyan', 'blue']}, 
             'NDMI 2018-07', false);
Map.addLayer(ndwi_07, {min: -1, max: 1, palette: ['brown', 'white', 'blue', 'darkblue']}, 
             'NDWI 2018-07', false);

// ----------------------------------------
// SUMMARY
// ----------------------------------------
print('');
print('='.repeat(50));
print('EXPORT TASKS CREATED FOR 2018');
print('='.repeat(50));
print('12 export tasks should appear in the Tasks tab:');
print('  - 6 NDMI files (July to December)');
print('  - 6 NDWI files (July to December)');
print('');
print('Output folders:');
print('  - Google Drive/DHS_NDMI_Extracts/');
print('  - Google Drive/DHS_NDWI_Extracts/');
print('');
print('Click RUN on each task to start the exports.');