// ----------------------------------------
// BETTER DIAGNOSTIC: ACTUALLY LOAD AND CHECK FILES
// ----------------------------------------

var BUCKET = 'ndmi_ndwi30m';
var year = 2018;
var months = [1, 2, 3, 4, 5, 6];

print('Testing actual file loading from: gs://' + BUCKET);
print('============================================================');

// First, let's try to actually load and visualize files to confirm they exist
months.forEach(function(month) {
  var monthStr = (month < 10) ? '0' + month : '' + month;
  
  print('\n>>> Testing ' + year + '-' + monthStr + ' <<<');
  
  // Test Pattern 1: Single file (no suffix)
  print('\nPattern 1: Single file (no suffix)');
  try {
    var ndmiSingle = ee.Image.loadGeoTIFF('gs://' + BUCKET + '/NDMI_' + year + '_' + monthStr + '.tif');
    var ndwiSingle = ee.Image.loadGeoTIFF('gs://' + BUCKET + '/NDWI_' + year + '_' + monthStr + '.tif');
    
    // Try to get actual properties to confirm it loaded
    var ndmiBands = ndmiSingle.bandNames();
    var ndwiBands = ndwiSingle.bandNames();
    
    print('✓ SINGLE FILE EXISTS - Both NDMI and NDWI loaded successfully');
    print('  NDMI bands:', ndmiBands);
    print('  NDWI bands:', ndwiBands);
    
    // Add first month to map for visualization
    if (month === 1) {
      Map.addLayer(ndmiSingle, {min: -1, max: 1, palette: ['red', 'yellow', 'green', 'cyan', 'blue']}, 
                   'NDMI Single ' + year + '-' + monthStr, false);
      Map.addLayer(ndwiSingle, {min: -1, max: 1, palette: ['brown', 'white', 'blue', 'darkblue']}, 
                   'NDWI Single ' + year + '-' + monthStr, false);
    }
  } catch (e) {
    print('✗ Single file pattern failed');
  }
  
  // Test Pattern 2: Four tiles
  print('\nPattern 2: Four tiles with coordinates');
  var tileSuffixes = [
    '-0000000000-0000000000',
    '-0000000000-0000032768',
    '-0000032768-0000000000',
    '-0000032768-0000032768'
  ];
  
  var ndmiTiles = [];
  var ndwiTiles = [];
  var ndmiSuccess = 0;
  var ndwiSuccess = 0;
  
  tileSuffixes.forEach(function(suffix, index) {
    try {
      var ndmiTile = ee.Image.loadGeoTIFF('gs://' + BUCKET + '/NDMI_' + year + '_' + monthStr + suffix + '.tif');
      ndmiTiles.push(ndmiTile);
      ndmiSuccess++;
      print('  ✓ NDMI tile ' + (index + 1) + ' found: ' + suffix);
    } catch (e) {
      print('  ✗ NDMI tile ' + (index + 1) + ' missing: ' + suffix);
    }
    
    try {
      var ndwiTile = ee.Image.loadGeoTIFF('gs://' + BUCKET + '/NDWI_' + year + '_' + monthStr + suffix + '.tif');
      ndwiTiles.push(ndwiTile);
      ndwiSuccess++;
      print('  ✓ NDWI tile ' + (index + 1) + ' found: ' + suffix);
    } catch (e) {
      print('  ✗ NDWI tile ' + (index + 1) + ' missing: ' + suffix);
    }
  });
  
  if (ndmiSuccess === 4 && ndwiSuccess === 4) {
    print('✓ FOUR TILES PATTERN - All 8 tiles found (4 NDMI + 4 NDWI)');
    
    // Mosaic and visualize first month
    if (month === 1) {
      var ndmiMosaic = ee.ImageCollection(ndmiTiles).mosaic();
      var ndwiMosaic = ee.ImageCollection(ndwiTiles).mosaic();
      
      Map.addLayer(ndmiMosaic, {min: -1, max: 1, palette: ['red', 'yellow', 'green', 'cyan', 'blue']}, 
                   'NDMI Mosaic ' + year + '-' + monthStr, false);
      Map.addLayer(ndwiMosaic, {min: -1, max: 1, palette: ['brown', 'white', 'blue', 'darkblue']}, 
                   'NDWI Mosaic ' + year + '-' + monthStr, false);
    }
  } else {
    print('✗ Four tiles pattern incomplete: NDMI=' + ndmiSuccess + '/4, NDWI=' + ndwiSuccess + '/4');
  }
});

print('\n============================================================');
print('ACTUAL FILE CHECK COMPLETE');
print('============================================================');
print('');
print('KEY FINDINGS:');
print('- If you see "SINGLE FILE EXISTS", use the single file pattern');
print('- If you see "FOUR TILES PATTERN", use the 4-tile mosaic pattern');
print('- If you see both working for some months, you have duplicate data');
print('');
print('The script will use whichever pattern actually loads data.');
print('');
print('Now let\'s create the correct extraction script based on what actually exists...');