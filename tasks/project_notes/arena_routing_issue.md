# Arena Routing Issue - Action Requests Misrouted

## Date: 2025-01-17

## Issue Found
"Plot me the map distribution for the evi variable" is going to Arena instead of tool calling.

## Root Cause Analysis

### Request Flow Order (in `request_interpreter.py`):
```python
def process_message():
    # Step 1: Check special workflows (line 144)
    special_result = self._handle_special_workflows(...)
    if special_result:
        return special_result

    # Step 2: Check Arena triggers (line 156-157) ← PROBLEM HERE!
    arena_result = self._check_arena_triggers(...)
    if arena_result and arena_result.get('use_arena'):
        return self._trigger_arena_interpretation(...)

    # Step 3: Standard tools (after line 170)
    # Tools like 'create_vulnerability_map', 'create_box_plot', etc.
```

### The Problem:
Arena triggers are checked BEFORE tool execution. Arena's trigger detection is too aggressive when `analysis_complete=True`.

### Arena Trigger Logic (`arena_trigger_detector.py`, lines 445-459):
```python
if context.get('analysis_complete', False) and context.get('data_loaded', False):
    interpretation_keywords = ['explain', 'what does', 'mean', 'why', 'how', 'interpret']
    ward_keywords = ['ward', 'area', 'region', 'risk']

    has_interpretation = any(kw in message_lower for kw in interpretation_keywords)
    has_ward = any(kw in message_lower for kw in ward_keywords)

    if has_interpretation or has_ward:
        return {'use_arena': True, ...}
```

This catches requests that should go to tools because it's too broad.

## Solution Needed

Add ACTION verb detection to skip Arena for tool commands:

### Option 1: Modify `_check_arena_triggers` in `request_interpreter.py`
```python
def _check_arena_triggers(self, user_message: str, ...):
    # Skip Arena for ACTION requests
    action_verbs = ['plot', 'create', 'generate', 'show', 'display', 'draw', 'make', 'build', 'produce']
    message_lower = user_message.lower()

    # If message starts with action verb, skip Arena
    for verb in action_verbs:
        if message_lower.startswith(verb) or f" {verb} " in message_lower:
            return {'use_arena': False, 'reason': 'Action request - route to tools'}

    # Continue with existing Arena trigger detection...
```

### Option 2: Modify Arena trigger detector itself
Update `detect_trigger` in `arena_trigger_detector.py` to exclude action requests:
```python
def detect_trigger(self, user_message: str, context: Dict[str, Any]):
    # Check for action requests first
    action_patterns = [
        r'^(plot|create|generate|show|display|draw|make|build|produce)',
        r'(plot|create|generate|show|display) .* (map|chart|graph|plot|visualization)'
    ]

    for pattern in action_patterns:
        if re.search(pattern, user_message.lower()):
            return {'use_arena': False, 'reason': 'Tool action request'}

    # Continue with existing trigger detection...
```

## Examples of Misrouted Requests

These should go to **TOOLS**, not Arena:
- "Plot me the map distribution for the evi variable" → `create_vulnerability_map` tool
- "Create a box plot of TPR values" → `create_box_plot` tool
- "Generate a PCA visualization" → `create_pca_map` tool
- "Show me the data distribution" → `create_variable_distribution` tool

These should go to **Arena**:
- "What does this mean?" → Arena interpretation
- "Explain these results" → Arena interpretation
- "Tell me about the variables in my data" → Arena (but needs data access fix)
- "What are the implications?" → Arena interpretation

## Impact
Users are getting Arena interpretations when they explicitly request tool actions like plotting or creating visualizations. This breaks the expected workflow and doesn't give users what they asked for.

## Recommendation
Implement Option 1 (modify `_check_arena_triggers`) as it's a cleaner separation of concerns. Arena trigger detector should remain focused on interpretation triggers, while the request interpreter handles routing logic.