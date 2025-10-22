# TPR Data Joining Process - How It Works

## Date: 2025-01-06

## Overview
This documents how TPR calculated data is joined with shapefile identifiers to create the output CSV files.

## The Joining Flow

### Step 1: Calculate TPR (`tpr_calculator.py`)
```python
# Produces DataFrame with:
- WardName (cleaned)
- LGA 
- TPR (calculated value)
- Method (standard/alternative)
- RDT_Tested, RDT_Positive
- Microscopy_Tested, Microscopy_Positive
- Total_Tested, Total_Positive
- Facility_Count
```

### Step 2: Merge with Shapefile (`output_generator._merge_with_shapefile()`)

This is the KEY step where TPR data joins with shapefile:

```python
def _merge_with_shapefile(self, tpr_data: pd.DataFrame, state_name: str):
    # 1. Load shapefile for the state
    state_gdf = shapefile_extractor.master_gdf
    
    # 2. Filter to specific state
    state_gdf = state_gdf[state_gdf['State'].contains(state_name)]
    
    # 3. Identify identifier columns in shapefile:
    identifier_cols = ['StateCode', 'WardCode', 'WardName', 
                      'LGACode', 'LGAName', 'Urban', 'AMAPCODE']
    
    # 4. CRITICAL MERGE LOGIC:
    if 'LGA' in tpr_data and 'LGAName' in state_gdf:
        # Best case: Merge on BOTH WardName AND LGA for unique matches
        merged = tpr_data.merge(
            state_gdf[identifier_cols + ['geometry']],
            left_on=['WardName', 'LGA'],
            right_on=['WardName', 'LGAName'],
            how='left'
        )
    else:
        # Fallback: Merge on WardName only (less precise)
        merged = tpr_data.merge(
            state_gdf[identifier_cols + ['geometry']],
            on='WardName',
            how='left'
        )
    
    # Result: TPR data now has shapefile identifiers + geometry
```

### Step 3: Generate Output Files

#### 3a. TPR Analysis CSV (`_generate_tpr_csv()`)
```python
# Contains:
- State, LGA, WardName
- TPR, TPR_Method
- RDT_Tested, RDT_Positive
- Microscopy_Tested, Microscopy_Positive
- Total_Tested, Total_Positive
- Facility_Count
- Analysis metadata
```

#### 3b. Main Analysis CSV (`_generate_main_csv()`)
```python
# This is for risk analysis pipeline!
# Contains:
- WardName (FIRST column)
- Identifiers: WardCode, LGA, LGACode, StateCode, Urban, AMAPCODE
- TPR (just the value)
- Environmental variables (based on zone):
  - North_East: housing_quality, evi, ndwi, soil_wetness
  - etc.
```

#### 3c. Shapefile (`_generate_shapefile()`)
```python
# GeoDataFrame with:
- All columns from Main CSV
- Plus geometry column
- Exported as .shp/.shx/.dbf/.prj files
```

## Key Insights

### 1. Why WardName AND LGA?
- **Problem**: Multiple wards can have same name in different LGAs
- **Solution**: Join on BOTH WardName and LGA for unique matching
- **Example**: "Central Ward" exists in both Yola North LGA and Yola South LGA

### 2. Identifier Columns from Shapefile
These come from the shapefile, NOT calculated:
- `WardCode`: Unique ward identifier
- `LGACode`: Unique LGA identifier  
- `StateCode`: State identifier
- `AMAPCODE`: Administrative code
- `Urban`: Urban/rural flag

### 3. Ward Name Matching Issues

#### Current Implementation:
```python
# Uses exact match or normalized match
tpr_data['ward_norm'] = normalize_ward_name(tpr_data['WardName'])
shapefile['ward_norm'] = normalize_ward_name(shapefile['WardName'])
merge on 'ward_norm'
```

#### What We Need (Interactive):
```python
# When exact match fails:
LLM: "'Bajoga Ward' in TPR doesn't match shapefile.
      Should I match to 'Bajoga' (95% similar)?"
User: "Yes"
# Then apply the match
```

### 4. Environmental Variables Extraction
```python
# After merge, if geometry exists:
if 'geometry' in main_df:
    # Extract zone-specific variables
    zone = STATE_TO_ZONE[state_name]  # e.g., 'North_East'
    zone_vars = ZONE_VARIABLES[zone]  # e.g., ['evi', 'ndwi', ...]
    
    # Use RasterExtractor to get values
    main_df = raster_extractor.extract_zone_variables(
        main_df,  # Has geometry column
        zone,
        zone_vars
    )
```

## The Problem We're Solving

### Current Issues:
1. **Silent Failures**: When ward names don't match, merge fails silently
2. **No User Input**: Can't verify fuzzy matches
3. **Lost Data**: Unmatched wards get dropped

### Our Solution:
1. **Interactive Matching**: Ask user to verify fuzzy matches
2. **Preserve All Data**: Keep unmatched wards with warning
3. **Transparency**: Show what matched and what didn't

## Integration Points for Interactive System

### 1. Before Merge:
```python
# In interactive_conversation.py
def prepare_for_merge(self, tpr_data, shapefile_wards):
    # Get user verification for fuzzy matches
    matches, unmatched = self.match_wards_interactive(
        tpr_data, shapefile_wards
    )
    
    # Apply verified matches to data
    tpr_data['WardName_Matched'] = tpr_data['WardName'].map(matches)
    
    return tpr_data
```

### 2. During Merge:
```python
# Modified _merge_with_shapefile()
def _merge_with_shapefile(self, tpr_data, state_name):
    # Use WardName_Matched if available (from interactive matching)
    merge_col = 'WardName_Matched' if 'WardName_Matched' in tpr_data else 'WardName'
    
    merged = tpr_data.merge(
        state_gdf[identifier_cols + ['geometry']],
        left_on=[merge_col, 'LGA'],
        right_on=['WardName', 'LGAName'],
        how='left'
    )
```

### 3. After Merge:
```python
# Report to user
matched = merged['geometry'].notna().sum()
total = len(merged)

if matched < total:
    self.llm.warn_user(
        f"Note: {total - matched} wards couldn't be matched to shapefile.
        They will be included in CSV but not in map visualization."
    )
```

## Summary

The joining process:
1. **Calculate TPR** → Get WardName, LGA, TPR values
2. **Match with Shapefile** → Add WardCode, LGACode, geometry, etc.
3. **Extract Zone Variables** → Use geometry to get environmental data
4. **Generate Outputs** → TPR CSV, Main CSV (for risk analysis), Shapefile

The key improvement needed:
- **Interactive ward matching** before the merge to ensure maximum data retention