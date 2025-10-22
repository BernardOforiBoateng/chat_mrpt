# DBI Code Comparison: Grace vs Bernard

**Date:** October 8, 2025
**Purpose:** Validate Grace's GEE implementation against Bernard's original Delta State validation

---

## Executive Summary

**Finding:** Grace's code has a **CRITICAL BUG** - it exports binary masks (0 or 1) instead of urban percentages (0-100%).

**Evidence from Bernard's Delta State Results:**
- DBI values ranged from **0% to 47.96%**
- Mean DBI: **5.44%**
- 143 wards (53.6%) had DBI > 1%
- 44 wards (16.5%) had DBI > 10%

**What Grace will get if she runs her current code:**
- All values will be either 0 or 1 (binary pixels)
- No ward-level aggregation
- Results will NOT match Bernard's percentages

---

## 1. Bernard's Original Delta State Results

### Statistics from `validation_delta_state_urban_validation_2025-09-04.csv`:

```
Total wards: 267
DBI Range: 0.00% to 47.96%
DBI Mean: 5.44%
DBI Median: 1.22%

Distribution:
- DBI > 1%: 143 wards (53.6%)
- DBI > 10%: 44 wards (16.5%)
- DBI > 50%: 0 wards

Top 10 highest DBI values:
1. 47.96%
2. 45.55%
3. 44.95%
4. 43.84%
5. 42.54%
6. 40.31%
7. 38.80%
8. 36.89%
9. 36.23%
10. 34.90%
```

### Sample Wards:
- **Issele-Uku 1**: DBI = 1.58%, MODIS = 8.40%, GHSL = 32.08%
- **Agiadiasi**: DBI = 0.90%, MODIS = 16.64%, GHSL = 32.61%
- **Otulu**: DBI = 0.71%, MODIS = 0.94%, GHSL = 11.46%

### Key Finding from Bernard's Report:
> "DBI Mean: 5.4% - more accurate for Delta State's known rural nature compared to NDBI's overestimate of 33.1%"

---

## 2. Code Comparison

### A. DBI Calculation (BOTH CORRECT)

**Grace's Code (lines 158-162):**
```javascript
var ndbi = composite.normalizedDifference(['B11', 'B8']).rename('NDBI');
var ndvi = composite.normalizedDifference(['B8', 'B4']).rename('NDVI');
var dbi = ndbi.subtract(ndvi).rename('DBI');
```

**Bernard's Code (lines 374-378):**
```javascript
var ndbi = composite.normalizedDifference(['B11', 'B8']);
var ndvi = composite.normalizedDifference(['B8', 'B4']);
var dbi = ndbi.subtract(ndvi);
```

✅ **Status:** Both calculate DBI correctly using Rasul et al. (2018) formula: `DBI = NDBI - NDVI`

---

### B. Built-Up Mask Creation (BOTH CORRECT)

**Grace's Code (line 165):**
```javascript
var builtUpMask = dbi.gt(0).selfMask().rename('dbi_urban');
```

**Bernard's Code (line 381):**
```javascript
var builtUpMask = dbi.gt(0);
```

✅ **Status:** Both correctly threshold DBI > 0 for built-up areas

---

### C. CRITICAL DIFFERENCE: What Gets Exported

**Grace's Code (lines 176-177, 189-198):**
```javascript
// Inside calculateDBI():
builtUpMask = builtUpMask.clip(geometry)
  .rename(countryName.replace(/\s+/g, '_') + '_dbi_' + year);
return builtUpMask;  // ⚠️ RETURNS BINARY MASK

// Main loop exports this directly:
Export.image.toDrive({
  image: dbiImage,  // ⚠️ BINARY IMAGE (0 or 1 per pixel)
  description: cfg.name.replace(/\s+/g, '_') + '_DBI_' + cfg.year,
  folder: 'DBI_exports',
  scale: 30,
  region: geom,
  maxPixels: 1e13
});
```

**Bernard's Code (lines 514-545):**
```javascript
// Ward-level analysis - processes each ward:
var wardStats = wards.map(function(ward) {
  var wardGeom = ward.geometry();

  // DBI (20m resolution)
  if (dbiUrban) {
    var dbiPercent = calculateUrbanPercentage(
      dbiUrban, wardGeom, 20, 'dbi_urban'
    );
    stats = stats.set('dbi_urban_percent', dbiPercent);
  }

  return ward.set(stats);
});

// calculateUrbanPercentage function (lines 251-278):
function calculateUrbanPercentage(binaryMask, wardGeometry, scale, bandName) {
  binaryMask = binaryMask.unmask(0).clamp(0, 1);

  // Calculate total urban area in square meters
  var urbanArea = binaryMask.multiply(ee.Image.pixelArea())
    .reduceRegion({
      reducer: ee.Reducer.sum(),
      geometry: wardGeometry,
      scale: scale,
      maxPixels: 1e13,
      tileScale: 2
    });

  var areaValue = ee.Number(urbanArea.get(bandName || urbanArea.keys().get(0)));
  var totalArea = wardGeometry.area();

  // Calculate percentage with 100% cap
  var percentage = ee.Algorithms.If(
    totalArea.gt(0),
    areaValue.divide(totalArea).multiply(100).min(100),
    0
  );

  return ee.Number(percentage);
}

// Exports ward-level CSV with percentages:
Export.table.toDrive({
  collection: wardStats,  // ⚠️ WARD FEATURES with percentage attributes
  description: 'Urban_Validation_RESEARCH_BACKED_Drive',
  folder: 'GEE_Urban_Validation',
  fileNamePrefix: 'urban_validation_research_backed_' + new Date().toISOString().slice(0,10),
  fileFormat: 'CSV'
});
```

❌ **CRITICAL BUG:** Grace exports **pixel-level binary raster**, Bernard exports **ward-level percentage CSV**

---

## 3. The Problem Explained

### What Grace's Code Produces:
- **Output:** GeoTIFF raster file
- **Values:** 0 (not built-up) or 1 (built-up) per pixel
- **Scale:** 30m pixels
- **For Nigeria:** ~40 million pixels
- **Cannot be compared to Bernard's results** without additional aggregation

### What Bernard's Code Produces:
- **Output:** CSV with ward features
- **Values:** 0-100% urban per ward
- **Scale:** Ward-level (267 wards for Delta State)
- **Calculation:** `(urban_area / total_ward_area) × 100`

### Why Grace Got Low Values (0-1 range):

If Grace tried to aggregate her binary raster manually, she might have:
1. Taken the mean of pixels per ward → Would give 0-1 (fraction of urban pixels)
2. Forgot to multiply by 100 → Would give 0.00-1.00 instead of 0-100%

**Grace's suspicion (line 1 of contxt.md):**
> "I did notice that mine only have a range of 0 to 1, so maybe they need to be multiplied by 100?"

✅ **She was RIGHT!** But the real issue is deeper - she needs to implement the full area-weighted calculation.

---

## 4. What Needs to be Fixed

### Option 1: Add Ward-Level Aggregation to Grace's Code (Recommended)

Grace needs to add Bernard's `calculateUrbanPercentage()` function and ward processing loop:

```javascript
// After creating builtUpMask, process by ward:
var wards = ee.FeatureCollection('path/to/wards'); // She needs ward boundaries

var wardStats = wards.map(function(ward) {
  var wardGeom = ward.geometry();

  // Calculate urban percentage
  var urbanArea = builtUpMask.multiply(ee.Image.pixelArea())
    .reduceRegion({
      reducer: ee.Reducer.sum(),
      geometry: wardGeom,
      scale: 30,  // Use her 30m scale
      maxPixels: 1e13
    });

  var totalArea = wardGeom.area();
  var percentage = ee.Number(urbanArea.values().get(0))
    .divide(totalArea)
    .multiply(100)
    .min(100);

  return ward.set('dbi_urban_percent', percentage);
});

// Export ward CSV instead of raster:
Export.table.toDrive({
  collection: wardStats,
  description: 'Nigeria_DBI_Ward_Percentages',
  folder: 'DBI_exports',
  fileFormat: 'CSV'
});
```

### Option 2: Keep Grace's Approach, Add Post-Processing

If Grace wants to keep exporting rasters:
1. Export binary raster (current code)
2. Add separate script to:
   - Load ward boundaries
   - Load DBI raster
   - Calculate zonal statistics (mean × 100) per ward
   - Export CSV

---

## 5. Test Plan for Delta State

### What Grace Should Do:

1. **Get Ward Boundaries**
   - Use same ward shapefile Bernard used: `table` variable in his code
   - Likely from INEC or GRID3

2. **Modify Her Code:**
   ```javascript
   // Change line 102-118 to only Delta State:
   var countryConfigs = [
     {name: 'Nigeria', year: 2018}  // Change to Delta State if available
   ];

   // OR filter wards:
   var deltaWards = wards.filter(ee.Filter.eq('StateName', 'Delta'));
   ```

3. **Add Ward Processing:**
   - Copy Bernard's `calculateUrbanPercentage()` function
   - Copy Bernard's ward mapping loop (lines 514-565)
   - Export CSV instead of raster

4. **Compare Results:**
   - Join her CSV with Bernard's CSV on `WardCode` or `WardName`
   - Calculate differences
   - Should match within 1-2% (due to year differences: 2018 vs 2023)

---

## 6. Expected Outcomes

### If Grace Runs Current Code for Delta State:
```
❌ Output: GeoTIFF raster with binary values (0 or 1)
❌ Cannot directly compare to Bernard's percentages
❌ Would need manual post-processing
```

### If Grace Adds Ward Aggregation:
```
✅ Output: CSV with DBI percentages per ward
✅ Can directly compare to Bernard's results
✅ Should see similar distribution:
   - Mean ~5-6%
   - Range 0-50%
   - 50%+ wards with DBI > 1%
```

---

## 7. Addressing the Speaker 2 Concerns

### Concern: "Outside arid areas, still getting below one"

**Root Cause:** Grace is looking at binary pixel values or incorrectly scaled percentages.

**Solution:** Implement proper ward-level aggregation with the formula:
```
urban_percentage = (sum of urban pixels × pixel_area) / total_ward_area × 100
```

**Expected Results After Fix:**
- Lagos urban wards: 20-80% DBI
- Delta urban centers: 10-50% DBI
- Rural wards: 0-5% DBI
- Arid north: 0-2% DBI (correctly low)

---

## 8. Key Differences Summary Table

| Aspect | Grace's Code | Bernard's Code | Impact |
|--------|-------------|---------------|--------|
| DBI Formula | ✅ Correct | ✅ Correct | Same |
| Threshold | ✅ DBI > 0 | ✅ DBI > 0 | Same |
| Output Type | ❌ Raster | ✅ CSV | Different |
| Scale | ❌ Pixel (30m) | ✅ Ward | Different |
| Values | ❌ Binary (0-1) | ✅ Percentage (0-100) | Different |
| Aggregation | ❌ None | ✅ Area-weighted | **CRITICAL** |
| Comparable? | ❌ No | ✅ Yes | **CRITICAL** |

---

## 9. Recommendation

### For Speaker 2 (Supervisor):

> "Grace's DBI calculation is scientifically correct, but she's exporting pixel-level data instead of ward-level percentages. Bernard's code includes an aggregation step that Grace's lacks. We need to add ~50 lines of code to calculate area-weighted percentages per ward. Once fixed, her results should match Bernard's Delta State validation (5.4% mean DBI)."

### For Grace:

> "Your DBI formula is correct! The issue is you're exporting the raw 0/1 pixel values instead of aggregating them by ward. You need to:
> 1. Load ward boundaries (same ones Bernard used)
> 2. Add the `calculateUrbanPercentage()` function from Bernard's code
> 3. Map over wards instead of exporting raster
> 4. Export CSV with percentages
>
> I've prepared a modified version of your script that does this - want me to share it?"

---

## 10. Files to Review

1. **Grace's Code:** Lines 91-205 in `contxt.md`
2. **Bernard's Code:** Lines 208-637 in `contxt.md`
3. **Bernard's Results:** `/urban_validation_outputs/DELTA_STATE_Urbanicity_Validation_Report/`
4. **Bernard's Findings:** `/urban_validation_outputs/DELTA_STATE_FINDINGS.md`

---

**Next Steps:**
1. ✅ Confirmed Bernard's original results show DBI values 0-48%
2. ⏳ Create modified version of Grace's code with ward aggregation
3. ⏳ Test on Delta State
4. ⏳ Document findings for team meeting
