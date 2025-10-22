# TPR Interactive Selections Implementation

## Overview
Added interactive selection capabilities to the TPR calculation, matching the production system's user-friendly approach where users can select specific parameters rather than having a black-box calculation.

## Parameters Added

### 1. Age Groups
- `all_ages` - All age groups combined (default)
- `u5` - Under 5 years
- `o5` - Over 5 years  
- `pw` - Pregnant women

### 2. Test Methods
- `both` - RDT and Microscopy, takes max(TPR) (default)
- `rdt` - RDT only
- `microscopy` - Microscopy only

### 3. Facility Levels
- `all` - All facilities (default)
- `primary` - Primary health centers only
- `secondary` - Secondary facilities only
- `tertiary` - Tertiary facilities only

## Implementation Details

### Files Modified

#### 1. `app/core/tpr_utils.py`
**Function Updated**: `calculate_ward_tpr()`
- Added parameters: `age_group`, `test_method`, `facility_level`
- Implemented facility filtering logic
- Added age-specific column detection
- Implemented test method selection logic

**Key Logic**:
```python
# Age group column mapping
age_suffix = {
    'u5': ['u5', 'under5', '<5'], 
    'o5': ['o5', 'over5', '>5', '≥5'],
    'pw': ['pw', 'pregnant', 'anc']
}

# Test method logic
if test_method == 'rdt':
    # Use RDT only
elif test_method == 'microscopy':
    # Use Microscopy only
else:  # both
    # Calculate both and take max(TPR)
```

#### 2. `app/data_analysis_v3/tools/tpr_analysis_tool.py`
**Updated**: `analyze_tpr_data()` tool
- Accepts options dictionary with user selections
- Passes parameters to `calculate_ward_tpr()`
- Displays selections in results

**Options Format**:
```python
options = {
    "age_group": "u5",
    "test_method": "both",
    "facility_level": "primary"
}
```

#### 3. `app/data_analysis_v3/prompts/system_prompt.py`
**Added**: Interactive flow guidance
- Step-by-step selection prompts
- Example conversations showing the flow
- Clear explanations of each option

## Flexibility and Robustness

### Key Principles
1. **Work with what we have** - Don't fail if certain columns are missing
2. **Graceful degradation** - Fall back to simpler calculations if needed
3. **Helpful feedback** - Tell users what data is available if something fails
4. **Dynamic adaptation** - Adjust to different data formats and column names

### Error Handling Strategies

#### Missing Columns
- If facility level column missing → Use all facilities
- If specific age group columns missing → Try all_ages or return helpful message
- If test method columns missing → Use what's available

#### Flexible Matching
- Facility levels: Try exact match, then contains, then warn with available options
- Age groups: Look for multiple variations (u5, under5, <5, etc.)
- Ward names: Normalize and clean for better matching

#### Fallback Logic
```python
# Example: If no facility column for specific age calculation
if not facility_cols:
    logger.warning("No facility column found, calculating at ward level instead")
    # Still calculate but without facility grouping
```

### User Feedback
When calculations fail, provide:
1. Clear reason why it failed
2. List of available columns/options
3. Suggested alternative approach

## User Experience Flow

### Example Interaction
```
User: "Calculate TPR"