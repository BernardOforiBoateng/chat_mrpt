// Download MONTHLY NDMI and NDWI raster files for Nigeria from Sentinel-2
// Years: 2015, 2018, and 2021
// NDMI: Normalized Difference Moisture Index = (NIR - SWIR1) / (NIR + SWIR1)
// NDWI: Normalized Difference Water Index = (Green - NIR) / (Green + NIR)

// Define Nigeria boundary
var nigeria = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017')
  .filter(ee.Filter.eq('country_na', 'Nigeria'));

// Function to mask clouds from Sentinel-2 images
function maskS2clouds(image) {
  var qa = image.select('QA60');
  
  // Bits 10 and 11 are clouds and cirrus, respectively
  var cloudBitMask = 1 << 10;
  var cirrusBitMask = 1 << 11;
  
  // Both flags should be set to zero, indicating clear conditions
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

// Process monthly data for each year
var years = [2015, 2018, 2021];

years.forEach(function(year) {
  // Define months to process
  var startMonth = (year === 2015) ? 7 : 1; // Sentinel-2 starts from June 2015
  var endMonth = 12;
  
  for (var month = startMonth; month <= endMonth; month++) {
    var startDate = ee.Date.fromYMD(year, month, 1);
    var endDate = startDate.advance(1, 'month');
    
    // Load and process Sentinel-2 collection for the month
    var s2Collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
      .filterBounds(nigeria)
      .filterDate(startDate, endDate)
      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
      .map(maskS2clouds)
      .map(addIndices);
    
    // Check if there are images for this month
    var imageCount = s2Collection.size();
    
    // Only process if images are available
    var monthlyComposite = s2Collection.select(['NDMI', 'NDWI']).median();
    
    // Clip to Nigeria boundary
    var ndmiMonthly = monthlyComposite.select('NDMI').clip(nigeria);
    var ndwiMonthly = monthlyComposite.select('NDWI').clip(nigeria);
    
    // Format month with leading zero
    var monthStr = (month < 10) ? '0' + month : '' + month;
    
    // Export NDMI monthly
    Export.image.toDrive({
      image: ndmiMonthly,
      description: 'Nigeria_NDMI_S2_' + year + '_' + monthStr,
      folder: 'GEE_Nigeria_Monthly',
      fileNamePrefix: 'Nigeria_NDMI_S2_' + year + '_' + monthStr,
      scale: 10,
      crs: 'EPSG:4326',
      region: nigeria.geometry(),
      maxPixels: 1e13,
      fileFormat: 'GeoTIFF'
    });
    
    // Export NDWI monthly
    Export.image.toDrive({
      image: ndwiMonthly,
      description: 'Nigeria_NDWI_S2_' + year + '_' + monthStr,
      folder: 'GEE_Nigeria_Monthly',
      fileNamePrefix: 'Nigeria_NDWI_S2_' + year + '_' + monthStr,
      scale: 10,
      crs: 'EPSG:4326',
      region: nigeria.geometry(),
      maxPixels: 1e13,
      fileFormat: 'GeoTIFF'
    });
    
    // Print month info
    print('Processing ' + year + '-' + monthStr + ', Images available: ', imageCount);
  }
});

// Visualization parameters
var ndmiVis = {min: -0.8, max: 0.8, palette: ['red', 'yellow', 'green', 'cyan', 'blue']};
var ndwiVis = {min: -0.5, max: 0.5, palette: ['brown', 'white', 'blue', 'darkblue']};

// Add example visualization for a specific month
var exampleYear = 2021;
var exampleMonth = 7; // July

var exampleStartDate = ee.Date.fromYMD(exampleYear, exampleMonth, 1);
var exampleEndDate = exampleStartDate.advance(1, 'month');

var exampleCollection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(nigeria)
  .filterDate(exampleStartDate, exampleEndDate)
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
  .map(maskS2clouds)
  .map(addIndices);

var exampleComposite = exampleCollection.select(['NDMI', 'NDWI']).median();
var exampleNDMI = exampleComposite.select('NDMI').clip(nigeria);
var exampleNDWI = exampleComposite.select('NDWI').clip(nigeria);

Map.addLayer(exampleNDMI, ndmiVis, 'NDMI Example - July 2021');
Map.addLayer(exampleNDWI, ndwiVis, 'NDWI Example - July 2021');

// Center map on Nigeria
Map.centerObject(nigeria, 6);

// Print total number of export tasks
var totalExports = 0;
years.forEach(function(year) {
  var monthsInYear = (year === 2015) ? 6 : 12; // 6 months for 2015, 12 for others
  totalExports += monthsInYear * 2; // 2 indices per month
});

print('Total export tasks created: ' + totalExports);
print('Files will be saved to Google Drive folder: GEE_Nigeria_Monthly');