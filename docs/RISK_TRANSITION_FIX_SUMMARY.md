# Risk Analysis Transition Fix - Summary

## The Issue
After TPR calculation completed, the transition prompt asking if users want to proceed with risk analysis was being removed, causing the workflow to exit data analysis mode.

## Root Cause
The transition prompt was being added by the formatter but then immediately stripped out when removing iframe HTML content. The code at line 384 was doing:
```python
message = message.split('<iframe')[0].strip()
```
This removed everything after the iframe tag, including the transition prompt.

## The Fix
Modified the iframe removal logic to preserve content after the iframe tag if it contains the transition prompt:

```python
# Remove iframe HTML from message if it exists but preserve transition prompt
if '<iframe' in message:
    # Split by iframe to preserve content before and after
    parts = message.split('<iframe')
    message_before = parts[0].strip()
    
    # Check if there's important content after the iframe (like transition prompt)
    if '</iframe>' in message:
        remaining = message.split('</iframe>', 1)[-1].strip()
        if 'Next Step:' in remaining or 'Would you like' in remaining or 'risk analysis' in remaining:
            # Preserve the transition prompt that comes after the iframe
            message = message_before + "\n\n" + remaining
        else:
            message = message_before
    else:
        message = message_before
```

## Files Modified
- `app/data_analysis_v3/core/tpr_workflow_handler.py` (lines 381-400)

## Expected Result
After TPR calculation completes:
1. Visualization is displayed
2. Transition prompt appears: "Would you like to proceed to the risk analysis to rank wards and plan for ITN distribution?"
3. User can reply "yes" to continue or "no" to stop
4. System transitions smoothly to risk analysis without exiting data analysis mode