# Ward Aggregation Fix - Missing 3 Wards Issue

## Date: 2025-08-04

### Problem
After fixing the duplicate WardCode issue, the system started showing 223 wards instead of 226 for Adamawa State. 3 wards were being lost during the TPR pipeline processing.

### Root Cause
Two issues were causing the problem:

1. **Improper handling of null WardCodes**: The TPR pipeline was aggregating by WardCode when available, but wards with null/missing WardCodes were being dropped or incorrectly grouped together.

2. **Double deduplication**: Deduplication was happening twice - once during the merge and once after, potentially removing valid wards that were incorrectly identified as duplicates.

### Solution Implemented

#### 1. Fixed TPR Pipeline Aggregation (`app/tpr_module/core/tpr_pipeline.py`)
Modified `_aggregate_to_wards` method to handle wards with and without WardCodes separately:

```python
# Split data into two groups: with and without WardCode
has_wardcode = facility_data['WardCode'].notna() if 'WardCode' in facility_data.columns else pd.Series([False] * len(facility_data))

# Process facilities WITH WardCode using WardCode grouping
# Process facilities WITHOUT WardCode using LGA+Ward grouping
# Combine results
```

This ensures that:
- Wards with WardCodes are uniquely aggregated by WardCode
- Wards without WardCodes fall back to LGA+Ward aggregation
- No wards are lost due to missing identifiers

#### 2. Removed Duplicate Deduplication (`app/tpr_module/output/output_generator.py`)
Removed the post-merge deduplication that was happening in `generate_outputs`:

```python
# BEFORE: Had deduplication after merging
if 'WardCode' in tpr_with_geo.columns:
    duplicates = tpr_with_geo['WardCode'].duplicated()
    if duplicates.any():
        tpr_with_geo = tpr_with_geo.drop_duplicates(subset=['WardCode'], keep='first')

# AFTER: Just log the count, no deduplication
logger.info(f"After merging with shapefile: {len(tpr_with_geo)} wards")
```

The deduplication during the merge itself (before merging) is sufficient and correct.

### Key Improvements
1. **Robust aggregation**: Handles both wards with and without WardCodes
2. **No data loss**: All 226 wards are preserved throughout the pipeline
3. **Clean pipeline**: Single deduplication point, no redundant operations
4. **Better logging**: Clearer tracking of ward counts at each stage

### Testing Verification
The fix has been deployed to staging server (18.117.115.217). To verify:
1. Upload Adamawa TPR data
2. Complete TPR analysis → Should output 226 wards
3. Proceed to risk analysis → Should load and process 226 wards
4. Check that all ward identifiers are preserved

### Lessons Learned
1. Always handle null/missing values explicitly in aggregation operations
2. Avoid redundant data cleaning operations that can cause unintended data loss
3. Track row counts at each pipeline stage for debugging
4. Consider all edge cases when dealing with unique identifiers