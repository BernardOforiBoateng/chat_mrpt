# CRITICAL FIX: LangGraph Agent Not Using Tools

## The Problem in One Sentence
**The model isn't calling the Python analysis tool because tools are bound in the wrong order and there's no handler for option 1.**

## Root Cause (From AgenticDataAnalysis Comparison)

### Original (WORKS):
```python
model = llm.bind_tools(tools)  # Bind tools FIRST
# ... then later ...
model = chat_template | model  # Apply template to tool-bound model
```

### Ours (BROKEN):
```python
model = chat_template | llm.bind_tools(tools)  # Wrong order!
```

## THE FIX - 3 Critical Changes

### Fix 1: Tool Binding Order
**File**: `app/data_analysis_v3/core/agent.py`
**Line**: 85

**CHANGE FROM**:
```python
self.model = self.chat_template | self.llm.bind_tools(self.tools)
```

**TO**:
```python
# Bind tools FIRST (like original AgenticDataAnalysis)
self.llm_with_tools = self.llm.bind_tools(self.tools)
# Then apply template
self.model = self.chat_template | self.llm_with_tools
```

### Fix 2: Add Option 1 Handler
**File**: `app/data_analysis_v3/core/agent.py`
**After Line**: 647 (before option 2 check)

**ADD**:
```python
# Check if user selected option 1 (Data Analysis with LangGraph)
if user_query.strip() == "1":
    logger.info("User selected option 1 - activating LangGraph data analysis")
    # Force tool usage by asking a specific analysis question
    analysis_prompt = "Use Python code to analyze the uploaded data. Show me the shape, columns, data types, and first 5 rows."
    # Continue with normal flow but with enhanced prompt
    user_query = analysis_prompt
    # Don't return early - let it flow to the graph execution
```

### Fix 3: Simplify System Prompt
**File**: `app/data_analysis_v3/prompts/system_prompt.py`
**Line**: 6 (After "## Role")

**ADD**:
```python
## CRITICAL INSTRUCTION
You MUST use the analyze_data tool for ALL data analysis requests.
When asked about data, ALWAYS write Python code using the tool.
NEVER give text-only responses for data questions.

Example: If asked "show me the data", use analyze_data with Python code like:
```python
print(f"Shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(df.head())
```
```

## Why This Will Fix It

1. **Correct Tool Binding**: Model will properly detect it has tools available
2. **Option 1 Handler**: Explicitly triggers analysis mode with clear instructions
3. **Clear Prompt**: Forces model to use tools instead of text responses

## Testing After Fix

1. Upload `adamawa_tpr_cleaned.csv`
2. Select option 1
3. Ask "Show me a summary of the data"

**Expected**:
- Console should show tool call to `analyze_data`
- Python code execution
- Actual data output (shape, columns, rows)

**NOT Expected**:
- Generic text about data analysis
- No tool calls in console

## Verification in Console

Look for in browser console:
```
Tool call: analyze_data
Python code: print(df.shape)...
Output: (1234, 15)...
```

## If Still Not Working

Check:
1. Is `analyze_data` in `self.tools`?
2. Does model have `tool_calls` in response?
3. Is `_route_to_tools` being called?
4. Add logging: `logger.info(f"Model response: {llm_outputs}")`

## The AgenticDataAnalysis Way

Remember, the original ALWAYS uses tools because:
- Prompt explicitly says "Execute python code using the tool"
- Tools bound before template
- Simple, direct workflow

We need to match this simplicity!