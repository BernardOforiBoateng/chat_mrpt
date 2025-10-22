# Slack Message to Team

---

**@Speaker2 @Grace**

## Update: Grace's DBI Investigation

I ran Grace's code for Delta State as requested. **Good news—Grace's methodology is correct!** Found the issue.

### What I Found:

**Grace's DBI raster:** ✅ Correct
- Tested for Delta State 2018: **3.32% urban**
- My original Delta 2023: **5.44% urban**
- The 2% difference is just 5 years of urbanization growth—totally reasonable

**The bug:** Lines 93 & 102 in Grace's buffer script need `.multiply(100)`

### The Issue:
Grace's DBI/GHSL values are **fractions** (0-1), not **percentages** (0-100%). When you take the mean of binary pixels (0 or 1), you get fractions.

**Example:** A cluster that's 5.4% urban shows as `0.054` instead of `5.4`

### The Fix:
```javascript
// Line 93 - change from:
var ghslValue = safeGetNumber(ghslDict, 'ghsl');
// To:
var ghslValue = safeGetNumber(ghslDict, 'ghsl').multiply(100);

// Line 102 - change from:
var dbiValue = safeGetNumber(dbiDict, 'dbi');
// To:
var dbiValue = safeGetNumber(dbiDict, 'dbi').multiply(100);
```

### Why MODIS Works:
Grace's MODIS function already multiplies by 100 (line 57). She just needs to do the same for DBI/GHSL.

### Grace's Intuition:
> "maybe they need to be multiplied by 100?"

**You were exactly right, Grace!** 💯

### Validation:
@Speaker2 you were correct—my Delta State analysis **did** have values above 1 (when expressed as %). 143 wards out of 267 had DBI > 1%, ranging up to 47.96%.

---

**TL;DR:** Grace's rasters are fine. Just add `.multiply(100)` in two places. 5-minute fix.

Let me know if you want me to share the detailed test results or help with anything else!
