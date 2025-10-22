# TPR Blank Map Investigation Findings

**Date**: 2025-09-29
**Issue**: TPR distribution maps showing blank for Benue, Ebonyi, Kebbi, Nasarawa, and Plateau states
**Status**: ROOT CAUSE IDENTIFIED

## Investigation Summary

The TPR maps appear blank because the visualizations are not being automatically generated during the TPR workflow. The system is detecting the states correctly but stopping at the user interaction phase rather than completing the full TPR calculation and map generation.

## Key Findings

### 1. Data Files ✅
- All problematic states have valid CSV files in `/www/all_states_cleaned/`
- File sizes are appropriate (443KB - 2.7MB)
- State names in CSV files are correct: "Benue", "Ebonyi", "Kebbi", "Nasarawa", "Plateau"

### 2. Shapefile Data ✅
- Master shapefile at `www/complete_names_wards/wards.shp` contains ALL states
- Confirmed presence of all problematic states:
  - Benue: 277 wards
  - Ebonyi: 235 wards
  - Kebbi: 225 wards
  - Nasarawa: 147 wards
  - Plateau: 325 wards
- Ward name matching is excellent (99.4% match rate for Plateau)

### 3. State Name Normalization ⚠️
- The `normalize_state_name()` function in `tpr_analysis_tool.py` has hardcoded mappings
- **MISSING**: Benue is not in the state_mappings dictionary (line 422-437)
- Other states (Ebonyi, Kebbi, Nasarawa, Plateau) ARE in the mappings

### 4. Workflow Issue 🔴
The main issue is that the TPR workflow is **interactive** and stops to ask users for selections:
- It detects the state correctly
- But then asks for facility level selection
- Then asks for age group selection
- Only AFTER these selections does it generate the map

**Current Behavior**:
1. User uploads data
2. System detects state (e.g., "Benue")
3. System asks: "Which facility level?"
4. **STOPS HERE** - waiting for user input
5. Map is never generated because workflow doesn't complete

**Expected Behavior**:
The system should either:
- Auto-select defaults and generate the map immediately
- OR store the visualization and make it available even during the selection process

## Code Locations

### Files Involved
1. `/app/data_analysis_v3/tools/tpr_analysis_tool.py`
   - `normalize_state_name()` - Line 406-445 (missing Benue)
   - `create_tpr_map()` - Line 448-660 (map generation logic)
   - `analyze_tpr_data()` - Line 707+ (main workflow)

2. `/app/data_analysis_v3/core/tpr_workflow_handler.py`
   - Handles the interactive TPR workflow
   - Implements progressive disclosure pattern

## Root Causes

### Primary Issue
The TPR workflow uses **progressive disclosure** which requires user interaction to complete. The visualization is only generated AFTER the user makes all selections (facility level, age group).

### Secondary Issue (Benue only)
The `normalize_state_name()` function is missing "Benue" from its hardcoded state mappings dictionary, though the code has fallback strategies that should still work.

## Why Some States Work

States like Adamawa likely work because:
1. They might have been tested with direct API calls that complete the workflow
2. OR they were tested before the progressive disclosure update
3. OR someone manually completed the workflow for those states

## Solution Options

### Option 1: Auto-Complete Workflow (Recommended)
When a user asks for "TPR distribution map", automatically use defaults:
- Facility Level: "all"
- Age Group: "all"
- Generate and display the map immediately

### Option 2: Pre-Generate Visualizations
Generate visualizations at upload time with default parameters and store them, making them available immediately when requested.

### Option 3: Fix Progressive Disclosure
Modify the TPR workflow to generate and store visualizations at each step, not just at the end.

## Test Results

### Plateau Test
- Upload: ✅ Successful
- State Detection: ✅ "Plateau" detected
- Visualization: ❌ Not generated (workflow incomplete)

### Benue Test
- Upload: ✅ Successful
- State Detection: ✅ "Benue" detected
- Visualization: ❌ Not generated (workflow incomplete)

## Verification Commands

```bash
# Check state in shapefile
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 \
  "python3 -c \"import geopandas as gpd; \
   gdf = gpd.read_file('/home/ec2-user/ChatMRPT/www/complete_names_wards/wards.shp'); \
   print('Benue wards:', len(gdf[gdf['StateName'] == 'Benue']))\""

# Test direct TPR calculation
python tests/test_plateau_visualization.py
python tests/test_benue_state_mapping.py
```

## Recommendation

The issue is NOT with the data or shapefiles. The problem is that the TPR workflow requires user interaction to complete, and visualizations are only generated after all selections are made.

**Immediate Fix**: Modify the TPR workflow to automatically use default parameters when a user specifically asks for a "TPR distribution map" without going through the selection process.

**Code Change Needed**: In the TPR workflow handler, detect when users want to see the map directly and auto-complete with defaults:
- Facility Level: "all"
- Age Group: "all"

This would allow the map to be generated and displayed immediately without requiring the interactive selection process.