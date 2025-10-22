# TPR Integration Implementation TODO

## Overview
Implement minimal TPR integration that enables Data Analysis V3 to detect TPR data, calculate test positivity rates using production logic, and seamlessly prepare data for risk analysis pipeline.

## Phase 1: Core TPR Functionality

### [ ] 1. Create TPR Utility Functions
**File:** `app/core/tpr_utils.py` (NEW)
- [ ] Create `is_tpr_data(df)` function to detect TPR columns
  - Check for RDT, Microscopy, LLIN, tested, positive, fever columns
  - Return boolean and confidence score
- [ ] Create `calculate_ward_tpr(df, method='standard')` function
  - Implement production logic from deleted tpr_calculator.py
  - All ages: Calculate TPR for each method separately, then max(TPR)
  - Specific age: Max at facility level, then aggregate
- [ ] Add column mapping for encoding issues (≥ vs â‰¥)
- [ ] Add validation functions for TPR data

### [ ] 2. Create Main TPR Analysis Tool
**File:** `app/data_analysis_v3/tools/tpr_analysis_tool.py` (NEW)
- [ ] Import required libraries and dependencies
- [ ] Create `@tool` decorated function `analyze_tpr_data`
- [ ] Implement action="analyze" for basic exploration
- [ ] Implement action="calculate_tpr" 
  - Group by WardName, LGA
  - Apply production calculation logic
  - Handle missing data gracefully
  - Return formatted results with confidence intervals
- [ ] Implement action="prepare_for_risk"
  - Calculate ward-level TPR first
  - Call enhanced variable extractor
  - Merge TPR with environmental data
  - Save as raw_data.csv
  - Extract/create shapefile
  - Set session flags

## Phase 2: Environmental Data Integration

### [ ] 3. Enhance Variable Extractor for Real Rasters
**File:** `app/services/variable_extractor.py` (MODIFY)
- [ ] Replace placeholder values with real raster extraction
- [ ] Add `_extract_from_raster()` method using rasterio
- [ ] Connect to `/rasters/` directory structure:
  - EVI, NDVI, NDMI, NDWI (vegetation indices)
  - rainfall_monthly, temperature_monthly
  - urban_extent, distance_to_water_bodies
  - elevation, housing, night_time_lights
- [ ] Add coordinate extraction for ward centroids
- [ ] Implement caching for extracted values
- [ ] Add error handling for missing rasters

### [ ] 4. Shapefile Extraction from Nigeria Master File
**Master Shapefile:** `www/complete_names_wards/wards.shp`
**File to modify:** `app/services/shapefile_fetcher.py` 
- [ ] Load Nigeria master shapefile from `www/complete_names_wards/wards.shp`
- [ ] Extract state-specific features using state name filter
- [ ] Match ward names between TPR data and shapefile (with fuzzy matching)
- [ ] Join TPR results to shapefile geometries
- [ ] Package as raw_shapefile.zip with all required files (.shp, .shx, .dbf, .prj)
- [ ] Handle ward name variations (normalize and fuzzy match)

## Phase 3: System Integration

### [ ] 5. Enhance System Prompt
**File:** `app/data_analysis_v3/prompts/system_prompt.py` (MODIFY)
- [ ] Add TPR detection section
- [ ] Include calculation method explanations
- [ ] Add progressive disclosure guidance
- [ ] Include risk preparation prompts
- [ ] Example interactions for TPR data

### [ ] 6. Conditional Tool Loading
**File:** `app/data_analysis_v3/core/agent.py` (MODIFY)
- [ ] Import tpr_utils.is_tpr_data
- [ ] Check data on initialization
- [ ] Conditionally append TPR tool if detected
- [ ] Ensure tool is available in graph

### [ ] 7. Upload Detection Enhancement (Optional)
**File:** `app/web/routes/upload_routes.py` (MODIFY if needed)
- [ ] Add TPR detection on file upload
- [ ] Store TPR metadata in session
- [ ] Set appropriate flags

## Phase 4: Testing

### [ ] 8. Unit Tests
- [ ] Test TPR detection with various column formats
- [ ] Test calculation logic matches production exactly
- [ ] Test environmental extraction from rasters
- [ ] Test shapefile creation

### [ ] 9. Integration Testing with Adamawa Data
- [ ] Load `ad_Adamawa_State_TPR_LLIN_2024.xlsx`
- [ ] Verify TPR detection works
- [ ] Test calculate_tpr action
- [ ] Test prepare_for_risk action
- [ ] Verify raw_data.csv created correctly
- [ ] Verify raw_shapefile.zip created
- [ ] Confirm risk analysis can start

### [ ] 10. End-to-End Testing
- [ ] Upload → Detect → Calculate → Prepare → Risk Analysis
- [ ] Test with multiple state files
- [ ] Verify no disruption to normal data analysis
- [ ] Test error handling and edge cases

## Implementation Notes

### Nigeria Shapefile Extraction Logic
```python
# Master Shapefile: www/complete_names_wards/wards.shp
# Contains: 9,410 Nigerian wards with complete boundaries
# Key columns: StateName, StateCode, WardName, LGAName, geometry
# CRS: EPSG:4326 (WGS84)

def extract_state_shapefile(state_name, tpr_data):
    # 1. Load master shapefile
    master_gdf = gpd.read_file('www/complete_names_wards/wards.shp')
    # Columns: ['StateCode', 'WardCode', 'WardName', 'LGACode', 'Urban', 
    #           'StateName', 'LGAName', 'geometry']
    
    # 2. Filter by state (e.g., "Adamawa" matches "Adamawa" in StateName)
    # Handle variations: "Adamawa State" vs "Adamawa", "ad Adamawa State" vs "Adamawa"
    clean_state = state_name.replace(' State', '').replace('ad ', '').replace('kw ', '')
    state_gdf = master_gdf[master_gdf['StateName'].str.contains(clean_state, case=False)]
    
    # 3. Match ward names with TPR data
    # TPR has: "Girei Ward" or "ad Girei Ward"
    # Shapefile has: "Girei"
    # Normalize both sides for matching
    
    # 4. Join TPR results to geometries
    merged_gdf = state_gdf.merge(tpr_data, 
                                 left_on='WardName_normalized', 
                                 right_on='WardName_normalized',
                                 how='left')
    
    # 5. Save as shapefile components
    temp_dir = tempfile.mkdtemp()
    merged_gdf.to_file(f"{temp_dir}/ward_boundaries.shp")
    
    # 6. Create ZIP with all components
    with zipfile.ZipFile('raw_shapefile.zip', 'w') as zf:
        for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
            file_path = f"{temp_dir}/ward_boundaries{ext}"
            if os.path.exists(file_path):
                zf.write(file_path, f"ward_boundaries{ext}")
    
    return 'raw_shapefile.zip'
```

### Production TPR Calculation Logic (CRITICAL)
```python
# All ages aggregation:
1. Sum all RDT tested across facilities
2. Sum all RDT positive across facilities  
3. Calculate RDT_TPR = (RDT_positive_sum / RDT_tested_sum) * 100
4. Sum all Microscopy tested across facilities
5. Sum all Microscopy positive across facilities
6. Calculate Micro_TPR = (Micro_positive_sum / Micro_tested_sum) * 100
7. Final TPR = max(RDT_TPR, Micro_TPR)

# Specific age group:
1. For each facility:
   tested = max(facility.rdt_tested, facility.micro_tested)
   positive = max(facility.rdt_positive, facility.micro_positive)
2. Sum across facilities: total_tested, total_positive
3. TPR = (total_positive / total_tested) * 100
```

### File Structure for Risk Analysis
```
instance/uploads/{session_id}/
├── raw_data.csv          # Ward-level data with TPR + environmental vars
├── raw_shapefile.zip      # Geographic boundaries
└── tpr_metadata.json      # Optional metadata
```

### Critical CSV Columns (Must Include)
```python
# Identifiers (REQUIRED for joining)
'WardCode'           # Unique ward ID from shapefile
'StateCode'          # Two-letter state code  
'LGACode'            # LGA identifier
'WardName'           # Human-readable name
'LGA'                # LGA name
'State'              # State name
'GeopoliticalZone'   # North-East, South-West, etc.

# TPR Metrics (if TPR data exists)
'TPR', 'Total_Tested', 'Total_Positive', ...

# Environmental (NULL if no raster coverage)
'Rainfall_Annual', 'Temperature_Mean', 'EVI', ...

# Note: Both CSV and shapefile DBF must have identical columns
```

### Session Flags Required
```python
session['data_loaded'] = True
session['csv_loaded'] = True
session['shapefile_loaded'] = True
session['upload_type'] = 'csv_shapefile'
```

## Success Criteria
- [ ] TPR detection works for all 37 state files
- [ ] Calculation matches production logic exactly
- [ ] Environmental variables extracted from real rasters
- [ ] Seamless transition to risk analysis
- [ ] No disruption to existing workflows
- [ ] Clear user communication about capabilities

## Review Section
*To be completed after implementation*

### What Worked
- 

### Challenges Faced
- 

### Decisions Made
- 

### Next Steps
-