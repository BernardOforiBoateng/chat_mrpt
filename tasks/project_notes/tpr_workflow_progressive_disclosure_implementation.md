# TPR Workflow Progressive Disclosure Implementation

**Date**: 2025-09-28
**Author**: Claude
**Status**: Completed Core Implementation

## Summary
Successfully implemented progressive disclosure for TPR workflow to address user feedback about information overload. Visualizations are now generated but only shown when users request them.

## Changes Made

### 1. TPR Workflow Handler (`tpr_workflow_handler.py`)
- **Store instead of display**: Modified `handle_facility_selection()` and `handle_age_group_selection()` to store visualizations in state instead of returning them
- **Clear state on start**: Added state clearing in `start_workflow()` to remove old visualizations
- **Improved introduction**: Added comprehensive workflow introduction message with 3-step overview
- **New retrieval method**: Added `get_pending_visualizations()` to retrieve stored visualizations for agent

### 2. Message Formatters (`formatters.py`)
- **Conversational tone**: Updated all format methods to be more conversational and natural
- **Gentle hints**: Added hints about data availability without forcing it
- **Context-aware recommendations**: Provide data-driven recommendations based on actual dataset

### 3. System Prompt (`system_prompt.py`)
- **Visualization guidance**: Added instructions for agent to check for pending visualizations
- **Request handling**: Guidance on how to respond to "show data" type requests

### 4. Agent (`agent.py`)
- **Visualization detection**: Added logic to detect when users ask for data/charts
- **On-demand display**: Retrieves and shows pending visualizations only when requested
- **Smooth fallback**: Routes to AI with context when not a visualization request

## Key Design Decisions

### Why Store Instead of Defer Generation?
- **Instant response**: When user asks for data, it's already ready
- **No delay**: Avoids 2-3 second generation time during conversation
- **Memory efficient**: Visualizations are small (just HTML strings)
- **Consistent**: Same visualizations throughout the stage

### Progressive Disclosure Pattern
```
Before: [Auto-show 2 charts] → User overwhelmed → Make decision
After: [Generate but hide] → User asks if needed → Show charts → Make decision
```

### User Control Levels
1. **Minimal**: Just see options and decide (no charts)
2. **Guided**: Ask for help and get recommendations
3. **Full**: Request data and see all visualizations
4. **Power**: Type keywords directly (1, 2, 3, 4)

## Test Results

### Basic Workflow Test
- ✅ Visualizations not auto-displayed
- ✅ Visualizations stored in state
- ✅ Retrieval method works
- ✅ No breaking changes to workflow

### Expected User Experience
**Without requesting data:**
- Clean, conversational prompts
- No charts unless asked
- Gentle hints about availability
- Quick progression through workflow

**With data requests:**
- Instant display when asked
- Clear explanations with charts
- Return to workflow question
- Full control over depth

## Production Deployment Notes

### Files Changed
1. `app/data_analysis_v3/core/tpr_workflow_handler.py`
2. `app/data_analysis_v3/core/formatters.py`
3. `app/data_analysis_v3/prompts/system_prompt.py`
4. `app/data_analysis_v3/core/agent.py`

### Deployment Command
```bash
# Deploy to both production instances
for ip in 3.21.167.170 18.220.103.20; do
    scp -i ~/.ssh/chatmrpt-key.pem [files] ec2-user@$ip:/home/ec2-user/ChatMRPT/app/data_analysis_v3/
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$ip 'sudo systemctl restart chatmrpt'
done
```

### Rollback Plan
If issues occur, visualizations can be re-enabled by changing:
```python
"visualizations": None  # Current (progressive)
# to
"visualizations": facility_viz  # Original (auto-show)
```

## Metrics to Monitor

### Success Indicators
- Reduced time per stage selection
- Fewer user questions/confusion
- Higher workflow completion rate
- Positive user feedback

### Potential Issues
- Users might not know data is available (monitor)
- Power users might find hints annoying (can remove)
- Some users might always ask for data (that's OK)

## Future Enhancements

### Phase 2 Possibilities
1. **User preferences**: Remember if user always asks for data
2. **Smart defaults**: Show data automatically for complex decisions
3. **Contextual display**: Auto-show if user hesitates >30 seconds
4. **Interactive selection**: Make charts clickable for selection

## Conclusion

The implementation successfully addresses the "information ambush" problem while maintaining all functionality. Users now have control over information depth, leading to a more comfortable and empowering workflow experience.

The solution is:
- **Simple**: Minimal code changes
- **Effective**: Solves the core problem
- **Backward compatible**: Easy to revert if needed
- **User-friendly**: Gives control without complexity