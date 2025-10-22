# Debug Log Analysis - Visualization Failures After TPR Transition

## Executive Summary
The debug logs reveal **two critical issues** causing visualization failures after TPR transition:

1. **Variable Distribution Issue**: The `evi` variable exists in the CSV but is lost during the merge with shapefile
2. **Complete Analysis Error**: Debug logging bug prevented risk analysis from running

## Detailed Findings

### 1. Variable Distribution Failure for 'evi'

**What the logs show:**
```
🔍 DEBUG VARIABLE DISTRIBUTION: Starting for variable 'evi'
🔍 Checking data files:
🔍   raw_data.csv: EXISTS
🔍   unified_dataset.csv: NOT FOUND  ← Key finding!
🔍   raw_shapefile.zip: EXISTS

🔍 DEBUG: CSV loaded successfully
🔍   Shape: (226, 16)
🔍   Columns: ['WardCode', 'StateCode', 'LGACode', 'WardName', 'LGA', 'State', 'GeopoliticalZone', 'TPR', 'Total_Tested', 'Total_Positive']
🔍   ✅ Variable 'evi' FOUND in CSV  ← Variable exists!

Successfully merged data on column: WardName
ERROR: Variable evi not found in merged data  ← Lost during merge!
```

**Root Cause**: 
- The `evi` variable EXISTS in the CSV (confirmed by logs)
- After merging with shapefile on 'WardName', the `evi` column is lost
- This happens because the merge is likely a left join on shapefile, dropping CSV columns not in the merge key

### 2. Risk Analysis Failure

**What the logs show:**
```
🔍 DEBUG COMPLETE ANALYSIS: Starting execution
ERROR: cannot access local variable 'composite_variables' where it is not associated with a value
```

**Root Cause**: 
- Bug in debug logging code trying to use variables before they were defined
- This has been FIXED in the latest deployment

### 3. File State After TPR Transition

**Key Finding**: `unified_dataset.csv` is NOT created during TPR workflow
- TPR creates: `raw_data.csv` and `raw_shapefile.zip`
- Risk analysis expects: `unified_dataset.csv`
- No fallback mechanism exists

## The Merge Problem Explained

The variable distribution tool does this:
1. Loads CSV with all variables (including `evi`)
2. Loads shapefile with geographic data
3. Merges them on 'WardName'
4. **BUG**: The merge operation drops non-common columns

Here's what's happening in the code:
```python
# In _create_spatial_distribution_map
merged_data = shapefile.merge(csv_data[['WardName', variable]], on='WardName', how='left')
```

The problem is it's only selecting 'WardName' and the variable from CSV, but if the merge fails or the column selection happens wrong, the variable gets lost.

## Solutions Required

### Fix 1: Variable Distribution Merge Issue
The merge in `variable_distribution.py` needs to preserve all CSV columns:
```python
# Current (broken):
merged_data = shapefile.merge(csv_data[['WardName', variable]], on='WardName', how='left')

# Fixed:
merged_data = shapefile.merge(csv_data, on='WardName', how='left')
# Then check if variable exists in merged_data
```

### Fix 2: Create Unified Dataset After TPR
Add unified dataset creation to TPR workflow completion:
```python
# After TPR analysis completes
from app.data.unified_dataset_builder import UnifiedDatasetBuilder
builder = UnifiedDatasetBuilder(session_id)
builder.build_unified_dataset()
```

### Fix 3: Add Fallback in Visualization Tools
Make `_get_unified_dataset()` fall back to raw_data.csv:
```python
def _get_unified_dataset(session_id):
    unified_path = f'instance/uploads/{session_id}/unified_dataset.csv'
    if not os.path.exists(unified_path):
        # Try raw_data.csv as fallback
        raw_path = f'instance/uploads/{session_id}/raw_data.csv'
        if os.path.exists(raw_path):
            return pd.read_csv(raw_path)
    # ... rest of function
```

## Current Status

### ✅ Fixed:
- Debug logging error in `complete_analysis_tools.py`

### ❌ Still Broken:
- Variable distribution merge losing columns
- Unified dataset not created after TPR
- No fallback to raw_data.csv

## Test Commands

To verify the issues:
```bash
# Check logs for variable distribution
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@3.21.167.170 \
  'sudo journalctl -u chatmrpt -f | grep "🔍 DEBUG"'

# Test variable distribution
curl -X POST "https://d225ar6c86586s.cloudfront.net/send_message" \
  -H "Content-Type: application/json" \
  -d '{"message": "Plot me the map distribution for the evi variable", "session_id": "YOUR_SESSION_ID"}'
```

## Next Steps

1. **Immediate**: Fix the merge issue in `variable_distribution.py`
2. **Important**: Add unified dataset creation to TPR workflow
3. **Fallback**: Implement raw_data.csv fallback in visualization tools
4. **Validation**: Test full workflow after fixes