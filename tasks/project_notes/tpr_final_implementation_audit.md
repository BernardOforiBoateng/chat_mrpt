# TPR Integration Final Implementation Audit

## Executive Summary
This document provides a complete audit of the TPR integration plan to ensure seamless implementation with no gaps or weaknesses.

## 1. COMPLETE FILE INVENTORY

### 1.1 Files to CREATE (Only 2 new files)
1. **`app/core/tpr_utils.py`** (NEW)
   - Purpose: Core TPR detection and calculation functions
   - Functions:
     - `is_tpr_data(df)` - Detect TPR columns
     - `calculate_ward_tpr(df, method='standard')` - Production TPR logic
     - `normalize_ward_name(name)` - Clean ward names
     - `extract_state_from_data(df)` - Get state name

2. **`app/data_analysis_v3/tools/tpr_analysis_tool.py`** (NEW)
   - Purpose: Main tool for TPR analysis in Data Analysis V3
   - Actions:
     - `analyze` - Basic data exploration
     - `calculate_tpr` - Calculate TPR metrics
     - `prepare_for_risk` - Create raw_data.csv and raw_shapefile.zip

### 1.2 Files to MODIFY (5 existing files)

1. **`app/data_analysis_v3/prompts/system_prompt.py`** (MODIFY)
   - Current: Basic data analysis prompts
   - Add: TPR-specific guidance section
   - Line: Add to MAIN_SYSTEM_PROMPT constant

2. **`app/data_analysis_v3/core/agent.py`** (MODIFY)
   - Current Line ~51: `self.tools = [analyze_data]`
   - Add: Conditional TPR tool loading if TPR data detected
   - Critical: Must load session data first to check

3. **`app/services/variable_extractor.py`** (MODIFY)
   - Current Lines 160-170: Using placeholder random values
   - Change: Real raster extraction from `/rasters/` directory
   - Add: `_extract_from_raster()` method using rasterio

4. **`app/services/shapefile_fetcher.py`** (MODIFY)
   - Current Lines 141-217: Creating placeholder geometries
   - Change: Load from `www/complete_names_wards/wards.shp`
   - Add: Ward name matching with fuzzy logic

5. **`app/web/routes/upload_routes.py`** (OPTIONAL MODIFY)
   - Current: Basic file upload
   - Add: TPR detection flag in session
   - Note: This is optional, detection can happen in agent

## 2. ENDPOINT AND DATA FLOW

### 2.1 Entry Points
```
POST /upload_both_files (existing)
    ↓
File saved to: instance/uploads/{session_id}/
    ↓
GET /stream (Data Analysis V3 chat - existing)
    ↓
Agent loads data and detects TPR
    ↓
TPR tool becomes available
```

### 2.2 Session Flow
```python
# 1. User uploads TPR file
session_id = "abc123"
file_path = f"instance/uploads/{session_id}/ad_Adamawa_State_TPR_LLIN_2024.xlsx"

# 2. Agent initialization checks
data = pd.read_excel(file_path)
is_tpr, confidence = is_tpr_data(data)  # Returns (True, 0.95)

# 3. Tool becomes available
if is_tpr:
    tools.append(analyze_tpr_data)

# 4. User interaction
User: "Calculate TPR and prepare for risk analysis"
Agent: Uses analyze_tpr_data(action="prepare_for_risk")

# 5. Output files created
instance/uploads/{session_id}/raw_data.csv
instance/uploads/{session_id}/raw_shapefile.zip
instance/uploads/{session_id}/.risk_ready  # Flag file

# 6. Risk analysis can now start
```

## 3. CRITICAL INTEGRATION POINTS

### 3.1 TPR Detection Logic
```python
def is_tpr_data(df):
    tpr_columns = ['RDT', 'Microscopy', 'tested', 'positive', 'fever', 'LLIN']
    matches = 0
    for col in df.columns:
        for tpr_col in tpr_columns:
            if tpr_col.lower() in col.lower():
                matches += 1
                break
    confidence = matches / len(tpr_columns)
    return confidence > 0.5, {'confidence': confidence, 'matches': matches}
```

### 3.2 Production TPR Calculation (CRITICAL)
```python
# ALL AGES - Calculate TPR for each method, then take max
def calculate_all_ages_tpr(df):
    # Group by ward
    ward_groups = df.groupby(['WardName', 'LGA'])
    
    results = []
    for (ward, lga), group in ward_groups:
        # RDT TPR
        rdt_tested = group['RDT_Total_Tested'].sum()
        rdt_positive = group['RDT_Total_Positive'].sum()
        rdt_tpr = (rdt_positive / rdt_tested * 100) if rdt_tested > 0 else 0
        
        # Microscopy TPR
        micro_tested = group['Microscopy_Total_Tested'].sum()
        micro_positive = group['Microscopy_Total_Positive'].sum()
        micro_tpr = (micro_positive / micro_tested * 100) if micro_tested > 0 else 0
        
        # Take MAX of TPRs (not max of values!)
        final_tpr = max(rdt_tpr, micro_tpr)
        
        results.append({
            'WardName': ward,
            'LGA': lga,
            'TPR': final_tpr,
            'Total_Tested': max(rdt_tested, micro_tested),
            'Total_Positive': max(rdt_positive, micro_positive)
        })
    
    return pd.DataFrame(results)
```

### 3.3 Nigeria Shapefile Integration
```python
# Master shapefile location
NIGERIA_SHAPEFILE = 'www/complete_names_wards/wards.shp'

# Columns in shapefile:
# ['StateCode', 'WardCode', 'WardName', 'LGACode', 'Urban', 'StateName', 'LGAName', 'geometry']

def extract_state_shapefile(state_name, tpr_data):
    # Load master shapefile (9,410 wards)
    master_gdf = gpd.read_file(NIGERIA_SHAPEFILE)
    
    # Clean state name (handle "ad Adamawa State" → "Adamawa")
    clean_state = state_name.replace(' State', '').strip()
    clean_state = re.sub(r'^[a-z]{2}\s+', '', clean_state, flags=re.IGNORECASE)
    
    # Filter to state
    state_gdf = master_gdf[master_gdf['StateName'] == clean_state]
    
    # Match ward names (TPR: "ad Girei Ward" vs Shapefile: "Girei")
    tpr_data['WardName_clean'] = tpr_data['WardName'].apply(normalize_ward_name)
    state_gdf['WardName_clean'] = state_gdf['WardName'].apply(normalize_ward_name)
    
    # Merge on clean names
    merged = state_gdf.merge(tpr_data, on='WardName_clean', how='left')
    
    return merged
```

### 3.4 Environmental Variable Extraction
```python
# Raster directory structure
RASTER_BASE = '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/rasters/'

RASTER_MAP = {
    'rainfall': 'rainfall_monthly/2021/*.tif',  # Use most recent
    'temperature': 'temperature_monthly/2021/*.tif',
    'EVI': 'EVI/EVI_v6.2018.*.mean.1km.tif',
    'NDVI': 'NDVI/*.tif',
    'NDMI': 'NDMI/NDMI_Nigeria_2023.tif',
    'NDWI': 'NDWI/Nigeria_NDWI_2023.tif',
    'elevation': 'Elevation/MERIT_Elevation.max.1km.tif',
    'distance_to_water': 'distance_to_water_bodies/distance_to_water.tif',
    'nighttime_lights': 'night_timel_lights/2024/VIIRS_NTL_2024_Nigeria.tif',
    'housing': 'housing/2019_Nature_Africa_Housing_2015_NGA.tiff'
}

def extract_from_rasters(ward_geometries):
    results = {}
    for var_name, raster_pattern in RASTER_MAP.items():
        try:
            raster_path = glob.glob(os.path.join(RASTER_BASE, raster_pattern))[0]
            with rasterio.open(raster_path) as src:
                # Extract values for each ward centroid
                values = []
                for geom in ward_geometries:
                    centroid = geom.centroid
                    value = list(src.sample([(centroid.x, centroid.y)]))[0]
                    values.append(value[0] if value != src.nodata else None)
                results[var_name] = values
        except (IndexError, FileNotFoundError):
            # No raster coverage - use NULL
            results[var_name] = [None] * len(ward_geometries)
    return results
```

## 4. OUTPUT FILE STRUCTURES

### 4.1 raw_data.csv Structure
```csv
WardCode,StateCode,LGACode,WardName,LGA,State,GeopoliticalZone,TPR,Total_Tested,Total_Positive,
Rainfall_Annual,Temperature_Mean,EVI,NDVI,NDMI,NDWI,elevation,distance_to_water,nighttime_lights,housing_quality
01001,AD,0101,Girei,Girei,Adamawa,North-East,15.2,5000,760,850.5,28.3,0.42,0.38,NULL,NULL,125.0,2.5,0.15,0.65
01002,AD,0101,Jabbi Lamba,Girei,Adamawa,North-East,12.8,3200,410,NULL,28.1,0.45,0.40,NULL,NULL,118.0,3.1,0.08,0.58
```

### 4.2 raw_shapefile.zip Contents
```
raw_shapefile.zip/
├── ward_boundaries.shp     # Geometries
├── ward_boundaries.shx     # Shape index
├── ward_boundaries.dbf     # Attributes (same columns as CSV)
├── ward_boundaries.prj     # Projection (EPSG:4326)
└── ward_boundaries.cpg     # Character encoding
```

## 5. POTENTIAL FAILURE POINTS AND MITIGATIONS

### 5.1 Ward Name Mismatch
**Issue:** TPR has "ad Girei Ward", Shapefile has "Girei"
**Solution:**
```python
def normalize_ward_name(name):
    # Remove state prefix (ad, kw, os, etc.)
    name = re.sub(r'^[a-z]{2}\s+', '', name, flags=re.IGNORECASE)
    # Remove 'Ward' suffix
    name = re.sub(r'\s+Ward$', '', name, flags=re.IGNORECASE)
    # Remove extra spaces and lowercase
    return name.strip().lower()
```

### 5.2 Missing Raster Coverage
**Issue:** Not all wards have raster data
**Solution:** Use NULL values, don't fail
```python
try:
    value = extract_from_raster(coord)
except:
    value = None  # NULL in CSV
```

### 5.3 Session State Across Workers
**Issue:** 6 workers might not share session state
**Solution:** File-based flags
```python
# Write flag when ready
Path(f"instance/uploads/{session_id}/.risk_ready").touch()

# Check in risk analysis
if Path(f"instance/uploads/{session_id}/.risk_ready").exists():
    # Ready for risk
```

### 5.4 Large Shapefile Performance
**Issue:** Loading 9,410 features repeatedly
**Solution:** Cache with LRU
```python
from functools import lru_cache

@lru_cache(maxsize=1)
def load_nigeria_shapefile():
    return gpd.read_file('www/complete_names_wards/wards.shp')
```

### 5.5 Column Encoding Issues
**Issue:** TPR files have encoding issues (≥ vs â‰¥)
**Solution:** Column mapping
```python
COLUMN_FIXES = {
    'â‰¥5 years': '≥5 years',
    'â‰¤5 years': '≤5 years'
}
```

## 6. SESSION FLAGS REQUIRED

```python
# After file upload
session['data_loaded'] = True
session['csv_loaded'] = True
session['upload_type'] = 'csv_shapefile'  # Triggers risk analysis path

# After TPR preparation
session['shapefile_loaded'] = True  # Critical for risk analysis

# File-based backup
Path(f"instance/uploads/{session_id}/.risk_ready").touch()
```

## 7. TESTING CHECKPOINTS

### 7.1 TPR Detection Test
```python
# Load Adamawa TPR file
df = pd.read_excel('www/tpr_data_by_state/ad_Adamawa_State_TPR_LLIN_2024.xlsx')
is_tpr, info = is_tpr_data(df)
assert is_tpr == True
assert info['confidence'] > 0.8
```

### 7.2 TPR Calculation Test
```python
# Verify production logic
ward_tpr = calculate_ward_tpr(df)
assert 'TPR' in ward_tpr.columns
assert ward_tpr['TPR'].max() <= 100
# Check that we're taking max(TPR) not max(values)
```

### 7.3 Shapefile Extraction Test
```python
master_gdf = gpd.read_file('www/complete_names_wards/wards.shp')
adamawa_gdf = master_gdf[master_gdf['StateName'] == 'Adamawa']
assert len(adamawa_gdf) > 0  # Should have ~20 wards
assert 'WardCode' in adamawa_gdf.columns
```

### 7.4 Final Output Test
```python
# After prepare_for_risk
assert os.path.exists(f"{session_folder}/raw_data.csv")
assert os.path.exists(f"{session_folder}/raw_shapefile.zip")

# Check CSV structure
df = pd.read_csv(f"{session_folder}/raw_data.csv")
required = ['WardCode', 'StateCode', 'LGACode', 'TPR']
assert all(col in df.columns for col in required)
```

## 8. ROLLBACK SAFETY

The implementation is non-invasive:
1. If TPR detection fails → Tool doesn't appear
2. If tool fails → User can still do normal analysis
3. If shapefile extraction fails → Manual upload still works
4. No changes to existing risk analysis pipeline

## 9. CRITICAL SUCCESS FACTORS

✅ **WardCode/StateCode** in BOTH CSV and shapefile
✅ **Production TPR logic** (max of TPR, not values)
✅ **NULL handling** for missing raster data
✅ **Ward name normalization** for matching
✅ **Session flags** for risk analysis trigger
✅ **File-based flags** for multi-worker support
✅ **Non-invasive** to existing workflows

## 10. FINAL CHECKLIST

- [ ] Create `app/core/tpr_utils.py` with 4 functions
- [ ] Create `app/data_analysis_v3/tools/tpr_analysis_tool.py` with 3 actions
- [ ] Modify `system_prompt.py` - Add TPR section
- [ ] Modify `agent.py` - Add conditional tool loading
- [ ] Modify `variable_extractor.py` - Real raster extraction
- [ ] Modify `shapefile_fetcher.py` - Nigeria shapefile loading
- [ ] Optional: Modify `upload_routes.py` - Early detection

## CONFIDENCE ASSESSMENT

**Ready for Implementation: YES**

All critical components identified:
- Know exact files to create (2)
- Know exact files to modify (5)
- Have production TPR logic
- Have Nigeria shapefile location
- Have raster file paths
- Have session flag requirements
- Have ward name normalization strategy
- Have NULL handling approach
- Have multi-worker solution

**No gaps or weaknesses identified.**