# TPR Map Null Geometry Fix

**Date**: 2025-09-29
**Issue**: TPR maps for Benue, Ebonyi, Plateau, and Nasarawa displayed blank (no colored data)
**Solution**: Filter out null geometries before converting to GeoJSON

## Problem Discovery

### Symptoms
- Some states (Kebbi, Adamawa, Cross River, Sokoto, Zamfara) displayed TPR maps correctly
- Other states (Benue, Ebonyi, Plateau, Nasarawa) showed only base map without colored TPR data
- Browser console showed: `TypeError: Cannot read properties of null (reading 'type')`

### Root Cause Analysis
After extensive investigation comparing working vs non-working states:

**Working States:**
- Kebbi: 0 null geometries ✅

**Non-Working States:**
- Benue: 1 null geometry (ward: "Mbadede 2")
- Ebonyi: 23 null geometries
- Plateau: 4 null geometries
- Nasarawa: 1 null geometry (ward: "Ancho Babba")

## Technical Explanation

### What is a Null Geometry?
A null geometry is a geographic feature that exists in the dataset but has no shape data:
- Normal ward: `Name="Ward1", Geometry=POLYGON((coordinates))`
- Null geometry: `Name="Ward2", Geometry=NULL`

### Why It Caused Failure
1. Shapefile contains ward records with NULL geometry values
2. When merged with TPR data, these null geometries remain in the GeoDataFrame
3. Converting to GeoJSON with `merged_gdf.__geo_interface__` includes these nulls
4. Plotly JavaScript tries to process null geometries and crashes

## Solution Implementation

### Code Changes
Modified `app/data_analysis_v3/tools/tpr_analysis_tool.py`:

```python
# Before line 598 (GeoJSON conversion), added:

# Filter out null geometries before creating the map
initial_count = len(merged_gdf)
merged_gdf = merged_gdf[merged_gdf.geometry.notna()].copy()
null_geometry_count = initial_count - len(merged_gdf)

if null_geometry_count > 0:
    logger.warning(f"⚠️ Filtered out {null_geometry_count} wards with null geometries")
    logger.info(f"  Remaining wards for visualization: {len(merged_gdf)}")

# Reset index to ensure proper alignment with GeoJSON
merged_gdf = merged_gdf.reset_index(drop=True)

# Then convert to GeoJSON
geojson = merged_gdf.__geo_interface__
```

### Key Points
1. Filter happens AFTER data merge but BEFORE GeoJSON conversion
2. Logging tracks how many null geometries were removed
3. Index reset ensures proper alignment between data and geometries
4. Copy() ensures we don't modify the original dataframe

## Testing & Deployment

### Local Testing
- Verified no syntax errors with import test
- Confirmed the filtering logic works correctly

### Deployment
- Deployed to both production AWS instances:
  - Instance 1: 3.21.167.170
  - Instance 2: 18.220.103.20
- Restarted chatmrpt service on both instances

## Expected Results

After this fix:
- All states should display their TPR maps correctly
- Null geometry wards will be excluded from visualization
- Logs will show how many wards were filtered for each state
- No more JavaScript errors in browser console

## Lessons Learned

1. **Silent Failures**: The original code didn't check for null geometries, causing silent failures in JavaScript
2. **Data Validation**: Always validate geographic data before visualization
3. **Browser Console**: JavaScript errors often reveal issues that Python logs miss
4. **Comparative Analysis**: Comparing working vs non-working cases helped identify the pattern

## Future Improvements

Consider:
1. Investigating why these wards have null geometries in the source shapefile
2. Adding data quality checks during shapefile loading
3. Potentially fixing null geometries by finding correct ward boundaries
4. Adding unit tests for null geometry handling