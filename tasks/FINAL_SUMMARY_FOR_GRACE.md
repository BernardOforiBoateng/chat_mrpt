# Mali Urban Analysis - Final Summary for Grace

**Date:** October 8, 2025
**Question:** "Why is urban southwest Mali showing very low urbanicity in DBI?"

---

## Quick Answer

You identified **TWO separate issues**:

1. ✅ **GHSL capped at 30%** → Geography bug (Nigeria rasters used for Mali) - **FIXED**
2. ⚠️ **DBI shows low values (~35%)** → DBI doesn't work well in non-arid regions - **CONFIRMED, NOT FIXED**

---

## Issue #1: GHSL Geography Bug

### The Problem
```
Your code (context.md):
Line 239: var ghsl = ee.Image("projects/ee-gracebea/assets/Nigeria_GHSL_2018");
Line 240: var dbi = ee.Image("projects/ee-gracebea/assets/Nigeria_DBI_2018");

Used for Mali analysis! ❌
```

### Evidence
| Location | Your GHSL | Corrected GHSL | Difference |
|----------|-----------|----------------|------------|
| Urban Bamako (45 pts) | 29.7% (capped) | 99.3% | **+69.6%** |
| All Mali (345 pts) | 15.1% | 26.6% | **+11.5%** |

**GHSL Max Values:**
- Your result: 30.0% (capped) ❌
- Corrected: 100.0% ✓

### The Fix
Use Mali-specific or global GHSL:
```javascript
// Option 1: Mali-specific (if it exists)
var ghsl = ee.Image("projects/ee-gracebea/assets/Mali_GHSL_2018");

// Option 2: Global dataset (recommended)
var ghsl = ee.Image('JRC/GHSL/P2023A/GHS_SMOD/2020').select('smod_code');
var ghslUrban = ghsl.gte(21).and(ghsl.lte(30));
```

Also:
- Change scale from 1000m → 30m (line 306)
- Add `.multiply(100)` to GHSL (line 309)

---

## Issue #2: DBI Low in Non-Arid Regions

### The Problem
DBI shows **~35% urban** for Bamako, but MODIS/GHSL show **85-99% urban**.

### Evidence - Non-Arid Southwest Mali (86 points)

| Method | Grace (Original) | Bernard (Corrected) | Agreement with Urban Reality |
|--------|------------------|---------------------|------------------------------|
| **MODIS** | 52.7% | 49.0% | ✓ Moderate |
| **GHSL** | 23.6% (wrong) | 62.7% (fixed) | ✓ High |
| **DBI** | 28.4% | 27.2% | ❌ TOO LOW |

### Evidence - Urban Bamako Core (45 points, MODIS > 50%)

| Method | Percentage | Assessment |
|--------|------------|------------|
| **MODIS** | 85-87% | ✓ High urban (reference) |
| **GHSL (fixed)** | 99% | ✓ Agrees with MODIS |
| **DBI** | 35-36% | ❌ Underestimates by ~50% |

### Why DBI Fails in Non-Arid Regions

**DBI Formula:** DBI = NDBI - NDVI

**The issue:**
1. Bamako is **non-arid** (blue dots in your aridity map)
2. Non-arid urban areas have **vegetation** (trees, parks, gardens)
3. Vegetation → **high NDVI**
4. DBI = NDBI - **high NDVI** → **low DBI**
5. The NDVI subtraction **penalizes** vegetated urban areas

**Design intent:** DBI (Rasul et al. 2018) was designed for **arid regions** where vegetation is sparse.

### Correlation Analysis

Correlation with MODIS urban %:
- **GHSL:** r = 0.867 ✓ Strong correlation
- **DBI:** r = 0.189 ❌ Weak correlation

DBI doesn't capture Mali's urban patterns well.

---

## Visual Evidence

### Your Maps (b.png and bb.png)
- **b.png:** Shows southwest Mali is **non-arid** (blue dots)
- **bb.png:** Shows same region has **low DBI** (dark blue/purple, 0-30%)

### Our Comparison Maps
1. **mali_grace_style_comparison.png:**
   - 4-panel comparison: Grace vs Bernard
   - Shows DBI stays low even with corrections
   - Shows GHSL fix (from 30% → 99%)

2. **bernard_dbi_map_grace_style.png:**
   - Matches your bb.png style exactly
   - Confirms low DBI persists in southwest Mali

3. **bernard_ghsl_map_fixed.png:**
   - Shows GHSL now properly detects urban areas
   - Urban Bamako: bright green (90-100%)

---

## Recommendations

### For Your Analysis

| Region | Recommended Method | Why |
|--------|-------------------|-----|
| **Non-arid southwest Mali** | GHSL or MODIS | DBI underestimates by ~50% |
| **Arid northern Mali** | DBI works as designed | Low vegetation, DBI accurate |

### Next Steps

1. **Fix GHSL geography (critical):**
   ```
   - Check if Mali_GHSL_2018 exists in your assets
   - If not, create it using your DBI creation script
   - Or use global GHSL: JRC/GHSL/P2023A/GHS_SMOD/2020
   - Apply scale and multiply fixes
   ```

2. **For DBI in non-arid regions (optional):**
   ```
   Consider using NDBI alone (without subtracting NDVI):
   var ndbi = composite.normalizedDifference(['B11', 'B8']);
   var urbanMask = ndbi.gt(0.1);  // Adjust threshold as needed
   ```

3. **Re-run analysis:**
   ```
   - Use corrected script (grace_code_CORRECTED.js)
   - Export new CSV: Mali_points_CORRECTED
   - Verify GHSL max > 30%
   - Compare DBI with GHSL/MODIS for validation
   ```

---

## Files for You

### Evidence Files
- `Bernard_Mali_Test.csv` - Corrected analysis results (345 points)
- `mali_grace_style_comparison.png` - 4-panel visual comparison
- `bernard_dbi_map_grace_style.png` - Matches your bb.png style
- `mali_comparison_charts.png` - Statistical evidence
- `mali_analysis_final_map.html` - Interactive map

### Scripts
- `bernard_test_mali.js` - Full test script with all corrections
- `grace_code_CORRECTED.js` - Your buffer script with fixes applied
- `export_mali_shapefile.js` - Export Mali boundary from FAO GAUL

### Documentation
- `MALI_FINAL_REPORT.md` - Complete technical analysis
- `dbi_analysis_summary.txt` - Detailed DBI findings
- `RESPONSE_TO_GRACE_FINAL.txt` - Concise message

---

## Bottom Line

**Your instinct was 100% correct:** Urban southwest Mali (Bamako) should NOT show low urbanicity.

**Root causes identified:**
1. ✅ **GHSL issue:** Wrong geography (Nigeria raster) - **You can fix this**
2. ⚠️ **DBI limitation:** Doesn't work in non-arid regions - **Use GHSL/MODIS instead**

**Action items:**
1. Fix GHSL geography bug (lines 239-240)
2. Use GHSL or MODIS for non-arid southwest Mali
3. Use DBI for arid northern Mali (where it works)

Let me know if you need help creating Mali-specific rasters or have questions!

— Bernard
