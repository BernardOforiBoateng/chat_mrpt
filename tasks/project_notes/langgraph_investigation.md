# LangGraph Data Analysis Agent Investigation
**Date**: 2025-01-18
**Issue**: After selecting option 1 (Data Analysis), the LangGraph agent is not performing as expected

## Console Log Analysis

### What's Working ✅
1. **File Upload**: Successfully uploaded (session: `68a8db3b-7268-4569-b0fa-0fe922b4c3db`)
2. **Data Overview**: Appears correctly with 3 options
3. **Option Selection**: User selects "1" successfully
4. **API Communication**: All requests go to correct endpoint `/api/v1/data-analysis/chat`
5. **Response Reception**: Backend returns responses with messages
6. **Data Analysis Mode**: Properly activated in frontend

### What's NOT Working ❌
1. **No Tool Execution**: The agent isn't using the Python analysis tools
2. **Generic Responses**: Getting simple text responses instead of data analysis
3. **No Visualizations**: No charts or graphs being generated
4. **No Code Execution**: The analyze_data tool isn't being invoked

## Code Investigation Findings

### 1. Missing Option 1 Handler
**File**: `app/data_analysis_v3/core/agent.py`
- **Problem**: No explicit handling for when user types "1"
- Only option "2" (TPR workflow) is explicitly handled (line 649)
- When "1" is typed, it falls through to general LangGraph workflow

### 2. LangGraph Workflow Structure
**Correct Setup**:
- Graph built with agent and tools nodes ✅
- Routing function exists ✅
- Tools are bound to model ✅
- analyze_data tool is available ✅

### 3. Tool Invocation Issue
**Root Cause**: The AI model (gpt-4o) is not deciding to use tools
- The routing function (`_route_to_tools`) only routes to tools if AI message has `tool_calls`
- The model is responding directly without generating tool calls
- System prompt doesn't explicitly instruct when to use tools

### 4. Workflow Flow
When user types "1" or asks questions:
1. Request goes to agent's `analyze` method
2. Falls through all condition checks to general workflow (line 693)
3. Creates input state with data files
4. Invokes LangGraph with state
5. Model responds WITHOUT calling tools
6. Response returned as plain text

## Key Code Sections

### Missing Option 1 Handler
```python
# Line 649: Only handles option 2
if user_query.strip() == "2":
    # TPR workflow handling
    ...
# NO handling for option "1"!
```

### Tool Routing Logic
```python
# Line 279: Only routes if tool_calls exist
if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
    return "tools"
return "__end__"
```

## Why LangGraph Isn't Working

### Primary Issues:
1. **No Explicit Tool Triggering**: System prompt doesn't tell model WHEN to use tools
2. **Missing Option 1 Logic**: No code to explicitly start data analysis workflow
3. **Model Not Using Tools**: GPT-4o is choosing to respond directly instead of calling analyze_data
4. **Fallback to Text**: Without tool calls, system defaults to text-only responses

### Secondary Issues:
1. **Context Not Set**: When "1" is selected, no context is set to force tool usage
2. **No Tool Forcing**: Unlike option 2 (TPR), option 1 doesn't force a specific workflow
3. **Generic Prompting**: User questions like "Show me a summary" don't trigger tool usage

## Expected vs Actual Behavior

### Expected (with LangGraph):
1. User selects option 1
2. Agent recognizes data analysis mode
3. User asks question
4. Model calls analyze_data tool with Python code
5. Tool executes code and returns results
6. Visualizations generated with Plotly
7. Results formatted and displayed

### Actual:
1. User selects option 1
2. Nothing special happens (falls through)
3. User asks question
4. Model responds with text only
5. No tools called
6. No code execution
7. No visualizations

## Required Fixes

### Option 1: Add Explicit Option 1 Handler
```python
if user_query.strip() == "1":
    # Force data analysis mode
    # Set flag to ensure tool usage
    # Return confirmation message
```

### Option 2: Improve System Prompt
- Add explicit instructions for when to use analyze_data tool
- Include examples of tool usage
- Force tool usage for data-related queries

### Option 3: Tool Forcing Mechanism
- When in data analysis mode, force tool usage
- Modify agent_node to always generate tool calls for analysis queries
- Add pre-processing to detect analysis intent

## Current State Summary

**The LangGraph integration is structurally complete but functionally inactive because:**
1. The model isn't choosing to use tools
2. There's no forcing mechanism for option 1
3. The workflow falls through to basic text responses
4. System prompt doesn't guide tool usage effectively

**Result**: Users get generic text responses instead of actual data analysis with Python execution and visualizations.

## Recommendations

1. **Immediate Fix**: Add explicit handler for option "1" that forces tool usage
2. **System Prompt Update**: Add clear instructions for tool usage
3. **Tool Forcing**: Implement mechanism to ensure tools are used for analysis
4. **Testing**: Create test cases to verify tool execution
5. **Monitoring**: Add logging to track when tools are/aren't called