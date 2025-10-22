# TPR Workflow Formatting Fixes - January 25, 2025

## Problem Summary
The TPR (Test Positivity Rate) workflow in Data Analysis V3 had several formatting and content issues:
1. Only showing 2 of 4 age groups (missing Over 5 Years and Pregnant Women)
2. Bullet points running together on single lines without proper formatting
3. Incorrect positivity rates displayed during age group selection
4. Prompt text saying "1-4" even when fewer options were available
5. Column sanitization breaking age group pattern matching

## Investigation Findings

### Root Cause Analysis
1. **Column Sanitization Issue**: The `ColumnSanitizer` was converting special characters:
   - `<5` → `lt_5` 
   - `≥5` → `gte_5`
   - This broke pattern matching in `tpr_data_analyzer.py`

2. **Pattern Matching**: Age group detection patterns only looked for original column names, not sanitized versions

3. **Formatting Issues**: Missing line breaks (`\n`) between bullet points in `MessageFormatter`

4. **Static Prompts**: Hardcoded "(1-4)" instead of dynamically matching available options

## Solutions Implemented

### 1. Enhanced Age Group Detection (tpr_data_analyzer.py)
```python
# Added patterns for both original and sanitized column names
'under_5': {
    'test_patterns': ['<5', 'u5', 'under 5', 'under_5', '≤5', 
                    'lt_5', 'lte_5', '5yrs', '_5yr', 'lt5', 'lte5',
                    'children', 'child'],  # Added sanitized versions
}
```

### 2. Improved Column Pattern Matching
- Added regex support for complex patterns
- Fallback to substring matching if regex fails
- Debug logging for pattern matching results

### 3. Fixed Message Formatting (formatters.py)
```python
# Added proper line breaks
message += f"**{option_number}. {group['name']}** {group.get('icon', '')}"
message += "\n"  # Line break after title

# Statistics with proper formatting
message += f"   • {group['tests_available']:,} tests available\n"
message += f"   • Current positivity: {group['positivity_rate']:.1f}%\n"
message += f"   • {group['description']}\n\n"  # Double line break
```

### 4. Dynamic Prompt Generation
```python
# Update prompt to match actual available options
if len(available_options) == 1:
    message += f"\nEnter {available_options[0]} to proceed:"
elif len(available_options) == 2:
    message += f"\nWhich age group? ({available_options[0]} or {available_options[1]}):"
else:
    message += f"\nWhich age group? ({available_options[0]}-{available_options[-1]}):"
```

### 5. Improved Positivity Rate Calculation
- Special handling for "all ages" to sum across all test columns
- Better numeric type checking before summing
- Separate test and positive column detection

## Files Modified
1. `app/data_analysis_v3/core/tpr_data_analyzer.py`
   - Enhanced age group pattern matching
   - Added debug logging
   - Improved column finding methods
   - Better positivity rate calculation

2. `app/data_analysis_v3/core/formatters.py`
   - Fixed line breaks in all formatting methods
   - Dynamic prompt generation
   - Consistent formatting across messages

## Testing Results
- Created `test_tpr_formatting.py` to validate fixes
- Successfully detected 3 of 4 age groups (Pregnant Women missing in test data)
- Formatting displays correctly with proper line breaks
- Prompts match actual available options
- Positivity rates calculate accurately

## Deployment
- Deployed to both staging instances:
  - Instance 1: 3.21.167.170
  - Instance 2: 18.220.103.20
- Services restarted successfully
- Available for testing at: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com

## Lessons Learned
1. **Column Sanitization Impact**: Always consider how data transformations affect downstream pattern matching
2. **Pattern Robustness**: Include patterns for both original and transformed data
3. **Dynamic UI**: Never hardcode option counts - always calculate dynamically
4. **Testing with Real Data**: Test with actual production data files to catch edge cases

## Future Improvements
1. Consider preserving original column names alongside sanitized versions
2. Add more comprehensive pattern matching for age groups
3. Implement fuzzy matching for column detection
4. Add unit tests for each formatter method

## Impact
These fixes ensure:
- All available age groups are detected and displayed
- Clean, readable formatting for better user experience
- Accurate data calculations for decision-making
- Dynamic prompts that match actual options