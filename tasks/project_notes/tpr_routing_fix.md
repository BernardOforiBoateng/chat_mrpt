# TPR Transition Routing Fix

## Date: 2025-09-11

## Problem
After TPR workflow transition, messages like "Run the malaria risk analysis" and "Check data quality" were incorrectly routing to Arena mode instead of Tools.

## Root Cause Analysis

### Issue 1: Missing Examples in Mistral Prompt
The Mistral prompt didn't include specific examples for these common analysis commands:
- "Run the malaria risk analysis"
- "Check data quality"
- "perform analysis"

### Issue 2: Session Context Bug
The critical issue was in how `has_uploaded_files` was determined:

```python
# BEFORE: Only checked for actual files
has_uploaded_files = False
if os.path.exists(session_folder):
    for f in os.listdir(session_folder):
        if f.endswith(('.csv', '.xlsx', '.xls', '.shp', '.zip')):
            has_uploaded_files = True
            break
```

**Problem**: After TPR transition, the session flags (`csv_loaded`, `analysis_complete`) were set to True, but:
- TPR workflow might not create files in `instance/uploads/{session_id}/`
- Or files might be in a different location/format
- So `has_uploaded_files` remained False even though data was loaded

This caused Mistral to receive context saying "User has uploaded data: False" even after successful TPR workflow completion!

## Solution Implemented

### Fix 1: Enhanced Mistral Prompt
Added specific examples and keywords:
- Keywords: Added "check" and "perform" to action keywords
- Examples: Added explicit cases for common analysis commands
  - "Run the malaria risk analysis" → NEEDS_TOOLS
  - "Check data quality" → NEEDS_TOOLS
  - "perform analysis" → NEEDS_TOOLS
  - "check the data" → NEEDS_TOOLS

### Fix 2: Trust Session Flags
```python
# AFTER: Trust session flags after TPR transition
if session.get('csv_loaded', False) or session.get('analysis_complete', False):
    has_uploaded_files = True
```

This ensures that after TPR workflow sets the session flags, the routing context correctly reflects that data is available.

## Files Modified
- `/app/web/routes/analysis_routes.py`
  - Lines 98-129: Enhanced Mistral prompt with new examples
  - Lines 490-493: Added session flag trust for regular endpoint
  - Lines 1334-1337: Added session flag trust for streaming endpoint

## Testing & Verification

### Test Cases
1. "Run the malaria risk analysis" → Should route to Tools ✓
2. "Check data quality" → Should route to Tools ✓
3. "perform analysis" → Should route to Tools ✓
4. "run analysis on the data" → Should route to Tools ✓

### Deployment
- Deployed to Instance 1 (3.21.167.170) ✓
- Deployed to Instance 2 (18.220.103.20) ✓
- Services restarted on both instances

## Impact
This fix ensures that after TPR workflow completion, when users request analysis operations, they are correctly routed to Tools instead of Arena mode. This is critical for the user experience as Arena models cannot perform actual data analysis.

## Lessons Learned
1. **Session state consistency** - When multiple workflows (TPR, main) share session state, ensure all code paths check the same indicators
2. **File-based checks aren't always reliable** - Session flags may be more accurate than filesystem checks in distributed systems
3. **Explicit examples help LLMs** - Adding specific phrases to the prompt improves routing accuracy
4. **Test the full workflow** - Issues may only appear after specific workflow transitions