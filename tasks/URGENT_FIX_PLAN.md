# URGENT FIX PLAN - TPR Workflow Broken

## Date: 2025-10-13 03:20 UTC

## Summary:
I broke 3 things when refactoring to 2-route. Here's the MINIMAL fix needed:

## Fix #1: Add Confirmation Keyword Check in Routes

**File**: `app/web/routes/data_analysis_v3_routes.py`
**Location**: BEFORE the 2-route logic (around line 399)
**Change**: Add keyword matching for confirmation BEFORE attempting LLM extraction

```python
# BEFORE 2-route logic starts
if current_state.get('tpr_awaiting_confirmation'):
    confirmation_keywords = ['yes', 'y', 'continue', 'proceed', 'start', 'begin', 'ok', 'okay', 'sure', 'ready']
    message_clean = message.lower().strip()
    if message_clean in confirmation_keywords or any(kw in message_clean.split() for kw in confirmation_keywords):
        # Execute confirmation
        response = tpr_handler.execute_confirmation()
        return jsonify(response)
```

This fixes: "sure thing" → auto-select state ✅

## Fix #2: Restore analyze_tpr_data Tool Call

**File**: `app/data_analysis_v3/tpr/workflow_manager.py`
**Location**: `execute_age_selection()` method, lines 520-543
**Change**: Replace the ENTIRE try block (lines 522-543) with the tool call from backup

```python
# Calculate TPR using the tool (like backup did)
import json
import os
from ..tools.tpr_analysis_tool import analyze_tpr_data

# Prepare options for the tool
options = {
    'age_group': age_group,
    'facility_level': facility_level,
    'test_method': 'both'  # Always use maximum of both methods (WHO standard)
}

# Create graph state for the tool
graph_state = {
    'session_id': self.session_id,
    'data_loaded': True,
    'data_file': f"instance/uploads/{self.session_id}/uploaded_data.csv"
}

# Save data to CSV for tool to access (if not already saved)
data_path = f"instance/uploads/{self.session_id}/uploaded_data.csv"
if not os.path.exists(data_path):
    df.to_csv(data_path, index=False)
    logger.info(f"✅ Saved data to {data_path} for TPR tool")

# Call the tool
logger.info(f"🎯 Calling TPR tool with options: {options}")
result = analyze_tpr_data.invoke({
    'thought': f"Calculating TPR for {self.tpr_selections.get('state', 'state')} with user selections",
    'action': "calculate_tpr",
    'options': json.dumps(options),
    'graph_state': graph_state
})

logger.info(f"✅ TPR tool completed")

# Format the tool results
from ..core.formatters import MessageFormatter
formatter = MessageFormatter(self.session_id)
message = formatter.format_tool_tpr_results(result)

# Mark workflow complete
self.state_manager.mark_tpr_workflow_inactive()
self.state_manager.update_workflow_stage(ConversationStage.INITIAL)

return {
    "success": True,
    "message": message,
    "session_id": self.session_id,
    "stage": "COMPLETE",
    "workflow": 'tpr'
}
```

This fixes: 'TPRDataAnalyzer' object has no attribute 'calculate_tpr' ✅

## Fix #3: LLM Already Works - Just Needs Fix #1

The LLM extraction is actually fine. Once Fix #1 is in place, it will work correctly because:
- "sure thing" will be caught by keyword matching
- "Let's go with primary" will be extracted by LLM as "primary"
- "over five years" has synonym mapping to "o5"

## What NOT to Change:
- Don't touch the LLM extraction logic
- Don't touch execute_confirmation() - it works
- Don't remove natural language support

## Testing After Fixes:
1. "sure thing" → should auto-select state
2. "Let's go with primary" → should extract "primary" command
3. "u5" → should trigger TPR calculation via tool

**DO I HAVE PERMISSION TO APPLY THESE FIXES?**
