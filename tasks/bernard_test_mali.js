// ========================================================
// BERNARD'S TEST - Mali Urban Analysis
// Testing Grace's methodology with corrections
// Date: October 8, 2025
// ========================================================

// ========================================================
// SAFE NUMBER GETTER
// ========================================================
function safeGetNumber(dict, key) {
  var val = ee.Dictionary(dict).get(key);
  return ee.Number(ee.Algorithms.If(ee.Algorithms.IsEqual(val, null), 0, val));
}

// ========================================================
// USER INPUTS - LOAD MALI POINTS
// ========================================================

// Load agricultural points from uploaded asset
// GEE auto-imports this as 'table' - use that or the full path
var pointsRaw = table;  // OR: ee.FeatureCollection("projects/epidemiological-intelligence/assets/agric_points")
var maliPoints = pointsRaw.filter(ee.Filter.eq('CountryName', 'Mali'));

// Ensure points have geometry
var points = maliPoints.map(function(f) {
  var lon = ee.Number(f.get('long'));
  var lat = ee.Number(f.get('lat'));
  var geom = ee.Geometry.Point([lon, lat]);
  return ee.Feature(geom).copyProperties(f).set({'lat': lat, 'long': lon});
});

print('Mali points loaded:', points.size());

// ========================================================
// LOAD RASTERS
// ========================================================

// Option 1: Create DBI on the fly from Sentinel-2
// Option 2: Load pre-made rasters (if you have them)

// For GHSL - use global GHSL dataset
var ghsl = ee.Image('JRC/GHSL/P2023A/GHS_SMOD/2020').select('smod_code');
// GHSL SMOD: 21-30 = urban classes
var ghslUrban = ghsl.gte(21).and(ghsl.lte(30)).rename('ghsl');

// For DBI - calculate from Sentinel-2 for Mali
var year = 2018;
var mali = ee.FeatureCollection('FAO/GAUL_SIMPLIFIED_500m/2015/level0')
  .filter(ee.Filter.eq('ADM0_NAME', 'Mali'));
var maliGeom = mali.geometry();

var s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
  .filterDate(year + '-01-01', year + '-12-31')
  .filterBounds(maliGeom)
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20));

print('Sentinel-2 images for Mali 2018:', s2.size());

var composite = s2.median();

// Calculate DBI = NDBI - NDVI
var ndbi = composite.normalizedDifference(['B11', 'B8']).rename('NDBI');
var ndvi = composite.normalizedDifference(['B8', 'B4']).rename('NDVI');
var dbi = ndbi.subtract(ndvi).rename('DBI');
var dbiUrban = dbi.gt(0).rename('dbi');

// For aridity - simplified approach using precipitation
// Arid = < 250mm annual rainfall
var worldclim = ee.Image('WORLDCLIM/V1/BIO');
var annualPrecip = worldclim.select('bio12'); // Annual precipitation
var aridMask = annualPrecip.lt(250).rename('arid_flag'); // < 250mm = arid

// ========================================================
// MODIS URBAN FUNCTION
// ========================================================
function getModisUrbanPercent(pt, year) {
  var geom = pt.geometry().buffer(2000);

  var startDate = ee.Date.fromYMD(year, 1, 1);
  var col = ee.ImageCollection('MODIS/006/MCD12Q1')
    .filterDate(startDate, startDate.advance(1, 'year'));

  var size = col.size();
  var modisImage = ee.Image(
    ee.Algorithms.If(size.gt(0),
      col.first().select('LC_Type1'),
      ee.Image.constant(0).rename('LC_Type1')
    )
  );

  var urban = modisImage.eq(13);

  var meanUrbanDict = urban.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: geom,
    scale: 500,
    maxPixels: 1e9
  });

  return safeGetNumber(meanUrbanDict, 'LC_Type1').multiply(100);
}

// ========================================================
// CALCULATE ALL VALUES
// ========================================================
function calculateAllUrban(pt) {
  var geom = pt.geometry();

  // MODIS
  var modisValue = getModisUrbanPercent(pt, 2018);

  // Arid flag
  var aridDict = aridMask.reduceRegion({
    reducer: ee.Reducer.first(),
    geometry: geom,
    scale: 500,
    maxPixels: 1e9
  });
  var aridValue = safeGetNumber(aridDict, 'arid_flag');

  // GHSL with 2km buffer - CORRECTED VERSION
  var ghslDict = ghslUrban.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: geom.buffer(2000),
    scale: 30,  // ✓ CORRECTED: was 1000
    maxPixels: 1e9
  });
  var ghslValue = safeGetNumber(ghslDict, 'ghsl').multiply(100);  // ✓ CORRECTED: added multiply

  // DBI with 2km buffer
  var dbiDict = dbiUrban.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: geom.buffer(2000),
    scale: 30,
    maxPixels: 1e9
  });
  var dbiValue = safeGetNumber(dbiDict, 'dbi').multiply(100);

  return pt.set({
    'modis_urban_percent': modisValue,
    'arid_flag': aridValue,
    'GHSL_pct': ghslValue,
    'DBI_pct': dbiValue
  });
}

// ========================================================
// RUN CALCULATION
// ========================================================
var pointsWithAll = points.map(calculateAllUrban);

print('');
print('===== RESULTS =====');
print(pointsWithAll);

// ========================================================
// EXPORT
// ========================================================
Export.table.toDrive({
  collection: pointsWithAll,
  description: 'Bernard_Mali_Test',
  fileFormat: 'CSV'
});

// ========================================================
// VISUALIZATION
// ========================================================
Map.addLayer(ghslUrban, {palette: ['white', 'red']}, 'GHSL Urban');
Map.addLayer(dbiUrban, {palette: ['white', 'blue']}, 'DBI Urban');
Map.addLayer(points, {color: 'yellow'}, 'Test Points');
Map.centerObject(mali, 6);

// ========================================================
// WHAT TO CHECK
// ========================================================
print('');
print('===== EXPECTED RESULTS =====');
print('For Bamako urban points (12.6N, -8.0W):');
print('  MODIS: 70-90% (should be high)');
print('  GHSL: 60-80% (should be high, NOT capped at 30%)');
print('  DBI: Compare to GHSL - should be similar');
print('  Arid: 0 (not arid)');
print('');
print('For arid northern points (16N, 0E):');
print('  MODIS: 0-10% (low, desert)');
print('  GHSL: 0-10% (low)');
print('  DBI: Compare to GHSL');
print('  Arid: 1 (arid)');
print('');
print('Check Tasks tab to export results');
