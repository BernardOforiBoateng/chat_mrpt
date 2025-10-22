// ----------------------------------------
// EXTRACT DHS CLUSTER VALUES FROM NDMI/NDWI FILES IN CLOUD STORAGE
// ----------------------------------------
// This script extracts NDMI and NDWI values at DHS cluster points
// from the tiled TIFF files in your Cloud Storage bucket

// ----------------------------------------
// USER INPUTS
// ----------------------------------------
// Load your DHS point layer (UPDATE THIS PATH to your asset)
// You need to upload your DHS CSV as an Earth Engine asset first
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
Map.addLayer(bufferedPoints, {color: 'red'}, 'DHS Clusters (2km buffer)');

// ----------------------------------------
// CONFIGURATION
// ----------------------------------------
// Your Cloud Storage bucket
var bucketPath = 'gs://ndmi_ndwi30m/';

// Years and months to process
var years = [2015, 2018, 2021, 2023, 2024];
var startMonth = 7;  // July
var endMonth = 12;   // December

// Tile suffixes (based on your file naming)
var tileSuffixes = [
  '-0000000000-0000000000',
  '-0000000000-0000023296',
  '-0000023296-0000000000',
  '-0000023296-0000023296'
];

// ----------------------------------------
// SUPPORTING FUNCTIONS
// ----------------------------------------
// Load a single tile for NDMI
function loadNDMITile(year, month, suffix) {
  var monthStr = (month < 10) ? '0' + month : '' + month;
  var filePath = bucketPath + 'NDMI_' + year + '_' + monthStr + suffix + '.tif';
  try {
    return ee.Image.loadGeoTIFF(filePath);
  } catch (e) {
    print('Warning: Could not load ' + filePath);
    return null;
  }
}

// Load a single tile for NDWI
function loadNDWITile(year, month, suffix) {
  var monthStr = (month < 10) ? '0' + month : '' + month;
  var filePath = bucketPath + 'NDWI_' + year + '_' + monthStr + suffix + '.tif';
  try {
    return ee.Image.loadGeoTIFF(filePath);
  } catch (e) {
    print('Warning: Could not load ' + filePath);
    return null;
  }
}

// Add metadata properties to each feature
function addMetadata(year, month) {
  return function(feature) {
    return feature.set({
      'year': year,
      'month': month,
      'year_month': year + '_' + (month < 10 ? '0' + month : '' + month)
    });
  };
}

// ----------------------------------------
// MAIN PROCESSING LOOP
// ----------------------------------------
var exportCount = 0;

years.forEach(function(year) {
  for (var month = startMonth; month <= endMonth; month++) {
    
    var monthStr = (month < 10) ? '0' + month : '' + month;
    print('Processing: ' + year + '-' + monthStr);
    
    // Load all 4 NDMI tiles for this month
    var ndmiTiles = [];
    for (var i = 0; i < tileSuffixes.length; i++) {
      var ndmiTile = loadNDMITile(year, month, tileSuffixes[i]);
      if (ndmiTile !== null) {
        ndmiTiles.push(ndmiTile);
      }
    }
    
    // Load all 4 NDWI tiles for this month
    var ndwiTiles = [];
    for (var j = 0; j < tileSuffixes.length; j++) {
      var ndwiTile = loadNDWITile(year, month, tileSuffixes[j]);
      if (ndwiTile !== null) {
        ndwiTiles.push(ndwiTile);
      }
    }
    
    // Only proceed if we have tiles
    if (ndmiTiles.length > 0 && ndwiTiles.length > 0) {
      
      // Combine the tiles into mosaics and clip to Nigeria
      var ndmiMosaic = ee.ImageCollection(ndmiTiles).mosaic().clip(nigeria);
      var ndwiMosaic = ee.ImageCollection(ndwiTiles).mosaic().clip(nigeria);
      
      // Combine NDMI and NDWI into a single image
      var combinedImage = ndmiMosaic.rename('NDMI').addBands(ndwiMosaic.rename('NDWI'));
      
      // Visualize first month for inspection
      if (year === years[0] && month === startMonth) {
        Map.addLayer(ndmiMosaic, {min: -1, max: 1, palette: ['red', 'yellow', 'green', 'cyan', 'blue']}, 
                     'NDMI Sample: ' + year + '-' + monthStr, false);
        Map.addLayer(ndwiMosaic, {min: -1, max: 1, palette: ['brown', 'white', 'blue', 'darkblue']}, 
                     'NDWI Sample: ' + year + '-' + monthStr, false);
      }
      
      // Extract mean NDMI and NDWI within each buffer
      var samples = combinedImage.reduceRegions({
        collection: bufferedPoints,
        reducer: ee.Reducer.mean(),
        scale: 30,
        tileScale: 4  // Helps with computation
      }).map(addMetadata(year, month));
      
      // Export to Google Drive
      Export.table.toDrive({
        collection: samples,
        description: 'DHS_NDMI_NDWI_' + year + '_' + monthStr,
        folder: 'DHS_NDMI_NDWI_Extracts',
        fileFormat: 'CSV'
      });
      
      exportCount++;
      print('Created export task for ' + year + '-' + monthStr);
      
    } else {
      print('Skipping ' + year + '-' + monthStr + ' - no tiles found');
    }
  }
});

// ----------------------------------------
// SUMMARY
// ----------------------------------------
print('');
print('=== SUMMARY ===');
print('Total export tasks created: ' + exportCount);
print('Files will be saved to Google Drive folder: DHS_NDMI_NDWI_Extracts');
print('Each CSV will contain NDMI and NDWI values for all DHS clusters');
print('');
print('=== NEXT STEPS ===');
print('1. Go to the Tasks tab');
print('2. Click RUN on each export task');
print('3. Check your Google Drive folder for results');
print('');
print('=== IMPORTANT ===');
print('Make sure you have uploaded your DHS points as an Earth Engine asset!');
print('Update line 12 with the correct path to your DHS points asset.');