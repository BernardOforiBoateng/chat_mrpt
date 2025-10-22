// ========================================================
// Export Mali Boundary from FAO GAUL
// For use in visualization with Bernard's test results
// ========================================================

// Load Mali boundary from FAO GAUL (same as used in analysis)
var gaul = ee.FeatureCollection('FAO/GAUL_SIMPLIFIED_500m/2015/level0');
var mali = gaul.filter(ee.Filter.eq('ADM0_NAME', 'Mali'));

print('Mali boundary:', mali);

// Add to map
Map.addLayer(mali, {color: 'blue'}, 'Mali Boundary');
Map.centerObject(mali, 6);

// Fix: Export as GeoJSON instead to avoid mixed geometry issue
// Or export as KML which handles mixed geometries
Export.table.toDrive({
  collection: mali,
  description: 'Mali_Boundary_FAO_GAUL',
  fileFormat: 'GeoJSON'  // Changed from SHP to GeoJSON
});

print('✓ Go to Tasks tab and run the export');
print('✓ Mali boundary GeoJSON will be saved to Google Drive');
print('✓ GeoJSON can be easily converted to shapefile or used directly in Python');
