// ============================================
// EXPORT NDMI/NDWI DIRECTLY FROM GEE TO CLOUD STORAGE
// Much faster than Drive → Cloud Storage transfer!
// ============================================

// Load Nigeria boundary
var nigeria = ee.FeatureCollection('FAO/GAUL/2015/level0')
                 .filter(ee.Filter.eq('ADM0_NAME', 'Nigeria'));

Map.centerObject(nigeria, 6);
Map.addLayer(nigeria, {color: 'blue'}, 'Nigeria boundary');

// Configuration
var years = [2015, 2018, 2021, 2023, 2024];
var startMonth = 7;  // July
var endMonth = 12;   // December

// YOUR CLOUD STORAGE BUCKET
var BUCKET = 'ndmi_ndwi30m';

// Function to calculate indices using HLS data
function calculateIndices(img, sensor) {
  var green = sensor === 'S2' ? img.select('B3') : img.select('B3');
  var nir = sensor === 'S2' ? img.select('B8A') : img.select('B5');
  var swir1 = sensor === 'S2' ? img.select('B11') : img.select('B6');
  
  var ndmi = img.expression(
    '(NIR - SWIR1) / (NIR + SWIR1)', {
      'NIR': nir,
      'SWIR1': swir1
    }
  ).rename('NDMI');
  
  var ndwi = img.expression(
    '(GREEN - NIR) / (GREEN + NIR)', {
      'GREEN': green,
      'NIR': nir
    }
  ).rename('NDWI');
  
  return ndmi.addBands(ndwi).copyProperties(img, img.propertyNames());
}

// Function to compute monthly mean indices
function computeMonthlyMeanIndices(year, month) {
  var start = ee.Date.fromYMD(year, month, 1);
  var end = start.advance(1, 'month');
  
  // Load HLS data
  var s2 = ee.ImageCollection('NASA/HLS/HLSS30/v002')
              .filterDate(start, end)
              .filterBounds(nigeria);
  
  var l8 = ee.ImageCollection('NASA/HLS/HLSL30/v002')
              .filterDate(start, end)
              .filterBounds(nigeria);
  
  // Calculate indices
  var s2Indices = s2.map(function(img) {
    return calculateIndices(img, 'S2');
  });
  
  var l8Indices = l8.map(function(img) {
    return calculateIndices(img, 'L8');
  });
  
  // Merge and compute mean
  var mergedIndices = s2Indices.merge(l8Indices);
  var hasData = mergedIndices.size().gt(0);
  
  return ee.Algorithms.If(hasData,
    mergedIndices.mean()
      .set('month', month)
      .set('year', year),
    null
  );
}

// Process and export each year/month
var exportCount = 0;

years.forEach(function(year) {
  for (var month = startMonth; month <= endMonth; month++) {
    
    var monthStr = (month < 10) ? '0' + month : '' + month;
    
    // Compute monthly indices
    var monthlyImage = computeMonthlyMeanIndices(year, month);
    
    var processedImage = ee.Image(ee.Algorithms.If(
      monthlyImage,
      ee.Image(monthlyImage).clip(nigeria),
      ee.Image.constant(0).rename(['NDMI', 'NDWI']).clip(nigeria)
    ));
    
    // Get NDMI and NDWI as separate images
    var ndmiImage = processedImage.select('NDMI');
    var ndwiImage = processedImage.select('NDWI');
    
    // EXPORT NDMI DIRECTLY TO CLOUD STORAGE
    Export.image.toCloudStorage({
      image: ndmiImage,
      description: 'NDMI_' + year + '_' + monthStr,
      bucket: BUCKET,
      fileNamePrefix: 'NDMI_' + year + '_' + monthStr,
      region: nigeria.geometry(),
      scale: 30,
      maxPixels: 1e13,
      fileFormat: 'GeoTIFF',
      formatOptions: {
        cloudOptimized: true
      }
    });
    
    // EXPORT NDWI DIRECTLY TO CLOUD STORAGE
    Export.image.toCloudStorage({
      image: ndwiImage,
      description: 'NDWI_' + year + '_' + monthStr,
      bucket: BUCKET,
      fileNamePrefix: 'NDWI_' + year + '_' + monthStr,
      region: nigeria.geometry(),
      scale: 30,
      maxPixels: 1e13,
      fileFormat: 'GeoTIFF',
      formatOptions: {
        cloudOptimized: true
      }
    });
    
    exportCount += 2;
    print('Created export tasks for ' + year + '-' + monthStr);
  }
});

// Add visualization for checking
var sampleYear = 2021;
var sampleMonth = 7;
var sampleImage = computeMonthlyMeanIndices(sampleYear, sampleMonth);
if (sampleImage) {
  var sample = ee.Image(sampleImage).clip(nigeria);
  Map.addLayer(sample.select('NDMI'), 
    {min: -1, max: 1, palette: ['red', 'yellow', 'green', 'cyan', 'blue']}, 
    'NDMI Sample', false);
  Map.addLayer(sample.select('NDWI'), 
    {min: -1, max: 1, palette: ['brown', 'white', 'blue', 'darkblue']}, 
    'NDWI Sample', false);
}

print('====================================');
print('EXPORT SUMMARY');
print('====================================');
print('Total export tasks created: ' + exportCount);
print('Destination: gs://' + BUCKET + '/');
print('');
print('NEXT STEPS:');
print('1. Go to Tasks tab');
print('2. Click RUN on all tasks (you can run multiple at once)');
print('3. Exports will go DIRECTLY to Cloud Storage (faster!)');
print('4. No Drive involved = No space issues, much faster');
print('');
print('ADVANTAGES:');
print('- Faster: Uses Google internal network');
print('- No Drive space needed');
print('- Can run many exports in parallel');
print('- Files will be cloud-optimized GeoTIFFs');
print('');
print('Note: If files are large, GEE might still tile them');
print('but they will all be in your bucket!');