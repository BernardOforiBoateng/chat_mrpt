# TPR Workflow Correction - No Test Method Question

## Date: 2025-08-13

## Important Discovery
The production TPR system did NOT ask users to select test method. It automatically handled this intelligently.

## Actual Production Workflow

### Steps (Only 3 Questions!)
1. **State Selection** - Which state to analyze?
2. **Facility Level** - All facilities or specific level?
3. **Age Group** - Which age group?

### NO Test Method Question!
The system automatically:
- Calculated TPR for both RDT and Microscopy
- Took the **maximum** TPR value
- Handled missing data gracefully

## Code Evidence

From `app/core/tpr_utils.py`:
```python
def calculate_ward_tpr(df: pd.DataFrame, age_group: str = 'all_ages', 
                      test_method: str = 'both', facility_level: str = 'all'):
    """
    Production logic (from deleted tpr_calculator.py):
    - All ages: Calculate TPR for each method (RDT, Microscopy), then take max(TPR)
    - Specific age: Take max at facility level first, then aggregate
    """
```

Default: `test_method='both'` - automatically uses maximum of both methods

## Why This Makes Sense

1. **Simpler for Users**: One less decision to make
2. **Better Analysis**: Using max TPR captures worst-case scenario
3. **Handles Data Gaps**: Works whether facility has RDT, Microscopy, or both
4. **WHO Standard**: Aligns with WHO recommendation to use all available data

## Intelligent Data Handling

The system automatically:
- If only RDT data exists → Use RDT
- If only Microscopy exists → Use Microscopy  
- If both exist → Use max(RDT_TPR, Microscopy_TPR)
- Shows which method contributed to final TPR

## Correct TPR Workflow

### After User Selects TPR:

**Step 1: State Selection**
```
Which state would you like to analyze?

Based on your data:
1. Adamawa - 834 facilities, 15,234 tests
2. Kwara - 785 facilities, 14,567 tests
3. Osun - 837 facilities, 15,877 tests
```

**Step 2: Facility Level**
```
Which facilities in Adamawa?

1. All Facilities (Recommended) - 834 total
   Complete coverage across all levels
   
2. Primary Health Centers - 687 facilities
   Community-level, rural focus
   
3. Secondary Facilities - 125 facilities
   General hospitals
   
4. Tertiary Facilities - 22 facilities
   Teaching hospitals
```

**Step 3: Age Group**
```
Which age group for Adamawa (All facilities)?

1. All Ages (Recommended)
   - 15,234 tests available
   - Most comprehensive view
   
2. Under 5 Years
   - 6,093 tests (40% of total)
   - Highest risk group
   
3. Over 5 Years
   - 7,156 tests (47% of total)
   
4. Pregnant Women
   - 1,985 tests (13% of total)
   - Limited to ANC clinics
```

**Step 4: Automatic Calculation**
```
✅ Calculating TPR for Adamawa, All facilities, Under 5 years...

Using intelligent test method selection:
- RDT data: 4,874 tests found
- Microscopy data: 1,219 tests found
- Method: Using maximum TPR from both methods

[Results show...]
```

## Benefits of NOT Asking Test Method

1. **Reduces Complexity**: 3 questions instead of 4
2. **Better Epidemiology**: Max TPR is standard practice
3. **User-Friendly**: Non-technical users don't need to understand test differences
4. **Automatic Optimization**: System picks best available data

## Implementation Note

We should:
1. Remove test method question from the workflow
2. Use the existing `calculate_ward_tpr()` function with default `test_method='both'`
3. Show in results which test methods contributed
4. Explain in results that we used maximum TPR for safety

## What to Show in Results

```
📊 TPR Calculation Method:
- RDT Testing: 4,874 tests analyzed
- Microscopy: 1,219 tests analyzed  
- Approach: Maximum TPR used (WHO standard)
- This captures the worst-case scenario for intervention planning
```