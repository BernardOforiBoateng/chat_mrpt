# PCA Statistical Tests Implementation Plan

## Overview
Implement Kaiser-Meyer-Olkin (KMO) test and Bartlett's test of sphericity to determine if PCA is appropriate for the data. If tests fail (KMO < 0.5), only run composite analysis and inform the user.

## Current Pipeline Structure

### Analysis Flow
1. **Entry Point**: `RunCompleteAnalysis` tool (`app/tools/complete_analysis_tools.py`)
   - Currently runs both composite and PCA analyses sequentially
   - Calls `_run_composite_analysis()` then `_run_pca_analysis()`

2. **PCA Pipeline**: `PCAAnalysisPipeline` class (`app/analysis/pca_pipeline.py`)
   - Main method: `run_complete_pca_analysis()`
   - Pipeline steps:
     - Load raw data (line 70)
     - Apply variable selection (line 77-100)
     - Clean and prepare data (line 111)
     - Standardize data (line 120) - **_standardize_data()** method at line 350
     - Run PCA analysis (line 129) - **_run_pca_analysis()** method at line 386
     - Create rankings (line 138)

3. **Composite Pipeline**: (`app/analysis/pipeline.py`)
   - Independent of PCA, runs separately

4. **User Feedback**: `_generate_comprehensive_summary()` in `complete_analysis_tools.py` (line 303)

## Implementation Locations

### 1. Add Statistical Tests (in `pca_pipeline.py`)
**Location**: After `_standardize_data()` and before `_run_pca_analysis()`
- Add new method: `_check_pca_suitability()` 
- This will run KMO and Bartlett's tests
- Return a dict with:
  - `suitable: bool` (True if KMO >= 0.5 and Bartlett's p < 0.05)
  - `kmo_value: float`
  - `bartlett_p_value: float`
  - `message: str` (explanation of results)

### 2. Modify PCA Pipeline Flow (in `pca_pipeline.py`)
**Location**: In `run_complete_pca_analysis()` method around line 120-129
- After standardization, call `_check_pca_suitability()`
- If not suitable, return early with informative message
- Store test results for user feedback

### 3. Update Complete Analysis Tool (in `complete_analysis_tools.py`)
**Location**: In `_execute()` method around line 150
- Check if PCA was skipped due to statistical tests
- Adjust flow to handle PCA skipping gracefully
- Store test results for summary

### 4. Update User Messaging (in `complete_analysis_tools.py`)
**Location**: In `_generate_comprehensive_summary()` method
- Add information about statistical test results
- If PCA skipped, explain why and that composite analysis is sufficient
- Include KMO value and interpretation

## Statistical Tests Details

### Kaiser-Meyer-Olkin (KMO) Test
- Measures sampling adequacy for PCA
- Values range from 0 to 1
- Interpretation:
  - >= 0.9: Excellent
  - 0.8-0.9: Good
  - 0.7-0.8: Acceptable
  - 0.6-0.7: Mediocre
  - 0.5-0.6: Poor
  - < 0.5: Unacceptable (don't run PCA)

### Bartlett's Test of Sphericity
- Tests if correlation matrix is an identity matrix
- Null hypothesis: variables are uncorrelated
- If p-value < 0.05: reject null, PCA is appropriate
- If p-value >= 0.05: fail to reject null, PCA not recommended

## Implementation Steps

### Step 1: Install Required Dependencies
```python
# Need to ensure these are available:
from factor_analyzer import calculate_kmo
from factor_analyzer import calculate_bartlett_sphericity
# OR implement manually using scipy if factor_analyzer not available
```

### Step 2: Create Statistical Test Method
```python
def _check_pca_suitability(self) -> Dict[str, Any]:
    """
    Check if PCA is suitable using KMO and Bartlett's tests.
    
    Returns:
        Dict with test results and suitability determination
    """
    # Implementation here
```

### Step 3: Integrate into Pipeline
- Modify `run_complete_pca_analysis()` to check suitability
- Handle early return if tests fail

### Step 4: Update Complete Analysis Logic
- Modify `_run_pca_analysis()` to handle test failure
- Update result structure to include test information

### Step 5: Enhance User Messaging
- Add test results to summary
- Provide clear explanation when PCA is skipped

## Files to Modify

1. **Primary Changes**:
   - `app/analysis/pca_pipeline.py` - Add statistical tests
   - `app/tools/complete_analysis_tools.py` - Handle conditional PCA

2. **Secondary Changes**:
   - `app/analysis/engine.py` - May need updates for conditional PCA
   - `requirements.txt` - Add factor_analyzer if needed

3. **Documentation**:
   - Update docstrings to reflect new behavior
   - Add comments explaining statistical tests

## Testing Plan

1. Test with data that should pass both tests
2. Test with data that has KMO < 0.5
3. Test with data that fails Bartlett's test
4. Verify user messages are clear and informative
5. Ensure composite analysis still runs when PCA is skipped

## Success Criteria

1. ✅ KMO test correctly calculates values
2. ✅ Bartlett's test correctly calculates p-values
3. ✅ PCA skipped when KMO < 0.5
4. ✅ Composite analysis runs regardless of test results
5. ✅ User receives clear explanation of test results
6. ✅ System handles edge cases gracefully

## Notes

- Keep the implementation modular for easy testing
- Log test results for debugging
- Consider making thresholds configurable in future
- Ensure backward compatibility with existing analyses