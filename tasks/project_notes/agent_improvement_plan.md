# Data Analysis V3 Agent - Improvement Plan

## Core Problem
The agent often responds with text instead of executing code because:
1. System prompt explicitly allows "NO DATA REQUIRED" responses
2. No enforcement to use `analyze_data` tool when data IS available
3. Tool instruction buried at line 380 of 412-line prompt
4. Too many escape hatches for text-only responses

## Improvement Strategy: Force Tool Usage (Keep TPR)

### 1. Simplify System Prompt (Highest Impact)
**Current**: 412 lines with mixed instructions
**Target**: ~100 lines with clear directives

**Key Changes**:
```python
MAIN_SYSTEM_PROMPT = """
## PRIMARY DIRECTIVE
When data is loaded, you MUST use the analyze_data tool for ALL analysis questions.
Never provide text-only answers about the data - always execute code to get real results.
Only use text responses for greetings or when no data is loaded.

## Role
You are a data analysis agent that executes Python code to analyze health data.

## Critical Rules
1. **ALWAYS use analyze_data tool** when answering questions about loaded data
2. **ALWAYS use print()** to show outputs (you won't see results otherwise)
3. **NEVER show code** to users - only show results
4. **NEVER make up data** - only show actual execution results

## Data Access
- The main dataset is available as 'df'
- Use pandas, plotly, sklearn for analysis
- Variables persist between executions

## TPR Workflow Trigger
When user mentions "TPR", "test positivity rate", or "run TPR analysis":
- Acknowledge and start the TPR workflow
- Guide through: state → facility → age group → calculation
[Keep existing TPR instructions but condensed]

## Tool Usage Pattern
For EVERY data question, your response MUST be:
1. Think about what analysis is needed
2. Write Python code using analyze_data tool
3. Show only the printed results to the user
"""
```

### 2. Add Tool Enforcement in Agent Logic
**Location**: `app/data_analysis_v3/core/agent.py`

**Add after line 695** (where messages are prepared):
```python
# FORCE tool usage when data is available
if input_data_list and not self._is_greeting(user_query):
    # Modify the query to emphasize tool usage
    enforced_query = f"""
    REMEMBER: You MUST use the analyze_data tool to answer this.
    User question: {user_query}
    The data is loaded as 'df'. Use print() to show all outputs.
    """
    input_state["messages"][-1] = HumanMessage(content=enforced_query)
```

### 3. Remove Column Validation "Fixes"
**Location**: `app/data_analysis_v3/core/executor.py`

**Current** (lines 66-70): Tries to "fix" column names
**Change**: Trust the LLM, just log warnings

```python
# Line 66-70, replace with:
if code != original_code:
    logger.warning("Column name mismatch detected but proceeding anyway")
    # Use original code, don't "fix" it
    code = original_code
```

### 4. Improve Data Context Display
**Location**: `app/data_analysis_v3/core/agent.py` line 124

**Current**: Complex data summary
**Better**: Clear, simple column listing

```python
def _create_data_summary(self, state: DataAnalysisState) -> str:
    """Create clear data summary."""
    summaries = ["Data is loaded as 'df' with these exact columns:"]

    # Get the actual DataFrame
    if state.get("input_data"):
        for dataset in state["input_data"]:
            if dataset.get("data") is not None:
                df = dataset["data"]
                cols = list(df.columns)
                summaries.append(f"Columns: {cols}")
                summaries.append(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")
                summaries.append("Use these EXACT column names in your code.")
                break

    return "\n".join(summaries)
```

### 5. Fix Initial Response After Upload
**Location**: `app/web/routes/data_analysis_v3_routes.py` line 370

**Current**: Triggers generic "Show me what's in the uploaded data"
**Better**: Force immediate tool usage

```python
# Line 372, change to:
return await agent.analyze("""
Use the analyze_data tool to show:
1. df.shape
2. df.columns.tolist()
3. df.head()
4. df.dtypes
5. df.describe()
Print each result clearly.
""")
```

## Implementation Priority

### Phase 1: Quick Wins (30 minutes)
1. ✅ Simplify system prompt to ~100 lines
2. ✅ Add PRIMARY DIRECTIVE at top
3. ✅ Remove "NO DATA REQUIRED" sections

### Phase 2: Enforcement (30 minutes)
1. ✅ Add tool enforcement logic in agent
2. ✅ Modify initial upload response
3. ✅ Remove column "fixing" that breaks code

### Phase 3: Testing (30 minutes)
1. Test simple queries: "What columns are in the data?"
2. Test analysis: "Show me summary statistics"
3. Test TPR trigger: "Run TPR analysis"
4. Verify tool is ALWAYS used for data questions

## Success Metrics

### Before (Current State):
- Agent responds with text for data questions
- Says "Based on the data..." without executing code
- Column name errors from validation

### After (Target State):
- EVERY data question triggers analyze_data tool
- Only shows actual print() outputs
- TPR workflow still works perfectly
- No made-up responses

## What We're NOT Changing
1. ✅ Keep TPR workflow intact
2. ✅ Keep existing tool structure
3. ✅ Keep security features
4. ✅ Keep visualization support

## Key Insight
The original AgenticDataAnalysis works because it's **simple and strict**:
- 35-line prompt that says "Execute python code using the tool"
- No escape hatches for text responses
- Shows only print() outputs

We need the same strictness while preserving your TPR workflow.