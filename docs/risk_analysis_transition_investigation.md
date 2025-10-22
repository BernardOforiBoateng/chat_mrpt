# Risk Analysis Transition Issue - Investigation Report

## Problem Statement
After TPR calculation completes and visualization is shown, the system exits data analysis mode instead of transitioning to risk analysis. Users cannot proceed with risk analysis after TPR completion.

## Root Causes Identified

### Issue 1: Missing Transition Prompt
**Location**: `app/data_analysis_v3/core/tpr_workflow_handler.py`, line 405-412

After TPR calculation completes, the message returned does NOT include a prompt asking if the user wants to proceed with risk analysis. The message just ends with the TPR results and visualization.

```python
# Current (MISSING PROMPT):
return {
    "success": True,
    "message": message,  # Just TPR results, no transition prompt
    "session_id": self.session_id,
    "workflow": "tpr",
    "stage": "complete",
    "visualizations": visualizations
}
```

### Issue 2: Workflow Falls Through on Unmatched Input
**Location**: `app/data_analysis_v3/core/tpr_workflow_handler.py`, line 73-94

When in TPR_COMPLETE stage:
- If user says "yes/proceed/continue" → triggers risk analysis ✅
- If user says "no/stop/later" → exits workflow ✅  
- **If user says anything else → returns None** ❌

When `handle_workflow()` returns None:
- **Location**: `app/data_analysis_v3/core/agent.py`, line 573-585
- The agent falls through to the regular LangGraph workflow (line 668)
- This doesn't understand the TPR context and can't handle the transition

### Issue 3: Missing Flag Check Coordination
The system has a flag-based transition mechanism:
- **TPR tool creates flag**: `app/data_analysis_v3/tools/tpr_analysis_tool.py`, line 923-924
  - Creates `.tpr_waiting_confirmation` flag when TPR completes
- **Agent checks flag**: `app/data_analysis_v3/core/agent.py`, line 300-330
  - `_check_tpr_transition()` checks for the flag
  - But this only works if user provides confirmation message

However, without a prompt, users don't know they need to confirm!

## The Flow That's Breaking

1. User selects option "2" for TPR
2. TPR workflow guides through state/facility/age selection
3. TPR calculation completes, visualization shown
4. Stage set to TPR_COMPLETE, waiting for user response
5. **No prompt shown asking if user wants to proceed** ← ISSUE
6. User types something (not knowing what to say)
7. Message doesn't match yes/no keywords
8. `handle_workflow()` returns None
9. Falls through to regular agent
10. Regular agent doesn't understand context
11. Eventually exits data analysis mode

## Required Fixes

### Fix 1: Add Transition Prompt
In `tpr_workflow_handler.py`, after line 387, add:
```python
# Add transition prompt
message += "\n\n**Would you like to proceed with risk analysis?**\n"
message += "This will rank all wards by malaria risk using the TPR data along with other factors.\n"
message += "Reply 'yes' to continue or 'no' to stop here."
```

### Fix 2: Handle Fallback Case
In `tpr_workflow_handler.py`, line 93-94, instead of returning None:
```python
# If user response doesn't match, remind them of the options
else:
    return {
        "success": True,
        "message": "Please reply 'yes' to proceed with risk analysis or 'no' to stop here.",
        "session_id": self.session_id,
        "require_input": True
    }
```

### Fix 3: Better Integration Check
In `agent.py`, after line 574, add check for None result:
```python
if result:
    return result
elif state_manager.is_tpr_workflow_active():
    # TPR workflow returned None - provide guidance
    return {
        "success": True,
        "message": "I didn't understand your response. Would you like to proceed with risk analysis? Please reply 'yes' or 'no'.",
        "session_id": self.session_id
    }
```

## Impact
Without these fixes:
- Users complete TPR but can't proceed to risk analysis
- System appears to "forget" the context
- Data analysis mode exits prematurely
- Users must restart the entire workflow

## Testing Notes
To reproduce:
1. Upload CSV via Data Analysis tab
2. Select option "2" for TPR
3. Complete TPR workflow (state, facility, age selections)
4. After visualization appears, type anything
5. Observe: System exits data analysis mode instead of transitioning