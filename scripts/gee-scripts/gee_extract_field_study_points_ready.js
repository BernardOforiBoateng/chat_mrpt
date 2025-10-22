// ============================================
// EXTRACT NDMI/NDWI VALUES AT FIELD STUDY POINTS
// For E's analysis - 432 EA centroids in Kano and Ibadan
// Asset confirmed uploaded: 2025-08-13
// ============================================

// ----------------------------------------
// CONFIGURATION
// ----------------------------------------
var BUCKET = 'ndmi_ndwi30m';
var years = [2023, 2024];
var months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];  // All 12 months

// ----------------------------------------
// LOAD FIELD STUDY POINTS
// ----------------------------------------
// Asset confirmed: 432 features, 21.92KB, uploaded 2025-08-13
// Using the Table ID directly as shown in Earth Engine
var fieldStudyPoints = ee.FeatureCollection("projects/epidemiological-intelligence/assets/kn_ib_long_cs_combined");

print('Loading field study points...');
print('Expected: 432 points');
print('Actual loaded:', fieldStudyPoints.size());

// Buffer each point by 100 meters (smaller than DHS since these are more precise)
var bufferedPoints = fieldStudyPoints.map(function(feature) {
  return feature.buffer(100);
});

// Separate Kano and Ibadan points based on longitude
// Kano is around 8.5°E, Ibadan is around 3.9°E
var kanoPoints = fieldStudyPoints.filter(ee.Filter.gt('longitude', 6));
var ibadanPoints = fieldStudyPoints.filter(ee.Filter.lt('longitude', 6));

print('Kano points (longitude > 6):', kanoPoints.size());
print('Ibadan points (longitude < 6):', ibadanPoints.size());

// Visualize points on map
Map.centerObject(fieldStudyPoints, 7);
Map.addLayer(kanoPoints, {color: 'blue'}, 'Kano Field Study Points');
Map.addLayer(ibadanPoints, {color: 'green'}, 'Ibadan Field Study Points');

// ----------------------------------------
// FUNCTION TO LOAD RASTERS FROM CLOUD STORAGE
// ----------------------------------------
function loadMonthlyRaster(indexType, city, year, month) {
  var monthStr = (month < 10) ? '0' + month : '' + month;
  var cityName = (city === 'Kano') ? 'KanoMetro' : 'IbadanMetro';
  
  var filePath = 'gs://' + BUCKET + '/field_study/' + indexType + '_' + cityName + '_' + year + '_' + monthStr + '.tif';
  
  try {
    return ee.Image.loadGeoTIFF(filePath);
  } catch (e) {
    print('Warning: Could not load ' + filePath);
    return null;
  }
}

// ----------------------------------------
// PROCESS EACH MONTH AND CREATE EXPORTS
// ----------------------------------------
var exportCount = 0;
var skippedCount = 0;

years.forEach(function(year) {
  months.forEach(function(month) {
    var monthStr = (month < 10) ? '0' + month : '' + month;
    
    print('\nProcessing ' + year + '-' + monthStr + '...');
    
    // Load rasters for both cities
    var kanoNDMI = loadMonthlyRaster('NDMI', 'Kano', year, month);
    var kanoNDWI = loadMonthlyRaster('NDWI', 'Kano', year, month);
    var ibadanNDMI = loadMonthlyRaster('NDMI', 'Ibadan', year, month);
    var ibadanNDWI = loadMonthlyRaster('NDWI', 'Ibadan', year, month);
    
    // Check if all rasters are available
    if (kanoNDMI && kanoNDWI && ibadanNDMI && ibadanNDWI) {
      
      // Mosaic Kano and Ibadan rasters (they don't overlap)
      var ndmiMosaic = ee.ImageCollection([kanoNDMI, ibadanNDMI]).mosaic();
      var ndwiMosaic = ee.ImageCollection([kanoNDWI, ibadanNDWI]).mosaic();
      
      // Add visualization for first available month
      if (exportCount === 0) {
        Map.addLayer(ndmiMosaic, 
          {min: -1, max: 1, palette: ['red', 'yellow', 'green', 'cyan', 'blue']}, 
          'NDMI ' + year + '-' + monthStr, false);
        Map.addLayer(ndwiMosaic, 
          {min: -1, max: 1, palette: ['brown', 'white', 'blue', 'darkblue']}, 
          'NDWI ' + year + '-' + monthStr, false);
      }
      
      // ========================================
      // EXTRACT NDMI VALUES
      // ========================================
      var ndmiSamples = ndmiMosaic.rename('NDMI').reduceRegions({
        collection: bufferedPoints,
        reducer: ee.Reducer.mean(),
        scale: 30,
        tileScale: 4
      });
      
      // Add metadata to each point
      ndmiSamples = ndmiSamples.map(function(feature) {
        // Get coordinates to determine city
        var coords = feature.geometry().centroid().coordinates();
        var lon = ee.Number(coords.get(0));
        
        // Kano is east (around 8.5°E), Ibadan is west (around 3.9°E)
        var city = ee.String(ee.Algorithms.If(
          lon.gt(6),
          'Kano',
          'Ibadan'
        ));
        
        return feature.set({
          'year': year,
          'month': month,
          'year_month': year + '_' + monthStr,
          'city': city,
          'index_type': 'NDMI'
        });
      });
      
      // Export NDMI to Drive
      Export.table.toDrive({
        collection: ndmiSamples,
        description: 'FieldStudy_NDMI_' + year + '_' + monthStr,
        folder: 'FieldStudy_Extracts',
        fileNamePrefix: 'NDMI_' + year + '_' + monthStr,
        fileFormat: 'CSV'
      });
      
      // ========================================
      // EXTRACT NDWI VALUES
      // ========================================
      var ndwiSamples = ndwiMosaic.rename('NDWI').reduceRegions({
        collection: bufferedPoints,
        reducer: ee.Reducer.mean(),
        scale: 30,
        tileScale: 4
      });
      
      // Add metadata to each point
      ndwiSamples = ndwiSamples.map(function(feature) {
        // Get coordinates to determine city
        var coords = feature.geometry().centroid().coordinates();
        var lon = ee.Number(coords.get(0));
        
        // Kano is east, Ibadan is west
        var city = ee.String(ee.Algorithms.If(
          lon.gt(6),
          'Kano',
          'Ibadan'
        ));
        
        return feature.set({
          'year': year,
          'month': month,
          'year_month': year + '_' + monthStr,
          'city': city,
          'index_type': 'NDWI'
        });
      });
      
      // Export NDWI to Drive
      Export.table.toDrive({
        collection: ndwiSamples,
        description: 'FieldStudy_NDWI_' + year + '_' + monthStr,
        folder: 'FieldStudy_Extracts',
        fileNamePrefix: 'NDWI_' + year + '_' + monthStr,
        fileFormat: 'CSV'
      });
      
      exportCount += 2;
      print('✓ Created 2 exports for ' + year + '-' + monthStr);
      
    } else {
      skippedCount += 2;
      print('✗ Skipping ' + year + '-' + monthStr + ' - rasters not available yet');
    }
  });
});

// ----------------------------------------
// FINAL SUMMARY
// ----------------------------------------
print('\n' + '='.repeat(60));
print('FIELD STUDY POINT EXTRACTION SUMMARY');
print('='.repeat(60));
print('');
print('Input asset: kn_ib_long_cs_combined');
print('  - Total points: 432');
print('  - File size: 21.92KB');
print('  - Last modified: 2025-08-13');
print('');
print('Export tasks created: ' + exportCount);
print('Export tasks skipped: ' + skippedCount);
print('');
print('Expected outputs:');
print('  - Up to 48 CSV files (24 months × 2 indices)');
print('  - Output folder: Google Drive/FieldStudy_Extracts/');
print('  - Each CSV contains all 432 points with extracted values');
print('');
print('CSV columns will include:');
print('  - Original point attributes from shapefile');
print('  - mean (extracted NDMI or NDWI value)');
print('  - year, month, year_month');
print('  - city (Kano or Ibadan based on longitude)');
print('  - index_type (NDMI or NDWI)');
print('');
print('NEXT STEPS:');
print('1. Go to Tasks tab');
print('2. Click RUN on all export tasks');
print('3. Files will export to Google Drive/FieldStudy_Extracts/');
print('4. Share folder with E once complete');
print('');
print('Note: If some exports were skipped, it means those rasters');
print('are not yet available in Cloud Storage. Run this script again');
print('once all field study rasters have been exported.');