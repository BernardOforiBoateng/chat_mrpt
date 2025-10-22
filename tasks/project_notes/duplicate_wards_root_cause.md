# Duplicate Wards Root Cause Analysis

## Date: 2025-08-04

### The Missing Wards Mystery

#### What's Being Removed
The system is showing 223 wards instead of 226 for Adamawa State. Analysis revealed:

**4 Duplicate Ward Entries:**
1. **Fufore LGA**: "Ribadu" appears twice with identical TPR values (77.9%)
2. **Lamurde LGA**: "Lamurde (Lamurde)" appears twice with identical TPR values (61.0%)
3. **Mubi South LGA**: "Nasarawo" appears twice with identical TPR values (72.5%)
4. **Yola North LGA**: "Yelwa" appears twice with identical TPR values (73.2%)

**The Math:**
- TPR output has 223 data rows
- But 4 wards appear twice (4 duplicates)
- Actual unique wards = 219
- Missing wards = 226 - 219 = **7 wards are completely missing**

### Root Causes Identified

#### 1. Duplicate Creation During Aggregation
The groupby operation on ['LGA', 'Ward'] is somehow creating duplicate rows for certain wards. Possible reasons:
- Invisible characters or whitespace differences in ward names
- Multiple facilities with slightly different ward name spellings
- Data entry inconsistencies in the original NMEP data

#### 2. Enhanced Matcher Over-Matching
The enhanced ward matcher might be mapping multiple different ward names to the same output ward, causing duplicates when merging with shapefile.

#### 3. Deduplication Removing Valid Wards
When we deduplicate based on WardCode, wards with null WardCodes might be incorrectly removed, causing the count to drop.

### Fixes Applied

#### Fix 1: Add Deduplication After Aggregation
```python
# Remove duplicate LGA+Ward combinations after aggregation
ward_data = ward_data.drop_duplicates(subset=['LGA', 'Ward'], keep='first')
```

#### Fix 2: Improve Deduplication Logic for Null WardCodes
```python
# Only deduplicate among rows WITH WardCodes
# Keep rows without WardCode intact
has_wardcode = merged['WardCode'].notna()
if has_wardcode.any():
    # Only check duplicates among rows with WardCodes
    merged_with_code = merged[has_wardcode].copy()
    # Remove only the duplicate WardCode entries
```

#### Fix 3: Enhanced Logging
Added detailed logging to track:
- Unique ward combinations before aggregation
- Ward count after aggregation
- Null WardCode count
- Duplicate detection after merging

### The Complete Picture
The issue is a combination of:
1. **Data quality issues** in the NMEP source data (duplicate ward entries)
2. **Aggregation logic** not handling these duplicates properly
3. **Over-aggressive deduplication** removing valid wards with null WardCodes

### Verification Needed
After these fixes, the system should:
1. Output exactly 226 unique wards for Adamawa
2. No duplicate LGA+Ward combinations
3. All wards with and without WardCodes preserved
4. Clean TPR analysis results for risk assessment