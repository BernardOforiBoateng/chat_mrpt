# Immediate Action Plan to Fix Data Analysis V3

## The Core Problem
**We're letting the LLM interpret data instead of just showing raw output from code execution.**

## Quick Fix (1 Hour)

### Step 1: Bypass Response Formatting
**File**: `app/data_analysis_v3/tools/python_tool.py`
**Line**: 129-159

**Current (BAD)**:
```python
formatted_output = format_analysis_response(output, state_updates)
# ... validation logic ...
return formatted_output
```

**Change to (GOOD)**:
```python
# Just return the raw output from code execution!
return output
```

### Step 2: Fix Executor Hallucination Check
**File**: `app/data_analysis_v3/core/executor.py`
**Line**: 130-148

**Current (BAD)**:
```python
for pattern in hallucination_patterns:
    if re.search(pattern, output):
        output = "ERROR: Generic placeholder names detected"
```

**Change to (GOOD)**:
```python
# Remove this entire block - let the output speak for itself
```

### Step 3: Simplify System Prompt
**File**: `app/data_analysis_v3/prompts/system_prompt.py`

**Current**: 300+ lines
**Change to**: Add CRITICAL instruction at top:

```python
## CRITICAL EXECUTION RULE
When asked for "top N" items or any list:
1. Use pandas methods: df.nlargest(N, 'column') or df.head(N)
2. Use print() or for loop to show ALL items:
   ```python
   top_10 = df.nlargest(10, 'value_column')
   for i, row in top_10.iterrows():
       print(f"{i+1}. {row['name']}: {row['value']}")
   ```
3. NEVER type out results manually - always print from data
4. If data not available, print("Data not found") - don't make it up
```

## Full Fix (4 Hours)

### Phase 1: Remove Complexity
1. **Delete redundant files**:
   ```bash
   rm app/data_analysis_v3/core/agent_backup.py
   rm app/data_analysis_v3/core/agent_fixed.py
   rm app/data_analysis_v3/core/formatters.py
   rm app/data_analysis_v3/core/column_validator.py
   ```

2. **Move TPR-specific to separate module**:
   ```bash
   mkdir app/domain_specific/
   mkdir app/domain_specific/tpr/
   mv app/data_analysis_v3/core/tpr_* app/domain_specific/tpr/
   mv app/data_analysis_v3/tools/tpr_* app/domain_specific/tpr/
   ```

### Phase 2: Simplify Core Logic

**python_tool.py** - Complete rewrite:
```python
@tool
def analyze_data(thought: str, python_code: str, graph_state: dict = None) -> str:
    """Execute Python code for data analysis."""
    
    # Get session ID
    session_id = graph_state.get('session_id', 'default') if graph_state else 'default'
    executor = SecureExecutor(session_id)
    
    # Load data from state
    current_data = {}
    if graph_state and "input_data" in graph_state:
        for dataset in graph_state["input_data"]:
            if "data" in dataset:
                current_data[dataset.get("variable_name", "df")] = dataset["data"]
                current_data['df'] = dataset["data"]  # Always available as df
    
    # Execute code
    output, state_updates = executor.execute(python_code, current_data)
    
    # Return RAW output - no formatting!
    return output
```

**executor.py** - Simplify:
```python
def execute(self, code: str, initial_vars: Dict = None):
    """Execute Python code and return stdout."""
    
    exec_globals = {
        'pd': pd, 'np': np, 'px': px, 'go': go,
        'print': print,  # Ensure print is available
        'plotly_figures': []
    }
    
    if initial_vars:
        exec_globals.update(initial_vars)
    
    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    
    try:
        exec(code, exec_globals)
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout
    
    return output, {'current_variables': exec_globals}
```

### Phase 3: Clean System Prompt

**system_prompt.py** - Reduce to essentials:
```python
MAIN_SYSTEM_PROMPT = """
You are a data scientist helping users analyze their data.

## Rules
1. Write Python code using the analyze_data tool
2. Data is available as 'df' DataFrame
3. Use print() to show ALL output
4. Never type results manually - always print from data
5. For "top N" queries, use df.nlargest(N, col) and print all rows

## Available Libraries
- pandas as pd
- numpy as np  
- plotly.express as px
- plotly.graph_objects as go

## Examples
User: "Show top 5 items by value"
Code:
```python
top_5 = df.nlargest(5, 'value')
print("Top 5 items by value:")
for i, row in top_5.iterrows():
    print(f"{i+1}. {row['name']}: {row['value']}")
```

User: "What columns are available?"
Code:
```python
print("Columns:", df.columns.tolist())
print("Shape:", df.shape)
print("First 3 rows:")
print(df.head(3))
```
"""
```

## Testing Plan

### Test 1: Top N Query
```python
Query: "Show top 10 facilities by testing volume"
Expected: All 10 facilities with real names
```

### Test 2: No Hallucination
```python
Query: "Show facilities that don't exist"  
Expected: "Data not found" or similar
```

### Test 3: Percentage Validation
```python
Query: "Calculate percentages"
Expected: Valid 0-100% from actual calculations
```

## Benefits After Fix

1. **Simplicity**: 500 lines instead of 3000+
2. **Reliability**: No hallucination possible
3. **Scalability**: Works with any domain
4. **Maintainability**: Easy to understand and modify
5. **Performance**: Faster execution, less processing

## Rollback Plan

If issues arise:
1. Keep original files in `backup/` directory
2. Can revert individual changes
3. Test incrementally

## Success Metrics

After implementation:
- [ ] "Top 10" query returns 10 real items
- [ ] No "Facility A, B, C" in any response  
- [ ] Works with non-healthcare data
- [ ] Response time < 5 seconds
- [ ] Code base < 1000 lines total