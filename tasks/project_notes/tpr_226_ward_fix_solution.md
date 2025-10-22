# TPR 226 Ward Fix - Complete Solution

## Problem Summary
The TPR pipeline was producing 234 features for Adamawa State instead of the correct 226, causing data integrity issues.

## Root Causes Identified

### 1. Duplicate Rows in TPR Data
The TPR data (`Adamawa_plus.csv`) contained duplicate LGA+Ward combinations with different WardCodes:
- Fufore/Ribadu: 2 rows with WardCodes ADSFUR08 and ADSMWA10
- Yola North/Yelwa: 2 rows with WardCodes ADSMUB11 and ADSYLN11
- Total: 4 duplicate LGA+Ward combinations

### 2. Ward-Only Join Logic
The original join in `shapefile_extractor.py` was matching on ward name only, not considering LGA context. This caused issues when wards with the same name existed in different LGAs.

## Solution Implemented

### Fix 1: LGA+Ward Join (Line 178-184)
```python
# Join on both LGA and Ward for precise matching
joined = state_gdf.merge(
    tpr_data_mapped,
    left_on=['lga_normalized', ward_col_shp],
    right_on=['lga_normalized', ward_col_tpr],
    how='left',
    suffixes=('', '_tpr')
)
```

### Fix 2: TPR Data Deduplication (Line 152-163)
```python
# Deduplicate TPR data by LGA+Ward to prevent creating duplicate features
if lga_col_tpr and ward_col_tpr:
    # Check for duplicates
    tpr_duplicates = tpr_data.groupby([lga_col_tpr, ward_col_tpr]).size()
    tpr_duplicates = tpr_duplicates[tpr_duplicates > 1]
    if not tpr_duplicates.empty:
        logger.warning(f"Found {len(tpr_duplicates)} duplicate LGA+Ward combinations in TPR data")
        logger.info("Deduplicating TPR data by taking first occurrence per LGA+Ward")
        
        # Deduplicate by keeping first occurrence per LGA+Ward
        tpr_data = tpr_data.drop_duplicates(subset=[lga_col_tpr, ward_col_tpr], keep='first')
        logger.info(f"TPR data reduced to {len(tpr_data)} unique LGA+Ward combinations")
```

## Testing Results

### Before Fix
- Total features: 234 (8 extra)
- Duplicate wards: 8 different LGA+Ward combinations

### After Fix  
- Total features: **226** ✅
- Duplicate wards: **0** ✅
- Unique LGA+Ward combinations: **226** ✅

## Files Modified
- `/app/tpr_module/services/shapefile_extractor.py` - Added deduplication and LGA+Ward join logic

## Deployment Notes
The fix needs to be deployed to both AWS production instances:
- Instance 1: 172.31.44.52
- Instance 2: 172.31.43.200

## Key Learnings
1. **Data Quality**: Always check source data for duplicates before processing
2. **Join Keys**: Use composite keys (LGA+Ward) when names alone aren't unique
3. **Validation**: The master shapefile with 226 unique Adamawa wards served as ground truth
4. **Root Cause**: The NMEP source data doesn't have WardCodes, leading to incorrect assignments during processing