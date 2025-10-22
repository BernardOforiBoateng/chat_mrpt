# TPR Pipeline Creating 234 Rows Instead of 226 - Investigation Results

## Date: 2025-08-04

## Executive Summary
The TPR pipeline is creating 234 rows from 226 unique wards due to a flawed join operation in the shapefile extraction process.

## Investigation Findings

### 1. Master Shapefile is Correct
- Master Nigerian shapefile: **9,410 total features**
- Adamawa State features: **226 wards**
- Unique WardCodes: **226** 
- Duplicate WardCodes: **0**
- **Conclusion**: Master shapefile is clean with no duplicates

### 2. NMEP Source Data Has No WardCodes
- Original NMEP Excel file has NO WardCode column
- Contains only: State, LGA, Ward, Facility names, and test data
- WardCodes are being ADDED during TPR pipeline processing

### 3. The Duplication Happens During Shapefile Join

**Location**: `app/tpr_module/services/shapefile_extractor.py`, line 169

```python
joined = state_gdf.merge(
    tpr_data_mapped,
    left_on=ward_col_shp,
    right_on=ward_col_tpr,
    how='left',
    suffixes=('', '_tpr')
)
```

### 4. Root Cause Analysis

The duplication occurs because:

1. **Multiple wards share the same name across LGAs**:
   - "Ribadu" exists in both Fufore and Mayo-Belwa
   - "Lamurde" exists in both Lamurde LGA and Mubi South
   - "Nasarawo" exists in both Mubi South and Yola North
   - "Yelwa" exists in both Mubi North and Yola North

2. **TPR aggregation creates one row per LGA+Ward combination**:
   - TPR pipeline aggregates by ['LGA', 'Ward']
   - Creates 223 unique LGA+Ward combinations

3. **Shapefile join doesn't consider LGA**:
   - The join is on ward name ONLY
   - When TPR has "Ribadu (Fufore)" and "Ribadu (Mayo-Belwa)"
   - And shapefile has one "Ribadu" entry
   - The left join creates TWO rows for the shapefile's Ribadu

4. **Wrong WardCodes get assigned**:
   - During aggregation, facilities with different WardCodes get grouped
   - The pipeline takes the "first" WardCode it encounters
   - This assigns Mayo-Belwa's WardCode to Fufore's Ribadu

## The 8 Duplicate Entries Created

1. **Ribadu** → 2 entries (Fufore + Mayo-Belwa versions)
2. **Lamurde** → 2 entries (Lamurde LGA + Mubi South versions)  
3. **Nasarawo** → 2 entries (Mubi South + Yola North versions)
4. **Yelwa** → 2 entries (Mubi North + Yola North versions)

Total: 226 + 8 = 234 rows

## The 3 Missing Wards

After the duplicates are created (234), the system later deduplicates down to 223, losing 11 entries:
- 8 duplicates removed
- 3 additional wards lost in the process

## Solution Required

### Fix 1: Join on LGA + Ward
The shapefile join should match on BOTH LGA and Ward name, not just ward name:

```python
joined = state_gdf.merge(
    tpr_data_mapped,
    left_on=['LGAName', ward_col_shp],
    right_on=['LGA', ward_col_tpr],
    how='left'
)
```

### Fix 2: Validate WardCode Assignment
When aggregating facilities, validate that all facilities in a ward have consistent WardCodes.

### Fix 3: Use WardCode as Primary Key
Since WardCodes are unique identifiers, use them as the primary join key when available.

## Impact
- Risk analysis receives incorrect data (223 or 234 rows instead of 226)
- Some wards have wrong geographic attribution
- TPR values may be assigned to wrong locations
- Malaria intervention planning affected