/**
 * Multi-Method Urban Percentage Calculation for Nigerian Wards
 * 
 * This script implements three different urbanicity measurement methods:
 * 1. NDBI (Normalized Difference Built-up Index) using Sentinel-2
 * 2. Africapolis methodology (10K population + built-up continuity)
 * 3. GHSL Degree of Urbanization classification
 * 
 * Author: Bernard Ofori Boateng
 * Date: November 2024
 * Purpose: Validate ward urbanicity classification using multiple independent methods
 */

// ========================================
// CONFIGURATION
// ========================================

// Define the study area - adjust these coordinates for your specific state
var nigeria = ee.Geometry.Rectangle([2.668, 4.272, 14.680, 13.892]); // Nigeria bounding box

// Time period for analysis
var startDate = '2023-01-01';
var endDate = '2023-12-31';

// Cloud cover threshold
var cloudThreshold = 30;

// ========================================
// HELPER FUNCTIONS
// ========================================

/**
 * Mask clouds from Sentinel-2 imagery
 */
function maskS2clouds(image) {
  var qa = image.select('QA60');
  var cloudBitMask = 1 << 10;
  var cirrusBitMask = 1 << 11;
  var mask = qa.bitwiseAnd(cloudBitMask).eq(0)
      .and(qa.bitwiseAnd(cirrusBitMask).eq(0));
  return image.updateMask(mask).divide(10000);
}

/**
 * Calculate urban percentage for a given binary mask within wards
 */
function calculateUrbanPercentage(urbanMask, wards, methodName) {
  // Calculate pixel area in square meters
  var pixelArea = ee.Image.pixelArea();
  
  // Calculate urban area
  var urbanArea = urbanMask.multiply(pixelArea).rename('urban_area');
  
  // Calculate total area
  var totalArea = pixelArea.rename('total_area');
  
  // Reduce by wards
  var stats = urbanArea.addBands(totalArea).reduceRegions({
    collection: wards,
    reducer: ee.Reducer.sum(),
    scale: 10,
    crs: 'EPSG:4326'
  });
  
  // Calculate percentage
  var urbanPercentage = stats.map(function(feature) {
    var urbanAreaSum = ee.Number(feature.get('urban_area'));
    var totalAreaSum = ee.Number(feature.get('total_area'));
    var percentage = urbanAreaSum.divide(totalAreaSum).multiply(100);
    return feature.set(methodName + '_urban_percent', percentage);
  });
  
  return urbanPercentage;
}

// ========================================
// METHOD 1: NDBI (Normalized Difference Built-up Index)
// ========================================

function calculateNDBI() {
  print('Calculating NDBI...');
  
  // Load Sentinel-2 data
  var sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(nigeria)
    .filterDate(startDate, endDate)
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloudThreshold))
    .map(maskS2clouds);
  
  // Get median composite
  var composite = sentinel2.median();
  
  // Calculate NDBI = (SWIR - NIR) / (SWIR + NIR)
  // For Sentinel-2: SWIR = B11, NIR = B8
  var ndbi = composite.normalizedDifference(['B11', 'B8']).rename('NDBI');
  
  // Threshold NDBI to create urban mask (NDBI > 0 = urban)
  var urbanMask = ndbi.gt(0);
  
  // Visualization parameters
  var ndbiVis = {
    min: -1,
    max: 1,
    palette: ['blue', 'white', 'red']
  };
  
  Map.addLayer(ndbi.clip(nigeria), ndbiVis, 'NDBI');
  Map.addLayer(urbanMask.clip(nigeria), {palette: ['white', 'red']}, 'NDBI Urban Mask', false);
  
  return {
    ndbi: ndbi,
    urbanMask: urbanMask
  };
}

// ========================================
// METHOD 2: Africapolis Methodology
// ========================================

function calculateAfricapolis() {
  print('Calculating Africapolis methodology...');
  
  // Load WorldPop population data for Nigeria (2020)
  var population = ee.Image('WorldPop/GP/100m/pop/NGA_2020')
    .clip(nigeria);
  
  // Load Sentinel-2 for built-up area detection
  var sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(nigeria)
    .filterDate(startDate, endDate)
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloudThreshold))
    .map(maskS2clouds);
  
  var composite = sentinel2.median();
  
  // Calculate built-up area using NDBI as proxy
  var ndbi = composite.normalizedDifference(['B11', 'B8']);
  var builtUp = ndbi.gt(0.1); // Slightly higher threshold for built-up detection
  
  // Apply morphological operations to identify continuous built-up areas
  // Kernel for 200m continuity check (20 pixels at 10m resolution)
  var kernel = ee.Kernel.circle({radius: 10, units: 'pixels'});
  var continuousBuiltUp = builtUp
    .focal_max({kernel: kernel, iterations: 1})
    .focal_min({kernel: kernel, iterations: 1});
  
  // Population density threshold (10,000 per settlement)
  // Convert to density per 100m pixel
  var popDensityThreshold = 0.01; // Adjust based on your needs
  var highPopulation = population.gt(popDensityThreshold);
  
  // Combine criteria: continuous built-up AND sufficient population
  var africapolisUrban = continuousBuiltUp.and(highPopulation);
  
  // Visualization
  Map.addLayer(population.log(), {min: 0, max: 4, palette: ['white', 'yellow', 'red']}, 'Population Density (log)', false);
  Map.addLayer(continuousBuiltUp, {palette: ['white', 'orange']}, 'Continuous Built-up', false);
  Map.addLayer(africapolisUrban, {palette: ['white', 'purple']}, 'Africapolis Urban', false);
  
  return {
    urbanMask: africapolisUrban
  };
}

// ========================================
// METHOD 3: GHSL Degree of Urbanization
// ========================================

function calculateGHSL() {
  print('Calculating GHSL Degree of Urbanization...');
  
  // Load GHSL Degree of Urbanization data
  // Using the most recent available year (2020 or 2025)
  var ghsl = ee.Image('JRC/GHSL/P2023A/GHS_SMOD_V1/2020')
    .select('smod_code')
    .clip(nigeria);
  
  // GHSL Settlement Model codes:
  // 30: Urban centre
  // 23: Dense urban cluster
  // 22: Semi-dense urban cluster
  // 21: Suburban or peri-urban
  // 13: Rural cluster
  // 12: Low density rural
  // 11: Very low density rural
  // 10: Water
  
  // Define urban areas (codes 21-30)
  var urbanMask = ghsl.gte(21).and(ghsl.lte(30));
  
  // For more nuanced analysis, separate by urbanization level
  var urbanCentre = ghsl.eq(30);
  var urbanCluster = ghsl.gte(21).and(ghsl.lte(23));
  var rural = ghsl.gte(11).and(ghsl.lte(13));
  
  // Visualization with appropriate colors
  var ghslVis = {
    min: 10,
    max: 30,
    palette: ['0000FF', '4169E1', '87CEEB', 'FFFFE0', 'FFD700', 'FFA500', 'FF6347', 'FF0000']
  };
  
  Map.addLayer(ghsl, ghslVis, 'GHSL Degree of Urbanization');
  Map.addLayer(urbanMask, {palette: ['white', 'red']}, 'GHSL Urban Mask', false);
  Map.addLayer(urbanCentre, {palette: ['white', 'darkred']}, 'GHSL Urban Centre', false);
  
  return {
    ghsl: ghsl,
    urbanMask: urbanMask,
    urbanCentre: urbanCentre,
    urbanCluster: urbanCluster,
    rural: rural
  };
}

// ========================================
// ALTERNATIVE METHOD: EBBI (Enhanced Built-up and Bareness Index)
// ========================================

function calculateEBBI() {
  print('Calculating EBBI...');
  
  // Load Landsat 8 for thermal band
  var landsat8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
    .filterBounds(nigeria)
    .filterDate(startDate, endDate)
    .filter(ee.Filter.lt('CLOUD_COVER', cloudThreshold));
  
  // Apply scaling factors
  function applyScaleFactors(image) {
    var opticalBands = image.select('SR_B.*').multiply(0.0000275).add(-0.2);
    var thermalBands = image.select('ST_B.*').multiply(0.00341802).add(149.0);
    return image.addBands(opticalBands, null, true)
                .addBands(thermalBands, null, true);
  }
  
  var processedLandsat = landsat8.map(applyScaleFactors);
  var composite = processedLandsat.median();
  
  // EBBI = (NIR - TIR) / (NIR + TIR)
  // For Landsat 8: NIR = B5, TIR = B10
  var nir = composite.select('SR_B5');
  var tir = composite.select('ST_B10');
  
  var ebbi = nir.subtract(tir).divide(nir.add(tir)).rename('EBBI');
  
  // Threshold for urban areas (adjust based on your region)
  var urbanMask = ebbi.gt(0.05);
  
  Map.addLayer(ebbi.clip(nigeria), {min: -0.5, max: 0.5, palette: ['blue', 'white', 'red']}, 'EBBI', false);
  Map.addLayer(urbanMask.clip(nigeria), {palette: ['white', 'brown']}, 'EBBI Urban Mask', false);
  
  return {
    ebbi: ebbi,
    urbanMask: urbanMask
  };
}

// ========================================
// MAIN EXECUTION
// ========================================

function main() {
  // Center the map on Nigeria
  Map.centerObject(nigeria, 6);
  
  // Load ward boundaries (you'll need to import your shapefile)
  // For now, creating a sample ward collection
  // REPLACE THIS WITH YOUR ACTUAL WARD BOUNDARIES
  var wards = ee.FeatureCollection([
    ee.Feature(ee.Geometry.Rectangle([7.0, 11.0, 7.1, 11.1]), {ward_name: 'Sample_Ward_1'}),
    ee.Feature(ee.Geometry.Rectangle([7.1, 11.0, 7.2, 11.1]), {ward_name: 'Sample_Ward_2'}),
    ee.Feature(ee.Geometry.Rectangle([7.0, 11.1, 7.1, 11.2]), {ward_name: 'Sample_Ward_3'})
  ]);
  
  // Calculate urban percentages using each method
  var results = ee.FeatureCollection(wards);
  
  // Method 1: NDBI
  var ndbiResult = calculateNDBI();
  var ndbiUrbanPercent = calculateUrbanPercentage(ndbiResult.urbanMask, wards, 'NDBI');
  
  // Method 2: Africapolis
  var africapolisResult = calculateAfricapolis();
  var africapolisUrbanPercent = calculateUrbanPercentage(africapolisResult.urbanMask, wards, 'Africapolis');
  
  // Method 3: GHSL
  var ghslResult = calculateGHSL();
  var ghslUrbanPercent = calculateUrbanPercentage(ghslResult.urbanMask, wards, 'GHSL');
  
  // Method 4: EBBI (optional)
  var ebbiResult = calculateEBBI();
  var ebbiUrbanPercent = calculateUrbanPercentage(ebbiResult.urbanMask, wards, 'EBBI');
  
  // Combine all results
  var combinedResults = ndbiUrbanPercent
    .map(function(feature) {
      var africapolisFeature = africapolisUrbanPercent
        .filter(ee.Filter.eq('ward_name', feature.get('ward_name')))
        .first();
      var ghslFeature = ghslUrbanPercent
        .filter(ee.Filter.eq('ward_name', feature.get('ward_name')))
        .first();
      var ebbiFeature = ebbiUrbanPercent
        .filter(ee.Filter.eq('ward_name', feature.get('ward_name')))
        .first();
      
      return feature
        .set('Africapolis_urban_percent', africapolisFeature.get('Africapolis_urban_percent'))
        .set('GHSL_urban_percent', ghslFeature.get('GHSL_urban_percent'))
        .set('EBBI_urban_percent', ebbiFeature.get('EBBI_urban_percent'));
    });
  
  // Print results
  print('Combined Urban Percentage Results:', combinedResults);
  
  // Export results to Drive
  Export.table.toDrive({
    collection: combinedResults,
    description: 'Urban_Percentage_Multi_Methods',
    fileFormat: 'CSV'
  });
  
  // Export rasters for each method
  Export.image.toDrive({
    image: ndbiResult.ndbi,
    description: 'NDBI_Raster',
    scale: 10,
    region: nigeria,
    maxPixels: 1e13
  });
  
  Export.image.toDrive({
    image: ghslResult.ghsl,
    description: 'GHSL_Raster',
    scale: 1000,
    region: nigeria,
    maxPixels: 1e13
  });
  
  // Add ward boundaries to map
  Map.addLayer(wards, {color: 'black'}, 'Ward Boundaries');
}

// Run the main function
main();