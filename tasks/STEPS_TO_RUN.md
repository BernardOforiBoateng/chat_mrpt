# How to Test Grace's Code - Step by Step

**Goal:** Run Grace's DBI script for Delta State and compare to your original results

---

## Step 1: Open Google Earth Engine

1. Go to https://code.earthengine.google.com/
2. Log in with your account

---

## Step 2: Copy the Test Script

1. Open the file I created: `tasks/grace_code_delta_test.js`
2. Copy ALL the code
3. Paste it into a new GEE script
4. Save the script as "Grace_Delta_Test"

---

## Step 3: Run the Script

1. Click the **Run** button
2. Wait for processing (should take 1-2 minutes)
3. Look at the **Console** panel on the right side

---

## Step 4: Check the Console Output

You should see output like this:

```
===== Processing: Delta_State (2018) =====
Number of Sentinel-2 images found for Delta_State 2018: [some number]

===== VALIDATION CHECKS =====
Pixel Statistics (Binary Mask):
  Mean (fraction urban): 0.054
  Min: 1
  Max: 1

Area Statistics:
  Total Delta State area (km²): 17,698
  Total urban area (km²): 956
  Urban percentage: 5.4%

EXPECTED (from Bernard's original):
  Urban percentage should be ~5-6% for whole state
```

---

## Step 5: Interpret the Results

### Good Sign ✅:
- Urban percentage is around **5-6%** (matches your original mean of 5.44%)
- Pixel mean is around **0.05-0.06** (which is 5-6% as fraction)

### Bad Sign ❌:
- Urban percentage is way off (like 0.5% or 50%)
- Numbers don't make sense

---

## Step 6: Export and Compare

1. Go to the **Tasks** tab (top right, next to Console)
2. You should see a task: "Delta_State_DBI_2018_Grace_Method"
3. Click **Run** next to it
4. Accept the defaults and click **Run** again
5. Wait for export to complete (check your email for notification)
6. Download from Google Drive → DBI_exports folder

---

## Step 7: Optional - Ward-Level Comparison

**If you want to directly compare ward-by-ward:**

1. Find where your ward boundaries are stored in GEE
   - Check your Assets panel (left side)
   - Look for "nigeria_wards" or similar

2. In the script, find this line (around line 124):
   ```javascript
   var wards = ee.FeatureCollection('users/YOUR_USERNAME/nigeria_wards');
   ```

3. Replace `YOUR_USERNAME` with your actual GEE username

4. Uncomment the entire section (remove the `/*` at line 123 and `*/` at line 195)

5. Run the script again

6. This will create a second export task with ward-level percentages

7. Download and compare to your original CSV

---

## What to Report Back

After running this, you should be able to answer:

### Question 1: Does Grace's raster method produce correct values?
- **YES if:** Urban percentage ~5-6% for Delta State
- **NO if:** Wildly different percentage

### Question 2: Do ward-level percentages match your original?
- Compare mean, range, and specific wards
- Differences <5% are acceptable (different years: 2018 vs 2023)
- Differences >10% suggest methodological issue

### Question 3: Where is Grace's 0-1 problem coming from?
- **If raster is correct:** Problem is in her buffer calculation script (not shown)
- **If raster is wrong:** Problem is in the raster creation method

---

## Troubleshooting

### Error: "Collection contains no features"
- The Delta State filter didn't work
- Try: `print(deltaState)` to see what's loaded
- May need to adjust filter name (ADM1_NAME vs StateName)

### Error: "User memory limit exceeded"
- The area is too large
- Add `tileScale: 4` to reduceRegion calls
- Or reduce the `maxPixels` value

### Export takes forever
- This is normal for large areas
- Can take 10-30 minutes for Delta State
- You'll get email when done

### Can't find ward boundaries
- You may not have them as a GEE asset
- That's fine - just run without ward comparison
- The state-level statistics are enough to validate

---

## Quick Answer Path (No Ward Comparison)

**Fastest way to answer Speaker 2's question:**

1. Run the script
2. Look at console output
3. Check: "Urban percentage: X%"
4. Compare to your original mean: 5.44%
5. If close → Grace's method is correct ✅
6. If different → Grace's method has issue ❌

**That's it!** You can report back based on that single number.

---

## What to Tell Speaker 2 and Grace

### If values match (~5.4%):
> "I ran Grace's code for Delta State and got X% urban, which matches my original 5.44%. Grace's DBI raster creation method is correct. The 0-1 values she's seeing must be coming from her buffer calculation script (the second script she mentioned). We need to see that script to debug the issue."

### If values don't match:
> "I ran Grace's code for Delta State and got X% urban, but my original was 5.44%. There's a difference of Y%. Let me investigate where the methodological difference is."

---

## Need Help?

If you get stuck at any step, let me know and I'll help troubleshoot!
