# Original TPR Implementation - What to Do With It

## The Original (Flawed) TPR Implementation

These are the files from the ORIGINAL TPR system that had problems:

### Core Files (Original Implementation)
1. **`/app/tpr_module/core/tpr_conversation_manager.py`** 
   - The old conversation manager with rigid column detection
   - Had hardcoded column names like "RDT_Tested_SUM"
   - **STATUS**: Still used as fallback when `USE_INTERACTIVE_TPR=false`

2. **`/app/tpr_module/integration/tpr_handler.py`**
   - The original handler that couldn't handle ward name variations
   - Would drop wards that didn't match exactly
   - **STATUS**: Still used as fallback when `USE_INTERACTIVE_TPR=false`

3. **`/app/tpr_module/core/tpr_pipeline.py`**
   - Original pipeline that was too rigid
   - **STATUS**: Still being used (we call it from new handler)

4. **`/app/tpr_module/data/column_mapper.py`**
   - Had rigid column mapping logic
   - **STATUS**: Still exists but bypassed by interactive system

### What These Files Did Wrong:
- **Rigid column detection**: Expected exact column names
- **No ward name matching**: Dropped unmatched wards
- **No user interaction**: Couldn't ask for clarification
- **Hardcoded assumptions**: About data structure

## The New Implementation (What We Built)

### New Files We Created:
1. **`/app/tpr_module/interactive_conversation.py`** - Handles user dialogue
2. **`/app/tpr_module/integration/interactive_tpr_handler.py`** - New handler with fuzzy matching
3. **`/app/tpr_module/interactive_prompts.py`** - User-friendly prompts

### What We Fixed:
- **Fuzzy ward matching**: Matches "Doubeli" to "Doubeli Ward"
- **User verification**: Asks user when unsure
- **Dynamic detection**: No hardcoded column names
- **Maximum data retention**: Doesn't drop wards unnecessarily

## Current Situation

We have **TWO parallel implementations**:

```python
if USE_INTERACTIVE_TPR == 'true':
    # Use NEW implementation (with fuzzy matching)
    handler = InteractiveTPRHandler()  
else:
    # Use OLD implementation (rigid, flawed)
    handler = TPRHandler()  
```

## What Should We Do?

### Option 1: Keep Both (Current State)
- **Pros**: Safe rollback if new system has issues
- **Cons**: Maintaining two codebases

### Option 2: Remove Old Implementation
- **Pros**: Cleaner codebase, no confusion
- **Cons**: No fallback if issues arise

### Option 3: Gradual Deprecation (Recommended)
1. **Now**: Keep both, default to new
2. **After testing**: Make new the only option
3. **After 2 weeks stable**: Remove old files

## Files That Can Eventually Be Removed

Once we're confident in the new implementation:

### Can Remove:
- `/app/tpr_module/core/tpr_conversation_manager.py` - Old conversation manager
- `/app/tpr_module/integration/tpr_handler.py` - Old handler (keep get_tpr_handler function)
- `/app/tpr_module/data/column_mapper.py` - Rigid column mapping

### Must Keep:
- `/app/tpr_module/core/tpr_calculator.py` - Math is still correct
- `/app/tpr_module/data/geopolitical_zones.py` - Zone data still needed
- `/app/tpr_module/services/*` - All services still used
- `/app/tpr_module/output/output_generator.py` - Enhanced but still needed

## The Bottom Line

The original TPR implementation is **still there as a fallback**. We didn't delete it yet because:
1. It provides a safety net
2. You can instantly rollback by setting `USE_INTERACTIVE_TPR=false`
3. We should test the new system thoroughly first

Once you're happy with the new interactive system, we can remove the old implementation files.