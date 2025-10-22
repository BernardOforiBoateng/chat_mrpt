// ============================================
// EXTRACT NDMI/NDWI VALUES AT FIELD STUDY POINTS
// For E's analysis - 432 EA centroids in Kano and Ibadan
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
// Using the uploaded asset (432 features, uploaded 2025-08-13)
var fieldStudyPoints = ee.FeatureCollection("projects/epidemiological-intelligence/assets/kn_ib_long_cs_combined");

// Buffer each point by 100 meters (smaller than DHS since these are more precise)
var bufferedPoints = fieldStudyPoints.map(function(feature) {
  return feature.buffer(100);
});

// Separate Kano and Ibadan points for visualization
var kanoPoints = fieldStudyPoints.filter(ee.Filter.and(
  ee.Filter.gt('geometry.coordinates.0', 8.0),
  ee.Filter.lt('geometry.coordinates.0', 9.0)
));

var ibadanPoints = fieldStudyPoints.filter(ee.Filter.and(
  ee.Filter.gt('geometry.coordinates.0', 3.0),
  ee.Filter.lt('geometry.coordinates.0', 5.0)
));

print('Total field study points: ', fieldStudyPoints.size());
print('Kano points: ', kanoPoints.size());
print('Ibadan points: ', ibadanPoints.size());

// Visualize
Map.centerObject(fieldStudyPoints, 8);
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
// EXTRACT VALUES FOR EACH MONTH
// ----------------------------------------
var exportCount = 0;

years.forEach(function(year) {
  months.forEach(function(month) {
    var monthStr = (month < 10) ? '0' + month : '' + month;
    
    print('\nProcessing ' + year + '-' + monthStr + '...');
    
    // Load Kano rasters
    var kanoNDMI = loadMonthlyRaster('NDMI', 'Kano', year, month);
    var kanoNDWI = loadMonthlyRaster('NDWI', 'Kano', year, month);
    
    // Load Ibadan rasters
    var ibadanNDMI = loadMonthlyRaster('NDMI', 'Ibadan', year, month);
    var ibadanNDWI = loadMonthlyRaster('NDWI', 'Ibadan', year, month);
    
    if (kanoNDMI && kanoNDWI && ibadanNDMI && ibadanNDWI) {
      
      // Mosaic Kano and Ibadan rasters (they don't overlap)
      var ndmiMosaic = ee.ImageCollection([kanoNDMI, ibadanNDMI]).mosaic();
      var ndwiMosaic = ee.ImageCollection([kanoNDWI, ibadanNDWI]).mosaic();
      
      // Visualize first month
      if (year === 2023 && month === 7) {
        Map.addLayer(ndmiMosaic, 
          {min: -1, max: 1, palette: ['red', 'yellow', 'green', 'cyan', 'blue']}, 
          'NDMI July 2023', false);
        Map.addLayer(ndwiMosaic, 
          {min: -1, max: 1, palette: ['brown', 'white', 'blue', 'darkblue']}, 
          'NDWI July 2023', false);
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
      
      // Add metadata
      ndmiSamples = ndmiSamples.map(function(feature) {
        // Determine city based on coordinates
        var lon = feature.geometry().coordinates().get(0);
        var city = ee.String(ee.Algorithms.If(
          ee.Number(lon).gt(7),
          'Kano',
          'Ibadan'
        ));
        
        return feature.set({
          'year': year,
          'month': month,
          'year_month': year + '_' + monthStr,
          'city': city
        });
      });
      
      // Export NDMI to Drive
      Export.table.toDrive({
        collection: ndmiSamples,
        description: 'FieldStudy_NDMI_' + year + '_' + monthStr,
        folder: 'FieldStudy_NDMI_Extracts',
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
      
      // Add metadata
      ndwiSamples = ndwiSamples.map(function(feature) {
        // Determine city based on coordinates
        var lon = feature.geometry().coordinates().get(0);
        var city = ee.String(ee.Algorithms.If(
          ee.Number(lon).gt(7),
          'Kano',
          'Ibadan'
        ));
        
        return feature.set({
          'year': year,
          'month': month,
          'year_month': year + '_' + monthStr,
          'city': city
        });
      });
      
      // Export NDWI to Drive
      Export.table.toDrive({
        collection: ndwiSamples,
        description: 'FieldStudy_NDWI_' + year + '_' + monthStr,
        folder: 'FieldStudy_NDWI_Extracts',
        fileFormat: 'CSV'
      });
      
      exportCount += 2;
      print('✓ Created exports for ' + year + '-' + monthStr);
      
    } else {
      print('✗ Skipping ' + year + '-' + monthStr + ' - rasters not ready yet');
    }
  });
});

// ----------------------------------------
// SUMMARY
// ----------------------------------------
print('\n' + '='.repeat(60));
print('FIELD STUDY POINT EXTRACTION SUMMARY');
print('='.repeat(60));
print('');
print('Export tasks created: ' + exportCount + ' (should be 48)');
print('  - 2 years (2023, 2024)');
print('  - 12 months each');
print('  - 2 indices (NDMI, NDWI)');
print('');
print('Output folders:');
print('  - Google Drive/FieldStudy_NDMI_Extracts/');
print('  - Google Drive/FieldStudy_NDWI_Extracts/');
print('');
print('Each CSV will contain:');
print('  - EA cluster ID and coordinates');
print('  - Mean NDMI or NDWI value (100m buffer)');
print('  - Year, month, city metadata');
print('  - All 432 field study points');
print('');
print('Files for E:');
print('  1. Rasters: gs://ndmi_ndwi30m/field_study/');
print('  2. Point extracts: These CSV files');
print('');
print('IMPORTANT: Make sure kn_ib_long_cs_combined is uploaded to Earth Engine!');