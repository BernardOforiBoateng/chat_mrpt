// ----------------------------------------
// EXTRACT DHS CLUSTER VALUES FROM NDMI/NDWI TIFF FILES
// ----------------------------------------
// This script extracts NDMI and NDWI values at DHS cluster points
// from the tiled TIFF files in Google Drive

// ----------------------------------------
// USER INPUTS
// ----------------------------------------
// Load your DHS point layer (you need to upload this as an EE asset)
var points = ee.FeatureCollection("projects/ee-ozodiegwui/assets/2015_DHS_cluster_points");

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
// Years and months to process
var years = [2015, 2018, 2021, 2023, 2024];
var startMonth = 7;  // July
var endMonth = 12;   // December

// Google Cloud Storage bucket path where your TIFF files are stored
// UPDATE THIS to match where your files are stored
var bucketPath = 'gs://your-bucket-name/Nigeria_NDMI_NDWI_HLS/';

// These are the tile suffixes (based on your existing files)
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
  return ee.Image.loadGeoTIFF(filePath);
}

// Load a single tile for NDWI
function loadNDWITile(year, month, suffix) {
  var monthStr = (month < 10) ? '0' + month : '' + month;
  var filePath = bucketPath + 'NDWI_' + year + '_' + monthStr + suffix + '.tif';
  return ee.Image.loadGeoTIFF(filePath);
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
years.forEach(function(year) {
  for (var month = startMonth; month <= endMonth; month++) {
    
    var monthStr = (month < 10) ? '0' + month : '' + month;
    print('Processing: ' + year + '-' + monthStr);
    
    // Load all 4 NDMI tiles for this month
    var ndmiTiles = [];
    for (var i = 0; i < tileSuffixes.length; i++) {
      try {
        var ndmiTile = loadNDMITile(year, month, tileSuffixes[i]);
        ndmiTiles.push(ndmiTile);
      } catch (e) {
        print('Warning: Could not load NDMI tile ' + i + ' for ' + year + '-' + monthStr);
      }
    }
    
    // Load all 4 NDWI tiles for this month
    var ndwiTiles = [];
    for (var j = 0; j < tileSuffixes.length; j++) {
      try {
        var ndwiTile = loadNDWITile(year, month, tileSuffixes[j]);
        ndwiTiles.push(ndwiTile);
      } catch (e) {
        print('Warning: Could not load NDWI tile ' + j + ' for ' + year + '-' + monthStr);
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
                     'NDMI Sample: ' + year + '-' + monthStr);
        Map.addLayer(ndwiMosaic, {min: -1, max: 1, palette: ['brown', 'white', 'blue', 'darkblue']}, 
                     'NDWI Sample: ' + year + '-' + monthStr);
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
        fileFormat: 'CSV',
        selectors: ['DHSID', 'DHSCLUST', 'NDMI', 'NDWI', 'year', 'month', 'year_month']  // Adjust based on your DHS fields
      });
      
      print('Export created for ' + year + '-' + monthStr);
      
    } else {
      print('Skipping ' + year + '-' + monthStr + ' - no tiles found');
    }
  }
});

// ----------------------------------------
// ALTERNATIVE: If files are in Google Drive (not Cloud Storage)
// ----------------------------------------
// If your TIFF files are in Google Drive, you'll need to:
// 1. Download them to Cloud Storage first, OR
// 2. Process them locally using Python

print('Total export tasks created: ' + (years.length * 6));
print('Files will be saved to Google Drive folder: DHS_NDMI_NDWI_Extracts');
print('Each CSV will contain NDMI and NDWI values for all DHS clusters');

// ----------------------------------------
// NOTES:
// ----------------------------------------
// 1. Update the bucketPath to match where your TIFF files are stored
// 2. Make sure the DHS points asset path is correct
// 3. The script assumes 4 tiles per month (adjust tileSuffixes if different)
// 4. Output CSVs will have columns: DHSID, DHSCLUST, NDMI, NDWI, year, month
// 5. Each DHS cluster gets the mean value within its 2km buffer