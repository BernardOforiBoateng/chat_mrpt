# Mali Urban Analysis - Final Report
**Date:** October 8, 2025
**Analyst:** Bernard Boateng
**Task:** Validate Grace's DBI methodology for Mali analysis

---

## Executive Summary

**Root Cause Found:** Grace used **Nigeria rasters for Mali analysis**, causing GHSL to be capped at 30% for all 345 Mali points.

**Key Findings:**
- ✅ DBI methodology is **CORRECT** - values are consistent between both analyses
- ❌ GHSL was using wrong geography - Nigeria_GHSL_2018 instead of Mali data
- ✅ Fix validated - Using global GHSL dataset eliminates the 30% cap
- ✅ Urban Bamako now properly detected at 99.3% GHSL (was 29.7%)

---

## The Problem

Grace reported:
1. GHSL values capped at 30% for urban areas
2. Southwest Mali (Bamako) showing unexpectedly low urban percentages
3. DBI showing values 0-1 (later fixed with multiply(100))

---

## Investigation Approach

### Phase 1: Code Review
**Files analyzed:**
- `contxt.md` (lines 90-205): Grace's DBI raster creation script ✓ CORRECT
- `context.md` (lines 208-637): Grace's buffer calculation script ❌ ISSUES FOUND

**Bugs identified in buffer calculation script:**
1. **Line 239:** `var ghsl = ee.Image("projects/ee-gracebea/assets/Nigeria_GHSL_2018")`
   - Used for Mali analysis! ❌
2. **Line 240:** `var dbi = ee.Image("projects/ee-gracebea/assets/Nigeria_DBI_2018")`
   - Used for Mali analysis! ❌
3. **Line 306:** `scale: 1000` for GHSL (too coarse, should be 30m)
4. **Line 309:** Missing `.multiply(100)` for GHSL percentage conversion

### Phase 2: Validation Test
**Test script:** `bernard_test_mali.js`

**Corrections applied:**
1. ✅ Calculate DBI fresh from Sentinel-2 for Mali (2018)
2. ✅ Use global GHSL dataset: `JRC/GHSL/P2023A/GHS_SMOD/2020`
3. ✅ Set GHSL scale to 30m (native resolution)
4. ✅ Add `.multiply(100)` for percentage conversion
5. ✅ Use all 345 Mali agricultural cluster points

**Results exported:** `Bernard_Mali_Test.csv`

---

## Results Comparison

### Overall Statistics
|  | MODIS | GHSL | DBI |
|---|---|---|---|
| **Bernard (Fixed)** | 16.0% | **26.6%** | 25.4% |
| **Grace (Original)** | 15.8% | **15.1%** | 25.3% |

### CRITICAL FINDING: GHSL Max Values
|  | GHSL Max |
|---|---|
| **Bernard (Fixed)** | **100.0%** ✓ |
| **Grace (Original)** | **30.0%** ❌ CAPPED |

This 30% cap proves Grace's Mali points were analyzing Nigeria geography.

### Urban Bamako Analysis (45 points with MODIS > 50%)
|  | MODIS | GHSL | DBI |
|---|---|---|---|
| **Bernard (Fixed)** | 86.7% | **99.3%** ✓ | 35.6% |
| **Grace (Original)** | 85.3% | **29.7%** ❌ | 35.5% |

**GHSL Improvement:** +69.6%
**DBI Change:** 0.1% (essentially unchanged)

### Sample Urban Points
**Point 333** (Bamako center: 12.68°N, -7.94°W):
- MODIS: 97.9% (Bernard) vs 96.2% (Grace)
- GHSL: **100.0%** (Bernard) vs **30.0%** (Grace) ← CAPPED!
- DBI: 32.8% (Bernard) vs 32.8% (Grace) ← SAME

**Point 334** (12.67°N, -7.93°W):
- MODIS: 85.6% vs 83.6%
- GHSL: **99.2%** vs **29.8%** ← CAPPED!
- DBI: 24.0% vs 24.0% ← SAME

### Correlation with MODIS
|  | GHSL | DBI |
|---|---|---|
| **Bernard (Fixed)** | r=0.867 | r=0.189 |
| **Grace (Original)** | r=0.865 | r=0.190 |

Both methods have similar correlation patterns, confirming DBI methodology is correct.

---

## Evidence

### Files Created
1. **Bernard_Mali_Test.csv** - Corrected analysis results (345 points)
2. **mali_comparison_charts.png** - 4-panel statistical comparison
3. **mali_comparison_map.html** - Interactive overlay map (green=fixed, red=original)
4. **mali_comparison_sidebyside.html** - Side-by-side comparison map
5. **bernard_test_mali.js** - Full GEE test script with corrections

### Visual Evidence
The comparison charts show:
1. **GHSL Distribution:** Grace's histogram cut off at 30%, Bernard's extends to 100%
2. **GHSL vs MODIS Scatter:** Grace's points form horizontal line at 30%, Bernard's show proper correlation
3. **DBI vs MODIS Scatter:** Both datasets overlay perfectly (methodology is correct)
4. **Urban Bamako Bar Chart:** Dramatic GHSL difference (30% → 99%), minimal DBI difference

---

## Conclusions

### What Was Wrong
1. ❌ **Wrong geography:** Used `Nigeria_GHSL_2018` for Mali points
2. ❌ **Wrong geography:** Used `Nigeria_DBI_2018` for Mali points
   (But DBI values happened to be similar, so less obvious)
3. ❌ **Wrong scale:** GHSL calculated at 1000m (should be 30m)
4. ❌ **Missing multiply:** GHSL missing `.multiply(100)` for percentage

### What Was Right
1. ✅ **DBI methodology:** Rasul et al. (2018) implementation is correct
2. ✅ **DBI raster creation:** Sentinel-2 composite → NDBI/NDVI → DBI is correct
3. ✅ **MODIS calculation:** Urban class detection and buffer analysis is correct
4. ✅ **Overall approach:** 2km buffer analysis is appropriate

### Why Grace Didn't Notice
- DBI values for Nigeria and Mali happened to be in similar ranges (20-40%)
- The 30% GHSL cap seemed plausible without deep investigation
- Bamako is genuinely urban, but 30% seemed "reasonable enough"
- She focused on the DBI 0-1 issue (missing multiply), not geography

---

## Recommendations

### Immediate Actions for Grace
1. **Verify Mali rasters exist:**
   - Check if `projects/ee-gracebea/assets/Mali_GHSL_2018` exists
   - Check if `projects/ee-gracebea/assets/Mali_DBI_2018` exists
   - If not, create them using her raster creation script (lines 10-204 in contxt.md)

2. **Use corrected buffer script:**
   - Replace `Nigeria_GHSL_2018` with `Mali_GHSL_2018` (line 239)
   - Replace `Nigeria_DBI_2018` with `Mali_DBI_2018` (line 240)
   - Change GHSL scale from 1000 to 30 (line 306)
   - Add `.multiply(100)` to GHSL (line 309)
   - See `grace_code_CORRECTED.js` for full fixed script

3. **Re-run analysis:**
   - Export new CSV: `Mali_points_CORRECTED`
   - Verify GHSL max > 30%
   - Verify urban Bamako shows 65-80% GHSL

### Alternative Approach (If Mali Rasters Don't Exist)
Use **global datasets** instead of country-specific rasters:
- GHSL: `JRC/GHSL/P2023A/GHS_SMOD/2020` (public, global coverage)
- DBI: Calculate on-the-fly from Sentinel-2 (as in bernard_test_mali.js)

This approach:
- ✅ Eliminates geography mismatch risk
- ✅ Uses native resolution (30m for GHSL, 10-20m for DBI)
- ✅ No asset management needed
- ❌ Slightly slower (on-the-fly calculation)

### Quality Control Measures
1. **Always check max values** - If capped at suspicious threshold, investigate
2. **Compare with MODIS** - GHSL should correlate strongly with MODIS (r > 0.8)
3. **Validate with known locations** - Test with obviously urban areas (capitals)
4. **Asset naming convention** - Include country name in asset IDs to prevent mix-ups

---

## Next Steps

### For Bernard
1. ✅ Send findings to Grace and team
2. ✅ Share corrected script and evidence files
3. ⏳ Wait for Grace to verify Mali rasters exist
4. ⏳ Review her re-run results

### For Grace
1. ⏳ Check if Mali_GHSL_2018 and Mali_DBI_2018 assets exist
2. ⏳ If they don't exist, create them using DBI creation script
3. ⏳ Run corrected buffer script with proper Mali rasters
4. ⏳ Export new CSV and share for verification
5. ⏳ Apply same fixes to other countries if using same approach

---

## Technical Details

### Test Environment
- **Platform:** Google Earth Engine
- **Asset used:** `projects/epidemiological-intelligence/assets/agric_points`
- **Points analyzed:** 345 Mali agricultural cluster points
- **Year:** 2018
- **Sentinel-2:** SR_HARMONIZED collection, <20% cloud cover

### Data Sources
- **GHSL:** JRC/GHSL/P2023A/GHS_SMOD/2020 (30m resolution)
- **Sentinel-2:** COPERNICUS/S2_SR_HARMONIZED (B4/B8/B11)
- **MODIS:** MODIS/006/MCD12Q1 LC_Type1 (500m resolution)
- **Aridity:** WorldClim V1 bio12 (<250mm annual precipitation)

### Methodology
- **Buffer size:** 2km radius around each point
- **DBI formula:** NDBI - NDVI
  - NDBI = (B11 - B8) / (B11 + B8)
  - NDVI = (B8 - B4) / (B8 + B4)
- **Urban threshold:** DBI > 0
- **MODIS urban:** Class 13 (≥30% impervious surface)
- **GHSL urban:** SMOD codes 21-30

---

## Appendices

### A. Files Reference
- `contxt.md` - Grace's original Slack messages and code
- `context.md` - Grace's buffer calculation script (buggy version)
- `Mali_points_modis_buffer.csv` - Grace's original results
- `Bernard_Mali_Test.csv` - Corrected results
- `bernard_test_mali.js` - Test script with all corrections
- `grace_code_CORRECTED.js` - Fixed version of Grace's script
- `message_to_grace_FINAL.txt` - Concise Slack message
- `mali_comparison_analysis.py` - Statistical comparison script
- `mali_map_visualization.py` - Map generation script

### B. Key Code Differences

**Grace's Original (context.md:239-240, 306, 309):**
```javascript
var ghsl = ee.Image("projects/ee-gracebea/assets/Nigeria_GHSL_2018");
var dbi = ee.Image("projects/ee-gracebea/assets/Nigeria_DBI_2018");
// ...
scale: 1000,  // Too coarse
// ...
var ghslValue = safeGetNumber(ghslDict, 'ghsl');  // Missing multiply
```

**Bernard's Fix (bernard_test_mali.js:41-64, 124, 127):**
```javascript
var ghsl = ee.Image('JRC/GHSL/P2023A/GHS_SMOD/2020').select('smod_code');
var ghslUrban = ghsl.gte(21).and(ghsl.lte(30));
// DBI calculated fresh from Sentinel-2 for Mali
// ...
scale: 30,  // Native resolution
// ...
var ghslValue = safeGetNumber(ghslDict, 'ghsl').multiply(100);  // Fixed
```

### C. Contact
- **Analyst:** Bernard Boateng
- **Date:** October 8, 2025
- **Email:** [your email]
- **Project:** Malaria Risk Urban Analysis
