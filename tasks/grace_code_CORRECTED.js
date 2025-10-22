// ========================================================
// CORRECTED VERSION - Mali Urban Analysis
// All issues from original code fixed
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
// USER INPUTS
// ========================================================

// Load agricultural points
var pointsRaw = ee.FeatureCollection("projects/ee-gracebea/assets/agric_points");
var maliPoints = pointsRaw.filter(ee.Filter.eq('CountryName', 'Mali'));  // ✓ FIXED: Changed from nigeriaPoints

// Ensure points have geometry
var points = maliPoints.map(function(f) {
  var lon = ee.Number(f.get('long'));
  var lat = ee.Number(f.get('lat'));
  var geom = ee.Geometry.Point([lon, lat]);
  return ee.Feature(geom).copyProperties(f).set({'lat': lat, 'long': lon});
});

print('Mali points loaded:', points.size());

// ========================================================
// LOAD ASSETS
// ========================================================

// ✓ FIXED: Changed from Nigeria to Mali rasters
// IMPORTANT: Verify these asset paths exist in your GEE account
var ghsl = ee.Image("projects/ee-gracebea/assets/Mali_GHSL_2018").select([0]).rename('ghsl');
var dbi  = ee.Image("projects/ee-gracebea/assets/Mali_DBI_2018").select([0]).rename('dbi');

// Aridity classification (global, so no change needed)
var KOPPEN_ASSET = "projects/ee-gracebea/assets/koppen_geiger_0p00833333";
var KOPPEN_ARID_VALUES = [4,5,6,7];
var koppen = ee.Image(KOPPEN_ASSET);
var aridMask = koppen.remap(
  KOPPEN_ARID_VALUES,
  ee.List.repeat(1, KOPPEN_ARID_VALUES.length),
  0
).rename('arid_flag');

// ========================================================
// MODIS URBAN FUNCTION WITH 2 KM BUFFER
// ========================================================
function getModisUrbanPercent(pt, year) {
  var geom = pt.geometry().buffer(2000); // 2 km buffer

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

  // Urban pixels (class 13)
  var urban = modisImage.eq(13);

  // Reduce over the buffer to get mean urban fraction
  var meanUrbanDict = urban.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: geom,
    scale: 500,      // MODIS native resolution
    maxPixels: 1e9
  });

  // Convert to percentage
  return safeGetNumber(meanUrbanDict, 'LC_Type1').multiply(100);
}

// ========================================================
// FUNCTION TO CALCULATE ALL VALUES
// ========================================================
function calculateAllUrban(pt) {
  var geom = pt.geometry();

  // MODIS urban % within 2 km
  var modisValue = getModisUrbanPercent(pt, 2018);

  // Arid flag at point location
  var aridDict = aridMask.reduceRegion({
    reducer: ee.Reducer.first(),
    geometry: geom,
    scale: 500,
    maxPixels: 1e9
  });
  var aridValue = safeGetNumber(aridDict, 'arid_flag');

  // GHSL within 2 km buffer
  // ✓ FIXED: Changed scale from 1000 to 30
  var ghslDict = ghsl.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: geom.buffer(2000),
    scale: 30,  // ✓ FIXED: Was 1000, now 30
    maxPixels: 1e9
  });
  // ✓ FIXED: Added multiply(100)
  var ghslValue = safeGetNumber(ghslDict, 'ghsl').multiply(100);

  // DBI within 2 km buffer
  var dbiDict = dbi.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: geom.buffer(2000),
    scale: 30,
    maxPixels: 1e9
  });
  var dbiValue = safeGetNumber(dbiDict, 'dbi').multiply(100);  // ✓ Already correct

  return pt.set({
    'modis_urban_percent': modisValue,
    'arid_flag': aridValue,
    'GHSL_pct': ghslValue,
    'DBI_pct': dbiValue
  });
}

// ========================================================
// APPLY TO ALL POINTS
// ========================================================
var pointsWithAll = points.map(calculateAllUrban);

// Print first few points to check
print("Mali points with all urban & arid values:", pointsWithAll.limit(10));

// ========================================================
// VALIDATION CHECKS
// ========================================================
print('');
print('===== VALIDATION CHECKS =====');

// Sample a few points to verify values
var sampleStats = pointsWithAll.limit(5).aggregate_array('modis_urban_percent');
print('Sample MODIS values:', sampleStats);

// Check for suspicious patterns
var ghslStats = pointsWithAll.limit(100).aggregate_stats('GHSL_pct');
print('GHSL statistics (first 100 points):', ghslStats);
print('  - If max is capped at 30%, Mali raster is wrong');
print('  - If max > 30%, raster is correct');

// ========================================================
// EXPORT TO DRIVE
// ========================================================
Export.table.toDrive({
  collection: pointsWithAll,
  description: 'Mali_points_CORRECTED',
  fileFormat: 'CSV'
});

// ========================================================
// VISUALIZATION
// ========================================================
Map.addLayer(ghsl, {min:0, max:1, palette:['white','red']}, 'GHSL (Mali)');
Map.addLayer(dbi, {min:0, max:1, palette:['white','blue']}, 'DBI (Mali)');
Map.addLayer(points, {color:'yellow'}, 'Mali Points');
Map.centerObject(points, 6);

// ========================================================
// SUMMARY OF FIXES
// ========================================================
print('');
print('===== FIXES APPLIED =====');
print('1. ✓ Changed GHSL from Nigeria to Mali raster');
print('2. ✓ Changed DBI from Nigeria to Mali raster');
print('3. ✓ Changed GHSL scale from 1000m to 30m');
print('4. ✓ Added multiply(100) to GHSL');
print('5. ✓ Fixed variable name from nigeriaPoints to maliPoints');
print('');
print('Compare old results (Mali_points_modis_buffer.csv) with new export');
print('Expected changes in urban Bamako:');
print('  MODIS: ~85% (should stay same)');
print('  GHSL: Old=30% (capped) → New=60-80% (if Mali raster correct)');
print('  DBI:  Old=35% → New=should align better with GHSL');
