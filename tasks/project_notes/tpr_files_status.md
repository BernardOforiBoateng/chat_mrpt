# TPR Module Files Status - Old vs New Implementation

## Files That Have Been SUPERSEDED (Can be Deprecated)

### 1. Original LLM-First Attempt (Not Used)
These were created when we first tried the pure LLM approach but aren't being used:
- `/app/tpr_module/conversation.py` - ReAct conversation handler (SUPERSEDED by interactive_conversation.py)
- `/app/tpr_module/prompts.py` - Chain-of-Thought prompts (SUPERSEDED by interactive_prompts.py)
- `/app/tpr_module/sandbox.py` - Sandboxed execution (NOT NEEDED - we don't generate code anymore)
- `/app/web/routes/tpr_react_routes.py` - Flask routes for ReAct pattern (NOT USED)

### 2. Legacy Rigid Implementation (Partially Superseded)
- `/app/tpr_module/integration/tpr_handler.py` - Old rigid handler (SUPERSEDED by interactive_tpr_handler.py)
  - BUT: Still used as fallback when USE_INTERACTIVE_TPR=false
  
## Files That Are STILL NEEDED (Modified/Enhanced)

### 1. Core Calculation Logic (Keep - Used by Both)
- `/app/tpr_module/core/tpr_calculator.py` - TPR formulas (KEEP - correct math)
- `/app/tpr_module/core/tpr_pipeline.py` - Pipeline orchestration (KEEP - still used)
- `/app/tpr_module/core/tpr_state_manager.py` - Session state (KEEP - both handlers use it)

### 2. Data Processing (Keep - Foundation)
- `/app/tpr_module/data/nmep_parser.py` - Parse NMEP files (KEEP - both use it)
- `/app/tpr_module/data/geopolitical_zones.py` - Zone variables (KEEP - critical data)
- `/app/tpr_module/data/column_mapper.py` - Column detection (KEEP - enhanced by interactive)
- `/app/tpr_module/data/data_validator.py` - Data validation (KEEP)

### 3. Services (Keep - Shared Infrastructure)
- `/app/tpr_module/services/shapefile_extractor.py` - Extract shapefiles (KEEP - enhanced with fuzzy matching)
- `/app/tpr_module/services/state_selector.py` - State selection (KEEP)
- `/app/tpr_module/services/raster_extractor.py` - Environmental variables (KEEP)
- `/app/tpr_module/services/facility_filter.py` - Filter facilities (KEEP)
- `/app/tpr_module/services/threshold_detector.py` - Urban threshold detection (KEEP)

### 4. Output Generation (Keep - Enhanced)
- `/app/tpr_module/output/output_generator.py` - Generate files (MODIFIED - now uses WardName_Matched)
- `/app/tpr_module/output/tpr_report_generator.py` - HTML reports (KEEP)

### 5. Integration Layer (Keep - Current Implementation)
- `/app/tpr_module/integration/__init__.py` - Handler factory (MODIFIED - supports both)
- `/app/tpr_module/integration/interactive_tpr_handler.py` - NEW interactive handler (ACTIVE)
- `/app/tpr_module/integration/upload_detector.py` - Detect TPR uploads (KEEP)
- `/app/tpr_module/integration/tpr_workflow_router.py` - Route workflows (KEEP)
- `/app/tpr_module/integration/risk_transition.py` - Transition to risk analysis (KEEP)

### 6. Interactive Implementation (New - Active)
- `/app/tpr_module/interactive_conversation.py` - Interactive dialogue manager (ACTIVE)
- `/app/tpr_module/interactive_prompts.py` - User-friendly prompts (ACTIVE)

### 7. Web Routes (Keep - In Use)
- `/app/web/routes/tpr_routes.py` - Main TPR routes (MODIFIED - handles both handlers)

## Summary

### Can Be Removed (4 files):
```
app/tpr_module/conversation.py
app/tpr_module/prompts.py  
app/tpr_module/sandbox.py
app/web/routes/tpr_react_routes.py (if it exists)
```

### Must Keep as Fallback (1 file):
```
app/tpr_module/integration/tpr_handler.py  # Legacy but needed for rollback
```

### Active and Enhanced (Everything else):
All other files are either:
- Part of the new interactive implementation
- Shared infrastructure used by both
- Enhanced to support ward matching

## Recommendation

1. **Don't delete yet** - Keep old files for 1-2 weeks after deployment
2. **Add deprecation warnings** to old files:
   ```python
   import warnings
   warnings.warn(
       "This module is deprecated. Use interactive_conversation.py instead.",
       DeprecationWarning,
       stacklevel=2
   )
   ```
3. **Monitor usage** - Check logs to see if legacy handler is still being used
4. **Clean up after stable** - Remove deprecated files after confirming interactive mode works well

## Migration Path

Current state allows both:
- `USE_INTERACTIVE_TPR=true` → New interactive handler with ward matching
- `USE_INTERACTIVE_TPR=false` → Legacy handler (immediate rollback if needed)

This dual-mode approach ensures safety during transition.