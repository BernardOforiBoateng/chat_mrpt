# Fix Plan: Data Upload Overview Issue

## Problem Summary
After file upload, the data overview with two options (Data Analysis vs TPR Workflow) is not appearing. The system shows "Starting analysis..." but gets stuck.

## Root Cause
The `/api/v1/data-analysis/chat` endpoint is being called after upload but is not returning the expected data overview message. The frontend expects a response with `success: true` and a `message` containing the overview, but this is not being generated correctly.

## Step-by-Step Fix Plan

### Step 1: Add Debug Logging to Backend
**File**: `app/web/routes/data_analysis_v3_routes.py`
- Add logging to track the exact response being returned
- Log the message content and success status
- Verify the agent is being called correctly

### Step 2: Fix Initial Data Overview Generation
**File**: `app/data_analysis_v3/core/agent.py`
- Ensure the `analyze` method properly handles "analyze uploaded data" message
- Verify the `_generate_user_choice_summary` method creates the two-option overview
- Check that the response includes both options:
  1. Start Data Analysis (Option 1)
  2. TPR Workflow (Option 2)

### Step 3: Verify Session Data Loading
**File**: `app/data_analysis_v3/core/agent.py`
- Ensure uploaded data is properly loaded from session folder
- Check that data file paths are correctly resolved
- Verify data is accessible to the agent before analysis

### Step 4: Format Response Correctly
**Expected Response Format**:
```json
{
  "success": true,
  "message": "📊 **I've successfully loaded your data!**\n\nData Overview:\n- [details]\n\nHow would you like to proceed?\n\n1️⃣ **Start Data Analysis**\n2️⃣ **Calculate TPR**",
  "session_id": "xxx"
}
```

### Step 5: Test Frontend Message Display
- Ensure the message is properly added to the chat
- Verify the message content is displayed with formatting
- Check that users can select options 1 or 2

## Implementation Order

1. **First**: Add comprehensive logging to understand current behavior
2. **Second**: Fix the data overview generation in the agent
3. **Third**: Ensure proper response formatting
4. **Fourth**: Test end-to-end flow with sample data

## Testing Strategy

1. Upload sample CSV + Shapefile
2. Check console for successful upload
3. Verify `/api/v1/data-analysis/chat` is called
4. Confirm response contains overview message
5. Verify overview displays with two clickable options
6. Test both option selections work correctly

## Success Criteria

✅ After file upload, users see a data overview
✅ Overview shows data statistics (rows, columns, location)
✅ Two clear options are presented:
   - Option 1: Start Data Analysis
   - Option 2: Calculate TPR (Test Positivity Rate)
✅ Users can select either option to proceed
✅ No "Starting analysis..." stuck state

## Files to Modify

1. `app/data_analysis_v3/core/agent.py` - Fix analyze method
2. `app/web/routes/data_analysis_v3_routes.py` - Add logging
3. Potentially: `app/data_analysis_v3/prompts/system_prompt.py` - Update prompts

## Rollback Plan

If fixes cause issues:
1. Revert to backup version from GitHub
2. Test with original code to confirm it worked
3. Apply fixes incrementally with testing between each