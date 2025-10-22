# Modified GEE Code for NDMI and NDWI Export

## Changes from Original:
- Years: 2015, 2018, 2021, 2023, 2024
- Months: 7-12 (July to December) instead of 10-12
- Variables: NDMI and NDWI instead of EVI
- Exports two separate files per month (one for NDMI, one for NDWI)

## Code:

```javascript
// Load Nigeria boundary
var nigeria = ee.FeatureCollection('FAO/GAUL/2015/level0')
                 .filter(ee.Filter.eq('ADM0_NAME', 'Nigeria'));
// Center the map and display boundary
Map.centerObject(nigeria, 6);
Map.addLayer(nigeria, {color: 'blue'}, 'Nigeria boundary');
// Define years and months to process
var years = [2015, 2018, 2021, 2023, 2024];
var startMonth = 7;  // July
var endMonth = 12;   // December
// Function to calculate NDMI and NDWI for an image given its sensor
function calculateIndices(img, sensor) {
  var green = sensor === 'S2' ? img.select('B3') : img.select('B3');
  var nir = sensor === 'S2' ? img.select('B8A') : img.select('B5');
  var swir1 = sensor === 'S2' ? img.select('B11') : img.select('B6');
  
  // NDMI = (NIR - SWIR1) / (NIR + SWIR1)
  var ndmi = img.expression(
    '(NIR - SWIR1) / (NIR + SWIR1)', {
      'NIR': nir,
      'SWIR1': swir1
    }
  ).rename('NDMI');
  
  // NDWI = (Green - NIR) / (Green + NIR)
  var ndwi = img.expression(
    '(GREEN - NIR) / (GREEN + NIR)', {
      'GREEN': green,
      'NIR': nir
    }
  ).rename('NDWI');
  
  return img.addBands([ndmi, ndwi]);
}
// Function to compute mean indices for a given month and year
function computeMonthlyMeanIndices(month, year) {
  var start = ee.Date.fromYMD(year, month, 1);
  var end = start.advance(1, 'month');
  var s2 = ee.ImageCollection('NASA/HLS/HLSS30/v002')
              .filterDate(start, end)
              .filterBounds(nigeria);
  var l8 = ee.ImageCollection('NASA/HLS/HLSL30/v002')
              .filterDate(start, end)
              .filterBounds(nigeria);
  var s2Indices = s2.map(function(img) {
    return calculateIndices(img, 'S2');
  });
  var l8Indices = l8.map(function(img) {
    return calculateIndices(img, 'L8');
  });
  var mergedIndices = s2Indices.merge(l8Indices);
  var hasData = mergedIndices.size().gt(0);
  return ee.Algorithms.If(hasData,
    mergedIndices.select(['NDMI', 'NDWI']).mean()
      .set('month', month)
      .set('system:time_start', start.millis()),
    null
  );
}
// Loop through years and months to schedule exports
years.forEach(function(year) {
  var monthList = ee.List.sequence(startMonth, endMonth);
  monthList.getInfo().forEach(function(month) {
    var monthlyImage = computeMonthlyMeanIndices(month, year);
    // Evaluate to check if image exists
    ee.Algorithms.If(monthlyImage !== null, ee.Image(monthlyImage).getInfo(function(info) {
      if (info !== null) {
        var img = ee.Image(monthlyImage);
        
        // Export NDMI to Google Drive
        Export.image.toDrive({
          image: img.select('NDMI'),
          description: 'NDMI_' + year + '_' + month,
          folder: 'Nigeria_NDMI_NDWI_HLS',
          fileNamePrefix: 'NDMI_' + year + '_' + month,
          region: nigeria.geometry(),
          scale: 30,
          maxPixels: 1e13,
          fileFormat: 'GeoTIFF'
        });
        
        // Export NDWI to Google Drive
        Export.image.toDrive({
          image: img.select('NDWI'),
          description: 'NDWI_' + year + '_' + month,
          folder: 'Nigeria_NDMI_NDWI_HLS',
          fileNamePrefix: 'NDWI_' + year + '_' + month,
          region: nigeria.geometry(),
          scale: 30,
          maxPixels: 1e13,
          fileFormat: 'GeoTIFF'
        });
      }
    }), null);
  });
});
```

## Output Files:
For each year (2015, 2018, 2021, 2023, 2024):
- `NDMI_[year]_7.tif` through `NDMI_[year]_12.tif`
- `NDWI_[year]_7.tif` through `NDWI_[year]_12.tif`

Total: 60 files (5 years × 6 months × 2 indices)

## Storage Location:
- Google Drive folder: `Nigeria_NDMI_NDWI_HLS`
- Resolution: 30m
- Format: GeoTIFF