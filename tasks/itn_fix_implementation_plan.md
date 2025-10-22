# ITN Issues Fix Implementation Plan

## Priority Order
1. **Fix Threshold Control** (High Priority - User-facing functionality broken)
2. **Fix Missing Areas** (High Priority - Data completeness issue) 
3. **Add Logging & Validation** (Medium Priority - Debugging support)

## Phase 1: Fix Threshold Control

### Step 1.1: Store ITN Parameters in Session
**File**: `app/analysis/itn_pipeline.py`
- After line 529, save parameters to session/Redis
- Store: total_nets, avg_household_size, method, session_id
- Use both file-based and Redis storage for multi-worker support

### Step 1.2: Fix JavaScript Update Function  
**File**: `app/analysis/itn_pipeline.py` (in map generation section)
- Modify the JavaScript in the threshold control HTML
- Change from hard-coded values to session-retrieved values
- Replace `window.location.reload()` with iframe src update
- Include session_id in the API request

### Step 1.3: Update Backend Endpoint
**File**: `app/web/routes/itn_routes.py`
- Modify `/api/itn/update-distribution` endpoint
- Retrieve stored parameters from session/Redis
- Use stored values if not provided in request
- Return new map filename for iframe update

### Step 1.4: Implement Dynamic Map Loading
**File**: `app/analysis/itn_pipeline.py`
- Generate unique map filenames with timestamp
- Return map filename in API response
- Update JavaScript to change iframe src dynamically

## Phase 2: Fix Missing Areas

### Step 2.1: Preserve All Shapefile Wards
**File**: `app/analysis/itn_pipeline.py`
- Modify line 399 to NOT remove wards without population
- Instead, flag them as "No Population Data"
- Use a default population estimate based on area/density

### Step 2.2: Improve Ward Matching
**File**: `app/analysis/itn_pipeline.py`
- Lower fuzzy matching threshold from 75% to 70%
- Implement two-pass matching:
  - First pass: exact match (normalized)
  - Second pass: fuzzy match with lower threshold
- Add LGA-based disambiguation for duplicate ward names

### Step 2.3: Visual Indicators for Unmatched Wards
**File**: `app/analysis/itn_pipeline.py` (generate_itn_map function)
- Add a third category for visualization: "Unmatched/No Data"
- Use distinct visual style (gray with diagonal stripes)
- Include explanatory text in hover tooltips

### Step 2.4: Add Matching Report
**File**: `app/analysis/itn_pipeline.py`
- Generate matching summary after fuzzy matching
- Save as `ward_matching_report.json` in session folder
- Include: matched count, unmatched wards list, match scores

## Phase 3: Add Comprehensive Logging

### Step 3.1: Ward Matching Logs
**File**: `app/analysis/itn_pipeline.py`
- Add debug logging for each matching attempt
- Log fuzzy match scores and decisions
- Track wards filtered at each stage

### Step 3.2: Threshold Update Logs
**Files**: `app/web/routes/itn_routes.py`, `app/analysis/itn_pipeline.py`
- Log incoming threshold update requests
- Log parameter retrieval from session
- Log map generation with new threshold

### Step 3.3: User-Facing Warnings
**File**: `app/tools/itn_planning_tools.py`
- Add warnings to the success message when wards are unmatched
- Include count of excluded wards
- Suggest checking ward names in uploaded data

## Implementation Checklist

### Quick Fixes (Do First)
- [ ] Fix hard-coded JavaScript values
- [ ] Add session_id to update requests
- [ ] Store ITN parameters in session

### Core Fixes  
- [ ] Implement dynamic map loading
- [ ] Preserve all shapefile wards
- [ ] Improve fuzzy matching logic
- [ ] Add visual indicators for missing data

### Enhancement Fixes
- [ ] Generate matching reports
- [ ] Add comprehensive logging
- [ ] Add user warnings
- [ ] Create validation dashboard

## Testing Plan

### Test Scenario 1: Threshold Updates
1. Run ITN planning with 30% threshold
2. Change threshold to 50% and click Update
3. Verify map updates with new allocation
4. Check that total nets remains constant

### Test Scenario 2: Missing Wards
1. Upload data with known ward name mismatches
2. Run ITN planning
3. Verify all geographic areas appear on map
4. Check that unmatched wards show as "No Data"

### Test Scenario 3: Multi-Worker
1. Run ITN planning on one worker
2. Update threshold (may hit different worker)
3. Verify session state is maintained
4. Check Redis for stored parameters

## Deployment Notes
- Test on staging first with known problematic datasets
- Deploy to all production instances simultaneously
- Clear browser cache after deployment
- Monitor logs for matching failures