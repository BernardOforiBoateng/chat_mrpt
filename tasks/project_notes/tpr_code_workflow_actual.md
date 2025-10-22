# TPR Workflow - Actual Code Flow

## Complete TPR Processing Steps from Code

### 1. **File Upload & Detection** (`upload_detector.py`)
```python
def detect_tpr_upload():
    # Check if Excel file (.xlsx, .xls)
    # Check for 'raw' sheet
    # Check for specific columns:
    #   - 'Persons tested positive for malaria by RDT <5yrs'
    #   - 'Persons presenting with fever & tested by RDT <5yrs'
```

### 2. **Parse NMEP File** (`nmep_parser.py`)
```python
def parse_file():
    # Step 1: Read 'raw' sheet specifically
    self.data = pd.read_excel(file_path, sheet_name='raw')
    
    # Step 2: Apply column mapping
    self.data = mapper.map_columns(self.data)
    
    # Step 3: Clean state names (remove prefix)
    self.data['State_clean'] = self.data['state'].apply(lambda x: self._clean_state_name(x))
    
    # Step 4: Clean ward names (remove prefix)
    self.data['WardName'] = self.data['ward'].apply(lambda x: self._clean_ward_name(x))
    
    # Step 5: Extract metadata (year, month, states)
```

### 3. **TPR Pipeline Processing** (`tpr_pipeline.py`)
```python
def run():
    # Step 1: Map columns to standard names
    mapped_data = self.column_mapper.map_nmep_columns(nmep_data)
    
    # Step 2: Filter for selected state
    state_data = self._filter_state_data(mapped_data, state_name)
    
    # Step 3: Apply facility level filter
    filtered_data = self.facility_filter.filter_by_level(state_data, facility_level)
    
    # Step 4: Apply age group filter
    age_filtered_data = self._apply_age_filter(filtered_data, age_group)
    
    # Step 5: Calculate TPR
    tpr_results = self.calculator.calculate_tpr(age_filtered_data)
    
    # Step 6: Aggregate to ward level
    ward_results = self._aggregate_to_wards(tpr_results)
    
    # Step 7: Match with shapefile boundaries
    matched_results = self._match_with_shapefile(ward_results, state_boundaries)
    
    # Step 8: Detect thresholds and recommendations
    threshold_results = self.threshold_detector.detect_thresholds(matched_results)
    
    # Step 9: Extract environmental variables
    final_results = self.raster_extractor.extract_zone_variables(matched_results, zone)
    
    # Step 10: Generate outputs
    output_paths = self.output_generator.generate_outputs(final_results, state_name)
```

## Key Files in Order of Execution

### 1. Entry Point
- **`upload_detector.py`**: Detects if uploaded file is TPR
  - Checks for Excel format
  - Looks for 'raw' sheet ← **RIGID!**
  - Checks for specific column names ← **RIGID!**

### 2. Data Loading
- **`nmep_parser.py`**: Parses the Excel file
  - Hardcoded to read 'raw' sheet ← **NEEDS CHANGE**
  - Has fixed column mappings ← **NEEDS CHANGE**
  
### 3. Column Mapping
- **`column_mapper.py`**: Maps columns to standard names
  - Has dictionary of expected column names
  - Maps variations like "Health Faccility" → "facility"
  - Missing mappings for "orgunitlevel2" etc. ← **NEEDS UPDATE**

### 4. Processing Pipeline
- **`tpr_pipeline.py`**: Main processing workflow
  - Uses mapped column names throughout
  - All logic is column-name agnostic (good!)
  - Just needs correct mapped names

### 5. TPR Calculation
- **`tpr_calculator.py`**: Calculates positivity rates
  ```python
  # Example calculation
  tpr = (positive_cases / tested_cases) * 100
  ```

### 6. Output Generation
- **`output_generator.py`**: Creates maps and reports
- **`tpr_visualizer.py`**: Generates visualizations

## The Critical Points for Dynamic Detection

### 1. **Detection Phase** (`upload_detector.py` line 78)
```python
# CURRENT (Rigid):
if 'raw' not in excel_file.sheet_names:
    return False

# NEEDED (Flexible):
# Find any sheet with data
data_sheet = find_data_sheet(excel_file)
```

### 2. **Column Check** (`upload_detector.py` lines 83-87)
```python
# CURRENT (Rigid):
required_cols = [
    'Persons tested positive for malaria by RDT <5yrs',
    'Persons presenting with fever & tested by RDT <5yrs'
]

# NEEDED (Flexible):
# Use pattern matching
has_test_columns = detect_test_columns(df)
```

### 3. **Parsing** (`nmep_parser.py` line 108)
```python
# CURRENT (Rigid):
self.data = pd.read_excel(file_path, sheet_name='raw')

# NEEDED (Flexible):
sheet_name = detect_data_sheet(file_path)
self.data = pd.read_excel(file_path, sheet_name=sheet_name)
```

### 4. **Column Mapping** (`column_mapper.py`)
```python
# CURRENT (Missing):
# No mappings for orgunitlevel2, orgunitlevel3, etc.

# NEEDED (Add):
'orgunitlevel2': 'state',
'orgunitlevel3': 'lga',
'orgunitlevel4': 'ward',
'orgunitlevel5': 'facility'
```

## Summary: Where to Make Changes

**Only 4 files need updates:**
1. `upload_detector.py` - Make sheet/column detection flexible
2. `nmep_parser.py` - Load any sheet, not just 'raw'
3. `column_mapper.py` - Add new column mappings
4. `tpr_pipeline.py` - Already flexible! Just uses mapped names

**Everything else stays the same!** The actual TPR calculations, aggregations, visualizations all work perfectly once we get the columns mapped correctly.