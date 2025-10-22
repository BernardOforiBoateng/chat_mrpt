# TPR Distribution Map Investigation Findings
Date: 2024-09-23

## Issue Summary
TPR distribution maps appear blank for certain states (Akwa Ibom, Benue, Nasarawa, Plateau, Kebbi, Ebonyi) while working correctly for others (Adamawa, Cross River, Sokoto).

## Investigation Findings

### 1. Root Cause Identified: State Name Mismatch
**Primary Issue**: The state names in the uploaded TPR data don't match the state names in the shapefile.

#### Evidence:
- **Akwa Ibom Case**:
  - Data file has: `Akwa-Ibom State` (with hyphen)
  - Shapefile has: `Akwa Ibom` (with space, no hyphen)
  - Result: No match → Blank map

- **Working States**:
  - Adamawa, Cross River, Sokoto all have exact name matches between data and shapefile

### 2. Technical Analysis

#### Map Generation Process:
1. Code loads Nigeria master shapefile with 9,410 wards
2. Filters shapefile by state name from uploaded data
3. Attempts exact match first: `master_gdf[master_gdf['StateName'] == clean_state]`
4. If no match, tries case-insensitive: `master_gdf[master_gdf['StateName'].str.lower() == clean_state.lower()]`
5. Problem: Neither handles hyphen vs space differences

#### Files Verified:
- All sessions have TPR data uploaded correctly
- Map HTML files are generated (sizes: 582KB-911KB)
- Maps contain correct state names and TPR values in the HTML
- But visualization appears blank due to name mismatch

### 3. Affected States Analysis

| State | Data Format | Shapefile Format | Status |
|-------|------------|------------------|--------|
| Akwa Ibom | Akwa-Ibom State | Akwa Ibom | ❌ Blank |
| Ebonyi | Ebonyi State | Ebonyi | ✅ Should work |
| Nasarawa | Nasarawa State | Nasarawa | ✅ Should work |
| Benue | Benue State | Benue | ✅ Should work |
| Plateau | Unknown | Plateau | Need to verify |
| Kebbi | Unknown | Kebbi | Need to verify |

### 4. Why Some "Should Work" States Still Show Blank

Despite having correct state names, some maps may still appear blank due to:
1. **Ward Name Mismatches**: Even if state matches, individual ward names might not match between TPR data and shapefile
2. **Map Rendering Issue**: The deprecated `Choroplethmapbox` requires proper configuration
3. **Missing TPR Values**: If ward matching fails, no TPR values get plotted

### 5. Solution Required

The code needs to be enhanced to handle state name variations:
1. Add normalization for hyphens vs spaces
2. Implement fuzzy matching for state names
3. Add better logging for debugging mismatches
4. Consider migrating from deprecated Choroplethmapbox to newer Choropleth

## Next Steps
1. Fix state name matching logic to handle variations
2. Improve ward name matching algorithm
3. Add detailed logging for debugging
4. Test with all problematic states