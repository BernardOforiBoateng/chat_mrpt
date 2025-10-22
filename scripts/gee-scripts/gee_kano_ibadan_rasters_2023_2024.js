// ========================================
// GENERATE NDMI/NDWI RASTERS FOR KANO & IBADAN ONLY
// 2023 and 2024, Months 1-12
// Exports directly to Cloud Storage
// ========================================

// ----------------------------------------
// CONFIGURATION
// ----------------------------------------
var BUCKET = 'ndmi_ndwi30m';
var years = [2023, 2024];
var startMonth = 1;  
var endMonth = 12;   // All months for E's analysis

// ----------------------------------------
// DEFINE STUDY AREAS (Smaller = Faster!)
// ----------------------------------------

// Option 1: Use state boundaries
var kanoState = ee.FeatureCollection('FAO/GAUL/2015/level1')
                  .filter(ee.Filter.eq('ADM1_NAME', 'Kano'));
var oyoState = ee.FeatureCollection('FAO/GAUL/2015/level1')
                 .filter(ee.Filter.eq('ADM1_NAME', 'Oyo'));

// Option 2: Use smaller city boundaries (MUCH faster processing)
// Kano city center with 50km buffer
var kanoCity = ee.Geometry.Point([8.5227, 11.9960]).buffer(50000);

// Ibadan city center with 40km buffer  
var ibadanCity = ee.Geometry.Point([3.9470, 7.3775]).buffer(40000);

// Use city boundaries for faster processing
var kanoRegion = kanoCity;  // Switch to kanoState if you need full state
var ibadanRegion = ibadanCity;  // Switch to oyoState if you need full state

// Visualize regions
Map.centerObject(kanoRegion, 9);
Map.addLayer(kanoRegion, {color: 'blue'}, 'Kano Area');
Map.addLayer(ibadanRegion, {color: 'green'}, 'Ibadan Area');

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
  
  // Load HLS data for the specific region only
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
    
    print('Processing ' + year + '-' + monthStr + '...');
    
    // ========================================
    // KANO EXPORTS
    // ========================================
    var kanoMonthly = ee.Image(computeMonthlyIndices(year, month, kanoRegion));
    
    // Check if we have data
    var imageCount = ee.Number(kanoMonthly.get('image_count'));
    print('  Kano ' + year + '-' + monthStr + ' images available: ', imageCount);
    
    // Export NDMI for Kano
    Export.image.toCloudStorage({
      image: kanoMonthly.select('NDMI'),
      description: 'NDMI_Kano_' + year + '_' + monthStr,
      bucket: BUCKET,
      fileNamePrefix: 'kano_ibadan/NDMI_Kano_' + year + '_' + monthStr,
      region: kanoRegion,
      scale: 30,
      maxPixels: 1e13,
      fileFormat: 'GeoTIFF',
      formatOptions: {
        cloudOptimized: true
      }
    });
    
    // Export NDWI for Kano
    Export.image.toCloudStorage({
      image: kanoMonthly.select('NDWI'),
      description: 'NDWI_Kano_' + year + '_' + monthStr,
      bucket: BUCKET,
      fileNamePrefix: 'kano_ibadan/NDWI_Kano_' + year + '_' + monthStr,
      region: kanoRegion,
      scale: 30,
      maxPixels: 1e13,
      fileFormat: 'GeoTIFF',
      formatOptions: {
        cloudOptimized: true
      }
    });
    
    // ========================================
    // IBADAN EXPORTS
    // ========================================
    var ibadanMonthly = ee.Image(computeMonthlyIndices(year, month, ibadanRegion));
    
    // Check if we have data
    var ibadanCount = ee.Number(ibadanMonthly.get('image_count'));
    print('  Ibadan ' + year + '-' + monthStr + ' images available: ', ibadanCount);
    
    // Export NDMI for Ibadan
    Export.image.toCloudStorage({
      image: ibadanMonthly.select('NDMI'),
      description: 'NDMI_Ibadan_' + year + '_' + monthStr,
      bucket: BUCKET,
      fileNamePrefix: 'kano_ibadan/NDMI_Ibadan_' + year + '_' + monthStr,
      region: ibadanRegion,
      scale: 30,
      maxPixels: 1e13,
      fileFormat: 'GeoTIFF',
      formatOptions: {
        cloudOptimized: true
      }
    });
    
    // Export NDWI for Ibadan
    Export.image.toCloudStorage({
      image: ibadanMonthly.select('NDWI'),
      description: 'NDWI_Ibadan_' + year + '_' + monthStr,
      bucket: BUCKET,
      fileNamePrefix: 'kano_ibadan/NDWI_Ibadan_' + year + '_' + monthStr,
      region: ibadanRegion,
      scale: 30,
      maxPixels: 1e13,
      fileFormat: 'GeoTIFF',
      formatOptions: {
        cloudOptimized: true
      }
    });
    
    exportCount += 4;  // 2 indices × 2 cities
  }
});

// ----------------------------------------
// DISPLAY SAMPLE FOR VERIFICATION
// ----------------------------------------
var sampleKano = ee.Image(computeMonthlyIndices(2023, 7, kanoRegion));
var sampleIbadan = ee.Image(computeMonthlyIndices(2023, 7, ibadanRegion));

Map.addLayer(sampleKano.select('NDMI'), 
  {min: -1, max: 1, palette: ['red', 'yellow', 'green', 'cyan', 'blue']}, 
  'NDMI Kano July 2023', false);
Map.addLayer(sampleIbadan.select('NDWI'), 
  {min: -1, max: 1, palette: ['brown', 'white', 'blue', 'darkblue']}, 
  'NDWI Ibadan July 2023', false);

// ----------------------------------------
// SUMMARY
// ----------------------------------------
print('\n' + '='.repeat(60));
print('EXPORT SUMMARY');
print('='.repeat(60));
print('Total export tasks created: ' + exportCount);
print('  - Years: 2023, 2024');
print('  - Months: 1-12 (all months)');
print('  - Cities: Kano, Ibadan');
print('  - Indices: NDMI, NDWI');
print('');
print('Files will be saved to:');
print('  gs://' + BUCKET + '/kano_ibadan/');
print('');
print('Expected files:');
print('  - 96 files total (2 years × 12 months × 2 cities × 2 indices)');
print('  - Each file ~10-50 MB (much smaller than Nigeria-wide)');
print('');
print('ADVANTAGES of this approach:');
print('  ✓ MUCH faster processing (small regions)');
print('  ✓ Single files (no tiles to merge)');
print('  ✓ Ready to share with E');
print('');
print('Go to Tasks tab and click RUN on all exports!');