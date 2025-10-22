# Grace's Code - Issues Documented

**Date:** October 8, 2025

---

## Issues Found in context.md

### Issue 1: Wrong Geographic Region for GHSL (Line 239)
**Current:**
```javascript
var ghsl = ee.Image("projects/ee-gracebea/assets/Nigeria_GHSL_2018").select([0]).rename('ghsl');
```

**Problem:** Using Nigeria GHSL raster for Mali analysis

**Evidence from data:**
- GHSL capped at 30.0% for all 345 Mali points
- In urban Bamako (MODIS=85%), GHSL=30%

**Fix:**
```javascript
var ghsl = ee.Image("projects/ee-gracebea/assets/Mali_GHSL_2018").select([0]).rename('ghsl');
```

---

### Issue 2: Wrong Geographic Region for DBI (Line 240)
**Current:**
```javascript
var dbi  = ee.Image("projects/ee-gracebea/assets/Nigeria_DBI_2018").select([0]).rename('dbi');
```

**Problem:** Using Nigeria DBI raster for Mali analysis

**Fix:**
```javascript
var dbi  = ee.Image("projects/ee-gracebea/assets/Mali_DBI_2018").select([0]).rename('dbi');
```

---

### Issue 3: GHSL Scale Too Coarse (Line 306)
**Current:**
```javascript
var ghslDict = ghsl.reduceRegion({
  reducer: ee.Reducer.mean(),
  geometry: geom.buffer(2000),
  scale: 1000,  // ❌ 1km resolution
  maxPixels: 1e9
});
```

**Problem:** 1000m scale is too coarse, loses urban detail

**Fix:**
```javascript
scale: 30,  // Match DBI resolution
```

---

### Issue 4: GHSL Missing multiply(100) (Line 309)
**Current:**
```javascript
var ghslValue = safeGetNumber(ghslDict, 'ghsl');
```

**Problem:** Returns fraction (0-1) not percentage (0-100%)

**Evidence from data:**
- Actually shows values like "30.0" in CSV, not "0.30"
- This suggests Grace may have already applied multiply(100) OR the raster itself is scaled differently
- Need to verify

**Fix:**
```javascript
var ghslValue = safeGetNumber(ghslDict, 'ghsl').multiply(100);
```

---

### Issue 5: Wrong Country Filter for Points (Line 226)
**Current:**
```javascript
var nigeriaPoints = pointsRaw.filter(ee.Filter.eq('CountryName', 'Nigeria'));
```

**Problem:** Code is filtered for Nigeria but analyzing Mali

**Evidence from CSV:** Points are actually Mali (lat/lon match Mali geography)

**Likely explanation:** Grace changed the filter to 'Mali' when running, but the variable name is still `nigeriaPoints`

**Fix:**
```javascript
var maliPoints = pointsRaw.filter(ee.Filter.eq('CountryName', 'Mali'));
```

---

## Summary of Issues

| Issue | Line | Severity | Impact on Results |
|-------|------|----------|-------------------|
| Nigeria GHSL for Mali | 239 | **CRITICAL** | Wrong geography → Wrong results |
| Nigeria DBI for Mali | 240 | **CRITICAL** | Wrong geography → Wrong results |
| GHSL scale 1000m | 306 | High | Loses detail |
| GHSL missing ×100 | 309 | Medium | Wrong units (if not fixed) |
| Variable name confusion | 226 | Low | Code clarity only |

---

## Current Results from Mali CSV

**Urban Bamako area (MODIS > 50%):**
- MODIS: 85.3% ✓
- GHSL: 29.7% ❌ (capped, wrong geography)
- DBI: 35.5% ⚠️ (might be wrong geography too)

**Expected after fixes:**
- MODIS: 85.3% (unchanged)
- GHSL: Should be 60-80% (if Mali raster is correct)
- DBI: Should be closer to GHSL/MODIS

---

## Next Steps

1. **Verify Grace has Mali rasters available:**
   - Does `projects/ee-gracebea/assets/Mali_GHSL_2018` exist?
   - Does `projects/ee-gracebea/assets/Mali_DBI_2018` exist?

2. **Create corrected script** with all fixes

3. **Run corrected script for Mali**

4. **Compare results:**
   - Old: MODIS=85%, GHSL=30%, DBI=35%
   - New: MODIS=85%, GHSL=??, DBI=??

5. **If GHSL/DBI still disagree with MODIS after fixes:**
   - Then we have a real methodological issue to investigate
   - Otherwise, issue was just wrong geography
