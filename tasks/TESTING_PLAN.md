# Testing Plan for Grace's Corrected Code

**Date:** October 8, 2025

---

## Issues Identified

Based on analysis of `Mali_points_modis_buffer.csv`:

1. **GHSL capped at 30%** - Indicates wrong geography (Nigeria raster used for Mali)
2. **DBI might be wrong geography too** - Using Nigeria_DBI_2018 for Mali points
3. **GHSL scale too coarse** - 1000m loses urban detail
4. **GHSL missing multiply(100)** - But data shows percentages, so unclear if already fixed

---

## Hypothesis

**If we fix the code, GHSL and DBI should align better with MODIS in urban areas.**

**Current (wrong):**
- Urban Bamako: MODIS=85%, GHSL=30% (capped), DBI=35%

**Expected (corrected):**
- Urban Bamako: MODIS=85%, GHSL=65-80%, DBI=60-75%

---

## Testing Steps

### Step 1: Verify Mali Rasters Exist

Grace needs to check if these assets exist:
- `projects/ee-gracebea/assets/Mali_GHSL_2018`
- `projects/ee-gracebea/assets/Mali_DBI_2018`

**If they DON'T exist:**
- Grace needs to create them first using her DBI raster creation script (lines 10-204 in contxt.md)
- Run for Mali, not Nigeria

**If they DO exist:**
- Proceed to Step 2

---

### Step 2: Run Corrected Code

1. Open `tasks/grace_code_CORRECTED.js` in GEE
2. Verify asset paths are correct (lines 32-33)
3. Click **Run**
4. Check console for validation messages:
   - GHSL max should be > 30% (not capped)
   - Sample values should look reasonable
5. Go to **Tasks** tab
6. Run export: `Mali_points_CORRECTED`
7. Download CSV from Google Drive

---

### Step 3: Compare Results

Compare old vs new CSV:

**Key metrics to check (for urban Bamako points, lat ~12.6, lon ~-8.0, MODIS > 50%):**

| Metric | Old (Wrong) | New (Fixed) | Status |
|--------|-------------|-------------|--------|
| GHSL max | 30.0% | Should be 70-90% | If still 30%, Mali raster missing |
| GHSL mean (urban) | 29.7% | Should be 65-80% | Should increase significantly |
| DBI mean (urban) | 35.5% | Should be 60-75% | Should increase to match GHSL/MODIS |
| MODIS mean (urban) | 85.3% | ~85% (same) | Should not change |

---

### Step 4: Analysis Script

Run this Python script to compare:

```python
import pandas as pd

# Load both CSVs
old = pd.read_csv('Mali_points_modis_buffer.csv')
new = pd.read_csv('Mali_points_CORRECTED.csv')

# Filter to urban Bamako area
bamako_old = old[(old['lat'] >= 11.6) & (old['lat'] <= 13.6) &
                  (old['long'] >= -9) & (old['long'] <= -7) &
                  (old['modis_urban_percent'] > 50)]

bamako_new = new[(new['lat'] >= 11.6) & (new['lat'] <= 13.6) &
                  (new['long'] >= -9) & (new['long'] <= -7) &
                  (new['modis_urban_percent'] > 50)]

print("URBAN BAMAKO COMPARISON")
print("="*60)
print(f"\nOLD (Wrong Geography):")
print(f"  MODIS: {bamako_old['modis_urban_percent'].mean():.1f}%")
print(f"  GHSL:  {bamako_old['GHSL_pct'].mean():.1f}% (max: {bamako_old['GHSL_pct'].max():.1f}%)")
print(f"  DBI:   {bamako_old['DBI_pct'].mean():.1f}%")

print(f"\nNEW (Fixed):")
print(f"  MODIS: {bamako_new['modis_urban_percent'].mean():.1f}%")
print(f"  GHSL:  {bamako_new['GHSL_pct'].mean():.1f}% (max: {bamako_new['GHSL_pct'].max():.1f}%)")
print(f"  DBI:   {bamako_new['DBI_pct'].mean():.1f}%")

print(f"\nCHANGES:")
print(f"  GHSL: {bamako_new['GHSL_pct'].mean() - bamako_old['GHSL_pct'].mean():+.1f}%")
print(f"  DBI:  {bamako_new['DBI_pct'].mean() - bamako_old['DBI_pct'].mean():+.1f}%")

# Check if GHSL is still capped
if bamako_new['GHSL_pct'].max() <= 30.1:
    print("\n⚠️  GHSL still capped at 30% - Mali raster is missing or wrong!")
else:
    print("\n✓ GHSL no longer capped - Fix worked!")
```

---

### Step 5: Interpret Results

**Scenario A: GHSL still capped at 30%**
- Mali raster doesn't exist or is also Nigeria data
- Grace needs to create proper Mali GHSL raster first

**Scenario B: GHSL now 65-80%, DBI now 60-75%**
- ✓ Fix worked!
- All three methods now agree
- Issue was wrong geography

**Scenario C: GHSL fixed but DBI still low (35%)**
- GHSL raster was wrong, now fixed
- DBI raster might still be wrong (Nigeria data)
- Or DBI methodology issue (less likely)

---

## What to Tell Grace Now

**Message to Grace:**

"I analyzed your Mali CSV. The issue is you're using **Nigeria rasters for Mali analysis**:
- Line 239: `Nigeria_GHSL_2018` for Mali points
- Line 240: `Nigeria_DBI_2018` for Mali points

This is why GHSL is capped at 30% and doesn't match Bamako's actual urbanicity.

**Before we can test if DBI methodology is correct, you need to:**

1. Create Mali GHSL and DBI rasters (or verify they exist)
2. Run the corrected script I've prepared: `tasks/grace_code_CORRECTED.js`
3. Share the new CSV so we can compare

**Specific fixes in the corrected script:**
- Use Mali rasters (not Nigeria)
- GHSL scale: 1000 → 30m
- GHSL multiply by 100
- All documented in `tasks/grace_code_issues_documented.md`

Can you check if `Mali_GHSL_2018` and `Mali_DBI_2018` exist in your assets? If not, we need to create them first."

---

## Expected Timeline

1. **Grace verifies/creates Mali rasters:** 1-2 hours
2. **Run corrected script:** 10-15 minutes
3. **Export and download:** 10 minutes
4. **Compare results:** 5 minutes
5. **Final diagnosis:** 10 minutes

**Total:** ~2-3 hours to get definitive answer

---

## Success Criteria

✓ GHSL max > 30% (not capped)
✓ GHSL in urban Bamako: 65-80%
✓ DBI in urban Bamako: 60-75%
✓ All three methods (MODIS, GHSL, DBI) agree within 20% for urban areas
