// ========================================
// SMARTER APPROACH: Use Convex Hull Around Field Study Points
// This creates a tighter boundary around actual study areas
// ========================================

// ----------------------------------------
// CONFIGURATION
// ----------------------------------------
var BUCKET = 'ndmi_ndwi30m';
var years = [2023, 2024];
var startMonth = 1;  
var endMonth = 12;

// ----------------------------------------
// LOAD FIELD STUDY POINTS AND CREATE CONVEX HULLS
// ----------------------------------------

// First, upload the shapefile to Earth Engine as an asset
var fieldStudyPoints = ee.FeatureCollection("projects/epidemiological-intelligence/assets/kn_ib_long_cs_combined");

// Separate Kano and Ibadan points
var kanoPoints = fieldStudyPoints.filter(ee.Filter.rangeContains('geometry.coordinates', 8.0, 9.0, 0));
var ibadanPoints = fieldStudyPoints.filter(ee.Filter.rangeContains('geometry.coordinates', 3.5, 4.5, 0));

// Create convex hulls (tightest polygon around points)
var kanoHull = kanoPoints.geometry().convexHull();
var ibadanHull = ibadanPoints.geometry().convexHull();

// Add small buffer (500m) to ensure all points are well within bounds
var kanoStudyArea = kanoHull.buffer(500);
var ibadanStudyArea = ibadanHull.buffer(500);

// Alternative: Use dissolve for exact EA coverage
// var kanoEAs = kanoPoints.map(function(f) { return f.buffer(500); });
// var kanoStudyArea = kanoEAs.union();

// Visualize
Map.centerObject(kanoStudyArea, 10);
Map.addLayer(kanoStudyArea, {color: 'blue'}, 'Kano Study Area (Convex Hull)');
Map.addLayer(ibadanStudyArea, {color: 'green'}, 'Ibadan Study Area (Convex Hull)');
Map.addLayer(kanoPoints, {color: 'red'}, 'Kano Field Points', false);
Map.addLayer(ibadanPoints, {color: 'orange'}, 'Ibadan Field Points', false);

// Calculate areas
print('Kano study area:', kanoStudyArea.area().divide(1e6), 'km²');
print('Ibadan study area:', ibadanStudyArea.area().divide(1e6), 'km²');

// ----------------------------------------
// OR USE ACTUAL CITY BOUNDARIES
// ----------------------------------------

// Option 2: Use existing Kano metro wards shapefile you have
// var kanoMetro = ee.FeatureCollection("projects/epidemiological-intelligence/assets/Kano_metro_ward_sixLGAs");
// var kanoStudyArea = kanoMetro.geometry();

// Option 3: Use administrative boundaries from FAO GAUL
// Level 2 = LGA level (more precise than state)
var kanoLGAs = ee.FeatureCollection('FAO/GAUL/2015/level2')
    .filter(ee.Filter.eq('ADM1_NAME', 'Kano'))
    .filter(ee.Filter.inList('ADM2_NAME', [
        'Kano Municipal', 'Fagge', 'Dala', 'Gwale', 'Kumbotso', 'Ungogo', 'Nassarawa', 'Tarauni'
    ])); // Core Kano metro LGAs

var ibadanLGAs = ee.FeatureCollection('FAO/GAUL/2015/level2')
    .filter(ee.Filter.eq('ADM1_NAME', 'Oyo'))
    .filter(ee.Filter.inList('ADM2_NAME', [
        'Ibadan North', 'Ibadan North-East', 'Ibadan North-West', 
        'Ibadan South-East', 'Ibadan South-West'
    ])); // Core Ibadan metro LGAs

// Uncomment to use LGA boundaries instead
// var kanoStudyArea = kanoLGAs.geometry();
// var ibadanStudyArea = ibadanLGAs.geometry();

// ----------------------------------------
// HLS INDICES FUNCTIONS (same as before)
// ----------------------------------------
function calculateIndices(img, sensor) {
  var green = sensor === 'S2' ? img.select('B3') : img.select('B3');
  var nir = sensor === 'S2' ? img.select('B8A') : img.select('B5');
  var swir1 = sensor === 'S2' ? img.select('B11') : img.select('B6');
  
  var ndmi = img.expression('(NIR - SWIR1) / (NIR + SWIR1)', {
    'NIR': nir,
    'SWIR1': swir1
  }).rename('NDMI');
  
  var ndwi = img.expression('(GREEN - NIR) / (GREEN + NIR)', {
    'GREEN': green,
    'NIR': nir
  }).rename('NDWI');
  
  return ndmi.addBands(ndwi);
}

function computeMonthlyIndices(year, month, region) {
  var start = ee.Date.fromYMD(year, month, 1);
  var end = start.advance(1, 'month');
  
  var s2 = ee.ImageCollection('NASA/HLS/HLSS30/v002')
              .filterDate(start, end)
              .filterBounds(region)
              .map(function(img) { return calculateIndices(img, 'S2'); });
  
  var l8 = ee.ImageCollection('NASA/HLS/HLSL30/v002')
              .filterDate(start, end)
              .filterBounds(region)
              .map(function(img) { return calculateIndices(img, 'L8'); });
  
  var merged = s2.merge(l8);
  var count = merged.size();
  
  return ee.Algorithms.If(
    count.gt(0),
    merged.median().clip(region).set('image_count', count),
    ee.Image.constant(0).rename(['NDMI', 'NDWI']).clip(region).set('image_count', 0)
  );
}

// ----------------------------------------
// EXPORTS (same structure as before)
// ----------------------------------------
var exportCount = 0;

years.forEach(function(year) {
  for (var month = startMonth; month <= endMonth; month++) {
    var monthStr = (month < 10) ? '0' + month : '' + month;
    
    // Kano exports
    var kanoMonthly = ee.Image(computeMonthlyIndices(year, month, kanoStudyArea));
    
    Export.image.toCloudStorage({
      image: kanoMonthly.select('NDMI'),
      description: 'NDMI_Kano_' + year + '_' + monthStr,
      bucket: BUCKET,
      fileNamePrefix: 'field_study/NDMI_Kano_' + year + '_' + monthStr,
      region: kanoStudyArea,
      scale: 30,
      maxPixels: 1e13,
      fileFormat: 'GeoTIFF',
      formatOptions: {
        cloudOptimized: true
      }
    });
    
    Export.image.toCloudStorage({
      image: kanoMonthly.select('NDWI'),
      description: 'NDWI_Kano_' + year + '_' + monthStr,
      bucket: BUCKET,
      fileNamePrefix: 'field_study/NDWI_Kano_' + year + '_' + monthStr,
      region: kanoStudyArea,
      scale: 30,
      maxPixels: 1e13,
      fileFormat: 'GeoTIFF',
      formatOptions: {
        cloudOptimized: true
      }
    });
    
    // Ibadan exports
    var ibadanMonthly = ee.Image(computeMonthlyIndices(year, month, ibadanStudyArea));
    
    Export.image.toCloudStorage({
      image: ibadanMonthly.select('NDMI'),
      description: 'NDMI_Ibadan_' + year + '_' + monthStr,
      bucket: BUCKET,
      fileNamePrefix: 'field_study/NDMI_Ibadan_' + year + '_' + monthStr,
      region: ibadanStudyArea,
      scale: 30,
      maxPixels: 1e13,
      fileFormat: 'GeoTIFF',
      formatOptions: {
        cloudOptimized: true
      }
    });
    
    Export.image.toCloudStorage({
      image: ibadanMonthly.select('NDWI'),
      description: 'NDWI_Ibadan_' + year + '_' + monthStr,
      bucket: BUCKET,
      fileNamePrefix: 'field_study/NDWI_Ibadan_' + year + '_' + monthStr,
      region: ibadanStudyArea,
      scale: 30,
      maxPixels: 1e13,
      fileFormat: 'GeoTIFF',
      formatOptions: {
        cloudOptimized: true
      }
    });
    
    exportCount += 4;
  }
});

print('\n' + '='.repeat(60));
print('CONVEX HULL APPROACH');
print('='.repeat(60));
print('This creates the tightest boundary around field study points');
print('Advantages:');
print('  ✓ No unnecessary rural areas');
print('  ✓ Follows actual distribution of study points');
print('  ✓ Smaller files, faster processing');
print('');
print('Choose your boundary method:');
print('  1. Convex Hull (tightest fit around points)');
print('  2. LGA boundaries (administrative units)');
print('  3. Rectangle (simplest but includes extra area)');