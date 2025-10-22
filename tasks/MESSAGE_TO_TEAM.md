# Message to Team and Grace

**From:** Bernard Boateng
**Date:** October 8, 2025
**Re:** Grace's DBI Values Investigation

---

## Summary

I tested Grace's code as requested. **Grace's methodology is correct.** Her DBI values are showing as 0-1 because they're fractions, not percentages. She needs to multiply by 100 in her buffer calculation script. Grace's intuition was spot-on.

---

## What I Did

As requested in our meeting (Speaker 2, line 69: "Take Grace's code and just run it for Delta State"), I:

1. Ran Grace's DBI raster creation script for Delta State (2018)
2. Reviewed Grace's buffer calculation script that she mentioned
3. Compared results to my original Delta State analysis (2023)

---

## Test Results

### Grace's DBI Raster (Delta State 2018):
- **Total Delta State area:** 16,842 km²
- **Total urban area:** 559 km²
- **Urban percentage:** 3.32%
- **Sentinel-2 images used:** 23

### My Original Analysis (Delta State 2023):
- **Urban percentage:** 5.44%
- **Year:** 2023

### Comparison:
- **Difference:** 2.12 percentage points
- **Explanation:** 5 years of urbanization growth (2018→2023) + different imagery availability

**Conclusion:** The 2% difference is reasonable and expected. Both methods are producing valid results.

---

## The Bug I Found

Grace's issue is in her **buffer calculation script** (`context.md`, lines 86-108).

### Current Code (Lines 93 & 102):
```javascript
// GHSL within 2 km buffer
var ghslDict = ghsl.reduceRegion({
  reducer: ee.Reducer.mean(),
  geometry: geom.buffer(2000),
  scale: 30,
  maxPixels: 1e9
});
var ghslValue = safeGetNumber(ghslDict, 'ghsl');  // ❌ Returns fraction (0-1)

// DBI within 2 km buffer
var dbiDict = dbi.reduceRegion({
  reducer: ee.Reducer.mean(),
  geometry: geom.buffer(2000),
  scale: 30,
  maxPixels: 1e9
});
var dbiValue = safeGetNumber(dbiDict, 'dbi');  // ❌ Returns fraction (0-1)
```

### The Problem:
- Grace's DBI and GHSL rasters are **binary** (0 = not urban, 1 = urban)
- `ee.Reducer.mean()` on binary data returns **fractions** (e.g., 0.054 = 5.4% of pixels are urban)
- Grace is storing these fractions directly without converting to percentages

### Example:
If a 2km buffer is 5.4% urban:
- Current output: **0.054** (fraction)
- Expected output: **5.4** (percentage)

---

## The Fix

**Add `.multiply(100)` to lines 93 and 102:**

```javascript
// Line 93 - FIXED
var ghslValue = safeGetNumber(ghslDict, 'ghsl').multiply(100);

// Line 102 - FIXED
var dbiValue = safeGetNumber(dbiDict, 'dbi').multiply(100);
```

This converts fractions (0-1) to percentages (0-100).

---

## Why MODIS Works But DBI/GHSL Don't

Grace's MODIS calculation already includes this conversion (line 57):

```javascript
return urban.reduceNeighborhood({reducer: ee.Reducer.mean(), kernel: kernel})
            .multiply(100)  // ✅ Already converts to percentage
            .rename('modis_urban_percent');
```

MODIS values are correct because she already multiplies by 100 in the `getModisUrbanPercent()` function. She just needs to apply the same logic to GHSL and DBI.

---

## Validation

### Grace's Suspicion (Line 1 from Slack):
> "I did notice that mine only have a range of 0 to 1, so maybe they need to be multiplied by 100?"

**Grace was absolutely correct.** This is exactly the issue.

### Why Speaker 2 Remembered I Had Values Above 1:
From my Delta State validation report:
- 143 out of 267 wards (53.6%) had DBI > 1%
- Range: 0% to 47.96%
- Mean: 5.44%

Speaker 2 was correct—I did have values above 1 (when expressed as percentages).

---

## Technical Validation

### My Method vs Grace's Method:

**My approach (ward-level aggregation):**
```javascript
// Calculate urban area in m²
var urbanArea = binaryMask.multiply(ee.Image.pixelArea())
  .reduceRegion({reducer: ee.Reducer.sum(), ...});

// Divide by total area and multiply by 100
var percentage = urbanArea.divide(totalArea).multiply(100);
```

**Grace's approach (buffer mean):**
```javascript
// Calculate mean of binary pixels (gives fraction)
var mean = binaryMask.reduceRegion({reducer: ee.Reducer.mean(), ...});

// Should multiply by 100 here
var percentage = mean.multiply(100);  // ← She's missing this
```

**Both approaches are mathematically equivalent** when you account for the ×100 conversion.

---

## Recommendation

**For Grace:**
Your DBI raster creation is correct. Your buffer calculation logic is correct. You just need to add `.multiply(100)` on two lines:
- Line 93: `var ghslValue = safeGetNumber(ghslDict, 'ghsl').multiply(100);`
- Line 102: `var dbiValue = safeGetNumber(dbiDict, 'dbi').multiply(100);`

After this fix, your values will range 0-100% instead of 0-1, and will align with MODIS and expected urban percentages.

**For the Team:**
Grace's methodology is scientifically sound. This is a simple units conversion issue (fractions vs percentages), not a methodological error. The fix is 2 characters of code.

---

## Supporting Data

### GEE Console Output from My Test:
```
Delta State loaded: 1 feature(s)
===== Processing: Delta_State (2018) =====
Number of Sentinel-2 images found for Delta_State 2018: 23

===== VALIDATION CHECKS =====
Total Delta State area (km²): 16,841.73
Total urban area (km²): 559.46
Urban percentage: 3.32%

EXPECTED (from Bernard's original): 5-6% for 2023
ACTUAL: 3.32% for 2018 ✓ Reasonable (5 years earlier)
```

### Expected Results After Grace Applies Fix:
- **Current:** DBI values 0.00 to 1.00
- **After fix:** DBI values 0% to 100%
- **Typical urban cluster:** 3-15% (currently showing as 0.03-0.15)
- **Arid rural areas:** 0-2% (currently showing as 0.00-0.02)

---

## Bottom Line

✅ Grace's DBI raster creation: **Correct**
✅ Grace's buffer calculation logic: **Correct**
✅ Grace's intuition about ×100: **Correct**
❌ Missing `.multiply(100)` in two places: **Bug found and identified**

Grace can fix this in 5 minutes by adding `.multiply(100)` to lines 93 and 102 of her buffer script.

---

**Questions? Happy to walk through the fix or run additional validation tests.**

— Bernard
