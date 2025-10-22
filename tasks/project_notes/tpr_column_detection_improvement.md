# TPR Column Detection Improvement Plan

## Current Problem
The existing code looks for 'rdt' and 'tested' separately, but actual columns are:
- "Persons presenting with fever & tested by RDT <5yrs"
- "Persons tested positive for malaria by RDT <5yrs"

## Solution: Improve `calculate_ward_tpr` in `tpr_utils.py`

### 1. Better Column Detection Logic
```python
# Instead of:
if 'rdt' in col.lower() and 'tested' in col.lower():

# Use more flexible patterns:
if ('rdt' in col.lower() and ('tested' in col.lower() or 'presenting' in col.lower())):
```

### 2. Handle Special Characters
- The actual data has "≥5yrs" but might come as "â‰¥5yrs" (encoding issue)
- Already have `fix_column_encoding()` function - just need to ensure it's comprehensive

### 3. Add Recommendations
When user doesn't specify, recommend:
- Facility Level: Primary (if available)
- Age Group: Under 5 
- Test Method: Both (max of RDT and Microscopy)

### 4. Flexible Matching Strategy
1. First try exact patterns
2. Then try partial matches
3. Show user what was detected
4. Let user confirm or adjust

## Implementation Steps
1. Update column detection in `calculate_ward_tpr` (lines 265-296)
2. Add recommendation logic to agent.py 
3. Improve error messages to show what columns were found
4. Test with multiple data formats