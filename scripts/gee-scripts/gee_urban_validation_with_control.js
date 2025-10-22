// =====================================================
// URBAN PERCENTAGE VALIDATION SCRIPT WITH CONTROL METHOD
// =====================================================
// Purpose: Validate urban percentage calculations using multiple methods
// Author: ChatMRPT Team
// Date: November 2024
// Project: epidemiological-intelligence
//
// TO SAVE THIS SCRIPT IN GEE:
// 1. Click "Save" button in GEE Code Editor
// 2. Choose repository: "epidemiological-intelligence" (or create new)
// 3. Script name: "urban_validation_control_methods"
// 4. Path: scripts/urban_validation/urban_validation_control_methods
// 5. Description: "Validates urban percentage using NDBI, Africapolis, GHSL, EBBI vs control"
// 
// TO ACCESS LATER:
// - Go to Scripts tab → epidemiological-intelligence → urban_validation
// - Or direct link will be: https://code.earthengine.google.com/?scriptPath=users/[your-username]/epidemiological-intelligence:urban_validation/urban_validation_control_methods
//
// REQUIREMENTS:
// - Access to: projects/ee-epidemiological-intelligence/assets/NGA_wards
// - Or backup: projects/ee-hephzibahadeniji/assets/NGA_wards
// =====================================================

// Define study area (Nigeria or specific state)
var nigeria = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017')
  .filter(ee.Filter.eq('country_na', 'Nigeria'));

// For Delta State specifically (adjust coordinates as needed)
var deltaState = ee.Geometry.Rectangle([5.05, 4.95, 6.7, 6.4]);

// Choose study area
var studyArea = nigeria; // Change to deltaState if needed

// Time period for analysis
var startDate = '2023-01-01';
var endDate = '2023-12-31';

Map.centerObject(studyArea, 6);

// =====================================================
// CONTROL METHOD: NASA HLS NDBI (Current Implementation)
// This is what we currently use in the system
// =====================================================

function calculateControlMethod() {
  print('=== CONTROL METHOD: NASA HLS NDBI ===');
  
  // Use NASA HLS dataset - current primary method
  var hls = ee.ImageCollection('NASA/HLS/HLSL30/v002')
    .filterBounds(studyArea)
    .filterDate(startDate, endDate)
    .filter(ee.Filter.lt('CLOUD_COVERAGE', 20));
  
  // Calculate NDBI (current method)
  var hlsComposite = hls.map(function(image) {
    var qa = image.select('Fmask');
    var mask = qa.eq(0).or(qa.eq(1)); // Clear or water
    
    // NDBI = (SWIR - NIR) / (SWIR + NIR)
    var ndbi = image.normalizedDifference(['B6', 'B5']).rename('NDBI');
    
    // Calculate NDVI for BUI
    var ndvi = image.normalizedDifference(['B5', 'B4']).rename('NDVI');
    
    // BUI = NDBI - NDVI (Built-up Index)
    var bui = ndbi.subtract(ndvi).rename('BUI');
    
    return bui.updateMask(mask);
  }).median();
  
  // Convert to percentage (matching current implementation)
  var controlUrban = hlsComposite
    .add(1).divide(2).multiply(100)
    .where(hlsComposite.lt(-0.2), 0)  // Rural threshold
    .where(hlsComposite.gt(0.3), 90)  // Urban core threshold
    .clip(studyArea)
    .rename('control_hls_ndbi');
  
  // Also add MODIS IGBP as secondary control
  var modis = ee.ImageCollection('MODIS/006/MCD12Q1')
    .filterDate(startDate, endDate)
    .first()
    .select('LC_Type1')  // IGBP classification
    .clip(studyArea);
  
  // Class 13 = Urban and Built-up Lands
  var modisUrban = modis.eq(13)
    .reduceNeighborhood({
      reducer: ee.Reducer.mean(),
      kernel: ee.Kernel.circle({radius: 500, units: 'meters'})
    })
    .multiply(100)
    .rename('control_modis_igbp');
  
  // Resample both to consistent 100m resolution
  return {
    hls: controlUrban.reproject({crs: 'EPSG:4326', scale: 100}),
    modis: modisUrban.reproject({crs: 'EPSG:4326', scale: 100})
  };
}

// =====================================================
// METHOD 1: NDBI using Sentinel-2 (Alternative)
// Higher resolution validation of NDBI approach
// =====================================================

function calculateNDBIMethod() {
  print('=== METHOD 1: NDBI (Sentinel-2) ===');
  
  var sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(studyArea)
    .filterDate(startDate, endDate)
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30));
  
  // Cloud masking function
  function maskS2clouds(image) {
    var qa = image.select('QA60');
    var cloudBitMask = 1 << 10;
    var cirrusBitMask = 1 << 11;
    var mask = qa.bitwiseAnd(cloudBitMask).eq(0)
        .and(qa.bitwiseAnd(cirrusBitMask).eq(0));
    return image.updateMask(mask);
  }
  
  var composite = sentinel2
    .map(maskS2clouds)
    .median();
  
  // Calculate NDBI: (SWIR - NIR) / (SWIR + NIR)
  // Sentinel-2: B11 (SWIR) and B8 (NIR)
  var ndbi = composite.normalizedDifference(['B11', 'B8']).rename('NDBI');
  
  // Calculate NDVI for comparison
  var ndvi = composite.normalizedDifference(['B8', 'B4']).rename('NDVI');
  
  // Built-up Index
  var bui = ndbi.subtract(ndvi);
  
  // Convert to urban percentage
  // Threshold based on literature: NDBI > 0 indicates built-up
  var urbanPercent = ndbi
    .where(ndbi.lt(-0.1), 0)      // Vegetation/water
    .where(ndbi.gte(-0.1).and(ndbi.lt(0)), 10)  // Mixed rural
    .where(ndbi.gte(0).and(ndbi.lt(0.1)), 30)   // Peri-urban
    .where(ndbi.gte(0.1).and(ndbi.lt(0.2)), 50) // Urban
    .where(ndbi.gte(0.2).and(ndbi.lt(0.3)), 70) // Dense urban
    .where(ndbi.gte(0.3), 90)      // Urban core
    .clip(studyArea)
    .rename('ndbi_sentinel2');
  
  // Resample to consistent 100m resolution
  return urbanPercent.reproject({
    crs: 'EPSG:4326',
    scale: 100
  });
}

// =====================================================
// METHOD 2: Africapolis Methodology
// Population + Building Continuity
// =====================================================

function calculateAfricapolisMethod() {
  print('=== METHOD 2: Africapolis ===');
  
  // 1. Get built-up areas from Sentinel-2
  var sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(studyArea)
    .filterDate(startDate, endDate)
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
    .median();
  
  // Calculate built-up index
  var builtup = sentinel2.normalizedDifference(['B11', 'B8']);
  
  // Threshold for built-up detection
  var builtMask = builtup.gt(0);
  
  // 2. Apply morphological operations for continuity
  // Buildings must be within 200m of each other
  var kernel = ee.Kernel.circle({radius: 200, units: 'meters'});
  var continuous = builtMask
    .focal_max({kernel: kernel, iterations: 1})
    .focal_min({kernel: kernel, iterations: 1});
  
  // 3. Get population data (WorldPop)
  var population = ee.ImageCollection('WorldPop/GP/100m/pop')
    .filterDate('2020-01-01', '2020-12-31')
    .first()
    .clip(studyArea);
  
  // 4. Calculate population density
  var popDensity = population
    .reduceNeighborhood({
      reducer: ee.Reducer.sum(),
      kernel: ee.Kernel.circle({radius: 1000, units: 'meters'})
    })
    .divide(3.14159); // per km²
  
  // 5. Apply Africapolis criteria
  // Urban: continuous built + >10,000 population in cluster
  var africanUrban = continuous
    .multiply(100)
    .where(popDensity.lt(100), 0)   // <100 people/km² = rural
    .where(popDensity.gte(100).and(popDensity.lt(300)), 20) // Low density
    .where(popDensity.gte(300).and(popDensity.lt(1000)), 50) // Medium
    .where(popDensity.gte(1000).and(popDensity.lt(5000)), 70) // Urban
    .where(popDensity.gte(5000), 90) // High density urban
    .updateMask(continuous)
    .unmask(0)
    .clip(studyArea)
    .rename('africapolis');
  
  // Resample to consistent 100m resolution
  return africanUrban.reproject({
    crs: 'EPSG:4326',
    scale: 100
  });
}

// =====================================================
// METHOD 3: GHSL Degree of Urbanization
// UN-recommended classification system
// =====================================================

function calculateGHSLMethod() {
  print('=== METHOD 3: GHSL Degree of Urbanization ===');
  
  // GHSL Settlement Model (SMOD)
  var ghsl = ee.Image('JRC/GHSL/P2023A/GHS_SMOD/2020')
    .select('smod_code')
    .clip(studyArea);
  
  // GHSL codes:
  // 10: Water
  // 11: Very low density rural
  // 12: Low density rural  
  // 13: Rural cluster
  // 21: Suburban or peri-urban
  // 22: Semi-dense urban cluster
  // 23: Dense urban cluster
  // 30: Urban centre
  
  var ghslUrban = ghsl
    .remap(
      [10, 11, 12, 13, 21, 22, 23, 30],
      [0,  0,  5,  10, 30, 50, 75, 95]
    )
    .rename('ghsl_degree');
  
  // Also get GHSL built-up surface
  var ghslBuilt = ee.Image('JRC/GHSL/P2023A/GHS_BUILT_S/2020')
    .select('built_surface')
    .clip(studyArea);
  
  // Calculate built-up percentage
  var builtPercent = ghslBuilt
    .divide(ghslBuilt.add(1).reduceNeighborhood({
      reducer: ee.Reducer.max(),
      kernel: ee.Kernel.square(1, 'pixels')
    }))
    .multiply(100)
    .rename('ghsl_built_percent');
  
  // Resample both to consistent 100m resolution
  return {
    smod: ghslUrban.reproject({crs: 'EPSG:4326', scale: 100}),
    built: builtPercent.reproject({crs: 'EPSG:4326', scale: 100})
  };
}

// =====================================================
// METHOD 4: EBBI (Enhanced Built-Up and Bareness Index)
// Uses thermal data for better discrimination
// =====================================================

function calculateEBBIMethod() {
  print('=== METHOD 4: EBBI (Bonus) ===');
  
  // Use Landsat 8 for thermal band
  var landsat8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
    .filterBounds(studyArea)
    .filterDate(startDate, endDate)
    .filter(ee.Filter.lt('CLOUD_COVER', 30));
  
  // Function to calculate EBBI
  function calculateEBBI(image) {
    // Scale and mask
    var opticalBands = image.select('SR_B.*').multiply(0.0000275).add(-0.2);
    var thermalBand = image.select('ST_B10').multiply(0.00341802).add(149.0)
      .subtract(273.15); // Convert to Celsius
    
    // NIR
    var nir = opticalBands.select('SR_B5');
    
    // SWIR
    var swir = opticalBands.select('SR_B6');
    
    // Thermal
    var tir = thermalBand;
    
    // EBBI = (SWIR - NIR) / (10 * sqrt(SWIR + TIR))
    var ebbi = swir.subtract(nir)
      .divide(swir.add(tir).sqrt().multiply(10))
      .rename('EBBI');
    
    return ebbi;
  }
  
  var ebbiComposite = landsat8
    .map(calculateEBBI)
    .median();
  
  // Convert to urban percentage
  var ebbiUrban = ebbiComposite
    .add(0.5).multiply(100) // Scale to 0-100
    .clamp(0, 100)
    .clip(studyArea)
    .rename('ebbi');
  
  // Resample to consistent 100m resolution
  return ebbiUrban.reproject({
    crs: 'EPSG:4326',
    scale: 100
  });
}

// =====================================================
// COMBINE ALL METHODS FOR COMPARISON
// =====================================================

print('Processing all methods...');

// Get control method
var control = calculateControlMethod();
if (control.hls) {
  Map.addLayer(control.hls, {min: 0, max: 100, palette: ['green', 'yellow', 'red']}, 
    'CONTROL: HLS NDBI', false);
} else {
  print('Warning: HLS NDBI control method returned null');
}
if (control.modis) {
  Map.addLayer(control.modis, {min: 0, max: 100, palette: ['green', 'yellow', 'red']}, 
    'CONTROL: MODIS IGBP', false);
}

// Method 1: NDBI Sentinel-2
var ndbiMethod = calculateNDBIMethod();
if (ndbiMethod) {
  Map.addLayer(ndbiMethod, {min: 0, max: 100, palette: ['green', 'yellow', 'orange', 'red']}, 
    'Method 1: NDBI Sentinel-2', false);
} else {
  print('Warning: NDBI Sentinel-2 method returned null');
}

// Method 2: Africapolis
var africapolisMethod = calculateAfricapolisMethod();
if (africapolisMethod) {
  Map.addLayer(africapolisMethod, {min: 0, max: 100, palette: ['green', 'yellow', 'orange', 'red']}, 
    'Method 2: Africapolis', false);
} else {
  print('Warning: Africapolis method returned null');
}

// Method 3: GHSL
var ghslMethod = calculateGHSLMethod();
if (ghslMethod.smod) {
  Map.addLayer(ghslMethod.smod, {min: 0, max: 100, palette: ['green', 'yellow', 'orange', 'red']}, 
    'Method 3: GHSL SMOD', false);
}
if (ghslMethod.built) {
  Map.addLayer(ghslMethod.built, {min: 0, max: 100, palette: ['green', 'yellow', 'orange', 'red']}, 
    'Method 3: GHSL Built', false);
}

// Method 4: EBBI
var ebbiMethod = calculateEBBIMethod();
if (ebbiMethod) {
  Map.addLayer(ebbiMethod, {min: 0, max: 100, palette: ['green', 'yellow', 'orange', 'red']}, 
    'Method 4: EBBI', false);
} else {
  print('Warning: EBBI method returned null');
}

// =====================================================
// VALIDATION: Sample at ward boundaries
// =====================================================

// Use the imported ward boundaries (imported as 'table' at the top)
var wards = table;  // This uses your imported shapefile

// Verify we're using the imported data
print('Using imported ward boundaries from:', 'projects/epidemiological-intelligence/assets/NGA_wards_complete');

// Optional: Filter for specific states if needed
// For Delta State only (using StateName field from your shapefile):
// var wards = table.filter(ee.Filter.eq('StateName', 'Delta'));
// Or use state code:
// var wards = table.filter(ee.Filter.eq('StateCode', 'DE'));

// Print ward count for verification
print('Total wards loaded:', wards.size());
print('Sample ward properties:', wards.first());

// Stack all urban percentage layers (only include non-null images)
var imagesToStack = [];

// Add each method if it exists
if (control && control.hls) imagesToStack.push(control.hls);
if (control && control.modis) imagesToStack.push(control.modis);
if (ndbiMethod) imagesToStack.push(ndbiMethod);
if (africapolisMethod) imagesToStack.push(africapolisMethod);
if (ghslMethod && ghslMethod.smod) imagesToStack.push(ghslMethod.smod);
if (ghslMethod && ghslMethod.built) imagesToStack.push(ghslMethod.built);
if (ebbiMethod) imagesToStack.push(ebbiMethod);

// Check if we have any valid images
if (imagesToStack.length === 0) {
  print('ERROR: No valid urban percentage images were generated');
  print('Please check data availability for the study area and time period');
} else {
  print('Successfully stacked ' + imagesToStack.length + ' urban percentage layers');
}

// Create the stack (will be empty if no valid images)
var urbanStack = imagesToStack.length > 0 ? ee.Image.cat(imagesToStack) : null;

// Only proceed with analysis if we have valid images
if (urbanStack !== null) {
  // Calculate mean urban percentage for each ward
  var wardStats = urbanStack.reduceRegions({
    collection: wards,
    reducer: ee.Reducer.mean(),
    scale: 100, // 100m resolution for accuracy
    crs: 'EPSG:4326'
  });

  // Export results to Cloud Storage bucket
  // Create bucket: urban-validation-nigeria or urbanmalaria-validation
  Export.table.toCloudStorage({
    collection: wardStats,
    description: 'Urban_Validation_Comparison',
    bucket: 'urban-validation-nigeria',  // Create this bucket in Google Cloud Console
    fileNamePrefix: 'ward_comparison/urban_validation_all_methods',
    fileFormat: 'CSV'
  });
  
  print('Export 1 ready: Urban_Validation_Comparison');
} else {
  print('ERROR: Cannot export ward statistics - no valid urban images');
}

// Alternative: Export to Google Drive (if bucket access issues)
// Export.table.toDrive({
//   collection: wardStats,
//   description: 'Urban_Validation_Comparison_Drive',
//   folder: 'GEE_Urban_Validation',
//   fileNamePrefix: 'urban_validation_all_methods',
//   fileFormat: 'CSV'
// });

// =====================================================
// STATISTICAL COMPARISON
// =====================================================

// Only create correlation analysis if we have valid images
if (urbanStack !== null) {
  // Create comparison points for correlation analysis
  var gridPoints = ee.FeatureCollection.randomPoints({
    region: studyArea,
    points: 1000,
    seed: 42
  });

  // Sample all methods at these points
  var sampledPoints = urbanStack.sampleRegions({
    collection: gridPoints,
    scale: 100,
    geometries: false
  });

  // Export for statistical analysis to Cloud Storage
  Export.table.toCloudStorage({
    collection: sampledPoints,
    description: 'Urban_Methods_Correlation',
    bucket: 'urban-validation-nigeria',  // Same dedicated bucket
    fileNamePrefix: 'correlation_analysis/methods_correlation_points',
    fileFormat: 'CSV'
  });
  
  print('Export 2 ready: Urban_Methods_Correlation');
} else {
  print('ERROR: Cannot export correlation points - no valid urban images');
}

// Alternative: Export to Google Drive (if bucket access issues)
// Export.table.toDrive({
//   collection: sampledPoints,
//   description: 'Urban_Methods_Correlation_Drive',
//   folder: 'GEE_Urban_Validation',
//   fileNamePrefix: 'methods_correlation_points',
//   fileFormat: 'CSV'
// });

// =====================================================
// VISUALIZATION: Difference Maps
// =====================================================

// Compare new methods against control (only if both exist)
if (control && control.hls && ndbiMethod) {
  var ndbiDiff = ndbiMethod.subtract(control.hls).rename('diff_ndbi_vs_control');
  Map.addLayer(ndbiDiff, {min: -50, max: 50, palette: ['blue', 'white', 'red']}, 
    'Difference: NDBI vs Control', false);
}

if (control && control.hls && africapolisMethod) {
  var africaDiff = africapolisMethod.subtract(control.hls).rename('diff_africa_vs_control');
  Map.addLayer(africaDiff, {min: -50, max: 50, palette: ['blue', 'white', 'red']}, 
    'Difference: Africapolis vs Control', false);
}

if (control && control.hls && ghslMethod && ghslMethod.smod) {
  var ghslDiff = ghslMethod.smod.subtract(control.hls).rename('diff_ghsl_vs_control');
  Map.addLayer(ghslDiff, {min: -50, max: 50, palette: ['blue', 'white', 'red']}, 
    'Difference: GHSL vs Control', false);
}

// =====================================================
// EXPORT SUMMARY
// =====================================================

print('===== VALIDATION SUMMARY =====');
print('Control Methods:');
print('1. NASA HLS NDBI (Primary) - Current implementation');
print('2. MODIS IGBP Urban Class - Secondary control');
print('');
print('Alternative Methods:');
print('1. NDBI using Sentinel-2 - Higher resolution validation');
print('2. Africapolis - Population + building continuity');
print('3. GHSL Degree of Urbanization - UN standard');
print('4. EBBI - Thermal-enhanced index');
print('');
print('Exports:');
print('1. Ward-level comparison CSV');
print('2. Statistical correlation points CSV');
print('');
print('Next Steps:');
print('1. Replace sample wards with actual Delta State boundaries');
print('2. Run exports and download CSVs');
print('3. Analyze with Python script for report generation');