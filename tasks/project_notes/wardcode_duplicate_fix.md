# WardCode Duplicate Fix

## Date: 2025-08-04

### The Real Issue
User correctly identified: **WardCodes are unique** - every single ward has a unique WardCode. The problem was that the TPR output was creating duplicate rows with the SAME WardCode but different ward name variations.

### Root Cause
The OutputGenerator was merging TPR data with shapefile based on WardName instead of WardCode, even when WardCode was available. This caused the enhanced matcher to create multiple entries for the same ward when handling name variations.

### Examples of Duplicates
- `ADSFUR08`: Appeared as both "Ribadu" and "Ribadu (Mayo-Belwa)"
- `ADSGYL06`: Appeared as both "Lamurde (Lamurde)" and "Lamurde (Mubi South)"
- Total: 11 WardCodes were duplicated, creating 234 rows instead of 226

### Solution Implemented
Modified `app/tpr_module/output/output_generator.py`:

1. **Prioritize WardCode matching**: When both TPR data and shapefile have WardCode, merge on WardCode instead of WardName
2. **Deduplicate if needed**: If duplicate WardCodes are found in TPR data, keep only the first occurrence
3. **Fallback to WardName**: Only use WardName matching when WardCode is not available

### Key Code Changes
```python
# BEFORE: Always merged on WardName
if 'WardName' in tpr_data.columns and 'WardName' in state_gdf.columns:
    merged = tpr_data.merge(state_gdf[merge_cols], on='WardName', ...)

# AFTER: Prioritize WardCode
if 'WardCode' in tpr_data.columns and 'WardCode' in state_gdf.columns:
    # Deduplicate if needed
    if tpr_data['WardCode'].duplicated().any():
        tpr_data = tpr_data.drop_duplicates(subset=['WardCode'], keep='first')
    merged = tpr_data.merge(state_gdf[merge_cols], on='WardCode', ...)
elif 'WardName' in tpr_data.columns and 'WardName' in state_gdf.columns:
    # Fallback to WardName matching
```

### Why This Works
- WardCode is the unique identifier for each ward
- Merging on WardCode ensures 1:1 mapping
- No duplicate rows can be created when merging on a unique key
- Maintains correct ward count (226 for Adamawa)

### Testing
Deployed to staging server for testing:
- TPR analysis should output 226 wards
- Risk analysis should load 226 wards (not 234)
- Each WardCode appears exactly once in the output

### Lesson Learned
Always use the unique identifier (WardCode) for merging when available, rather than relying on potentially ambiguous names (WardName).