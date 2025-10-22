# LangGraph Agent Fix Plan

## Quick Summary
**Problem**: When you select option 1 (Data Analysis), the LangGraph agent isn't actually using its Python tools. It's just giving text responses.

## Root Cause
1. **No handler for option "1"** - Code only handles option "2" (TPR)
2. **Model not using tools** - GPT-4o is responding directly without calling analyze_data tool
3. **No forcing mechanism** - Nothing tells the model it MUST use tools for data analysis

## The Fix (3 Steps)

### Step 1: Add Option 1 Handler
In `app/data_analysis_v3/core/agent.py`, add after line 647:
```python
# Check if user selected option 1 (Data Analysis)
if user_query.strip() == "1":
    logger.info("User selected option 1 - starting data analysis workflow")
    # Force the model to use tools by asking a specific analysis question
    return await self.analyze("Please analyze the uploaded data using Python code. Show me the shape, columns, and first few rows.")
```

### Step 2: Update System Prompt
Add to `app/data_analysis_v3/prompts/system_prompt.py`:
```
## Tool Usage Instructions
ALWAYS use the analyze_data tool when:
- Analyzing uploaded data
- Creating visualizations
- Calculating statistics
- Exploring patterns
- User is in data analysis mode

Format: Use analyze_data with Python code to perform the analysis.
```

### Step 3: Force Tool Usage for Analysis Queries
In `_agent_node` method, add logic to detect analysis queries:
```python
# If query is about data and we have data, force tool usage
if self._is_analysis_query(user_query) and state.get("input_data"):
    # Modify query to explicitly request tool usage
    enhanced_query = f"Use Python code to: {user_query}"
```

## Why This Will Work
1. Option 1 will have explicit handling
2. System will force tool usage for data queries
3. Model will be guided to use analyze_data tool
4. Python code will execute and generate results

## Test After Fix
1. Upload data
2. Select option 1
3. Ask "Show me a summary of the data"
4. Should see Python execution and actual data results

## Alternative Quick Fix
If you need it working immediately, modify the analyze method to always use tools when in data analysis mode:
```python
# At the start of analyze method
if hasattr(self, 'data_analysis_mode') and self.data_analysis_mode:
    # Force tool usage
    python_code = generate_analysis_code(user_query)
    return self.execute_analysis(python_code)
```