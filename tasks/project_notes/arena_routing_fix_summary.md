# Arena Routing Fix - Risk Analysis Mode

## Issue
Arena mode was being bypassed for general knowledge questions during risk analysis workflow. When users had uploaded data (CSV/shapefile), ALL questions were being routed to OpenAI with tools, even simple general knowledge questions like "what is malaria?" or "who are you?".

## Root Cause
The Mistral routing logic was biased toward "needs_tools" when it detected that data was uploaded (`has_uploaded_files: True`). The routing prompt included "Session has data: True" which made Mistral assume all questions were about that data.

## Solution Implemented

### 1. Improved Mistral Routing Prompt
- Removed the biasing "Session has data: True" line
- Added explicit decision tree logic
- Emphasized that uploaded data doesn't mean every question is about that data
- Added clear examples showing when to use Arena vs tools

### 2. Enhanced Pre-Routing Filter
- Expanded the pre-routing logic to catch more general knowledge questions
- Added patterns for: "what is", "how does", "explain", "tell me about", etc.
- Only bypasses pre-routing if the question explicitly references uploaded data

### 3. Fixed Fallback Logic
- Changed from auto-defaulting to "needs_tools" when data exists
- Now checks for explicit data references before routing to tools
- Defaults to "can_answer" (Arena mode) for general questions

## Files Modified
- `/app/web/routes/analysis_routes.py` - All routing logic changes

## Key Changes

### Before:
```python
# Biased prompt
Context:
- Session has data: True

# Fallback always used tools with data
if session_context.get('has_uploaded_files'):
    return "needs_tools"
```

### After:
```python
# Clear decision tree
CRITICAL ROUTING LOGIC:
Just because data is uploaded does NOT mean every question is about that data.

# Smart fallback checks for explicit references
data_references = ['my data', 'the data', 'uploaded', ...]
if any(ref in message_lower for ref in data_references):
    return "needs_tools"
return "can_answer"  # Default to Arena
```

## Testing
Created test scripts to verify:
- Pre-routing logic correctly identifies general questions
- Data-specific questions still route to tools
- Edge cases handled properly

All 16 test cases passed successfully.

## Result
Arena mode now correctly handles general knowledge questions even when users have uploaded data for risk analysis. The system only routes to OpenAI with tools when users explicitly ask about their uploaded data.