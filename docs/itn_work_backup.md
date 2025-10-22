# ITN Distribution Work Backup

## Summary of Changes Made

### 1. ITN Pipeline - Conversational Flow Implementation
**File: `/app/core/request_interpreter.py`**

Added conversational flow for ITN planning to ask users for inputs:
```python
# In _handle_special_workflows method:
# Handle ITN planning request
if 'itn' in user_lower and ('planning' in user_lower or 'distribution' in user_lower):
    # Check if we have the required parameters
    if session_data.get('itn_params_collected'):
        # Parameters already collected, run the planning
        return None  # Let normal flow handle it
    else:
        # Need to collect parameters
        response = """I'll help you plan ITN (Insecticide-Treated Net) distribution.

To optimize the distribution, I need two key inputs:

1. **Total number of nets available**: How many ITN nets do you have for distribution?
2. **Average household size**: What's the typical household size in this region? (default is 5)

Please provide these values and I'll calculate the optimal distribution plan based on the vulnerability rankings."""
        
        # Set state to expect ITN parameters
        try:
            from app.core.session_state import SessionStateManager
            state_manager = SessionStateManager()
            state_manager.update_state(session_id, {
                'expecting_itn_params': True
            })
        except:
            pass
        
        return {
            'response': response,
            'status': 'success',
            'tools_used': []
        }

# Handle ITN parameter collection
if session_data.get('expecting_itn_params') or (
    hasattr(self, '_check_session_state') and 
    self._check_session_state(session_id).get('expecting_itn_params')
):
    # Parse the user's response for ITN parameters
    import re
    
    # Look for numbers in the message
    numbers = re.findall(r'\d+(?:\.\d+)?', user_message)
    
    if numbers:
        total_nets = None
        household_size = 5.0  # default
        
        # Try to identify which number is which
        for i, num in enumerate(numbers):
            num_val = float(num)
            # Larger numbers are likely total nets
            if num_val > 100:
                total_nets = int(num_val)
            # Smaller numbers (2-10) might be household size
            elif 2 <= num_val <= 10 and i > 0:  # If it's the second number
                household_size = num_val
        
        # If we only got one number, assume it's total nets
        if len(numbers) == 1 and not total_nets:
            total_nets = int(float(numbers[0]))
        
        if total_nets:
            # Clear the expecting state
            try:
                from app.core.session_state import SessionStateManager
                state_manager = SessionStateManager()
                state_manager.update_state(session_id, {
                    'expecting_itn_params': False,
                    'itn_params_collected': True,
                    'itn_total_nets': total_nets,
                    'itn_household_size': household_size
                })
            except:
                pass
            
            # Now run ITN planning with these parameters
            response = f"Got it! Planning ITN distribution with {total_nets:,} nets and average household size of {household_size}.\n\n"
            
            # Execute ITN planning
            result = self._run_itn_planning(
                session_id=session_id,
                total_nets=total_nets,
                avg_household_size=household_size
            )
            
            if isinstance(result, dict) and 'response' in result:
                response += result['response']
            else:
                response += str(result)
            
            return {
                'response': response,
                'status': 'success',
                'tools_used': ['run_itn_planning']
            }
```

### 2. ITN Pipeline - Fixed Session ID Parameter
**File: `/app/analysis/itn_pipeline.py`**

Updated the calculate_itn_distribution function signature to accept session_id:
```python
def calculate_itn_distribution(data_handler, session_id: str, total_nets: int = 10000, avg_household_size: float = 5.0, urban_threshold: float = 30.0, method: str = 'composite') -> Dict[str, Any]:
    """Perform two-phase ITN distribution calculation."""
    # ... rest of implementation
```

### 3. Request Interpreter - Updated ITN Planning Tool
**File: `/app/core/request_interpreter.py`**

Updated _run_itn_planning to pass session_id correctly:
```python
def _run_itn_planning(self, session_id: str, total_nets: int = 10000, avg_household_size: float = 5.0, 
                     urban_threshold: float = 30.0, method: str = 'composite'):
    """Plan ITN distribution based on vulnerability rankings.
    DO NOT call this directly - let the system collect parameters first."""
    try:
        # Get session parameters if available
        try:
            from app.core.session_state import SessionStateManager
            state_manager = SessionStateManager()
            state = state_manager.get_state(session_id)
            
            # Use collected parameters if available
            if state.get('itn_params_collected'):
                total_nets = state.get('itn_total_nets', total_nets)
                avg_household_size = state.get('itn_household_size', avg_household_size)
        except:
            pass
        
        # Load data
        data_handler = self.data_service.get_handler(session_id)
        if not data_handler:
            return "No data loaded. Please upload data first."
        
        # Import and run ITN distribution calculation with session_id
        from app.analysis.itn_pipeline import calculate_itn_distribution
        
        result = calculate_itn_distribution(
            data_handler=data_handler,
            session_id=session_id,  # Pass session_id
            total_nets=total_nets,
            avg_household_size=avg_household_size,
            urban_threshold=urban_threshold,
            method=method
        )
```

### 4. Key Improvements Made:
1. **Conversational Flow**: ITN planning now asks users for inputs instead of using defaults
2. **Session State Management**: Properly tracks when expecting ITN parameters
3. **Parameter Parsing**: Intelligently extracts total nets and household size from user input
4. **Fixed DataHandler Issue**: Resolved the session_id attribute error by passing it as parameter
5. **Better User Experience**: Clear prompts and feedback about what's happening

### 5. Test File Created:
**File: `/test_itn_distribution.py`**
A comprehensive test file that validates the ITN distribution pipeline with various configurations.

## Known Issues to Address:
1. Timestamp JSON serialization error when running ITN planning
2. Need to handle the case where unified dataset might not have all required columns
3. Population data matching could be improved for edge cases