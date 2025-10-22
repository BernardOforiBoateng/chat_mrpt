# Task Summary: Bernard's Assignment

**Date:** October 8, 2025

---

## What You're Being Asked to Do

**From Speaker 2 (Line 69):**
> "Take Grace's code and just run it for Delta State. If you get the same result, then we know we're on the right track. If you get a completely different result, then you know something's wrong."

---

## The Situation

### Grace's Problem:
- She ran DBI analysis for Nigeria
- She's getting DBI values **between 0 and 1** (fractions)
- She suspects these might need to be multiplied by 100

### Speaker 2's Memory:
- Remembers YOU had DBI values **"above 1"** in your Delta State report
- Wants to confirm if that's true
- If true → Grace's method might be wrong
- If false → Maybe your method was wrong

### Your Actual Results (Verified):
✅ **You DID have values above 1**

From your Delta State validation (`validation_delta_state_urban_validation_2025-09-04.csv`):
- **143 wards (53.6%)** had DBI > 1%
- Range: 0% to 47.96%
- Mean: 5.44%
- Examples:
  - Issele-Uku 1: 1.58%
  - Agiadiasi: 0.90%
  - Highest ward: 47.96%

---

## Your Assignment

### What to Do:

1. **Take Grace's GEE script** (lines 91-205 in contxt.md)

2. **Modify it to run ONLY for Delta State** instead of all 15 countries

3. **Run Grace's script** and see what DBI values you get

4. **Compare results:**
   - If you get values 0-47% (like your original) → Grace's method is correct, she just needs to check her buffer calculation (line 7)
   - If you get values 0-1 (like Grace got) → Then there's something different between the two methods

5. **Report back** to Speaker 2 and Grace with findings

---

## The Key Difference Between the Two Codes

### Grace's Code (lines 91-205):
- Calculates DBI raster
- Exports as **image/raster file**
- She then uses a **SEPARATE script** (line 7) to calculate percentages within 2km buffer of cluster points
- The 0-1 values might be coming from that second buffer calculation script (NOT shown in contxt.md)

### Your Code (lines 208-637):
- Calculates DBI raster
- **Immediately aggregates** to ward-level using `calculateUrbanPercentage()` function
- Exports as **CSV with percentages**
- All in one script

---

## What Grace Actually Said (Line 7):

> "I realized the code I sent you was just to get the DBI rasters. **I used THIS CODE to calculate the percentages urban within 2km buffer** of each cluster point using the three methods rasters. So this produces the final low DBI values that I sent."

**Important:** Grace has a SECOND script (not shown) that:
1. Takes the DBI raster from the first script
2. Buffers each cluster point by 2km
3. Calculates % urban within that buffer
4. That's where she's getting 0-1 values

---

## Possible Outcomes

### Outcome 1: Grace's Raster is Correct (Most Likely)
- When you run Grace's script for Delta State, you get a raster with DBI values
- If you aggregate it by wards (like your original code), you'd get 0-47% range
- The 0-1 values Grace is seeing are from her **buffer calculation script**, not the raster creation script
- **Action:** Ask Grace to share her buffer calculation script to debug that

### Outcome 2: Grace's Raster Calculation is Wrong
- When you run Grace's script for Delta State, the exported raster itself is wrong
- **Action:** Compare the two DBI calculation methods line-by-line

### Outcome 3: Your Original Method Was Wrong
- Unlikely, since your results (5.44% mean for Delta) align with expectations
- Delta State is known to be mostly rural, so low DBI makes sense
- Your correlation with MODIS (r=0.839) validates your approach

---

## The Real Question Being Asked

**Is Grace's DBI calculation methodology correct?**

To answer this, you need to:
1. Run her exact code for Delta State
2. Export the raster
3. Aggregate it by wards (using your calculateUrbanPercentage method)
4. Compare to your original ward-level percentages

If they match → Her raster creation is fine, the issue is in her buffer script
If they don't match → There's a difference in the DBI calculation itself

---

## What You Should Do Next

### Step 1: Modify Grace's Script for Delta State

Change line 102-118 to:
```javascript
var countryConfigs = [
  {name: 'Nigeria', year: 2018}  // Keep Nigeria, we'll filter to Delta later
];
```

Add after line 128:
```javascript
// Filter to Delta State only
var deltaGeometry = ee.FeatureCollection("FAO/GAUL_SIMPLIFIED_500m/2015/level1")
  .filter(ee.Filter.eq('ADM1_NAME', 'Delta'))
  .geometry();
```

Change line 186 to use deltaGeometry instead of full country.

### Step 2: Run It

Export the DBI raster for Delta State using Grace's method.

### Step 3: Check the Raster Values

In GEE, after the raster is created, print some statistics:
```javascript
var dbiStats = builtUpMask.reduceRegion({
  reducer: ee.Reducer.mean(),
  geometry: deltaGeometry,
  scale: 30,
  maxPixels: 1e13
});
print('Mean DBI (should be binary 0 or 1):', dbiStats);
```

**Expected:** Should be around 0.05-0.10 (meaning 5-10% of pixels are urban)

### Step 4: Aggregate by Wards (Optional)

If you want to directly compare to your results, load your ward boundaries and aggregate:
```javascript
var wards = ee.FeatureCollection('your/ward/boundaries');
var deltaWards = wards.filter(ee.Filter.eq('StateName', 'Delta'));

var wardStats = deltaWards.map(function(ward) {
  var wardGeom = ward.geometry();

  // Your calculateUrbanPercentage function here
  var dbiPercent = calculateUrbanPercentage(
    builtUpMask, wardGeom, 30, 'dbi_urban'
  );

  return ward.set('dbi_percent', dbiPercent);
});

Export.table.toDrive({
  collection: wardStats,
  description: 'Grace_Method_Delta_Validation',
  fileFormat: 'CSV'
});
```

### Step 5: Compare

Compare the CSV from Grace's method to your original CSV:
- Are the DBI values similar (within 5%)?
- If yes → Grace's raster method is correct
- If no → Identify the difference

---

## Bottom Line

**You need to determine: Is there a difference between Grace's DBI raster calculation and yours?**

The fastest way:
1. Run Grace's script for Delta State
2. Check if the exported raster makes sense
3. Optionally aggregate by wards to directly compare to your results
4. Report back what you find

**Don't assume Grace is wrong or you are wrong. Just test and report the facts.**
