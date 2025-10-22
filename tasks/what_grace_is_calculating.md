# What Grace Is Actually Calculating

**Date:** October 8, 2025

---

## Grace's Input Data

**From line 225-234 in contxt.md:**
```javascript
var pointsRaw = ee.FeatureCollection("projects/ee-gracebea/assets/agric_points");
var nigeriaPoints = pointsRaw.filter(ee.Filter.eq('CountryName', 'Nigeria'));
```

Grace has **agricultural cluster points** (lat/lon coordinates).

---

## What She's Calculating Per Point

### 1. MODIS Urban % (Lines 290-291)
```javascript
var modisValue = getModisUrbanPercent(pt, 2018);
```

**What this does (from lines 254-282):**
- Creates a **2km buffer** around the point (line 255)
- Gets MODIS urban pixels (class 13)
- Calculates **mean fraction** of urban pixels within the 2km buffer
- **Multiplies by 100** to get percentage (line 281) ✅

**Output:** Percentage of the 2km buffer area that is urban according to MODIS

---

### 2. Arid Flag (Lines 293-300)
```javascript
var aridValue = safeGetNumber(aridDict, 'arid_flag');
```

**What this does:**
- Checks if the point location is in an arid climate zone
- Uses Köppen-Geiger climate classification
- Returns **1** if arid, **0** if not arid

**Output:** Binary flag (0 or 1)

---

### 3. GHSL Urban % (Lines 302-309)
```javascript
var ghslDict = ghsl.reduceRegion({
  reducer: ee.Reducer.mean(),
  geometry: geom.buffer(2000),  // 2km buffer
  scale: 1000,                   // ❌ 1km resolution (too coarse!)
  maxPixels: 1e9
});
var ghslValue = safeGetNumber(ghslDict, 'ghsl');  // ❌ MISSING .multiply(100)
```

**What this does:**
- Creates a **2km buffer** around the point
- Calculates **mean** of GHSL binary raster (0 or 1) within buffer
- Uses **1000m scale** (way too coarse - GHSL native is 10m)
- **Does NOT multiply by 100** ❌

**Output:** **FRACTION** (0-1) of the 2km buffer that is urban according to GHSL

**Problem:** Returns 0.25 instead of 25%

---

### 4. DBI Urban % (Lines 311-318)
```javascript
var dbiDict = dbi.reduceRegion({
  reducer: ee.Reducer.mean(),
  geometry: geom.buffer(2000),  // 2km buffer
  scale: 30,                     // ✅ 30m resolution
  maxPixels: 1e9
});
var dbiValue = safeGetNumber(dbiDict, 'dbi').multiply(100);  // ✅ HAS multiply(100)
```

**What this does:**
- Creates a **2km buffer** around the point
- Calculates **mean** of DBI binary raster (0 or 1) within buffer
- Uses **30m scale** ✅
- **Multiplies by 100** ✅

**Output:** **PERCENTAGE** (0-100) of the 2km buffer that is urban according to DBI

---

## Summary Table

| Metric | Buffer Size | Scale | Multiply by 100? | Output Range | Status |
|--------|-------------|-------|------------------|--------------|--------|
| **MODIS** | 2km | 500m | ✅ Yes (line 281) | 0-100% | ✅ Correct |
| **Arid Flag** | Point | 500m | N/A | 0 or 1 | ✅ Correct |
| **GHSL** | 2km | 1000m ❌ | ❌ No | 0-1 (fraction) | ❌ Wrong units + coarse scale |
| **DBI** | 2km | 30m | ✅ Yes (line 318) | 0-100% | ✅ Correct |

---

## What This Means

### Grace Is Calculating:
**"Within a 2km radius of each agricultural cluster point, what percentage of the area is classified as urban by each method?"**

### Example:
If a cluster point is in/near Bamako:
- **MODIS**: 45% urban (45% of 2km buffer is urban)
- **GHSL**: 0.42 (should be 42%, but missing multiply) ❌
- **DBI**: 38% urban (38% of 2km buffer is urban)
- **Arid**: 0 (not in arid zone)

---

## The Mali Issue Explained

**Grace says:** "Southwest Mali (Bamako area) shows low DBI values"

**Possible explanations:**

### 1. GHSL is in Wrong Units
- GHSL showing 0.25 looks "low" compared to MODIS 45%
- But 0.25 × 100 = 25%, which might be reasonable
- **Action:** Fix GHSL multiply and compare again

### 2. 2km Buffer Includes Rural Areas
- Agricultural cluster points might not be in urban core
- 2km buffer could include mix of urban + rural
- This would dilute the urban percentage
- **Check:** Are the cluster points actually IN Bamako, or just near it?

### 3. Different Resolutions Give Different Results
- MODIS: 500m (coarse, might overestimate)
- GHSL: Using 1000m ❌ (too coarse, losing detail)
- DBI: 30m ✅ (fine resolution, might show more nuanced patterns)
- **Action:** Fix GHSL scale to 30m and compare

### 4. DBI Might Actually Be Correct
- If Bamako cluster points are in **peri-urban** areas (not dense urban core)
- DBI at 30m resolution can distinguish this
- MODIS at 500m might over-classify mixed areas as urban
- **Need:** Actual data values to verify

---

## What Grace Should Do

1. **Fix GHSL code:**
   ```javascript
   var ghslValue = safeGetNumber(ghslDict, 'ghsl').multiply(100);
   ```

2. **Fix GHSL scale:**
   ```javascript
   scale: 30,  // or 10 for native resolution
   ```

3. **Re-run and export CSV**

4. **Compare values for Bamako area clusters:**
   - If MODIS = 45%, GHSL = 42%, DBI = 12% → DBI might be wrong
   - If MODIS = 45%, GHSL = 40%, DBI = 38% → All methods agree, cluster is urban
   - If MODIS = 8%, GHSL = 5%, DBI = 3% → All methods agree, cluster is rural (not in Bamako core)

5. **Check cluster point locations:**
   - Are they actually IN Bamako city, or just in "southwest Mali"?
   - A 2km buffer of a rural agricultural point will show low urban %

---

## Bottom Line

**We can't diagnose the issue without seeing:**
1. Actual numeric DBI/GHSL/MODIS values from Grace's CSV
2. Where the cluster points actually are (are they in Bamako city or just southwest Mali region?)

The code calculates what it's supposed to (urban % within 2km buffer), but:
- GHSL has wrong units (fraction vs %)
- GHSL has wrong scale (1000m too coarse)
- We don't know if the "low" values are actually wrong or just reflecting peri-urban/rural cluster locations
