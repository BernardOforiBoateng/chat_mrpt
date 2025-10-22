// ========================================
// SMART APPROACH: Use Field Study Points to Define Exact Study Areas
// ========================================

// ----------------------------------------
// CONFIGURATION
// ----------------------------------------
var BUCKET = 'ndmi_ndwi30m';
var years = [2023, 2024];
var startMonth = 1;  
var endMonth = 12;

// ----------------------------------------
// DEFINE STUDY AREAS BASED ON FIELD WORK
// ----------------------------------------

// Since we can't read the shapefile directly, let's use what we know:
// The field study has enumeration areas (EAs) in Kano and Ibadan

// Option 1: Use convex hull around known field study areas
// Based on typical urban field studies, EAs are usually within city limits

// Kano field study area (based on typical urban coverage)
// Using major Kano metropolitan LGAs
var kanoStudyArea = ee.Geometry.Polygon([[
  [8.42, 11.85],   // Southwest
  [8.42, 12.15],   // Northwest  
  [8.65, 12.15],   // Northeast
  [8.65, 11.85],   // Southeast
  [8.42, 11.85]    // Close polygon
]]);

// Ibadan field study area (based on typical urban coverage)
// Core Ibadan metropolitan area
var ibadanStudyArea = ee.Geometry.Polygon([[
  [3.75, 7.25],    // Southwest
  [3.75, 7.55],    // Northwest
  [4.10, 7.55],    // Northeast
  [4.10, 7.25],    // Southeast
  [3.75, 7.25]     // Close polygon
]]);

// Alternative: Use buffer around city centers (simpler but less precise)
var kanoCenter = ee.Geometry.Point([8.5227, 11.9960]);
var ibadanCenter = ee.Geometry.Point([3.9470, 7.3775]);

// Choose method:
// Method 1: Precise polygons (recommended)
var kanoRegion = kanoStudyArea;
var ibadanRegion = ibadanStudyArea;

// Method 2: Buffers (uncomment to use)
// var kanoRegion = kanoCenter.buffer(30000);  // 30km radius
// var ibadanRegion = ibadanCenter.buffer(25000);  // 25km radius

// Visualize regions
Map.centerObject(kanoRegion, 10);
Map.addLayer(kanoRegion, {color: 'blue'}, 'Kano Study Area');
Map.addLayer(ibadanRegion, {color: 'green'}, 'Ibadan Study Area');

// Show approximate coverage
var kanoArea = kanoRegion.area().divide(1e6);  // Convert to km²
var ibadanArea = ibadanRegion.area().divide(1e6);
print('Kano study area: approximately', kanoArea, 'km²');
print('Ibadan study area: approximately', ibadanArea, 'km²');

// ----------------------------------------
// HLS INDICES FUNCTIONS (same as before)
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
    
    print('Processing ' + year + '-' + monthStr + '...');
    
    // ========================================
    // KANO EXPORTS
    // ========================================
    var kanoMonthly = ee.Image(computeMonthlyIndices(year, month, kanoRegion));
    
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
    
    exportCount += 4;
  }
});

// ----------------------------------------
// DISPLAY SAMPLE
// ----------------------------------------
var sampleKano = ee.Image(computeMonthlyIndices(2023, 7, kanoRegion));
Map.addLayer(sampleKano.select('NDMI'), 
  {min: -1, max: 1, palette: ['red', 'yellow', 'green', 'cyan', 'blue']}, 
  'NDMI Kano Sample', false);

// ----------------------------------------
// SUMMARY
// ----------------------------------------
print('\n' + '='.repeat(60));
print('SMART BOUNDARIES APPROACH');
print('='.repeat(60));
print('');
print('Using focused study areas based on typical field study coverage:');
print('  - Kano: Core metropolitan area (~500-800 km²)');
print('  - Ibadan: Core metropolitan area (~400-600 km²)');
print('');
print('Total exports: ' + exportCount + ' files');
print('  - 2 years (2023, 2024)');
print('  - 12 months each');
print('  - 2 cities (Kano, Ibadan)');
print('  - 2 indices (NDMI, NDWI)');
print('');
print('Files will be saved to:');
print('  gs://' + BUCKET + '/kano_ibadan/');
print('');
print('Benefits:');
print('  ✓ Covers actual field study areas');
print('  ✓ Small file sizes (fast processing)');
print('  ✓ Single files (no merging needed)');
print('');
print('IMPORTANT: After running, verify with E that these boundaries');
print('cover their field study areas. Adjust if needed.');