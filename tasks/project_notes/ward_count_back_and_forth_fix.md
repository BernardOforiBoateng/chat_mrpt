# Ward Count Back-and-Forth Fix

## Date: 2025-08-04

### The Real Problem
After multiple attempts, the core issue was my attempted "fix" that split ward aggregation into two groups (with and without WardCodes). This created duplicate entries when the same ward had some facilities with WardCodes and some without.

### What Was Happening
1. **Initial State**: System showing 234 wards (8 duplicates due to enhanced matcher)
2. **After First Fix**: System showing 223 wards (3 missing due to over-aggressive deduplication)  
3. **After Second Fix**: Back to 234 wards (duplicates returned due to split aggregation)

### Root Cause Analysis
The split aggregation approach failed because:
- Some wards have facilities WITH WardCodes and some WITHOUT
- Aggregating them separately created two entries for the same ward
- Concatenating the results led to duplicates

Example:
- Ward "Ribadu" has 5 facilities
- 3 facilities have WardCode "ADSFUR08"
- 2 facilities have null WardCode
- Split aggregation created 2 rows for the same ward

### Final Solution
Reverted to simple, unified aggregation:

```python
# ALWAYS group by LGA and Ward (the natural unique key)
groupby_cols = ['LGA', 'Ward']

# Keep WardCode if available (as first value)
if 'WardCode' in facility_data.columns:
    first_cols['WardCode'] = 'first'
```

This ensures:
1. **One row per ward**: LGA+Ward combination is unique
2. **WardCode preserved**: First non-null WardCode is kept
3. **No duplicates**: Single aggregation pass prevents duplicate creation

### Additional Safety
Added deduplication after enhanced matcher runs:
```python
# Check for duplicates after enhanced matching
if 'WardCode' in merged.columns and merged['WardCode'].notna().any():
    duplicates = merged['WardCode'].duplicated()
    if duplicates.any():
        merged = merged.drop_duplicates(subset=['WardCode'], keep='first')
```

### Key Lesson
**Keep It Simple**: Complex split-and-merge logic often creates more problems than it solves. The original aggregation by LGA+Ward was correct and should have been preserved.

### Testing Verification
The fix maintains:
- Correct ward count (226 for Adamawa)
- All WardCodes preserved
- No duplicate entries
- Proper matching with shapefile