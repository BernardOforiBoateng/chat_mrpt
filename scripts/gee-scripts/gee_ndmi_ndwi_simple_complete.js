// Download ANNUAL files with MONTHLY bands for NDMI and NDWI for Nigeria from Sentinel-2
// Simple version with better coverage
// Years: 2015, 2018, and 2021

// Define Nigeria boundary
var nigeria = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017')
  .filter(ee.Filter.eq('country_na', 'Nigeria'));

// Function to mask clouds from Sentinel-2 images
function maskS2clouds(image) {
  var qa = image.select('QA60');
  var cloudBitMask = 1 << 10;
  var cirrusBitMask = 1 << 11;
  var mask = qa.bitwiseAnd(cloudBitMask).eq(0)
      .and(qa.bitwiseAnd(cirrusBitMask).eq(0));
  return image.updateMask(mask).divide(10000)
      .copyProperties(image, ["system:time_start"]);
}

// Function to add NDMI and NDWI bands
function addIndices(image) {
  var ndmi = image.normalizedDifference(['B8', 'B11']).rename('NDMI');
  var ndwi = image.normalizedDifference(['B3', 'B8']).rename('NDWI');
  return image.addBands([ndmi, ndwi]);
}

// Process each year
var years = [2015, 2018, 2021];

years.forEach(function(year) {
  var startMonth = (year === 2015) ? 7 : 1;
  var endMonth = 12;
  
  var allNdmiImages = [];
  var allNdwiImages = [];
  
  // Process each month with extended window for better coverage
  for (var month = startMonth; month <= endMonth; month++) {
    var monthStr = (month < 10) ? '0' + month : '' + month;
    
    // Use 2-month window centered on target month for better coverage
    var startDate = ee.Date.fromYMD(year, month, 1).advance(-15, 'day');
    var endDate = ee.Date.fromYMD(year, month, 1).advance(45, 'day');
    
    // Adjust for year boundaries
    if (month === 1) {
      startDate = ee.Date.fromYMD(year, 1, 1);
    }
    if (month === 12) {
      endDate = ee.Date.fromYMD(year, 12, 31);
    }
    
    // Get collection with relaxed cloud filter
    var monthlyCollection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
      .filterBounds(nigeria)
      .filterDate(startDate, endDate)
      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
      .map(maskS2clouds)
      .map(addIndices);
    
    // Create composite
    var monthlyComposite = monthlyCollection.select(['NDMI', 'NDWI']).median().clip(nigeria);
    
    // Rename bands
    var ndmiMonth = monthlyComposite.select('NDMI').rename('NDMI_' + monthStr);
    var ndwiMonth = monthlyComposite.select('NDWI').rename('NDWI_' + monthStr);
    
    allNdmiImages.push(ndmiMonth);
    allNdwiImages.push(ndwiMonth);
    
    // Print image count
    print(year + '-' + monthStr + ': ' + monthlyCollection.size().getInfo() + ' images');
  }
  
  // Combine all monthly bands
  var ndmiAnnual = ee.Image.cat(allNdmiImages);
  var ndwiAnnual = ee.Image.cat(allNdwiImages);
  
  // Export NDMI
  Export.image.toDrive({
    image: ndmiAnnual,
    description: 'Nigeria_NDMI_S2_' + year + '_Monthly',
    folder: 'GEE_Nigeria_Annual',
    fileNamePrefix: 'Nigeria_NDMI_S2_' + year + '_Monthly',
    scale: 10,
    crs: 'EPSG:4326',
    region: nigeria.geometry().bounds(),
    maxPixels: 1e13,
    fileFormat: 'GeoTIFF'
  });
  
  // Export NDWI
  Export.image.toDrive({
    image: ndwiAnnual,
    description: 'Nigeria_NDWI_S2_' + year + '_Monthly',
    folder: 'GEE_Nigeria_Annual',
    fileNamePrefix: 'Nigeria_NDWI_S2_' + year + '_Monthly',
    scale: 10,
    crs: 'EPSG:4326',
    region: nigeria.geometry().bounds(),
    maxPixels: 1e13,
    fileFormat: 'GeoTIFF'
  });
  
  print('Exported ' + year + ' with bands:', ndmiAnnual.bandNames().getInfo());
});

// Visualize data availability
var availability2021 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(nigeria)
  .filterDate('2021-01-01', '2021-12-31')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
  .map(maskS2clouds)
  .select('B2')
  .count()
  .clip(nigeria);

Map.centerObject(nigeria, 6);
Map.addLayer(availability2021, 
  {min: 0, max: 50, palette: ['red', 'yellow', 'green', 'blue']}, 
  '2021 Clear Observations Count');

print('==========================================');
print('Export Configuration:');
print('- Extended temporal window for better coverage');
print('- 30% cloud threshold');
print('- 10m resolution');
print('- 6 files total (3 years × 2 indices)');
print('==========================================');