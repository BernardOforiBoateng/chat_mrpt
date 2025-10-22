// ----------------------------------------
// EXTRACT DHS CLUSTER VALUES FROM NDMI/NDWI TIFF FILES
// Using Earth Engine Assets (after uploading from Google Drive)
// ----------------------------------------

// ----------------------------------------
// USER INPUTS
// ----------------------------------------
// Load your DHS point layer (update this path to your asset)
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
// Years and months to process
var years = [2015, 2018, 2021, 2023, 2024];
var startMonth = 7;  // July
var endMonth = 12;   // December

// Your Earth Engine asset path (after uploading)
// Format: projects/ee-epidemiological-intelligence/assets/NDMI_NDWI/
var assetBasePath = 'projects/ee-epidemiological-intelligence/assets/';

// ----------------------------------------
// SUPPORTING FUNCTIONS
// ----------------------------------------
// Function to load and mosaic tiles for a given index, year, and month
function loadAndMosaicTiles(indexType, year, month) {
  var monthStr = (month < 10) ? '0' + month : '' + month;
  var baseName = indexType + '_' + year + '_' + monthStr;
  
  // Try to load the 4 tiles (assuming they're named with suffixes 0000000000-0000000000, etc.)
  var tiles = [];
  
  // Option 1: If you uploaded each tile as separate asset with original names
  var tileSuffixes = [
    '-0000000000-0000000000',
    '-0000000000-0000023296',
    '-0000023296-0000000000',
    '-0000023296-0000023296'
  ];
  
  for (var i = 0; i < tileSuffixes.length; i++) {
    try {
      var assetPath = assetBasePath + baseName + tileSuffixes[i];
      var tile = ee.Image(assetPath);
      tiles.push(tile);
      print('Loaded: ' + assetPath);
    } catch (e) {
      // Try without suffix if tiles were merged before upload
      if (i === 0) {
        try {
          var singleAssetPath = assetBasePath + baseName;
          var singleTile = ee.Image(singleAssetPath);
          tiles.push(singleTile);
          print('Loaded single file: ' + singleAssetPath);
          break;  // No need to load more tiles
        } catch (e2) {
          print('Could not load: ' + baseName);
        }
      }
    }
  }
  
  if (tiles.length > 0) {
    // Mosaic all tiles together
    return ee.ImageCollection(tiles).mosaic().clip(nigeria);
  } else {
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
    
    // Load and mosaic NDMI tiles
    var ndmiMosaic = loadAndMosaicTiles('NDMI', year, month);
    
    // Load and mosaic NDWI tiles
    var ndwiMosaic = loadAndMosaicTiles('NDWI', year, month);
    
    // Only proceed if we have both indices
    if (ndmiMosaic !== null && ndwiMosaic !== null) {
      
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
      print('Export created for ' + year + '-' + monthStr);
      
    } else {
      print('Skipping ' + year + '-' + monthStr + ' - data not found in assets');
    }
  }
});

// ----------------------------------------
// HOW TO UPLOAD YOUR TIFF FILES AS ASSETS
// ----------------------------------------
print('');
print('=== HOW TO UPLOAD YOUR TIFF FILES AS EARTH ENGINE ASSETS ===');
print('');
print('1. Download TIFF files from your Google Drive to local computer');
print('2. Go to https://code.earthengine.google.com/');
print('3. In the Assets tab (left panel), click "NEW" → "Image upload" → "GeoTIFF"');
print('4. Select your TIFF file(s)');
print('5. Set Asset ID with this naming pattern:');
print('   projects/ee-epidemiological-intelligence/assets/NDMI_2015_07-0000000000-0000000000');
print('   OR if merged: projects/ee-epidemiological-intelligence/assets/NDMI_2015_07');
print('6. Click "UPLOAD"');
print('7. Wait for ingestion to complete (check Tasks tab)');
print('8. Repeat for all NDMI and NDWI files');
print('');
print('Alternative: Use Earth Engine Command Line Interface (earthengine CLI):');
print('earthengine upload image --asset_id=projects/ee-epidemiological-intelligence/assets/NDMI_2015_07 gs://your-bucket/NDMI_2015_07.tif');
print('');
print('Total export tasks to be created: ' + exportCount);
print('Files will be saved to Google Drive folder: DHS_NDMI_NDWI_Extracts');