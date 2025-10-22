# Upload TIFF Files from Google Drive to Earth Engine Assets

## Steps to Upload Your TIFF Files to Earth Engine:

1. **Download files from Google Drive to your local machine**
   - Go to your Google Drive folder
   - Select a few TIFF files at a time
   - Download them

2. **Upload to Earth Engine Assets**
   - Go to https://code.earthengine.google.com/
   - In the Assets tab (left panel), click "NEW" → "Image upload"
   - Select your TIFF files
   - Name them consistently (e.g., `NDMI_2015_07`, `NDWI_2015_07`)
   - Upload them to a folder in your assets

3. **Once uploaded, use this modified script:**

```javascript
// Load from Earth Engine Assets instead of Cloud Storage
var assetPath = 'projects/your-project/assets/NDMI_NDWI/';

function loadNDMIFromAsset(year, month) {
  var monthStr = (month < 10) ? '0' + month : '' + month;
  // Load all 4 tiles and mosaic them
  var tiles = [];
  for (var i = 0; i < 4; i++) {
    var tilePath = assetPath + 'NDMI_' + year + '_' + monthStr + '-' + i;
    tiles.push(ee.Image(tilePath));
  }
  return ee.ImageCollection(tiles).mosaic();
}
```

This is tedious but works within GEE's constraints.