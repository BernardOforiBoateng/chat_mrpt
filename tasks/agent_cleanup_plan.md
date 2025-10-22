# Agent Cleanup Plan - Remove ALL TPR Workflow Logic

## Current State
- File: `app/data_analysis_v3/core/agent.py`
- Lines: 851
- Backup: `agent.py.backup_20251001_013342`

## Problem
TPR workflow logic is scattered throughout the agent, causing:
- Hardcoded responses (lines 535-536)
- Keyword-first routing that bypasses GPT-4o
- Generic "Data has been prepared" messages
- Test scores of 25-32/100

## Lines to DELETE

### 1. Remove TPR selections tracking (line 36)
```python
# DELETE THIS:
self.tpr_selections = {}  # Store TPR selections to avoid repetition
```

### 2. Remove TPR tool checking (lines 54-58)
```python
# DELETE THIS:
# Set up tools - conditionally add TPR tool if TPR data detected
self.tools = [analyze_data]

# Check for TPR data and add TPR tool if detected
self._check_and_add_tpr_tool()

# REPLACE WITH:
self.tools = [analyze_data]
```

### 3. Remove _check_and_add_tpr_tool method (lines 234-283)
**DELETE ENTIRE METHOD**

### 4. Remove _check_tpr_transition method (lines 284-336)
**DELETE ENTIRE METHOD**

### 5. Remove TPR-specific data summary (lines 129-138)
```python
# DELETE THE TPR-SPECIFIC PART:
# Enhanced summary with context about TPR workflow if active
summary = f"\n\nVariable: {var_name}\nDescription: Dataset loaded with TPR malaria data"
...
# Add TPR-specific context if in workflow
```

### 6. MOST IMPORTANT: Remove entire TPR checking block in analyze() (lines 365-604)

**DELETE FROM:**
```python
logger.info(f"[DEBUG] analyze() called with query: {user_query[:100]}")
# CRITICAL: Check if TPR workflow is active FIRST
from app.data_analysis_v3.core.state_manager import DataAnalysisStateManager as StateManager
...
```

**DELETE UNTIL:**
```python
# Check for TPR transition confirmation first
```

**This removes ~240 lines of TPR workflow checking, keyword extraction, visualization handling**

### 7. Remove TPR context from state (lines 648-650, 664)
```python
# DELETE:
# Append TPR context to user query if present
if tpr_message_addon:
    user_query = user_query + tpr_message_addon
...
"tpr_context": tpr_context if tpr_context else None  # Include TPR context
```

### 8. Remove generate_overview_summary TPR logic (lines 795-847)
**The entire method has TPR-specific code - needs cleaning**

## What STAYS

### Core Agent Structure (KEEP)
- Lines 1-33: Imports and class definition
- Lines 34-83: __init__ (after removing TPR tool check)
- Lines 85-105: _build_graph()
- Lines 107-143: _create_data_summary() (after removing TPR part)
- Lines 145-182: _agent_node()
- Lines 184-212: _tools_node()
- Lines 214-232: _route_to_tools()

### Clean analyze() method (KEEP - after removing TPR block)
- Lines 605-740: The actual LangGraph invocation
  - Load input data
  - Create input state
  - Invoke graph
  - Process results

### Helper methods (KEEP)
- Lines 742-765: reset_chat()
- Lines 767-787: _has_confirmation_phrase()

## Target Result

After cleanup, agent.py should be ~300-350 lines containing ONLY:
1. __init__ with basic setup
2. Graph building
3. Agent node
4. Tools node
5. Route to tools
6. analyze() - clean LangGraph invocation
7. Helper methods

NO TPR logic whatsoever.

## Implementation Strategy

Given the complexity, recommend:
1. Create a Python script to do the surgery programmatically
2. Or manually create clean agent.py from scratch using AgenticDataAnalysis as template
3. Test that it works with simple queries
4. THEN add TPR bridge in routes layer

## Next Step

Create `agent_clean_surgery.py` script to automate the cleanup.
