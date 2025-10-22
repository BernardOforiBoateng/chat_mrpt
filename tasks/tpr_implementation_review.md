# TPR Implementation Review - Complete Flow Analysis

## 1. USER JOURNEY FLOW

```
User uploads TPR file (e.g., ad_Adamawa_State_TPR_LLIN_2024.xlsx)
                ↓
    Data Analysis V3 Tab (existing endpoint)
                ↓
    File saved to instance/uploads/{session_id}/
                ↓
    TPR Detection (automatic)
                ↓
    TPR Tool Available in Chat
                ↓
    User: "Calculate TPR" or "Prepare for risk analysis"
                ↓
    TPR Tool Executes
                ↓
    Creates raw_data.csv + raw_shapefile.zip
                ↓
    Risk Analysis Ready
```

## 2. FILES TO CREATE (Only 2 New Files)

### 2.1 `app/core/tpr_utils.py` (NEW)
```python
def is_tpr_data(df: pd.DataFrame) -> Tuple[bool, dict]:
    """
    Detect TPR data by checking columns
    Returns: (is_tpr, confidence_info)
    """
    
def calculate_ward_tpr(df: pd.DataFrame, method='standard') -> pd.DataFrame:
    """
    Calculate TPR using production logic:
    - All ages: Sum first, calc TPR for each method, take max(TPR)
    - Specific age: Max at facility, then sum
    Returns: DataFrame with WardName, LGA, TPR, Total_Tested, Total_Positive
    """
    
def normalize_ward_name(name: str) -> str:
    """Remove prefixes like 'ad ', suffixes like ' Ward'"""
    
def extract_state_from_data(df: pd.DataFrame) -> str:
    """Extract state name from 'ad Adamawa State' format"""
```

### 2.2 `app/data_analysis_v3/tools/tpr_analysis_tool.py` (NEW)
```python
@tool
def analyze_tpr_data(
    thought: str,
    action: str = "analyze",  # analyze, calculate_tpr, prepare_for_risk
    options: str = "{}",
    graph_state: InjectedState = None
) -> str:
    """
    Main TPR tool that:
    1. Detects TPR data automatically
    2. Calculates TPR when requested
    3. Prepares for risk analysis
    """
    
    if action == "calculate_tpr":
        # Use tpr_utils.calculate_ward_tpr()
        # Return formatted results
        
    elif action == "prepare_for_risk":
        # Step 1: Calculate TPR
        ward_tpr = calculate_ward_tpr(df)
        
        # Step 2: Load Nigeria shapefile
        master_gdf = gpd.read_file('www/complete_names_wards/wards.shp')
        state_gdf = master_gdf[master_gdf['StateName'] == state_name]
        
        # Step 3: Join to get WardCode, StateCode, LGACode
        merged = match_and_join_ward_data(ward_tpr, state_gdf)
        
        # Step 4: Extract environmental (with NULLs where no raster)
        env_data = extract_from_rasters(merged)
        
        # Step 5: Create final dataset with all columns
        final_df = prepare_final_dataset(merged, env_data)
        
        # Step 6: Save as raw_data.csv
        final_df.to_csv(f"{session_folder}/raw_data.csv")
        
        # Step 7: Create raw_shapefile.zip
        create_shapefile_package(state_gdf, final_df, session_folder)
        
        # Step 8: Set session flags
        set_risk_analysis_flags(session_id)
```

## 3. FILES TO MODIFY (5 Files)

### 3.1 `app/data_analysis_v3/prompts/system_prompt.py` (MODIFY)
**Current**: Basic data analysis prompts
**Add**: TPR-specific section
```python
# Add to MAIN_SYSTEM_PROMPT
"""
## TPR Data Detection and Handling

When you detect Test Positivity Rate data (columns containing RDT, Microscopy, LLIN):

1. Inform the user: "I've detected TPR data! You can analyze it normally, 
   plus calculate TPR metrics and prepare for risk analysis."

2. Use analyze_tpr_data tool with these actions:
   - action="analyze" for exploration
   - action="calculate_tpr" for TPR calculation  
   - action="prepare_for_risk" to create risk analysis files

3. TPR Calculation Rules:
   - All ages: Calculate TPR for each method, then max(TPR)
   - Specific age: Max at facility level, then aggregate
"""
```

### 3.2 `app/data_analysis_v3/core/agent.py` (MODIFY)
**Current Line ~51**: `self.tools = [analyze_data]`
**Change to**:
```python
# Line 51-55 (approximately)
self.tools = [analyze_data]

# Add TPR tool if TPR data detected
from app.core.tpr_utils import is_tpr_data
data = self._load_session_data()  # Need to add this method
if data is not None:
    is_tpr, _ = is_tpr_data(data)
    if is_tpr:
        from ..tools.tpr_analysis_tool import analyze_tpr_data
        self.tools.append(analyze_tpr_data)
```

### 3.3 `app/services/variable_extractor.py` (MODIFY)
**Current Lines 160-170**: Using placeholder random values
**Change to**: Real raster extraction
```python
def _extract_environmental_variable(self, areas: List[Dict], var_name: str) -> List[float]:
    """Extract from actual raster files"""
    
    # Map variable to raster file
    raster_map = {
        'rainfall': 'rasters/rainfall_monthly/*.tif',
        'temperature': 'rasters/temperature_monthly/*.tif',
        'EVI': 'rasters/EVI/*.tif',
        'NDVI': 'rasters/NDVI/*.tif',
        'elevation': 'rasters/Elevation/*.tif'
    }
    
    # Extract actual values using rasterio
    import rasterio
    values = []
    for area in areas:
        # Get ward centroid or polygon
        coord = get_ward_centroid(area['WardCode'])
        
        # Sample raster at coordinate
        with rasterio.open(raster_path) as src:
            value = list(src.sample([coord]))[0]
            values.append(value if value != src.nodata else None)
    
    return values
```

### 3.4 `app/services/shapefile_fetcher.py` (MODIFY)
**Current Lines 150-180**: Creating placeholder geometries
**Change to**: Use real Nigeria shapefile
```python
def extract_state_shapefile(self, state_name: str, tpr_data: pd.DataFrame) -> str:
    """Extract from Nigeria master shapefile"""
    
    # Load master shapefile
    master_gdf = gpd.read_file('www/complete_names_wards/wards.shp')
    
    # Filter by state
    clean_state = state_name.replace(' State', '').strip()
    state_gdf = master_gdf[master_gdf['StateName'] == clean_state]
    
    # Match ward names with fuzzy matching
    matched_gdf = self._match_wards(state_gdf, tpr_data)
    
    # Package as ZIP
    return self._create_shapefile_zip(matched_gdf)
```

### 3.5 `app/web/routes/upload_routes.py` (MODIFY - Optional)
**Lines 175-180**: After file upload
**Add**: TPR detection flag
```python
# Optional - helps with early detection
from app.core.tpr_utils import is_tpr_data
if csv_file:
    df = pd.read_csv(csv_file) if csv_file.filename.endswith('.csv') else pd.read_excel(csv_file)
    is_tpr, info = is_tpr_data(df)
    if is_tpr:
        session['has_tpr_data'] = True
        session['tpr_confidence'] = info['confidence']
```

## 4. POTENTIAL WEAKNESSES & SOLUTIONS

### Weakness 1: Ward Name Matching
**Issue**: TPR has "ad Girei Ward", Shapefile has "Girei"
**Solution**: Normalize both sides
```python
def normalize_ward_name(name):
    # Remove state prefixes
    name = re.sub(r'^[a-z]{2}\s+', '', name, flags=re.IGNORECASE)
    # Remove 'Ward' suffix
    name = re.sub(r'\s+Ward$', '', name, flags=re.IGNORECASE)
    # Remove extra spaces
    return name.strip()
```

### Weakness 2: Missing Raster Data
**Issue**: Not all regions have raster coverage
**Solution**: Return NULL, don't fail
```python
try:
    value = extract_from_raster(coord)
except (FileNotFoundError, ValueError):
    value = None  # NULL in CSV
```

### Weakness 3: Session State Across Workers
**Issue**: Multiple workers might not share session
**Solution**: Use file-based flags
```python
# Write flag file
flag_file = f"instance/uploads/{session_id}/.risk_ready"
Path(flag_file).touch()

# Check in risk analysis
if Path(f"instance/uploads/{session_id}/.risk_ready").exists():
    # Ready for risk analysis
```

### Weakness 4: Large Shapefile Loading
**Issue**: Master shapefile has 9,410 features
**Solution**: Cache in memory or use spatial index
```python
# Cache shapefile on first load
@lru_cache(maxsize=1)
def load_nigeria_shapefile():
    return gpd.read_file('www/complete_names_wards/wards.shp')
```

## 5. TESTING CHECKPOINTS

### Checkpoint 1: TPR Detection
```python
# Test with Adamawa file
df = pd.read_excel('www/tpr_data_by_state/ad_Adamawa_State_TPR_LLIN_2024.xlsx')
is_tpr, info = is_tpr_data(df)
assert is_tpr == True
assert info['confidence'] > 0.8
```

### Checkpoint 2: TPR Calculation
```python
# Verify production logic
ward_tpr = calculate_ward_tpr(df)
assert 'TPR' in ward_tpr.columns
assert ward_tpr['TPR'].max() <= 100
# Verify max logic matches production
```

### Checkpoint 3: Shapefile Extraction
```python
# Test state filtering
master_gdf = gpd.read_file('www/complete_names_wards/wards.shp')
adamawa_gdf = master_gdf[master_gdf['StateName'] == 'Adamawa']
assert len(adamawa_gdf) > 0  # Should have Adamawa wards
```

### Checkpoint 4: Environmental Extraction
```python
# Test raster reading
import rasterio
with rasterio.open('rasters/rainfall_monthly/some_file.tif') as src:
    # Verify we can read values
    assert src.crs is not None
```

### Checkpoint 5: Final Files
```python
# After prepare_for_risk
assert os.path.exists(f"{session_folder}/raw_data.csv")
assert os.path.exists(f"{session_folder}/raw_shapefile.zip")

# Check CSV has required columns
df = pd.read_csv(f"{session_folder}/raw_data.csv")
required = ['WardCode', 'StateCode', 'LGACode', 'TPR']
assert all(col in df.columns for col in required)
```

## 6. ENDPOINT FLOW

```
POST /upload_both_files
    → Saves file to instance/uploads/{session_id}/
    → Sets session['data_loaded'] = True

GET /stream (Data Analysis V3 chat)
    → Loads data
    → Detects TPR
    → Adds TPR tool if detected
    → User interacts with tool

Tool execution:
    → analyze_tpr_data(action="prepare_for_risk")
    → Creates raw_data.csv + raw_shapefile.zip
    → Sets flags

Risk Analysis:
    → Checks for raw_data.csv existence
    → Loads and proceeds with analysis
```

## 7. CRITICAL SUCCESS FACTORS

1. **WardCode Preservation**: MUST include WardCode in both CSV and shapefile
2. **NULL Handling**: Environmental variables can be NULL
3. **Production TPR Logic**: Must match exactly (max of TPR, not max of values for all ages)
4. **State Name Normalization**: Handle "Adamawa" vs "ad Adamawa State"
5. **Session Flags**: Set all required flags for risk analysis

## 8. ROLLBACK PLAN

If implementation fails:
1. TPR tool simply won't appear (non-invasive)
2. Users can still do normal data analysis
3. No changes to risk analysis pipeline
4. Can manually prepare files as fallback

## FINAL CONFIDENCE CHECK

✅ Know exactly what files to create (2)
✅ Know exactly what files to modify (5)
✅ Have production TPR logic documented
✅ Have Nigeria shapefile location and structure
✅ Have raster database locations
✅ Know session flag requirements
✅ Have ward name normalization strategy
✅ Have NULL handling strategy
✅ Non-invasive to existing workflows

**Ready for implementation!**