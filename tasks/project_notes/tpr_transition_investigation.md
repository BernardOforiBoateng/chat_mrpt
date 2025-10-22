# TPR → Risk Analysis Transition Investigation

## Problem Statement
After completing the TPR workflow in the Data Analysis tab, selecting "Yes" to transition to Risk Analysis does not work properly.

## Investigation Date
2025-09-10

## Root Cause Analysis

### 1. Frontend Behavior (React Application)
**Location**: `/frontend/src/hooks/useMessageStreaming.ts`

The frontend correctly:
- Sends messages to `/api/v1/data-analysis/chat` when in data analysis mode (line 36-38)
- Handles `exit_data_analysis_mode` flag from backend (lines 64-73)
- Would redirect to normal chat if backend provides `redirect_message`

### 2. Backend Issue Identified
**Location**: `/app/data_analysis_v3/tools/tpr_analysis_tool.py:952`

When TPR completes, it:
1. Sets `.tpr_waiting_confirmation` flag (line 923-924)
2. Returns a message asking "Would you like to proceed to the risk analysis stage?" (line 952)
3. BUT does NOT set any flag to indicate this is a transition prompt

### 3. Flow Breakdown
1. **TPR Completion**: Backend returns prompt message but stays in data analysis mode
2. **User says "Yes"**: Message goes to `/api/v1/data-analysis/chat` 
3. **Backend Processing**: 
   - Agent checks for `.tpr_waiting_confirmation` flag (agent.py:309)
   - If user confirms, it returns `trigger_analysis: True` (agent.py:338)
   - BUT this response doesn't include `exit_data_analysis_mode: true`
4. **Frontend remains in data analysis mode** because backend never signals to exit

## The Exact Breakpoint

**File**: `/app/data_analysis_v3/core/agent.py:325-339`

When user confirms transition with "Yes", the agent returns:
```python
return {
    'success': True,
    'message': "Great! I'll now proceed with the risk analysis...",
    'trigger_analysis': True  # <-- Missing exit_data_analysis_mode flag!
}
```

This response should include `'exit_data_analysis_mode': True` to signal the frontend to switch modes.

## Console Evidence
From the attached console logs (contxt.md):
- Lines 95-144: Multiple successful `/api/v1/data-analysis/chat` calls
- Line 125: TPR map successfully generated
- **NO request sent when user clicks "Yes"** after the transition prompt
- This confirms the frontend is waiting for proper backend signals

## Solution Required
The backend needs to be modified at `/app/data_analysis_v3/core/agent.py:325-339` to include:
```python
'exit_data_analysis_mode': True
```

Additionally, the data_analysis_v3_routes.py should be checked to ensure it properly handles the transition when `trigger_analysis: True` is returned.

## Files Involved
1. **Frontend**: `/frontend/src/hooks/useMessageStreaming.ts` (handles mode switching)
2. **Backend Agent**: `/app/data_analysis_v3/core/agent.py:325-339` (missing exit flag)
3. **TPR Tool**: `/app/data_analysis_v3/tools/tpr_analysis_tool.py:952` (generates prompt)
4. **Routes**: `/app/web/routes/data_analysis_v3_routes.py:252-268` (checks for transition)

## Impact
This bug prevents users from seamlessly transitioning from TPR analysis to Risk Analysis, forcing them to manually switch tabs or restart the process.