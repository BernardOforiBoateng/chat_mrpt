# Fix Broken TPR Workflow - Urgent

## Date: 2025-10-13 03:15 UTC

## What I Broke:

Comparing context.md (WORKING) vs contxt.md (BROKEN):

### Issue #1: LLM Command Extraction Too Restrictive
- **Symptom**: "sure thing" returns "You're currently in the TPR workflow at the 'TPR_STATE_SELECTION' stage"
- **Expected**: Auto-select single state → show facility selection
- **Root Cause**: LLM `extract_command()` returning None for valid confirmations
- **Fix Location**: `app/data_analysis_v3/core/tpr_language_interface.py:extract_command()`

### Issue #2: Natural Language Not Extracting Commands
- **Symptom**: "Ok then let's go with primarry" → agent responds instead of executing
- **Expected**: Extract "primary" command → execute facility selection
- **Root Cause**: LLM extraction failing on natural language variations
- **Fix Location**: Same as Issue #1

### Issue #3: Missing TPR Calculation Method
- **Symptom**: Error: 'TPRDataAnalyzer' object has no attribute 'calculate_tpr'
- **Expected**: Call `analyze_tpr_data` tool to calculate TPR
- **Root Cause**: I replaced tool call with direct method call that doesn't exist
- **Fix Location**: `app/data_analysis_v3/tpr/workflow_manager.py:execute_age_selection()`

## What Still Works:
- The OLD routing in backup has keyword matching BEFORE 2-route logic
- State auto-selection when confirmation is detected
- The `analyze_tpr_data` tool exists and works

## Fix Strategy:
1. Check why LLM extraction is failing (prompt? model? parameters?)
2. Restore `analyze_tpr_data` tool call in execute_age_selection()
3. Test with exact same inputs from context.md

## DO NOT:
- Restore entire files from backup without permission
- Remove natural language support
- Change working confirmation logic
