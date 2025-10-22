# Investigation Findings: Download and Ward Explanation Issues

## Executive Summary
Two critical issues were identified in the system:
1. **Download files not available** - Session context error prevents download tab from showing files
2. **Generic ward explanations** - System provides generic text instead of actual data values

## Issue 1: Download Files Not Available

### Symptoms
- User completes TPR analysis successfully
- Download tab shows "no files available. Run a TPR analysis first" 
- TPR download links exist in session but risk analysis download links are missing

### Root Cause
The critical error occurs when trying to set the `analysis_complete` flag after finishing the risk analysis:

```
WARNING in complete_analysis_tools: Failed to set analysis_complete flag: Working outside of request context.
```

This Flask error happens because the analysis completion code runs in a background thread or task that doesn't have access to the Flask request context. Without this flag being set, the download system doesn't recognize that analysis files are available.

### Evidence from Logs
```
Jul 23 17:00:54: Failed to mark analysis complete: Working outside of request context.
Jul 23 17:00:54: WARNING in complete_analysis_tools: Failed to set analysis_complete flag: Working outside of request context.
```

The system successfully stores TPR download links:
```
Jul 23 17:08:18: Stored 4 download links in session with forced update
```

But risk analysis download links are never created because the completion flag isn't set.

### Technical Details
- The error occurs in `app/tools/complete_analysis_tools.py`
- Flask sessions require an active HTTP request context
- The analysis runs in a separate thread/process without this context
- Without `analysis_complete=True` in session, download manager ignores analysis files

## Issue 2: Generic Ward Explanations

### Symptoms
- User asks "Why is Gwapopolok ward ranked so highly?"
- System executes SQL query to get ward data
- Response provides generic explanations without actual values

### Root Cause
The system successfully queries the data but doesn't use the results in the response. The LLM generates a generic explanation instead of incorporating the actual values.

### Evidence from Logs
SQL query executed:
```sql
SELECT WardName, composite_score, composite_rank, pca_score, pca_rank FROM df WHERE WardName = 'Gwapopolok'
```

Actual data values found:
- **TPR**: 89.4% (extremely high test positivity rate)
- **Housing Quality**: 0.0437 (very poor, close to 0)
- **Composite Score**: 0.676 (highest in the dataset)
- **Zone**: Climate stress and water access priority area

But the response says:
- "Gwapopolok has a high malaria prevalence rate" (no specific value)
- "The ward likely has poor housing conditions" (uses "likely" instead of actual value)
- No mention of the specific composite score

### Technical Details
- Query executes successfully via `execute_sql_query` tool
- Results are available but not passed to the LLM for response generation
- The LLM generates a template-like response without actual data

## Impact Assessment

### Download Issue Impact
- Users cannot download processed risk analysis results
- Forces users to manually copy data from chat interface
- Breaks expected workflow after analysis completion

### Ward Explanation Impact
- Users don't get data-driven insights
- Explanations lack credibility without specific values
- Cannot validate or understand the ranking methodology

## Recommendations for Fix

### For Download Issue
1. Move session updates to within the request context
2. Use Flask's `current_app.app_context()` for background tasks
3. Implement a callback mechanism to update session after analysis
4. Consider using Redis or database for cross-process session management

### For Ward Explanation Issue
1. Ensure SQL query results are passed to LLM in the prompt
2. Modify the tool to format results as part of the context
3. Update prompt to explicitly request using actual values
4. Add validation to ensure responses include queried data

## Session Comparison
Looking at two different sessions shows the pattern:
- Session `d6da74ce...`: First analysis, has TPR links but missing risk analysis links
- Session `5973e66f...`: Second analysis, starts fresh but encounters same issue

Both sessions show the same "Working outside of request context" error when completing analysis.