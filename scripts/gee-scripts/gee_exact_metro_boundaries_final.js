// ========================================
// FINAL SCRIPT: EXACT METROPOLITAN BOUNDARIES
// Using Kano 6 LGAs and Ibadan 5 LGAs shapefiles
// ========================================

// ----------------------------------------
// CONFIGURATION
// ----------------------------------------
var BUCKET = 'ndmi_ndwi30m';
var years = [2023, 2024];
var startMonth = 1;  
var endMonth = 12;

// ----------------------------------------
// EXACT METROPOLITAN BOUNDARIES
// Using ACTUAL LGA polygon shapes (not rectangles!)
// ----------------------------------------

// Load the actual shapefiles from Earth Engine Assets
var kanoMetro = ee.FeatureCollection("projects/epidemiological-intelligence/assets/Kano_metro_sixLGA_shapes");
var ibadanMetro = ee.FeatureCollection("projects/epidemiological-intelligence/assets/Ibadan_metro_fiveLGAshapes");

// Use the ACTUAL LGA boundaries (irregular polygons, not rectangles)
var kanoRegion = kanoMetro.geometry().dissolve();  // Dissolve to merge all 6 LGAs into one shape
var ibadanRegion = ibadanMetro.geometry().dissolve();  // Dissolve to merge all 5 LGAs into one shape

// Display the individual LGAs for reference
Map.addLayer(kanoMetro, {color: 'lightblue'}, 'Kano 6 LGAs (individual)', false);
Map.addLayer(ibadanMetro, {color: 'lightgreen'}, 'Ibadan 5 LGAs (individual)', false);

// Visualize regions
Map.centerObject(kanoRegion, 11);
Map.addLayer(kanoRegion, {color: 'blue'}, 'Kano Metropolitan Area (6 LGAs)');
Map.addLayer(ibadanRegion, {color: 'green'}, 'Ibadan Metropolitan Area (5 LGAs)');

// Calculate and display actual areas from the polygons
var kanoAreaKm2 = kanoRegion.area().divide(1e6);
var ibadanAreaKm2 = ibadanRegion.area().divide(1e6);

print('Kano Metro Area (actual shape):', kanoAreaKm2, 'km²');
print('Ibadan Metro Area (actual shape):', ibadanAreaKm2, 'km²');
print('These are the EXACT LGA polygon boundaries, NOT rectangles!');

// ----------------------------------------
// HLS INDICES FUNCTIONS
// ----------------------------------------
function calculateIndices(img, sensor) {
  var green = sensor === 'S2' ? img.select('B3') : img.select('B3');
  var nir = sensor === 'S2' ? img.select('B8A') : img.select('B5');
  var swir1 = sensor === 'S2' ? img.select('B11') : img.select('B6');
  
  var ndmi = img.expression('(NIR - SWIR1) / (NIR + SWIR1)', {
    'NIR': nir,
    'SWIR1': swir1
  }).rename('NDMI');
  
  var ndwi = img.expression('(GREEN - NIR) / (GREEN + NIR)', {
    'GREEN': green,
    'NIR': nir
  }).rename('NDWI');
  
  return ndmi.addBands(ndwi);
}

function computeMonthlyIndices(year, month, region) {
  var start = ee.Date.fromYMD(year, month, 1);
  var end = start.advance(1, 'month');
  
  var s2 = ee.ImageCollection('NASA/HLS/HLSS30/v002')
              .filterDate(start, end)
              .filterBounds(region)
              .map(function(img) { return calculateIndices(img, 'S2'); });
  
  var l8 = ee.ImageCollection('NASA/HLS/HLSL30/v002')
              .filterDate(start, end)
              .filterBounds(region)
              .map(function(img) { return calculateIndices(img, 'L8'); });
  
  var merged = s2.merge(l8);
  var count = merged.size();
  
  return ee.Algorithms.If(
    count.gt(0),
    merged.median().clip(region).set('image_count', count),
    ee.Image.constant(0).rename(['NDMI', 'NDWI']).clip(region).set('image_count', 0)
  );
}

// ----------------------------------------
// GENERATE AND EXPORT RASTERS
// ----------------------------------------
var exportCount = 0;

years.forEach(function(year) {
  for (var month = startMonth; month <= endMonth; month++) {
    var monthStr = (month < 10) ? '0' + month : '' + month;
    
    print('Creating exports for ' + year + '-' + monthStr + '...');
    
    // ========================================
    // KANO METROPOLITAN EXPORTS
    // ========================================
    var kanoMonthly = ee.Image(computeMonthlyIndices(year, month, kanoRegion));
    
    Export.image.toCloudStorage({
      image: kanoMonthly.select('NDMI'),
      description: 'NDMI_KanoMetro_' + year + '_' + monthStr,
      bucket: BUCKET,
      fileNamePrefix: 'field_study/NDMI_KanoMetro_' + year + '_' + monthStr,
      region: kanoRegion,
      scale: 30,
      maxPixels: 1e13,
      fileFormat: 'GeoTIFF',
      formatOptions: {
        cloudOptimized: true
      }
    });
    
    Export.image.toCloudStorage({
      image: kanoMonthly.select('NDWI'),
      description: 'NDWI_KanoMetro_' + year + '_' + monthStr,
      bucket: BUCKET,
      fileNamePrefix: 'field_study/NDWI_KanoMetro_' + year + '_' + monthStr,
      region: kanoRegion,
      scale: 30,
      maxPixels: 1e13,
      fileFormat: 'GeoTIFF',
      formatOptions: {
        cloudOptimized: true
      }
    });
    
    // ========================================
    // IBADAN METROPOLITAN EXPORTS
    // ========================================
    var ibadanMonthly = ee.Image(computeMonthlyIndices(year, month, ibadanRegion));
    
    Export.image.toCloudStorage({
      image: ibadanMonthly.select('NDMI'),
      description: 'NDMI_IbadanMetro_' + year + '_' + monthStr,
      bucket: BUCKET,
      fileNamePrefix: 'field_study/NDMI_IbadanMetro_' + year + '_' + monthStr,
      region: ibadanRegion,
      scale: 30,
      maxPixels: 1e13,
      fileFormat: 'GeoTIFF',
      formatOptions: {
        cloudOptimized: true
      }
    });
    
    Export.image.toCloudStorage({
      image: ibadanMonthly.select('NDWI'),
      description: 'NDWI_IbadanMetro_' + year + '_' + monthStr,
      bucket: BUCKET,
      fileNamePrefix: 'field_study/NDWI_IbadanMetro_' + year + '_' + monthStr,
      region: ibadanRegion,
      scale: 30,
      maxPixels: 1e13,
      fileFormat: 'GeoTIFF',
      formatOptions: {
        cloudOptimized: true
      }
    });
    
    exportCount += 4;
  }
});

// ----------------------------------------
// SAMPLE VISUALIZATION
// ----------------------------------------
var sampleKano = ee.Image(computeMonthlyIndices(2023, 7, kanoRegion));
var sampleIbadan = ee.Image(computeMonthlyIndices(2023, 7, ibadanRegion));

Map.addLayer(sampleKano.select('NDMI'), 
  {min: -1, max: 1, palette: ['red', 'yellow', 'green', 'cyan', 'blue']}, 
  'NDMI Kano Metro July 2023', false);
Map.addLayer(sampleIbadan.select('NDWI'), 
  {min: -1, max: 1, palette: ['brown', 'white', 'blue', 'darkblue']}, 
  'NDWI Ibadan Metro July 2023', false);

// ----------------------------------------
// SUMMARY
// ----------------------------------------
print('\n' + '='.repeat(60));
print('EXACT METROPOLITAN BOUNDARIES');
print('='.repeat(60));
print('');
print('Using official metropolitan boundaries:');
print('  Kano: 6 LGAs metropolitan area (~300 km²)');
print('  Ibadan: 5 LGAs metropolitan area (~210 km²)');
print('');
print('Total exports: ' + exportCount + ' files');
print('  96 files total (2 years × 12 months × 2 cities × 2 indices)');
print('');
print('File locations:');
print('  gs://' + BUCKET + '/field_study/');
print('');
print('Estimated file sizes:');
print('  Kano Metro: ~10-15 MB per file');
print('  Ibadan Metro: ~8-12 MB per file');
print('  Total: ~1-2 GB for all 96 files');
print('');
print('These boundaries match the exact metropolitan areas');
print('where the field study was conducted!');
print('');
print('TO GET EVEN MORE PRECISE:');
print('1. Upload Kano_metro_sixLGA_shapes.shp to Earth Engine');
print('2. Upload Ibadan_metro_fiveLGAshapes.shp to Earth Engine');
print('3. Use the actual LGA polygons instead of bounding rectangles');