# Final TPR Workflow Summary

## Date: 2025-08-13

## Final Design: 3-Step TPR Workflow

### The Complete Flow

1. **User uploads file** → Generic data summary (no TPR stats)

2. **User selects Option 1 (TPR)** → Begin TPR workflow

3. **Three Questions Only:**
   - **State?** → Show facilities and test counts per state
   - **Facility Level?** → Show distribution of facilities
   - **Age Group?** → Show test availability and positivity rates

4. **Automatic Calculation** → Use max(RDT, Microscopy) TPR

5. **Results** → Comprehensive TPR analysis with methodology explanation

## What We Fixed

### Problem 1: Conversation Amnesia
**Solution:** State management system that remembers selections

### Problem 2: Too Many Questions
**Solution:** Removed test method question - automatic handling

### Problem 3: Lack of Context
**Solution:** Rich statistics at each decision point (but only during TPR workflow)

### Problem 4: Information Overload
**Solution:** Progressive disclosure - TPR stats only when doing TPR

## Technical Implementation Summary

### 1. State Manager
```python
class DataAnalysisStateManager:
    - Stores conversation stage
    - Stores TPR selections (state, facility, age)
    - Persists across messages
    - File-based for multi-worker support
```

### 2. Enhanced Agent
```python
class DataAnalysisAgent:
    - Restores state on init
    - Tracks workflow progression
    - Shows contextual statistics
    - Handles automatic test method selection
```

### 3. TPR Data Analyzer
```python
class TPRDataAnalyzer:
    - Calculates statistics per option
    - Provides recommendations
    - Identifies data quality issues
    - Generates rich summaries
```

## User Experience Comparison

### Before (Broken)
- Generic options with no context
- Forgets previous selections
- Asks for test method unnecessarily
- No statistics to guide decisions

### After (Fixed)
- Progressive disclosure of information
- Remembers workflow state
- 3 questions instead of 4
- Rich context exactly when needed

## Key Design Principles

1. **Don't overwhelm on upload** - Keep initial summary generic
2. **Progressive disclosure** - Show TPR stats only during TPR workflow
3. **Contextual information** - Provide stats relevant to current decision
4. **Automatic best practices** - Handle test methods intelligently
5. **State persistence** - Remember user's journey

## Implementation Phases

### Phase 1: State Management (Core Fix)
- Create state manager
- Add state restoration
- Fix amnesia issue

### Phase 2: Workflow Simplification
- Remove test method question
- Implement 3-step flow
- Add automatic calculation

### Phase 3: Enhanced Information
- Add statistics per option
- Show recommendations
- Display data quality

## Files to Create/Modify

### New Files:
1. `app/data_analysis_v3/core/state_manager.py`
2. `app/data_analysis_v3/core/tpr_analyzer.py`

### Modified Files:
1. `app/data_analysis_v3/core/agent.py` - Add state management
2. `app/data_analysis_v3/prompts/system_prompt.py` - Update for 3-step flow
3. `app/web/routes/data_analysis_v3_routes.py` - Ensure state persistence

## Testing Plan

1. **Basic Flow**: Upload → TPR → 3 questions → Results
2. **State Persistence**: Refresh page mid-workflow
3. **Context Switch**: Start TPR, ask general question, resume TPR
4. **Data Variations**: Test with RDT only, Microscopy only, both
5. **Multi-worker**: Test across different server instances

## Success Criteria

✅ No more asking for confirmation of already-stated choices
✅ TPR workflow completes in 3 questions
✅ Users see relevant statistics for decisions
✅ State persists across page refreshes
✅ Works with multi-worker deployment

## Final Notes

- Based on production TPR module that worked well
- Simplified from initial plan (removed test method question)
- Balances information richness with simplicity
- Progressive disclosure prevents overwhelm
- Maintains flexibility for non-TPR analysis