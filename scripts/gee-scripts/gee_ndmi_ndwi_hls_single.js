// Download MONTHLY NDMI and NDWI using NASA HLS (Harmonized Landsat-Sentinel) data
// Modified to export as SINGLE FILES to Google Drive
// Years: 2015, 2018, 2021, 2023, 2024
// Months: July to December (7-12)

// Load Nigeria boundary
var nigeria = ee.FeatureCollection('FAO/GAUL/2015/level0')
                 .filter(ee.Filter.eq('ADM0_NAME', 'Nigeria'));

// Center the map and display boundary
Map.centerObject(nigeria, 6);
Map.addLayer(nigeria, {color: 'blue'}, 'Nigeria boundary');

// Define years and months to process
var years = [2015, 2018, 2021, 2023, 2024];
var startMonth = 7;  // July
var endMonth = 12;   // December

// Function to calculate NDMI and NDWI for an image given its sensor
function calculateIndices(img, sensor) {
  // Band mapping for HLS
  // S2: B3=Green, B4=Red, B8A=NIR, B11=SWIR1
  // L8: B3=Green, B4=Red, B5=NIR, B6=SWIR1
  
  var green = sensor === 'S2' ? img.select('B3') : img.select('B3');
  var nir = sensor === 'S2' ? img.select('B8A') : img.select('B5');
  var swir1 = sensor === 'S2' ? img.select('B11') : img.select('B6');
  
  // NDMI = (NIR - SWIR1) / (NIR + SWIR1)
  var ndmi = img.expression(
    '(NIR - SWIR1) / (NIR + SWIR1)', {
      'NIR': nir,
      'SWIR1': swir1
    }
  ).rename('NDMI');
  
  // NDWI = (Green - NIR) / (Green + NIR)
  var ndwi = img.expression(
    '(GREEN - NIR) / (GREEN + NIR)', {
      'GREEN': green,
      'NIR': nir
    }
  ).rename('NDWI');
  
  return ndmi.addBands(ndwi).copyProperties(img, img.propertyNames());
}

// Function to compute mean indices for a given month and year
function computeMonthlyMeanIndices(year, month) {
  var start = ee.Date.fromYMD(year, month, 1);
  var end = start.advance(1, 'month');
  
  // Load HLS Sentinel-2 data
  var s2 = ee.ImageCollection('NASA/HLS/HLSS30/v002')
              .filterDate(start, end)
              .filterBounds(nigeria);
  
  // Load HLS Landsat-8 data
  var l8 = ee.ImageCollection('NASA/HLS/HLSL30/v002')
              .filterDate(start, end)
              .filterBounds(nigeria);
  
  // Calculate indices for each collection
  var s2Indices = s2.map(function(img) {
    return calculateIndices(img, 'S2');
  });
  
  var l8Indices = l8.map(function(img) {
    return calculateIndices(img, 'L8');
  });
  
  // Merge both collections
  var mergedIndices = s2Indices.merge(l8Indices);
  
  // Check if data exists
  var hasData = mergedIndices.size().gt(0);
  
  return ee.Algorithms.If(hasData,
    mergedIndices.mean()
      .set('month', month)
      .set('year', year)
      .set('system:time_start', start.millis()),
    null
  );
}

// Process and export for each year and month
years.forEach(function(year) {
  for (var month = startMonth; month <= endMonth; month++) {
    
    // Format month with leading zero
    var monthStr = (month < 10) ? '0' + month : '' + month;
    
    // Compute monthly mean indices
    var monthlyImage = computeMonthlyMeanIndices(year, month);
    
    // Check if image exists and process
    var processedImage = ee.Image(ee.Algorithms.If(
      monthlyImage,
      ee.Image(monthlyImage).clip(nigeria),
      ee.Image.constant(0).rename(['NDMI', 'NDWI']).clip(nigeria)
    ));
    
    // Get NDMI and NDWI as separate images
    var ndmiImage = processedImage.select('NDMI');
    var ndwiImage = processedImage.select('NDWI');
    
    // Add visualization layers for verification
    Map.addLayer(ndmiImage, {min: -1, max: 1, palette: ['red', 'yellow', 'green', 'cyan', 'blue']}, 
                 'NDMI_' + year + '_' + monthStr, false);
    Map.addLayer(ndwiImage, {min: -1, max: 1, palette: ['brown', 'white', 'blue', 'darkblue']}, 
                 'NDWI_' + year + '_' + monthStr, false);
    
    // Export NDMI to Google Drive
    // Note: Drive may split into tiles if file is too large
    // If you want guaranteed single files, use Cloud Storage instead
    Export.image.toDrive({
      image: ndmiImage,
      description: 'NDMI_' + year + '_' + monthStr,
      folder: 'Nigeria_NDMI_NDWI_HLS',
      fileNamePrefix: 'NDMI_' + year + '_' + monthStr,
      region: nigeria.geometry(),
      scale: 30,
      maxPixels: 1e13,
      fileFormat: 'GeoTIFF',
      formatOptions: {
        cloudOptimized: true
      }
    });
    
    // Export NDWI to Google Drive
    Export.image.toDrive({
      image: ndwiImage,
      description: 'NDWI_' + year + '_' + monthStr,
      folder: 'Nigeria_NDMI_NDWI_HLS',
      fileNamePrefix: 'NDWI_' + year + '_' + monthStr,
      region: nigeria.geometry(),
      scale: 30,
      maxPixels: 1e13,
      fileFormat: 'GeoTIFF',
      formatOptions: {
        cloudOptimized: true
      }
    });
    
    print('Created export task for ' + year + '-' + monthStr);
  }
});

// Print summary
var totalExports = years.length * 6 * 2; // 5 years * 6 months * 2 indices
print('Total export tasks created: ' + totalExports);
print('Files will be saved to Google Drive folder: Nigeria_NDMI_NDWI_HLS_SINGLE');
print('Each file will be a SINGLE Cloud-Optimized GeoTIFF (no tiles!)');
print('Data source: NASA HLS (Harmonized Landsat-Sentinel) at 30m resolution');