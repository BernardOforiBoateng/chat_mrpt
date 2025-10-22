// Download ANNUAL files with MONTHLY bands for NDMI and NDWI for Nigeria from Sentinel-2
// Years: 2015, 2018, and 2021
// Output: 6 files total (3 years × 2 indices)

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
  // Define months to process
  var startMonth = (year === 2015) ? 7 : 1; // Sentinel-2 starts from July 2015
  var endMonth = 12;
  
  // Create lists to store all monthly images
  var allNdmiImages = [];
  var allNdwiImages = [];
  
  // Process each month
  for (var month = startMonth; month <= endMonth; month++) {
    var startDate = ee.Date.fromYMD(year, month, 1);
    var endDate = startDate.advance(1, 'month');
    
    // Format month with leading zero
    var monthStr = (month < 10) ? '0' + month : '' + month;
    
    // Load and process Sentinel-2 collection for the month
    var s2Collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
      .filterBounds(nigeria)
      .filterDate(startDate, endDate)
      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
      .map(maskS2clouds)
      .map(addIndices);
    
    // Check if collection has images
    var imageCount = s2Collection.size();
    
    // Create monthly composite with fallback for empty collections
    var monthlyComposite = ee.Image(ee.Algorithms.If(
      imageCount.gt(0),
      s2Collection.select(['NDMI', 'NDWI']).median(),
      // Create empty bands with proper names if no data
      ee.Image.constant(0).rename(['NDMI', 'NDWI']).updateMask(0)
    ));
    
    // Clip to Nigeria
    monthlyComposite = monthlyComposite.clip(nigeria);
    
    // Rename bands with month suffix
    var ndmiMonth = monthlyComposite.select('NDMI').rename('NDMI_' + monthStr);
    var ndwiMonth = monthlyComposite.select('NDWI').rename('NDWI_' + monthStr);
    
    // Add to lists
    allNdmiImages.push(ndmiMonth);
    allNdwiImages.push(ndwiMonth);
    
    // Print status
    print(year + '-' + monthStr + ' images found:', imageCount);
  }
  
  // Combine all NDMI monthly bands into single image
  var ndmiAnnual = ee.Image.cat(allNdmiImages);
  
  // Combine all NDWI monthly bands into single image
  var ndwiAnnual = ee.Image.cat(allNdwiImages);
  
  // Export annual NDMI file with all monthly bands
  Export.image.toDrive({
    image: ndmiAnnual,
    description: 'Nigeria_NDMI_S2_' + year + '_AllMonths',
    folder: 'GEE_Nigeria_Annual',
    fileNamePrefix: 'Nigeria_NDMI_S2_' + year + '_AllMonths',
    scale: 10,
    crs: 'EPSG:4326',
    region: nigeria.geometry().bounds(),
    maxPixels: 1e13,
    fileFormat: 'GeoTIFF'
  });
  
  // Export annual NDWI file with all monthly bands
  Export.image.toDrive({
    image: ndwiAnnual,
    description: 'Nigeria_NDWI_S2_' + year + '_AllMonths',
    folder: 'GEE_Nigeria_Annual',
    fileNamePrefix: 'Nigeria_NDWI_S2_' + year + '_AllMonths',
    scale: 10,
    crs: 'EPSG:4326',
    region: nigeria.geometry().bounds(),
    maxPixels: 1e13,
    fileFormat: 'GeoTIFF'
  });
  
  // Print band names
  print('Annual file for ' + year + ' created with bands:');
  print('NDMI bands:', ndmiAnnual.bandNames());
  print('NDWI bands:', ndwiAnnual.bandNames());
});

// Visualize sample month from 2021
var sampleDate = '2021-07-01';
var sampleViz = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(nigeria)
  .filterDate(sampleDate, '2021-08-01')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
  .map(maskS2clouds)
  .map(addIndices)
  .median()
  .clip(nigeria);

// Visualization parameters
var ndmiVis = {min: -0.2, max: 0.6, palette: ['red', 'yellow', 'green', 'cyan', 'blue']};
var ndwiVis = {min: -0.5, max: 0.5, palette: ['brown', 'white', 'cyan', 'blue']};

// Add layers to map
Map.centerObject(nigeria, 6);
Map.addLayer(sampleViz.select('NDMI'), ndmiVis, 'NDMI Sample July 2021');
Map.addLayer(sampleViz.select('NDWI'), ndwiVis, 'NDWI Sample July 2021');

// Print summary
print('==========================================');
print('Total files to export: 6');
print('- 3 NDMI annual files (2015, 2018, 2021)');
print('- 3 NDWI annual files (2015, 2018, 2021)');
print('Files will be saved to: GEE_Nigeria_Annual');
print('==========================================');