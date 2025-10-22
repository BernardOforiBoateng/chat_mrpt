// Download NDMI and NDWI raster files for Nigeria from Sentinel-2
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

// Process data for each year
var years = [2015, 2018, 2021];

years.forEach(function(year) {
  // Note: Sentinel-2 data starts from June 2015
  var startDate = year + '-01-01';
  var endDate = year + '-12-31';
  
  // For 2015, adjust start date since Sentinel-2 began operations in June
  if (year === 2015) {
    startDate = '2015-06-23';
  }
  
  // Load and process Sentinel-2 collection
  var s2Collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(nigeria)
    .filterDate(startDate, endDate)
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
    .map(maskS2clouds)
    .map(addIndices);
  
  // Calculate median composites
  var medianComposite = s2Collection.select(['NDMI', 'NDWI']).median();
  
  // Clip to Nigeria boundary
  var ndmiImage = medianComposite.select('NDMI').clip(nigeria);
  var ndwiImage = medianComposite.select('NDWI').clip(nigeria);
  
  // Visualization parameters
  var ndmiVis = {min: -0.8, max: 0.8, palette: ['red', 'yellow', 'green', 'cyan', 'blue']};
  var ndwiVis = {min: -0.5, max: 0.5, palette: ['brown', 'white', 'blue', 'darkblue']};
  
  // Add layers to map
  Map.addLayer(ndmiImage, ndmiVis, 'NDMI ' + year, false);
  Map.addLayer(ndwiImage, ndwiVis, 'NDWI ' + year, false);
  
  // Export NDMI
  Export.image.toDrive({
    image: ndmiImage,
    description: 'Nigeria_NDMI_Sentinel2_' + year,
    folder: 'GEE_Nigeria_Indices',
    fileNamePrefix: 'Nigeria_NDMI_S2_' + year + '_median',
    scale: 10,
    crs: 'EPSG:4326',
    region: nigeria.geometry(),
    maxPixels: 1e13,
    fileFormat: 'GeoTIFF'
  });
  
  // Export NDWI
  Export.image.toDrive({
    image: ndwiImage,
    description: 'Nigeria_NDWI_Sentinel2_' + year,
    folder: 'GEE_Nigeria_Indices',
    fileNamePrefix: 'Nigeria_NDWI_S2_' + year + '_median',
    scale: 10,
    crs: 'EPSG:4326',
    region: nigeria.geometry(),
    maxPixels: 1e13,
    fileFormat: 'GeoTIFF'
  });
  
  // Print statistics
  var ndmiStats = ndmiImage.reduceRegion({
    reducer: ee.Reducer.mean()
      .combine(ee.Reducer.stdDev(), '', true)
      .combine(ee.Reducer.minMax(), '', true),
    geometry: nigeria.geometry(),
    scale: 1000,
    maxPixels: 1e10
  });
  
  var ndwiStats = ndwiImage.reduceRegion({
    reducer: ee.Reducer.mean()
      .combine(ee.Reducer.stdDev(), '', true)
      .combine(ee.Reducer.minMax(), '', true),
    geometry: nigeria.geometry(),
    scale: 1000,
    maxPixels: 1e10
  });
  
  print('NDMI Statistics for ' + year + ':', ndmiStats);
  print('NDWI Statistics for ' + year + ':', ndwiStats);
});

// Center map on Nigeria
Map.centerObject(nigeria, 6);

// Optional: Export monthly composites for a specific year
function exportMonthlyComposites(year) {
  var months = ee.List.sequence(1, 12);
  
  months.evaluate(function(monthsList) {
    monthsList.forEach(function(month) {
      var startDate = ee.Date.fromYMD(year, month, 1);
      var endDate = startDate.advance(1, 'month');
      
      var monthlyCollection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(nigeria)
        .filterDate(startDate, endDate)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
        .map(maskS2clouds)
        .map(addIndices);
      
      var monthlyMedian = monthlyCollection.select(['NDMI', 'NDWI']).median();
      
      var ndmiMonthly = monthlyMedian.select('NDMI').clip(nigeria);
      var ndwiMonthly = monthlyMedian.select('NDWI').clip(nigeria);
      
      var monthStr = month < 10 ? '0' + month : '' + month;
      
      Export.image.toDrive({
        image: ndmiMonthly,
        description: 'Nigeria_NDMI_S2_' + year + '_month' + monthStr,
        folder: 'GEE_Nigeria_Indices',
        fileNamePrefix: 'Nigeria_NDMI_S2_' + year + '_month' + monthStr,
        scale: 10,
        crs: 'EPSG:4326',
        region: nigeria.geometry(),
        maxPixels: 1e13,
        fileFormat: 'GeoTIFF'
      });
      
      Export.image.toDrive({
        image: ndwiMonthly,
        description: 'Nigeria_NDWI_S2_' + year + '_month' + monthStr,
        folder: 'GEE_Nigeria_Indices',
        fileNamePrefix: 'Nigeria_NDWI_S2_' + year + '_month' + monthStr,
        scale: 10,
        crs: 'EPSG:4326',
        region: nigeria.geometry(),
        maxPixels: 1e13,
        fileFormat: 'GeoTIFF'
      });
    });
  });
}

// Uncomment to export monthly composites for a specific year
// exportMonthlyComposites(2021);