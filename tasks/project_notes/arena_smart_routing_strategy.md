# Smart Routing Strategy for Arena vs Tools

## Date: 2025-01-17

## The Challenge
We have a hybrid system where:
- OpenAI excels at understanding user intent and executing tools
- Arena (Ollama) provides cheaper interpretation but can't execute tools
- We want to minimize OpenAI API costs while maintaining functionality

## Current Problem
Arena intercepts ALL requests after analysis completes, including tool action requests that it can't handle.

## Proposed Solution: Intent-Based Routing

### Step 1: Classify User Intent FIRST

```python
def classify_intent(user_message: str) -> str:
    """Classify user intent to determine routing."""
    message_lower = user_message.lower()

    # 1. ACTION INTENT - Requires tool execution
    action_verbs = ['plot', 'create', 'generate', 'show', 'display',
                    'draw', 'make', 'build', 'produce', 'run', 'calculate']
    for verb in action_verbs:
        if verb in message_lower:
            return 'ACTION'

    # 2. INTERPRETATION INTENT - Can use Arena
    interpretation_phrases = ['what does this mean', 'explain', 'interpret',
                             'implications', 'why', 'understand']
    for phrase in interpretation_phrases:
        if phrase in message_lower:
            return 'INTERPRETATION'

    # 3. INFORMATION INTENT - Can use Arena (with data access)
    info_phrases = ['tell me about', 'describe', 'what is', 'list',
                    'show me the variables', 'what columns']
    for phrase in info_phrases:
        if phrase in message_lower:
            return 'INFORMATION'

    # 4. COMPLEX INTENT - May need both
    if 'and' in message_lower and ('explain' in message_lower or 'what' in message_lower):
        return 'COMPLEX'

    # Default to interpretation if data is loaded and analysis complete
    return 'INTERPRETATION' if context.get('analysis_complete') else 'ACTION'
```

### Step 2: Route Based on Intent

```python
def process_message(self, user_message: str, session_id: str, ...):
    # 1. Handle special workflows first (data_analysis_v3, etc.)
    special_result = self._handle_special_workflows(...)
    if special_result:
        return special_result

    # 2. Classify intent
    intent = classify_intent(user_message)

    # 3. Route based on intent
    if intent == 'ACTION':
        # OpenAI handles tool execution
        result = self._llm_with_tools(user_message, session_context, session_id)

        # Optional: Arena can interpret results afterward
        if result.get('tool_executed') and user_wants_interpretation():
            arena_interpretation = self._get_arena_interpretation(result)
            result['interpretation'] = arena_interpretation

    elif intent == 'INTERPRETATION':
        # Arena handles interpretation directly
        if ARENA_INTEGRATION_AVAILABLE and context.get('data_loaded'):
            return self._trigger_arena_interpretation(user_message, session_context, session_id)
        else:
            # Fallback to OpenAI if Arena unavailable
            return self._llm_with_tools(user_message, session_context, session_id)

    elif intent == 'INFORMATION':
        # Arena provides information (needs data access fix)
        if ARENA_INTEGRATION_AVAILABLE:
            return self._trigger_arena_information(user_message, session_context, session_id)
        else:
            return self._llm_with_tools(user_message, session_context, session_id)

    elif intent == 'COMPLEX':
        # Pipeline: OpenAI executes → Arena interprets
        tool_result = self._llm_with_tools(user_message, session_context, session_id)
        if tool_result.get('success'):
            interpretation = self._get_arena_interpretation(tool_result)
            return combine_results(tool_result, interpretation)

    # Default fallback
    return self._llm_with_tools(user_message, session_context, session_id)
```

## Intent Categories with Examples

### 1. ACTION INTENT → OpenAI Tools (Required)
- "Plot the map distribution for evi variable"
- "Create a vulnerability map"
- "Generate a box plot of TPR"
- "Show me the PCA visualization"
- "Run the malaria risk analysis"
- "Calculate statistics for each ward"

### 2. INTERPRETATION INTENT → Arena (Cost-Effective)
- "What does this mean?"
- "Explain these results"
- "What are the implications?"
- "Help me understand this analysis"
- "Why are these wards high risk?"
- "What patterns do you see?"

### 3. INFORMATION INTENT → Arena (With Data Access)
- "Tell me about my data"
- "What variables are in my dataset?"
- "Describe the columns"
- "List all the wards"
- "What's the data structure?"

### 4. COMPLEX INTENT → Pipeline (Both)
- "Plot the map and explain what it shows"
- "Run analysis and tell me what it means"
- "Create visualization and interpret the patterns"

## Benefits of This Approach

### 1. Cost Optimization
- ACTION requests use OpenAI only when necessary (tools)
- INTERPRETATION uses cheaper Arena models
- INFORMATION uses Arena (reducing OpenAI calls by ~50%)

### 2. Maintains Functionality
- All tool actions still work properly
- OpenAI's intelligence for tool selection preserved
- Arena provides multi-perspective interpretation

### 3. Clear User Experience
- Action requests execute immediately
- Interpretations get multiple viewpoints
- Complex requests get both execution and interpretation

## Implementation Priority

### Phase 1: Fix Routing Order (Quick Fix)
Move Arena check to after intent classification:
```python
# Current (WRONG):
1. Special workflows
2. Arena triggers  ← Too early!
3. Tools

# Fixed:
1. Special workflows
2. Intent classification
3. Route to appropriate handler
```

### Phase 2: Implement Intent Classifier
Add the `classify_intent()` function to properly categorize requests.

### Phase 3: Fix Arena Data Access
Enable Arena to read `raw_data.csv` for INFORMATION intents.

### Phase 4: Implement Pipeline Mode
For COMPLEX intents, execute with OpenAI then interpret with Arena.

## Expected Cost Savings

### Current State
- Every request after analysis → Arena (broken for actions)
- Cost: Near zero but functionality broken

### With Smart Routing
- ACTION requests (30%): OpenAI API calls
- INTERPRETATION requests (50%): Arena (free)
- INFORMATION requests (15%): Arena (free)
- COMPLEX requests (5%): OpenAI + Arena

**Expected savings: 65-70% reduction in OpenAI API costs while maintaining full functionality**

## Testing Examples

```python
# Test cases for routing verification
test_cases = [
    ("Plot the evi distribution map", "ACTION", "OpenAI"),
    ("What does this mean?", "INTERPRETATION", "Arena"),
    ("Tell me about my variables", "INFORMATION", "Arena"),
    ("Create a map and explain patterns", "COMPLEX", "Pipeline"),
    ("Show vulnerability rankings", "ACTION", "OpenAI"),
    ("Why is this ward high risk?", "INTERPRETATION", "Arena"),
]
```

## Summary

The best approach is **intent-based routing** that:
1. Preserves OpenAI's tool execution capabilities
2. Uses Arena for interpretation and information
3. Combines both for complex requests
4. Reduces costs by 65-70% while maintaining functionality

This is smarter than the current "Arena-intercepts-everything" approach and more efficient than "OpenAI-for-everything".