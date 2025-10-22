# Arena Think Tag Fix

**Date**: 2025-09-29
**Issue**: Qwen model's `<think>` tags were appearing in arena responses
**Solution**: Add think tag filtering to ollama_adapter.py

## Problem Description

In the arena system, when Qwen model generated a response, its internal thinking process wrapped in `<think>...</think>` tags was being displayed to users. This created a poor user experience where the model's internal reasoning was visible instead of just the final response.

Example of problematic output:
```
<think> Okay, the user said "hi". I need to respond appropriately... </think>
Hello! I'm ChatMRPT...
```

## Root Cause

The issue was in `app/core/ollama_adapter.py`:
- The `generate_async` method was returning raw responses from Ollama models
- Unlike the LLMAdapter class (used for OpenAI models), OllamaAdapter wasn't filtering think tags
- Arena uses OllamaAdapter for local models including Qwen

## Solution

Modified `ollama_adapter.py` to clean think tags from responses:

```python
# Clean think tags from response (for Qwen and other models)
import re
# Remove <think>...</think> tags and content
response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL | re.IGNORECASE)
# Also handle case where </think> is missing
if '<think>' in response_text:
    parts = response_text.split('</think>')
    if len(parts) > 1:
        response_text = parts[-1].strip()
    else:
        # If no closing tag, remove everything from <think> onwards
        response_text = response_text.split('<think>')[0].strip()

response_text = response_text.strip()
```

## Key Points

1. **Regex cleaning**: Removes complete `<think>...</think>` blocks
2. **Fallback handling**: Handles cases where closing tag is missing
3. **Case insensitive**: Works with various tag capitalizations
4. **Consistent with LLMAdapter**: Follows same pattern used for OpenAI models

## Files Modified

- `/app/core/ollama_adapter.py` - Added think tag cleaning to `generate_async` method

## Testing & Deployment

1. Verified no syntax errors locally
2. Deployed to both production instances:
   - Instance 1: 3.21.167.170 ✅
   - Instance 2: 18.220.103.20 ✅
3. Restarted services on both instances

## Expected Results

After this fix:
- Qwen responses in arena will show only the actual response content
- Internal thinking tags will be stripped before display
- User experience improved with cleaner responses
- Consistent behavior across all model types

## Related Code

LLMAdapter already had similar cleaning:
- `/app/core/llm_adapter.py` - Lines 142-143, 404-405, 444-449
- `/app/core/ollama_manager.py` - Lines 119-124

This fix brings OllamaAdapter to parity with existing cleaning mechanisms.