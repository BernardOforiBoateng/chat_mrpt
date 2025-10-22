# TPR Workflow - Complete Step-by-Step Process

## What is TPR Analysis?
TPR (Test Positivity Rate) analysis processes malaria testing data from health facilities to calculate positivity rates and identify high-burden areas for intervention.

## Current TPR Workflow in ChatMRPT

### 1. **File Upload** (`/upload` route)
```
User uploads TPR Excel file → System receives file
```

### 2. **File Detection** (`upload_detector.py`)
```python
# Current flow:
if is_tpr_file(file):
    # Checks for specific sheet names ('raw', 'pivot', 'tpr')
    # Checks for specific columns
    process_as_tpr()
else:
    process_as_regular_data()
```

### 3. **Data Parsing** (`nmep_parser.py`)
```python
# Current rigid process:
1. Load 'raw' sheet specifically
2. Look for exact column names:
   - 'State', 'LGA', 'Ward', 'Health Facility'
   - 'RDT tested <5', etc.
3. Fail if columns don't match exactly
```

### 4. **Data Processing** (`tpr_pipeline.py`)
```python
# Main processing steps:
1. Clean data (remove nulls, fix types)
2. Aggregate to ward level
3. Calculate positivity rates:
   - TPR = (Positive Cases / Total Tested) × 100
4. Merge with shapefile for geographic data
5. Generate rankings and classifications
```

### 5. **Analysis & Visualization** (`tpr_processor.py`)
```python
# Generate outputs:
1. Ward-level TPR statistics
2. Facility-level rankings
3. Create visualizations:
   - Choropleth maps (TPR by ward)
   - Facility marker maps
   - Statistical charts
4. Generate insights and recommendations
```

### 6. **Results Delivery** (`tpr_conversation_manager.py`)
```python
# Present to user:
1. Summary statistics
2. Interactive maps
3. Downloadable reports
4. AI-generated insights
```

## Detailed Workflow Breakdown

### Step 1: File Upload & Initial Detection
```
USER ACTION: Uploads "NMEP TPR and LLIN 2024.xlsx"
                            ↓
SYSTEM: Receives file in /upload endpoint
                            ↓
upload_detector.py: Checks if this is TPR data
    - Looks for test columns
    - Checks for location hierarchy
    - Identifies file type
```

### Step 2: Data Loading & Column Detection
```
CURRENT (Rigid):
    → Looks for 'raw' sheet
    → Expects exact column names
    → Fails if different

PROPOSED (Flexible):
    → Loads any sheet with data
    → Detects columns by pattern
    → Maps to internal names
```

### Step 3: Data Validation & Cleaning
```
Validate:
    - Test data integrity (positive ≤ tested)
    - Location hierarchy completeness
    - Date format consistency

Clean:
    - Remove empty rows
    - Fix encoding issues (≥ vs >=)
    - Standardize location names
```

### Step 4: Core TPR Calculations
```python
For each Ward:
    1. Sum all tested cases
    2. Sum all positive cases
    3. Calculate TPR = (positive/tested) × 100
    
For each Facility:
    1. Calculate facility-specific TPR
    2. Rank within ward
    3. Classify risk level (High/Medium/Low)
```

### Step 5: Geospatial Integration
```
1. Load shapefile with ward boundaries
2. Match TPR data to geographic areas:
    - Fuzzy match ward names
    - Handle spelling variations
3. Create spatial dataset for mapping
```

### Step 6: Visualization Generation
```
Maps Created:
1. Ward Choropleth Map
    - Color-coded by TPR levels
    - Interactive tooltips
    
2. Facility Marker Map
    - Sized by case volume
    - Colored by TPR
    
3. Statistical Charts
    - TPR trends over time
    - Comparative analysis
```

### Step 7: Report Generation
```
Generate comprehensive report:
1. Executive Summary
2. Key Findings:
    - Highest burden wards
    - Facilities needing intervention
3. Detailed Statistics
4. Recommendations
5. Exportable data files
```

## The Complete Flow Diagram

```
┌─────────────────┐
│ User Uploads    │
│ TPR Excel File  │
└────────┬────────┘
         ↓
┌─────────────────┐
│ File Detection  │ ← Where we need flexibility!
│ (Is this TPR?)  │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Column Mapping  │ ← Core improvement area
│ (Find columns)  │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Data Validation │
│ & Cleaning      │
└────────┬────────┘
         ↓
┌─────────────────┐
│ TPR Calculation │
│ (Ward & Facility)│
└────────┬────────┘
         ↓
┌─────────────────┐
│ Merge with      │
│ Shapefile       │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Generate Maps   │
│ & Visualizations│
└────────┬────────┘
         ↓
┌─────────────────┐
│ Create Reports  │
│ & Insights      │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Display Results │
│ to User         │
└─────────────────┘
```

## Key Files in the Workflow

1. **Entry Points**:
   - `app/web/routes/upload_routes.py` - File upload
   - `app/tpr_module/integration/upload_detector.py` - TPR detection

2. **Data Processing**:
   - `app/tpr_module/data/nmep_parser.py` - Parse Excel ← Needs update!
   - `app/tpr_module/core/tpr_pipeline.py` - Main processing ← Needs update!
   - `app/tpr_module/data/column_mapper.py` - Column mapping ← Replace!

3. **Analysis & Output**:
   - `app/tpr_module/analysis/tpr_processor.py` - Calculate TPR
   - `app/tpr_module/services/shapefile_extractor.py` - Merge geo data
   - `app/tpr_module/visualizations/tpr_visualizer.py` - Create maps

4. **User Interface**:
   - `app/tpr_module/core/tpr_conversation_manager.py` - Chat interface
   - `app/tpr_module/output/output_generator.py` - Format results

## What Changes with Dynamic Detection

### Before (Current):
```python
# Rigid expectations
if sheet_name != 'raw':
    raise Error("Expected 'raw' sheet")
if 'State' not in columns:
    raise Error("Missing 'State' column")
```

### After (Proposed):
```python
# Flexible detection
sheets = find_data_sheets(file)
columns = detect_column_types(sheet)
mapping = {
    'state': columns['hierarchy'][0],  # Whatever the state column is called
    'tested_<5': columns['test_data']['rdt_tested_under_5']  # Detected by pattern
}
# Process with mapped columns
```

## Success Metrics

1. **File Acceptance Rate**: From 1 format → Any format
2. **Processing Success**: 95%+ files process without error
3. **User Experience**: Clear feedback on what was detected
4. **Accuracy**: TPR calculations remain accurate
5. **Performance**: <5 seconds for 300K rows

This workflow understanding helps us see exactly where to inject flexibility (Steps 2-3) while keeping the rest of the robust pipeline intact!