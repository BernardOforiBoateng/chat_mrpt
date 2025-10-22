# TPR Module Implementation Plan

## Overview
The TPR module is a **standalone, conversational system** that guides users through TPR calculation and outputs standard CSV + Shapefile for the main ChatMRPT upload flow.

## Key Concept: TPR as a Pre-Processing Branch
```
User uploads NMEP Excel → TPR Module (Interactive Journey) → Standard CSV + Shapefile → Main Upload Flow
```

## Module Architecture

### 1. Core Components (`app/tpr_module/core/`)
- **`tpr_conversation_manager.py`** - Manages the interactive conversation flow
- **`tpr_state_manager.py`** - Tracks conversation state and user choices
- **`tpr_calculator.py`** - Core TPR calculation logic with RDT vs Microscopy comparison

### 2. Data Processing (`app/tpr_module/data/`)
- **`nmep_parser.py`** - Parses NMEP Excel files (focus on raw sheet)
- **`column_mapper.py`** - Maps NMEP columns to standard names
- **`data_validator.py`** - Validates data quality and completeness

### 3. Services (`app/tpr_module/services/`)
- **`state_selector.py`** - Handles state selection logic
- **`facility_filter.py`** - Filters by facility level (Primary, Secondary, etc.)
- **`threshold_detector.py`** - Detects 50% threshold violations
- **`alternative_calculator.py`** - Calculates TPR using outpatient denominator
- **`gee_variable_fetcher.py`** - Fetches environmental variables from GEE
- **`shapefile_extractor.py`** - Extracts state/ward boundaries from Nigerian shapefile

### 4. Visualization (`app/tpr_module/visualization/`)
- **`tpr_map_generator.py`** - Creates interactive TPR maps
- **`comparison_visualizer.py`** - Side-by-side map comparisons
- **`data_quality_visualizer.py`** - Shows missingness and data quality

### 5. Output Generation (`app/tpr_module/output/`)
- **`csv_generator.py`** - Creates standard CSV with TPR + environmental variables
- **`shapefile_packager.py`** - Packages shapefile for selected state
- **`report_generator.py`** - Creates methodology report

## Conversation Flow Implementation

### Step 1: File Upload Detection
```python
# When NMEP Excel uploaded, detect it's TPR data
if "Persons tested positive for malaria" in excel_columns:
    return TPRConversationManager.start()
```

### Step 2: Data Summary
```python
# Show comprehensive data overview
"I've analyzed your NMEP TPR data:
- 3 states found: Adamawa, Kwara, Osun
- 36 months of data (2022-2024)
- 2,632 health facilities
Which state would you like to analyze?"
```

### Step 3: State Selection
```python
# User selects state
selected_state = get_user_choice()
filter_data_to_state(selected_state)
```

### Step 4: Facility Level Selection
```python
# Recommend Primary facilities
"For Adamawa, I recommend Primary Health Facilities (91% of data).
They better reflect community transmission. OK?"
```

### Step 5: Age Group Selection
```python
# Show data availability
"Which age group for TPR calculation?
- Under 5: 68% data complete (recommended)
- Over 5: 71% data complete
- Pregnant Women: 25% data complete"
```

### Step 6: Column Comparison & Calculation
```python
# RDT vs Microscopy logic
for facility in facilities:
    numerator = max(rdt_positive, microscopy_positive)
    denominator = max(rdt_tested, microscopy_tested)
    facility_tpr = (numerator / denominator) * 100
```

### Step 7: Threshold Check & Alternative
```python
if any(ward_tpr > 50 and is_urban):
    show_map_with_problems()
    ask_user("These values seem high. Recalculate?")
    if yes:
        alternative_tpr = positive / outpatient_attendance * 100
```

### Step 8: Final Output Generation
```python
# Generate standard files
csv_data = combine_tpr_with_gee_variables()
shapefile = extract_state_boundaries()
return {
    'csv': 'adamawa_tpr_analysis.csv',
    'shapefile': 'adamawa_boundaries.zip'
}
```

## Integration with Main ChatMRPT

### Entry Point
```python
# In main upload handler
if is_tpr_file(uploaded_file):
    # Redirect to TPR module
    result = TPRModule.process_interactively(uploaded_file)
    # Result contains standard CSV + Shapefile
    # Continue with normal upload flow
    return process_standard_upload(result['csv'], result['shapefile'])
```

### No UI Changes Required
- Uses existing chat interface
- Maps and visualizations appear in chat
- User types responses naturally
- Progress shown in conversation

## Key Differences from Current Implementation

### Current (To Remove)
- Direct parsing to convergence format
- State selection in upload modal
- No user interaction during processing
- Mixed into main codebase

### New Modular Approach
- Interactive conversation flow
- Step-by-step validation
- Outputs standard CSV format
- Completely separate module
- Joins main flow at upload

## Development Strategy

### Phase 1: Core Infrastructure
1. Set up module structure
2. Create conversation manager
3. Implement NMEP parser
4. Basic TPR calculation

### Phase 2: Interactive Flow
1. State selection conversation
2. Facility level filtering
3. Age group selection
4. Threshold detection

### Phase 3: Visualizations
1. TPR maps in chat
2. Side-by-side comparisons
3. Data quality indicators

### Phase 4: Output & Integration
1. CSV generation with GEE variables
2. Shapefile extraction
3. Integration with main upload
4. Testing and refinement

## Benefits of This Approach

1. **Modularity** - Can develop/test without touching main code
2. **Educational** - Users understand TPR calculation process
3. **Flexible** - Easy to modify conversation flow
4. **Standard Output** - Works with existing upload pipeline
5. **No UI Changes** - Uses familiar chat interface

## Testing Strategy

### Unit Tests
- TPR calculation accuracy
- Column comparison logic
- Threshold detection

### Integration Tests
- Full conversation flow
- Output file generation
- Main upload integration

### User Tests
- Conversation clarity
- Map interpretability
- Decision points

This modular approach ensures clean separation while providing the interactive, educational experience your supervisors want.