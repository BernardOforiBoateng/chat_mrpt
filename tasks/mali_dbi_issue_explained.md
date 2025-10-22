# Grace's Mali DBI Issue - Explanation

**Date:** October 8, 2025

---

## What Grace Is Seeing

**From the maps:**
1. **b.png (Aridity)**: Southwest Mali (10-13°N) = Non-arid (blue dots) = WHERE BAMAKO IS (urban capital)
2. **bb.png (DBI values)**: Southwest Mali = LOW DBI (0-25%, purple/blue) ❌ WRONG - should be high
3. **bb.png (DBI values)**: Northern Mali (15-18°N, arid tan dots) = HIGH DBI (50-75%, yellow/orange) ❌ ALSO QUESTIONABLE

**Grace's concern (line 1 of contxt.md):**
> "It's saying the urban southwest region of Mali has very low urbanicity, which shouldn't be the case."

**She's absolutely right!** Southwest Mali contains Bamako (capital, most urban area), but DBI shows it as low urban %.

---

## The Core Problem: DBI Doesn't Work in Non-Arid Regions

### Why This Is Happening:

**DBI Formula:** DBI = NDBI - NDVI

**In NON-ARID regions (like southwest Mali):**
- Vegetation is present → **NDVI is HIGH**
- Urban areas still have some vegetation/greenery
- **DBI = NDBI - HIGH_NDVI = LOW value** ❌
- Even in urban Bamako!

**In ARID regions (like northern Mali):**
- Little vegetation → **NDVI is LOW**
- Bare soil/built-up areas dominate
- **DBI = NDBI - LOW_NDVI = HIGHER value** ✓
- But this can also flag bare desert as "urban"!

### This Is Why Rasul et al. (2018) Designed DBI Specifically for Arid Regions

The paper title literally says: **"Applying built-up and bare-soil indices from Landsat 8 to cities in dry climates"**

DBI is **NOT appropriate** for humid/vegetated regions like southwest Mali or southern Nigeria.

---

## Code Issues Found

### Issue 1: GHSL Not Multiplied by 100 (Line 309)
```javascript
// Line 309 - MISSING multiply(100)
var ghslValue = safeGetNumber(ghslDict, 'ghsl');
```

**Should be:**
```javascript
var ghslValue = safeGetNumber(ghslDict, 'ghsl').multiply(100);
```

### Issue 2: GHSL Using Wrong Scale (Line 306)
```javascript
// Line 306 - scale: 1000 is way too coarse!
var ghslDict = ghsl.reduceRegion({
  reducer: ee.Reducer.mean(),
  geometry: geom.buffer(2000),
  scale: 1000,  // ❌ 1km resolution - loses detail
  maxPixels: 1e9
});
```

**Should be:**
```javascript
scale: 10,  // ✓ GHSL native resolution is 10m
```

Or at least:
```javascript
scale: 30,  // ✓ Match DBI resolution
```

### Issue 3: DBI Applied Correctly! (Line 318)
```javascript
// Line 318 - ✓ CORRECT
var dbiValue = safeGetNumber(dbiDict, 'dbi').multiply(100);
```

Grace already fixed the DBI multiply issue! But it still shows wrong results because **DBI isn't appropriate for non-arid regions**.

---

## What This Means for Grace's Analysis

### For Arid Regions (Northern Mali, Northern Nigeria):
- ✓ Use DBI - it works well
- ✓ Low DBI values (0-2%) are expected and correct

### For Non-Arid Regions (Southwest Mali, Southern Nigeria):
- ❌ **Do NOT use DBI** - it will underestimate urban areas
- ✓ Use NDBI instead (without subtracting NDVI)
- ✓ Use GHSL
- ✓ Use MODIS

### The Solution:

Grace needs to **conditionally choose the index based on aridity**:

```javascript
function calculateAllUrban(pt) {
  var geom = pt.geometry();

  // Check if point is in arid region
  var aridDict = aridMask.reduceRegion({
    reducer: ee.Reducer.first(),
    geometry: geom,
    scale: 500,
    maxPixels: 1e9
  });
  var isArid = safeGetNumber(aridDict, 'arid_flag');

  // For ARID regions: use DBI
  // For NON-ARID regions: use NDBI (or just set DBI to null)
  var dbiValue = ee.Algorithms.If(
    isArid.eq(1),
    safeGetNumber(dbiDict, 'dbi').multiply(100),  // Use DBI in arid
    null  // Don't use DBI in non-arid (or use NDBI instead)
  );

  return pt.set({
    'modis_urban_percent': modisValue,
    'arid_flag': isArid,
    'GHSL_pct': ghslValue.multiply(100),  // ✓ Fix: multiply by 100
    'DBI_pct': dbiValue,  // Only valid in arid regions
    'use_dbi': isArid  // Flag indicating if DBI should be trusted
  });
}
```

---

## Summary for Grace

**Your maps are showing exactly what the literature predicts:**

1. **DBI works in arid regions** (northern Mali)
2. **DBI FAILS in non-arid regions** (southwest Mali/Bamako)
3. **This is not a bug in your code** - it's a limitation of the DBI index itself

**Fixes needed:**
1. ✓ DBI multiply(100): Already done (line 318)
2. ❌ GHSL multiply(100): Missing (line 309)
3. ❌ GHSL scale: Should be 10 or 30, not 1000 (line 306)
4. ⚠️ **Use DBI only in arid regions** - for non-arid, rely on GHSL/MODIS/NDBI

**For southwest Mali (urban Bamako):**
- Check GHSL values (after fixing multiply and scale)
- Check MODIS values
- **Ignore DBI values** - they will be incorrectly low

**This explains Speaker 2's concern** from the meeting - DBI values outside arid areas don't represent urban % accurately.

---

## What Bernard Should Tell Grace

"Grace, your maps are actually showing an important finding - **DBI doesn't work in non-arid regions**. This is a known limitation from the Rasul et al. (2018) paper - it's designed specifically for 'cities in dry climates.'

For southwest Mali (where Bamako is), DBI will underestimate urbanicity because the vegetation there gives high NDVI values, which DBI subtracts out.

**Solution:** Use DBI only in arid regions (northern Mali, northern Nigeria). For non-arid regions (southwest Mali, southern Nigeria), rely on GHSL and MODIS instead.

Also fix:
- Line 309: Add `.multiply(100)` to GHSL
- Line 306: Change GHSL scale from 1000 to 10 or 30

Your DBI code is correct - it's just the wrong tool for non-arid regions."
