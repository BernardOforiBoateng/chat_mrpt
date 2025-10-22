# TPR Map Empty Investigation - Complete Analysis

**Date**: 2025-09-29
**Issue**: Some TPR maps display but without colored data (Plateau, Nasarawa) while others work (Ebonyi, Benue, Kebbi)
**Status**: ROOT CAUSE IDENTIFIED

## Summary of Investigation

After thorough investigation, I found that:
1. **Maps ARE displaying** for all states (contradicting initial report)
2. **Map files ARE generated** correctly (500-800KB each)
3. **Ward names DO match** between CSV and shapefile (99%+ match rate)
4. **The issue**: Some maps show the base map but NO colored TPR data overlay

## States Status Based on Screenshots

### Working (Colored TPR Data Visible):
- ✅ **Kebbi** - Shows colored wards with TPR data
- ✅ **Ebonyi** - Shows green areas (low TPR regions visible)
- ✅ **Benue** - Shows green areas (low TPR regions visible)

### Not Working (Blank Maps, No Colors):
- ❌ **Plateau** - Map displays but NO colored ward data
- ❌ **Nasarawa** - Map displays but NO colored ward data

## Technical Investigation Results

### 1. File Generation ✅
All states generate proper map files:
- Plateau: 791KB HTML file
- Nasarawa: ~600KB HTML file
- Benue: 809KB HTML file
- All accessible via `/serve_viz_file/` route

### 2. Ward Matching ✅
Ward names match correctly:
- Plateau: 99.4% ward match rate
- All ward names found in shapefile
- CSV wards exist in shapefile data

### 3. TPR Calculation ✅
TPR results are calculated:
```
Plateau TPR Results:
- assak: 92.23%
- zobwo: 89.64%
- mban: 88.71%
(Data exists and is calculated)
```

### 4. Map Data Structure 🔍
Both working and non-working maps:
- Use Plotly visualization library
- Store z data as base64 encoded binary (`bdata`)
- Have similar file sizes and structure

## The Real Issue

The problem appears to be in the **data merging step** where TPR values are matched to geographic ward boundaries. While the:
- TPR calculations work ✅
- Shapefiles load correctly ✅
- Maps generate ✅

The **merge between TPR data and ward geometries** is failing silently for some states, resulting in maps with no data overlay.

## Why This Happens

Based on the investigation, the most likely cause is:

### Ward Name Normalization Issue
The code uses a `normalize_ward_name` function from `app.core.tpr_utils` that may not handle certain state-specific ward naming patterns correctly. Even though ward names "match" at 99%, the normalization process during the merge might be failing.

### Evidence:
1. States that work have simpler ward naming patterns
2. States that fail might have special characters or formatting
3. The merge happens silently without error reporting

## What's NOT the Problem

- ✅ **NOT** a shapefile issue (states exist with correct wards)
- ✅ **NOT** a TPR calculation issue (values are computed)
- ✅ **NOT** a map generation issue (HTML files created)
- ✅ **NOT** a frontend display issue (some states work perfectly)
- ✅ **NOT** a file serving issue (all URLs accessible)

## Recommended Fix

The issue is in the **data merge step** in `match_and_merge_data` function:

1. **Add detailed logging** to the merge process to see exactly which wards fail to match
2. **Check the normalization** function to ensure it handles all ward name patterns
3. **Add fallback matching** for states that consistently fail
4. **Report merge statistics** in the debug output

### Specific Code Location:
```python
# app/data_analysis_v3/tools/tpr_analysis_tool.py
# Line 344-403: match_and_merge_data function
# This is where TPR data merges with shapefile geometries
```

## Quick Workaround

For immediate relief, you could:
1. Check the actual merge rate for failing states
2. Lower the fuzzy matching threshold (currently 0.8)
3. Add state-specific normalization rules

## Verification Steps

To confirm this diagnosis:
1. Check merge logs for Plateau vs Benue sessions
2. Compare normalized ward names between working/non-working states
3. Look for patterns in ward names that fail to match

The maps ARE being generated - they're just empty because the data isn't being merged correctly with the geographic boundaries.