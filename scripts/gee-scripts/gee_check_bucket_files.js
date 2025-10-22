// ----------------------------------------
// DIAGNOSTIC: CHECK WHAT FILES EXIST IN BUCKET
// This will help us understand the naming pattern
// ----------------------------------------

var BUCKET = 'ndmi_ndwi30m';
var year = 2018;
var months = [1, 2, 3, 4, 5, 6];

print('Checking files in bucket: gs://' + BUCKET);
print('============================================================');

// Test all possible naming patterns
var testPatterns = [
  // Pattern A: 4 tiles with coordinates
  {
    name: 'Four tiles with coordinates',
    suffixes: [
      '-0000000000-0000000000',
      '-0000000000-0000032768', 
      '-0000032768-0000000000',
      '-0000032768-0000032768'
    ]
  },
  // Pattern B: Single file, no suffix
  {
    name: 'Single file (no tiles)',
    suffixes: ['']
  },
  // Pattern C: Numbered tiles
  {
    name: 'Numbered tiles',
    suffixes: ['_tile_0', '_tile_1', '_tile_2', '_tile_3']
  },
  // Pattern D: Two tiles only
  {
    name: 'Two tiles',
    suffixes: [
      '-0000000000-0000000000',
      '-0000032768-0000000000'
    ]
  }
];

// Check each month
months.forEach(function(month) {
  var monthStr = (month < 10) ? '0' + month : '' + month;
  
  print('\n--- Checking ' + year + '-' + monthStr + ' ---');
  
  ['NDMI', 'NDWI'].forEach(function(indexType) {
    print('\n' + indexType + ':');
    
    var foundPattern = false;
    
    testPatterns.forEach(function(pattern) {
      var foundFiles = [];
      var missingFiles = [];
      
      pattern.suffixes.forEach(function(suffix) {
        var filePath = 'gs://' + BUCKET + '/' + indexType + '_' + year + '_' + monthStr + suffix + '.tif';
        
        try {
          var img = ee.Image.loadGeoTIFF(filePath);
          // If we can load it, it exists
          foundFiles.push(suffix || '(no suffix)');
        } catch (e) {
          missingFiles.push(suffix || '(no suffix)');
        }
      });
      
      if (foundFiles.length > 0 && missingFiles.length === 0) {
        print('  ✓ ' + pattern.name + ' - ALL FILES FOUND');
        foundPattern = true;
      } else if (foundFiles.length > 0) {
        print('  ⚠ ' + pattern.name + ' - PARTIAL: Found ' + foundFiles.length + '/' + pattern.suffixes.length);
        print('    Found: ' + foundFiles.join(', '));
        print('    Missing: ' + missingFiles.join(', '));
      }
    });
    
    if (!foundPattern) {
      print('  ✗ No complete pattern found - files may be missing or use different naming');
    }
  });
});

print('\n============================================================');
print('DIAGNOSIS COMPLETE');
print('============================================================');
print('');
print('Based on the results above:');
print('1. If you see "Single file (no tiles) - ALL FILES FOUND":');
print('   Your files are not tiled, they are single files per month');
print('');
print('2. If you see "Two tiles - ALL FILES FOUND":');
print('   Your files have only 2 tiles instead of 4');
print('');
print('3. If you see "PARTIAL" for any pattern:');
print('   Some tiles are missing from your bucket');
print('');
print('4. If you see no matches:');
print('   The files might not be uploaded yet or use a completely different naming scheme');
print('');
print('To check manually in Cloud Shell:');
print('  gsutil ls gs://ndmi_ndwi30m/ | grep 2018_01');