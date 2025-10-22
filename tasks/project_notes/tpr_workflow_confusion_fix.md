# TPR Workflow vs General Agent Confusion Fix

## Date: 2025-01-19

## Problem
The Data Analysis V3 agent was confusing general analysis queries with TPR workflow requests, causing inappropriate routing:

1. User asked: "Show me monthly variations in test positivity" 
2. Agent triggered TPR workflow instead of performing analysis
3. UI showed 4 options when user wanted only 2 clear paths

## Root Causes

### 1. Overly Broad Keyword Matching
```python
# PROBLEMATIC CODE (line 675):
if ('test' in query_lower and 'positivity' in query_lower):
    return True  # Triggers for ANY mention of test + positivity!
```

### 2. Too Many Options
The system presented 4 options:
1. Calculate Test Positivity Rate (TPR)
2. Explore & Analyze Data  
3. Generate Summary Statistics (unnecessary)
4. Data Quality Report (unnecessary)

This created confusion about which option to choose.

## Solution Implemented

### 1. Fixed Keyword Detection (lines 673-683)
```python
# Only trigger for EXPLICIT TPR workflow requests
if ('calculate tpr' in query_lower) or \
   ('tpr calculation' in query_lower) or \
   ('guide' in query_lower and 'tpr' in query_lower) or \
   ('tpr workflow' in query_lower) or \
   ('guided' in query_lower and 'analysis' in query_lower):
    return True

# DO NOT trigger for general analysis queries
# e.g., "Show me test positivity trends" should go to general agent
```

### 2. Simplified to 2 Clear Paths (lines 615-624)
```python
summary += "\n**Choose your analysis approach:**\n\n"

summary += "1️⃣ **Guided TPR Analysis → Risk Assessment**\n"
summary += "   Step-by-step workflow to calculate Test Positivity Rate and prepare for risk analysis\n\n"

summary += "2️⃣ **Flexible Data Exploration**\n"
summary += "   Use AI to analyze patterns, create visualizations, and answer any questions about your data\n\n"
```

## Key Changes

1. **More Specific Triggers**: Now requires explicit phrases like "calculate tpr" or "tpr workflow"
2. **Clearer Options**: Reduced from 4 to 2 options with better descriptions
3. **Better Separation**: Clear distinction between guided workflow and flexible exploration

## Testing Scenarios

### Should Trigger TPR Workflow
- "1" or "calculate tpr"
- "guide me through tpr calculation"
- "tpr workflow"
- "guided analysis"

### Should NOT Trigger TPR Workflow  
- "Show me monthly variations in test positivity" → General agent analyzes
- "What's the test positivity trend?" → General agent analyzes
- "Compare positivity rates" → General agent analyzes
- "2" or any analysis question → General agent handles

## Files Modified
- `/app/data_analysis_v3/core/agent.py`
  - `_generate_user_choice_summary()` method
  - `_generate_fallback_summary()` method  
  - `_is_tpr_selection()` method

## Impact
- Users now have clearer choice between guided workflow and flexible analysis
- General analysis queries no longer incorrectly trigger TPR workflow
- Improved user experience with less confusion

## Deployment Notes
- Needs to be deployed to both staging instances
- No database changes required
- Backward compatible with existing sessions