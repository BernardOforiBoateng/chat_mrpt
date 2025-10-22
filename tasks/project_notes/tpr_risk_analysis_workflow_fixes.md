# TPR to Risk Analysis Workflow Fixes

## Date: 2025-08-13

### Problem Summary
User reported multiple issues with TPR (Test Positivity Rate) to Risk Analysis workflow in Data Analysis V3:

1. **Map Display Issue**: TPR map wasn't displaying directly in chat interface - just showing text saying "map created"
2. **Risk Analysis Trigger Error**: When user typed "yes" after TPR completion, risk analysis failed with DataHandler initialization error

### Root Causes Identified

#### 1. Map Display Issue
- **Cause**: TPR tool was returning inline HTML (`<iframe>` tags) in the message text
- **Production Pattern**: Production system uses separate `visualizations` array with structured objects
- **Frontend Expectation**: Visualization manager processes visualization objects separately from message text

#### 2. DataHandler Initialization Error
- **Cause**: `DataHandler` class requires `session_folder` as first argument
- **Code Location**: `app/data_analysis_v3/core/tpr_workflow_handler.py` line 350
- **Error**: `DataHandler.__init__() missing 1 required positional argument: 'session_folder'`

### Solutions Implemented

#### 1. Fixed Map Display (Completed)
**File**: `app/data_analysis_v3/core/tpr_workflow_handler.py`
- Added `visualizations` array to response structure
- Created structured visualization objects:
```python
visualization = {
    'type': 'iframe',
    'url': f'/serve_viz_file/{self.session_id}/tpr_distribution_map.html',
    'title': f'TPR Distribution - {self.tpr_selections.get("state", "State")}',
    'height': 600
}
```
- Removed iframe HTML from message text

**File**: `app/data_analysis_v3/tools/tpr_analysis_tool.py`
- Removed all iframe HTML generation (3 locations)
- Tool now returns simple text notification about map creation

#### 2. Fixed DataHandler Initialization (Completed)
**File**: `app/data_analysis_v3/core/tpr_workflow_handler.py`
- Changed from:
```python
data_handler = DataHandler()
data_handler.load_from_session(self.session_id)  # Method doesn't exist
```
- To:
```python
data_handler = DataHandler(session_folder)  # Proper initialization
# DataHandler automatically reloads data via _attempt_data_reload()
```

### Testing Approach

Created proper unit tests following CLAUDE.md guidelines:
- `test_datahandler_fix.py`: Industry-standard unit tests with mocking
- Tests verify:
  - DataHandler requires session_folder argument
  - DataHandler accepts session_folder properly
  - trigger_risk_analysis passes correct arguments
  - Error handling for missing files

### Deployment Status
- ✅ Deployed to both staging instances (3.21.167.170, 18.220.103.20)
- ✅ Services restarted successfully
- Ready for user testing at: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com

### Test Instructions for User
1. Upload TPR data file (Excel or CSV with TPR columns)
2. Say "guide me through TPR calculation"
3. Complete TPR workflow (select facility level, age group)
4. Verify map displays directly in chat interface
5. When asked about risk analysis, type "yes"
6. Verify risk analysis runs without DataHandler error

### Key Learnings
1. **Frontend-Backend Contract**: Must match production's visualization structure exactly
2. **Tool vs Handler Pattern**: Tools return strings; handlers structure responses for frontend
3. **Testing Importance**: Proper unit tests would have caught the DataHandler issue earlier
4. **Code Reading**: Always check constructor requirements before using a class

### Related Files Changed
- `app/data_analysis_v3/core/tpr_workflow_handler.py` (main fix)
- `app/data_analysis_v3/tools/tpr_analysis_tool.py` (removed HTML)
- `test_datahandler_fix.py` (unit tests)
- `deploy_datahandler_fix.sh` (deployment script)

### Next Steps
- User to test complete workflow on staging
- Monitor for any additional issues
- Consider adding more comprehensive integration tests