# FOUND THE BUG IN GRACE'S CODE

**Date:** October 8, 2025

---

## THE PROBLEM (Lines 86-108 in context.md)

### Grace's Buffer Calculation Code:

```javascript
// GHSL within 2 km buffer
var ghslDict = ghsl.reduceRegion({
  reducer: ee.Reducer.mean(),
  geometry: geom.buffer(2000),
  scale: 30,
  maxPixels: 1e9
});
var ghslValue = safeGetNumber(ghslDict, 'ghsl');

// DBI within 2 km buffer
var dbiDict = dbi.reduceRegion({
  reducer: ee.Reducer.mean(),       // ⚠️ THIS IS THE BUG
  geometry: geom.buffer(2000),
  scale: 30,
  maxPixels: 1e9
});
var dbiValue = safeGetNumber(dbiDict, 'dbi');
```

---

## THE BUG EXPLAINED

### What Grace is Doing:
1. She loads the **DBI binary raster** (line 29): values are **0 or 1** (not urban vs urban)
2. She buffers each cluster point by 2km (line 98)
3. She calculates `ee.Reducer.mean()` of the DBI raster within that buffer (line 97)
4. **Mean of binary pixels (0 or 1) = fraction between 0 and 1** ❌

### Example:
If a 2km buffer contains:
- 90% non-urban pixels (value = 0)
- 10% urban pixels (value = 1)

Then `mean() = (0.9 × 0) + (0.1 × 1) = 0.1`

**Grace gets: 0.1**
**She expects: 10%**

---

## THE FIX

### What Grace SHOULD Do:

Instead of just taking the mean, she needs to **multiply by 100** to convert fraction to percentage:

```javascript
// DBI within 2 km buffer
var dbiDict = dbi.reduceRegion({
  reducer: ee.Reducer.mean(),
  geometry: geom.buffer(2000),
  scale: 30,
  maxPixels: 1e9
});
var dbiValue = safeGetNumber(dbiDict, 'dbi').multiply(100);  // ⚠️ ADD .multiply(100)
```

**Same fix needed for GHSL (line 93):**

```javascript
var ghslValue = safeGetNumber(ghslDict, 'ghsl').multiply(100);  // ⚠️ ADD .multiply(100)
```

---

## WHY YOUR CODE WORKED

### Your Original Method (from contxt.md, line 256-278):

```javascript
function calculateUrbanPercentage(binaryMask, wardGeometry, scale, bandName) {
  binaryMask = binaryMask.unmask(0).clamp(0, 1);

  // Calculate total urban area in square meters
  var urbanArea = binaryMask.multiply(ee.Image.pixelArea())  // ⚠️ KEY DIFFERENCE
    .reduceRegion({
      reducer: ee.Reducer.sum(),                              // ⚠️ Using SUM
      geometry: wardGeometry,
      scale: scale,
      maxPixels: 1e13,
      tileScale: 2
    });

  var areaValue = ee.Number(urbanArea.get(bandName || urbanArea.keys().get(0)));
  var totalArea = wardGeometry.area();

  var percentage = ee.Algorithms.If(
    totalArea.gt(0),
    areaValue.divide(totalArea).multiply(100).min(100),      // ⚠️ MULTIPLY BY 100
    0
  );

  return ee.Number(percentage);
}
```

**Key Differences:**
1. You multiply by `pixelArea()` first → converts binary to area
2. You use `sum()` → adds up urban area
3. You divide by total area → gets fraction
4. You **multiply by 100** → converts to percentage ✅

**Grace:**
1. Takes `mean()` of binary → gets fraction
2. Forgets to multiply by 100 → stays as fraction (0-1) ❌

---

## GRACE'S SUSPICION WAS CORRECT

### What Grace Said (Line 1 in contxt.md):
> "I did notice that mine only have a range of 0 to 1, **so maybe they need to be multiplied by 100?**"

**Grace was RIGHT!** She just needed to add `.multiply(100)` to lines 93 and 102.

---

## THE COMPLETE FIX

### Fixed Code for context.md:

```javascript
// ========================================================
// FUNCTION TO CALCULATE ALL VALUES
// ========================================================
function calculateAllUrban(pt) {
  var geom = pt.geometry();

  // MODIS urban %
  var modis2018 = getModisUrbanPercent(2018);
  var modisDict = modis2018.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: geom,
    scale: 500,
    maxPixels: 1e9
  });
  var modisValue = safeGetNumber(modisDict, 'modis_urban_percent');
  // MODIS is already in %, no need to multiply (line 57 does it)

  // Arid flag
  var aridDict = aridMask.reduceRegion({
    reducer: ee.Reducer.first(),
    geometry: geom,
    scale: 500,
    maxPixels: 1e9
  });
  var aridValue = safeGetNumber(aridDict, 'arid_flag');

  // GHSL within 2 km buffer
  var ghslDict = ghsl.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: geom.buffer(2000),
    scale: 30,
    maxPixels: 1e9
  });
  var ghslValue = safeGetNumber(ghslDict, 'ghsl').multiply(100); // ✅ FIXED

  // DBI within 2 km buffer
  var dbiDict = dbi.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: geom.buffer(2000),
    scale: 30,
    maxPixels: 1e9
  });
  var dbiValue = safeGetNumber(dbiDict, 'dbi').multiply(100); // ✅ FIXED

  return pt.set({
    'modis_urban_percent': modisValue,
    'arid_flag': aridValue,
    'GHSL_pct': ghslValue,
    'DBI_pct': dbiValue
  });
}
```

---

## VALIDATION OF THE FIX

### Before Fix:
- Grace's values: **0 to 1** (fractions)
- Example: 0.054 (meaning 5.4% urban)

### After Fix:
- Grace's values: **0 to 100** (percentages)
- Example: 5.4 (meaning 5.4% urban)

---

## WHY MODIS WORKS BUT DBI/GHSL DON'T

Look at line 56-57 in context.md:

```javascript
return urban.reduceNeighborhood({reducer: ee.Reducer.mean(), kernel: kernel})
            .multiply(100)  // ⚠️ MODIS ALREADY MULTIPLIES BY 100
            .rename('modis_urban_percent');
```

**MODIS is already converted to percentage** in the `getModisUrbanPercent()` function!

But GHSL and DBI rasters are **binary (0 or 1)**, so they need the same `.multiply(100)` treatment.

---

## SUMMARY FOR THE TEAM

**Problem:** Grace's DBI and GHSL values are 0-1 instead of 0-100%

**Root Cause:** Taking `mean()` of binary raster gives fractions, not percentages

**Solution:** Add `.multiply(100)` to lines 93 and 102 in context.md

**Grace's Intuition:** She was 100% correct - they just needed to be multiplied by 100!

---

## TEST RESULTS RECONCILIATION

### Our Test (Grace's Raster for Delta State):
- **3.32% urban** for whole state ✅ Correct

### Grace's Buffer Results (Before Fix):
- Would show **0.0332** (fraction) instead of **3.32%** (percentage)

### After Fix:
- Will show **3.32%** (percentage) ✅ Matches expectations

---

## THE FIX IS LITERALLY 2 CHARACTERS

Change line 93:
```javascript
var ghslValue = safeGetNumber(ghslDict, 'ghsl');
```
To:
```javascript
var ghslValue = safeGetNumber(ghslDict, 'ghsl').multiply(100);
```

Change line 102:
```javascript
var dbiValue = safeGetNumber(dbiDict, 'dbi');
```
To:
```javascript
var dbiValue = safeGetNumber(dbiDict, 'dbi').multiply(100);
```

**That's it!**
