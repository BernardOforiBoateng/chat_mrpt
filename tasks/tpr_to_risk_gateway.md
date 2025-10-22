# TPR to Risk Analysis Gateway Implementation Plan

## Overview
Create a seamless transition from TPR analysis completion to risk analysis, automatically using TPR output files as input for the standard malaria risk assessment workflow.

## Current State Analysis

### TPR Output Files
1. **main_analysis.csv** - Contains TPR + environmental variables (this is what risk analysis needs)
2. **shapefile.zip** - State boundaries with all data
3. **tpr_analysis.csv** - Detailed TPR calculations (not needed for risk analysis)
4. **summary_report.md** - Summary report (informational only)

### Standard Risk Analysis Input Requirements
1. **CSV file** - Demographic/health data with ward-level information
2. **Shapefile** - Geographic boundaries as ZIP file

### Key Finding
TPR's `main_analysis.csv` + `shapefile.zip` exactly match what risk analysis needs!

## Implementation Plan

### Phase 1: Backend Infrastructure

- [ ] **Task 1.1**: Create TPR-to-Risk transition handler
  - Location: `app/tpr_module/integration/risk_transition.py`
  - Function to copy/link TPR outputs to risk analysis input format
  - Preserve session state while transitioning workflows
  
- [ ] **Task 1.2**: Add transition API endpoint
  - Location: `app/web/routes/tpr_routes.py`
  - Endpoint: `/api/tpr/transition-to-risk`
  - Validates TPR outputs exist
  - Prepares files for risk analysis
  - Returns transition status

- [ ] **Task 1.3**: Modify upload detector to recognize TPR transition
  - Update `app/web/routes/upload_routes.py`
  - Add new upload type: 'tpr_transition'
  - Skip file upload UI when transitioning from TPR

### Phase 2: Frontend Integration

- [ ] **Task 2.1**: Add "Continue to Risk Analysis" button
  - Location: TPR completion UI (in chat response)
  - Appears after successful TPR analysis
  - Styled as prominent call-to-action
  
- [ ] **Task 2.2**: Create transition UI flow
  - Show loading state during transition
  - Auto-navigate to risk analysis tab
  - Display success message with file info

- [ ] **Task 2.3**: Update chat interface for seamless experience
  - Preserve conversation history
  - Show transition context in chat
  - Enable risk analysis tools automatically

### Phase 3: Session Management

- [ ] **Task 3.1**: Implement dual-workflow session state
  - Track both TPR and risk analysis states
  - Preserve TPR results while running risk analysis
  - Allow switching between workflows

- [ ] **Task 3.2**: File management strategy
  - Create symbolic links vs copying files
  - Ensure proper cleanup on session end
  - Handle edge cases (missing files, corrupted data)

### Phase 4: User Experience Enhancements

- [ ] **Task 4.1**: Add workflow status indicator
  - Visual indicator showing TPR → Risk Analysis flow
  - Progress tracking across both analyses
  
- [ ] **Task 4.2**: Implement smart suggestions
  - After TPR: "Would you like to continue with risk analysis?"
  - Context-aware prompts based on TPR results
  
- [ ] **Task 4.3**: Create unified results view
  - Combined dashboard showing TPR + Risk results
  - Ability to download all outputs together

## Technical Details

### File Mapping
```
TPR Output → Risk Analysis Input
---------------------------------
main_analysis.csv → raw_data.csv
shapefile.zip → raw_shapefile.zip
```

### Session State Transition
```python
# Current TPR state
session['tpr_workflow_active'] = True
session['tpr_outputs'] = {...}

# Transition state
session['risk_workflow_active'] = True
session['risk_input_source'] = 'tpr_transition'
session['data_loaded'] = True
session['should_ask_analysis_permission'] = True
```

### UI Flow
1. User completes TPR analysis
2. Success message shows with "Continue to Risk Analysis" button
3. Click triggers transition API
4. Files are prepared in background
5. UI switches to risk analysis tab
6. Risk analysis starts with TPR data pre-loaded

## Benefits
1. **Zero Re-upload**: Users don't need to download and re-upload files
2. **Seamless Flow**: Natural progression from TPR to risk assessment
3. **Data Consistency**: Same ward boundaries and identifiers throughout
4. **Time Savings**: Immediate transition without manual steps
5. **Context Preservation**: Full analysis history in one session

## Edge Cases to Handle
1. TPR analysis fails or incomplete
2. Missing output files
3. User wants to use different data for risk analysis
4. Session timeout during transition
5. Browser refresh during transition

## Success Metrics
1. Transition completes in < 2 seconds
2. 100% of TPR outputs successfully used for risk analysis
3. No data loss during transition
4. User can access both TPR and risk results
5. Clear UI feedback throughout process

## Implementation Priority
Given the clear file compatibility and user workflow benefits, this should be implemented as a high-priority enhancement after TPR module stabilization.