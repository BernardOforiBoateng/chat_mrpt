// Download ANNUAL files with MONTHLY bands for NDMI and NDWI for Nigeria from Sentinel-2
// Enhanced version with better coverage
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

// Process each year with gap filling
var years = [2015, 2018, 2021];

years.forEach(function(year) {
  var startMonth = (year === 2015) ? 7 : 1;
  var endMonth = 12;
  
  var allNdmiImages = [];
  var allNdwiImages = [];
  
  // First, create seasonal/quarterly composites for gap filling
  var yearStart = ee.Date.fromYMD(year, startMonth, 1);
  var yearEnd = ee.Date.fromYMD(year, 12, 31);
  
  // Get all images for the year with relaxed cloud filter
  var yearlyCollection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(nigeria)
    .filterDate(yearStart, yearEnd)
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 40)) // Increased threshold
    .map(maskS2clouds)
    .map(addIndices);
  
  // Create seasonal composites for gap filling
  var seasonalComposite = yearlyCollection.select(['NDMI', 'NDWI']).median();
  
  // Process each month
  for (var month = startMonth; month <= endMonth; month++) {
    var startDate = ee.Date.fromYMD(year, month, 1);
    var endDate = startDate.advance(1, 'month');
    var monthStr = (month < 10) ? '0' + month : '' + month;
    
    // Get monthly collection with standard cloud filter
    var monthlyCollection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
      .filterBounds(nigeria)
      .filterDate(startDate, endDate)
      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
      .map(maskS2clouds)
      .map(addIndices);
    
    // Try 3-month window if monthly data is insufficient
    var extendedStart = startDate.advance(-1, 'month');
    var extendedEnd = endDate.advance(1, 'month');
    
    var extendedCollection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
      .filterBounds(nigeria)
      .filterDate(extendedStart, extendedEnd)
      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
      .map(maskS2clouds)
      .map(addIndices);
    
    var monthlyCount = monthlyCollection.size();
    var extendedCount = extendedCollection.size();
    
    // Create composite with fallback strategy
    var monthlyComposite = ee.Image(ee.Algorithms.If(
      monthlyCount.gt(5), // If enough images in the month
      monthlyCollection.select(['NDMI', 'NDWI']).median(),
      ee.Algorithms.If(
        extendedCount.gt(10), // Use extended window
        extendedCollection.select(['NDMI', 'NDWI']).median(),
        // Use seasonal composite as last resort
        seasonalComposite
      )
    ));
    
    // Clip and rename
    monthlyComposite = monthlyComposite.clip(nigeria);
    var ndmiMonth = monthlyComposite.select('NDMI').rename('NDMI_' + monthStr);
    var ndwiMonth = monthlyComposite.select('NDWI').rename('NDWI_' + monthStr);
    
    allNdmiImages.push(ndmiMonth);
    allNdwiImages.push(ndwiMonth);
    
    // Print coverage statistics
    var coverage = monthlyComposite.select('NDMI').unmask().gte(-1).reduceRegion({
      reducer: ee.Reducer.mean(),
      geometry: nigeria.geometry(),
      scale: 1000,
      maxPixels: 1e10
    });
    
    print(year + '-' + monthStr + ' coverage: ' + coverage.getInfo()['NDMI']);
  }
  
  // Combine bands
  var ndmiAnnual = ee.Image.cat(allNdmiImages);
  var ndwiAnnual = ee.Image.cat(allNdwiImages);
  
  // Fill any remaining gaps with nearest neighbor
  var kernel = ee.Kernel.square(2, 'pixels');
  ndmiAnnual = ndmiAnnual.focal_mean({
    kernel: kernel,
    iterations: 2
  }).blend(ndmiAnnual);
  
  ndwiAnnual = ndwiAnnual.focal_mean({
    kernel: kernel,
    iterations: 2
  }).blend(ndwiAnnual);
  
  // Export with optimized parameters
  Export.image.toDrive({
    image: ndmiAnnual.toFloat(),
    description: 'Nigeria_NDMI_S2_' + year + '_Complete',
    folder: 'GEE_Nigeria_Annual_Complete',
    fileNamePrefix: 'Nigeria_NDMI_S2_' + year + '_Complete',
    scale: 20, // Slightly coarser for complete coverage
    crs: 'EPSG:4326',
    region: nigeria.geometry().bounds(),
    maxPixels: 1e13,
    fileFormat: 'GeoTIFF',
    formatOptions: {
      cloudOptimized: true
    }
  });
  
  Export.image.toDrive({
    image: ndwiAnnual.toFloat(),
    description: 'Nigeria_NDWI_S2_' + year + '_Complete',
    folder: 'GEE_Nigeria_Annual_Complete',
    fileNamePrefix: 'Nigeria_NDWI_S2_' + year + '_Complete',
    scale: 20,
    crs: 'EPSG:4326',
    region: nigeria.geometry().bounds(),
    maxPixels: 1e13,
    fileFormat: 'GeoTIFF',
    formatOptions: {
      cloudOptimized: true
    }
  });
});

// Visualize coverage for 2021
var testYear = 2021;
var testCollection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(nigeria)
  .filterDate('2021-01-01', '2021-12-31')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
  .map(maskS2clouds)
  .map(addIndices);

var yearlyMedian = testCollection.select(['NDMI', 'NDWI']).median().clip(nigeria);
var pixelCount = testCollection.select('NDMI').count().clip(nigeria);

// Visualization
var ndmiVis = {min: -0.2, max: 0.6, palette: ['red', 'yellow', 'green', 'cyan', 'blue']};
var countVis = {min: 0, max: 100, palette: ['red', 'yellow', 'green']};

Map.centerObject(nigeria, 6);
Map.addLayer(yearlyMedian.select('NDMI'), ndmiVis, '2021 NDMI Yearly Median');
Map.addLayer(pixelCount, countVis, '2021 Valid Pixel Count');
Map.addLayer(nigeria, {}, 'Nigeria Boundary', false);

print('==========================================');
print('Enhanced Coverage Strategy:');
print('1. Primary: Monthly median (20% cloud filter)');
print('2. Fallback: 3-month window (30% cloud filter)');
print('3. Last resort: Seasonal composite (40% cloud filter)');
print('4. Gap filling: Focal mean interpolation');
print('==========================================');