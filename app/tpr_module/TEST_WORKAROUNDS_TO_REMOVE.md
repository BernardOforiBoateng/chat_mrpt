# Test-Specific Workarounds to Remove from TPR Module

This document lists all test-specific workarounds found in the TPR module that should be removed for production use.

## 1. TPR Conversation Manager (`core/tpr_conversation_manager.py`)

### Line 70: Test compatibility comment in docstring
```python
def get_response(self, command: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Generate response for a command (for test compatibility).
```

### Lines 83-92: Hardcoded test data initialization
```python
# Initialize parsed_data for tests
self.parsed_data = {
    'states': states,
    'metadata': metadata,
    'status': 'success'
}
```

### Lines 300-312: Initialize parsed_data for tests
```python
# Initialize parsed_data if needed (for tests)
if not self.parsed_data:
    available_states = self.state_manager.get_state('available_states')
    if available_states:
        self.parsed_data = {
            'states': available_states,
            'status': 'success'
        }
```

### Lines 332-339: Mock data creation on exception
```python
except (ValueError, AttributeError):
    # For tests, create mock data
    import pandas as pd
    state_data = pd.DataFrame({
        'State_clean': [selected_state] * 10,
        'level': ['Primary'] * 5 + ['Secondary'] * 3 + ['Tertiary'] * 2,
        'Health Faccility': [f'Facility_{i}' for i in range(10)]
    })
```

### Line 356: Response key added for tests
```python
'response': message,  # Add response key for tests
```

### Line 407: State update for test compatibility
```python
self.state_manager.update_state('facility_level', selected_level.lower())  # For test compatibility
```

### Lines 414-424: Skip data processing for tests
```python
except (ValueError, AttributeError):
    # For tests, skip data processing
    message = f"Good choice! Using **{selected_level}** facilities.\n\n"
    message += "Now, which age group should we calculate TPR for?\n\n"
    
    return {
        'status': 'success',
        'message': message,
        'response': message,
        'stage': 'age_selection'
    }
```

### Line 483: State update for test compatibility
```python
self.state_manager.update_state('age_group', age_group)  # For test compatibility
```

### Lines 495-502: Skip calculation for tests
```python
except (ValueError, AttributeError):
    # For tests, return success without actual calculation
    return {
        'status': 'success',
        'message': message,
        'response': message,
        'stage': self.current_stage.value
    }
```

## 2. TPR Calculator (`core/tpr_calculator.py`)

### Lines 46-49: Test compatibility wrapper method
```python
def calculate_tpr(self, data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate TPR for the given data.
    This is a simplified wrapper for calculate_ward_tpr for testing compatibility.
```

### Lines 215-235: Generic column names fallback for testing
```python
# Fallback to generic column names if age-specific not found
if rdt_tested_col not in ward_data.columns:
    # Try generic column names (for testing)
    generic_cols = {
        'rdt_tested': ['persons tested for malaria by rdt', 'rdt_tested'],
        'rdt_positive': ['persons tested positive for malaria by rdt', 'rdt_positive'],
        'micro_tested': ['persons tested for malaria by microscopy', 'microscopy_tested'],
        'micro_positive': ['persons tested positive for malaria by microscopy', 'microscopy_positive']
    }
```

## 3. State Selector Service (`services/state_selector.py`)

### Line 400: Test variable name
```python
for test_input in test_inputs:  # Variable named 'test_input' might be confusing
```

## Summary

The main patterns of test workarounds found:
1. **Try-except blocks** that catch `ValueError` or `AttributeError` and return mock data
2. **Comments** indicating test compatibility code
3. **Hardcoded fallback data** when normal data loading fails
4. **Additional response keys** added specifically for tests
5. **State updates** with comments indicating they're for test compatibility
6. **Generic column name fallbacks** in the calculator

## Recommendation

All these workarounds should be removed and replaced with proper test fixtures and mocking in the test files themselves. The production code should not contain any test-specific logic.