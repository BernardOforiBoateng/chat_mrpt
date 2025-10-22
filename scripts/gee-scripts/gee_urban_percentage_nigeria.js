// =====================================================
// Urban Percentage Download for Nigeria
// For ITN Distribution Planning in ChatMRPT
// =====================================================
// This script calculates urban percentage using multiple methods:
// 1. NASA HLS (Harmonized Landsat Sentinel-2) - Built-up index
// 2. VIIRS Night Lights - Urban proxy from luminosity
// 3. MODIS Urban Land Cover - Direct urban classification
// 4. Composite Urban Index - Combined metric
//
// Output: Annual urban percentage rasters (2020-2024)
// Resolution: 1km for computational efficiency
// =====================================================

// Define Nigeria boundary
var nigeria = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017')
  .filter(ee.Filter.eq('country_na', 'Nigeria'));

// Set visualization
Map.centerObject(nigeria, 6);

// =====================================================
// METHOD 1: NASA HLS (Harmonized Landsat Sentinel-2)
// Calculate Built-up Index using spectral indices
// =====================================================

function calculateHLSUrbanPercentage(year) {
  var startDate = ee.Date.fromYMD(year, 1, 1);
  var endDate = ee.Date.fromYMD(year, 12, 31);
  
  // Use NASA HLS dataset - consistent with your other environmental variables
  var hls = ee.ImageCollection('NASA/HLS/HLSL30/v002')
    .filterBounds(nigeria)
    .filterDate(startDate, endDate)
    .filter(ee.Filter.lt('CLOUD_COVERAGE', 20));
  
  // Function to calculate urban indices
  function calculateUrbanIndices(image) {
    // Calculate NDBI (Normalized Difference Built-up Index)
    // NDBI = (SWIR - NIR) / (SWIR + NIR)
    // Higher NDBI indicates built-up areas
    var ndbi = image.normalizedDifference(['B6', 'B5']).rename('NDBI');
    
    // Calculate NDVI (vegetation index - inverse of urban)
    var ndvi = image.normalizedDifference(['B5', 'B4']).rename('NDVI');
    
    // Calculate BUI (Built-up Index)
    // BUI = NDBI - NDVI
    var bui = ndbi.subtract(ndvi).rename('BUI');
    
    // Calculate UI (Urban Index) 
    // UI = (SWIR2 - NIR) / (SWIR2 + NIR)
    var ui = image.normalizedDifference(['B7', 'B5']).rename('UI');
    
    return image.addBands([ndbi, ndvi, bui, ui]);
  }
  
  // Apply cloud masking and calculate indices
  var processed = hls
    .map(function(image) {
      var qa = image.select('Fmask');
      var mask = qa.eq(0).or(qa.eq(1)); // Clear or water
      return image.updateMask(mask);
    })
    .map(calculateUrbanIndices);
  
  // Get annual composite
  var composite = processed.select(['NDBI', 'BUI', 'UI']).median();
  
  // Convert BUI to urban percentage
  // BUI ranges from -1 to 1, where positive values indicate built-up
  var urbanPercent = composite.select('BUI')
    .add(1).divide(2).multiply(100) // Scale to 0-100%
    .where(composite.select('BUI').lt(-0.2), 0) // Rural threshold
    .where(composite.select('BUI').gt(0.3), 90)  // Urban core threshold
    .clip(nigeria)
    .rename('hls_urban_percent_' + year);
  
  return urbanPercent;
}

// =====================================================
// METHOD 2: VIIRS Night Lights as Urban Proxy
// Higher light intensity = more urbanized
// =====================================================

function calculateNightLightsUrbanProxy(year) {
  var startDate = ee.Date.fromYMD(year, 1, 1);
  var endDate = ee.Date.fromYMD(year, 12, 31);
  
  // Use VIIRS Stray Light Corrected Nighttime Day/Night Band Composites
  var viirs = ee.ImageCollection('NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG')
    .filterDate(startDate, endDate)
    .select('avg_rad')
    .median()
    .clip(nigeria);
  
  // Normalize night lights to 0-100 scale
  // Urban threshold calibration based on Nigerian cities:
  // Rural: 0-1 nW/cm²/sr
  // Peri-urban: 1-10 nW/cm²/sr  
  // Urban: 10-50 nW/cm²/sr
  // Highly urban: >50 nW/cm²/sr
  
  var urbanPercent = viirs
    .where(viirs.lt(1), 0)           // Rural
    .where(viirs.gte(1).and(viirs.lt(5)), 20)   // Low density urban
    .where(viirs.gte(5).and(viirs.lt(10)), 40)  // Medium density
    .where(viirs.gte(10).and(viirs.lt(25)), 60) // Urban
    .where(viirs.gte(25).and(viirs.lt(50)), 80) // Highly urban
    .where(viirs.gte(50), 95)        // Urban core
    .rename('nightlights_urban_percent_' + year);
  
  return urbanPercent;
}

// =====================================================
// METHOD 3: MODIS Land Cover Urban Classification
// Direct urban/built-up classification
// =====================================================

function calculateMODISUrbanPercentage(year) {
  var startDate = ee.Date.fromYMD(year, 1, 1);
  
  // Use MODIS Land Cover Type
  var modis = ee.ImageCollection('MODIS/006/MCD12Q1')
    .filterDate(startDate, startDate.advance(1, 'year'))
    .first()
    .select('LC_Type1')  // IGBP classification
    .clip(nigeria);
  
  // Class 13 = Urban and Built-up Lands
  var urban = modis.eq(13);
  
  // Calculate urban percentage within 1km pixels
  // Use focal mean to get percentage in neighborhood
  var kernel = ee.Kernel.circle({radius: 500, units: 'meters'});
  var urbanPercent = urban
    .reduceNeighborhood({
      reducer: ee.Reducer.mean(),
      kernel: kernel
    })
    .multiply(100)
    .rename('modis_urban_percent_' + year);
  
  return urbanPercent;
}

// =====================================================
// METHOD 4: Dynamic World Urban Classification
// Google's near real-time land cover (2020+)
// =====================================================

function calculateDynamicWorldUrban(year) {
  // Dynamic World is available from June 2015 onwards
  if (year < 2020) {
    print('Dynamic World not recommended before 2020');
    return null;
  }
  
  var startDate = ee.Date.fromYMD(year, 1, 1);
  var endDate = ee.Date.fromYMD(year, 12, 31);
  
  var dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')
    .filterDate(startDate, endDate)
    .filterBounds(nigeria)
    .select('built')  // Built area probability
    .median()
    .clip(nigeria);
  
  // Scale to percentage (0-100)
  var urbanPercent = dw.multiply(100)
    .rename('dynamicworld_urban_percent_' + year);
  
  return urbanPercent;
}

// =====================================================
// COMPOSITE URBAN INDEX
// Combines multiple data sources for robust estimate
// =====================================================

function calculateCompositeUrbanIndex(year) {
  var components = [];
  var weights = [];
  
  // Add NASA HLS (primary method - consistent with other variables)
  var hls = calculateHLSUrbanPercentage(year);
  if (hls) {
    components.push(hls);
    weights.push(0.4);  // 40% weight - primary source
  }
  
  // Add Night Lights (good urban proxy)
  var nightlights = calculateNightLightsUrbanProxy(year);
  if (nightlights) {
    components.push(nightlights);
    weights.push(0.3);  // 30% weight
  }
  
  // Add MODIS (land cover classification)
  var modis = calculateMODISUrbanPercentage(year);
  if (modis) {
    components.push(modis);
    weights.push(0.2);  // 20% weight
  }
  
  // Add Dynamic World for recent years
  if (year >= 2020) {
    var dw = calculateDynamicWorldUrban(year);
    if (dw) {
      components.push(dw);
      weights.push(0.1);  // 10% weight for newest data
    }
  }
  
  // Calculate weighted average
  if (components.length > 0) {
    var composite = ee.Image(0);
    for (var i = 0; i < components.length; i++) {
      composite = composite.add(components[i].multiply(weights[i]));
    }
    
    // Normalize weights if not using all sources
    var totalWeight = weights.reduce(function(a, b) { return a + b; }, 0);
    composite = composite.divide(totalWeight);
    
    return composite.rename('composite_urban_percent_' + year);
  }
  
  return null;
}

// =====================================================
// EXPORT FUNCTIONS
// =====================================================

function exportUrbanPercentage(image, year, method) {
  // Resample to 1km resolution for consistency with other variables
  var resampled = image
    .reproject({
      crs: 'EPSG:4326',
      scale: 1000  // 1km resolution
    });
  
  Export.image.toDrive({
    image: resampled,
    description: 'Nigeria_Urban_' + method + '_' + year,
    folder: 'GEE_Nigeria_Urban',
    fileNamePrefix: 'Nigeria_Urban_' + method + '_' + year,
    scale: 1000,  // 1km
    crs: 'EPSG:4326',
    region: nigeria.geometry(),
    maxPixels: 1e13,
    fileFormat: 'GeoTIFF'
  });
}

// =====================================================
// MAIN PROCESSING - Generate exports for 2020-2024
// =====================================================

var years = [2020, 2021, 2022, 2023, 2024];

// Process each year
years.forEach(function(year) {
  print('Processing year: ' + year);
  
  // 1. Export NASA HLS-based urban percentage (PRIMARY METHOD)
  var hls = calculateHLSUrbanPercentage(year);
  exportUrbanPercentage(hls, year, 'HLS');
  
  // 2. Export Night Lights urban proxy
  var nightlights = calculateNightLightsUrbanProxy(year);
  if (year <= 2023) {  // VIIRS data might not be complete for 2024 yet
    exportUrbanPercentage(nightlights, year, 'NightLights');
  }
  
  // 3. Export MODIS urban classification
  if (year <= 2022) {  // MODIS might lag by 1-2 years
    var modis = calculateMODISUrbanPercentage(year);
    exportUrbanPercentage(modis, year, 'MODIS');
  }
  
  // 4. Export Dynamic World for recent years
  if (year >= 2020) {
    var dw = calculateDynamicWorldUrban(year);
    if (dw) {
      exportUrbanPercentage(dw, year, 'DynamicWorld');
    }
  }
  
  // 5. Export Composite Urban Index (RECOMMENDED)
  var composite = calculateCompositeUrbanIndex(year);
  if (composite) {
    exportUrbanPercentage(composite, year, 'Composite');
    
    // Add to map for visualization (only for 2023 as example)
    if (year === 2023) {
      Map.addLayer(composite, {
        min: 0, 
        max: 100, 
        palette: ['green', 'yellow', 'orange', 'red', 'darkred']
      }, 'Urban Percentage ' + year);
    }
  }
});

// =====================================================
// ADDITIONAL EXPORTS
// =====================================================

// Export static urban extent mask (areas >50% urban)
var urbanMask2023 = calculateCompositeUrbanIndex(2023);
if (urbanMask2023) {
  var urbanAreas = urbanMask2023.gt(50).selfMask();
  Export.image.toDrive({
    image: urbanAreas,
    description: 'Nigeria_Urban_Mask_2023',
    folder: 'GEE_Nigeria_Urban',
    fileNamePrefix: 'Nigeria_Urban_Mask_2023',
    scale: 1000,
    crs: 'EPSG:4326',
    region: nigeria.geometry(),
    maxPixels: 1e13,
    fileFormat: 'GeoTIFF'
  });
}

// =====================================================
// VALIDATION POINTS
// Major Nigerian cities for validation
// =====================================================

var cities = ee.FeatureCollection([
  ee.Feature(ee.Geometry.Point([3.3792, 6.5244]), {name: 'Lagos', expected_urban: 95}),
  ee.Feature(ee.Geometry.Point([7.4898, 9.0579]), {name: 'Abuja', expected_urban: 85}),
  ee.Feature(ee.Geometry.Point([8.5200, 12.0022]), {name: 'Kano', expected_urban: 75}),
  ee.Feature(ee.Geometry.Point([3.9470, 7.3775]), {name: 'Ibadan', expected_urban: 70}),
  ee.Feature(ee.Geometry.Point([5.6145, 6.3350]), {name: 'Port_Harcourt', expected_urban: 80}),
  ee.Feature(ee.Geometry.Point([7.7411, 4.5624]), {name: 'Calabar', expected_urban: 60}),
  ee.Feature(ee.Geometry.Point([5.2476, 7.2527]), {name: 'Rural_Edo', expected_urban: 10})
]);

Map.addLayer(cities, {color: 'blue'}, 'Validation Cities');

// Sample urban values at city points for 2023
var urban2023 = calculateCompositeUrbanIndex(2023);
if (urban2023) {
  var sampled = urban2023.sampleRegions({
    collection: cities,
    scale: 1000,
    geometries: true
  });
  
  print('Urban percentage at validation points (2023):', sampled);
}

// =====================================================
// SUMMARY STATISTICS
// =====================================================

print('===== EXPORT SUMMARY =====');
print('Years: 2020-2024');
print('Methods: GHSL, Night Lights, MODIS, Dynamic World, Composite');
print('Resolution: 1km (1000m)');
print('Region: Nigeria');
print('Total expected exports: ~20 files');
print('Output folder: GEE_Nigeria_Urban');
print('');
print('RECOMMENDED: Use Composite urban percentage for ITN analysis');
print('This combines multiple data sources for robust estimates');
print('');
print('After export completes:');
print('1. Download files from Google Drive');
print('2. Place in app/raster_database/urban/ directory');
print('3. Update unified_dataset_builder.py to include urban percentage');