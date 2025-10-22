# Fix TPR Workflow Hijacking & Agent Handoff Issues

**Date**: 2025-10-10
**Session**: TPR Workflow Investigation & Repair

## Problem Summary

The TPR workflow is hijacking user questions and forcing them to be interpreted as facility/age selections instead of allowing natural conversation and deviation to the agent. Users cannot:
- Ask about their data variables
- Request variable distributions
- Get explanations outside the narrow facility/age choices
- Use general language without exact keyword matches

Root causes identified:
1. **Weak keyword detection** - Missing common phrases like "tell me", "about", "variables"
2. **Wrong execution order** - Slot resolution happens before proper intent detection
3. **No graceful degradation** - Falls back to canned responses instead of agent handoff
4. **Timeout on large requests** - Plotting 25 variables times out (>60s CloudFront limit)
5. **Response hijacking** - Returns facility comparison even when user clearly asked something else

---

## Plan: Multi-Layer Fix

### ✅ Phase 1: Strengthen Intent Detection (1-2 hours)

**Goal**: Catch 95% of conversational deviations before they reach slot resolution

**Files to modify**:
- `app/data_analysis_v3/core/tpr_workflow_handler.py`

**Changes**:

#### 1.1 Expand `_is_information_request()` keywords
**Current**: `['why', 'what', 'how', 'help', 'explain', 'difference', 'recommend', 'choose']`
**Add**: `['tell', 'about', 'describe', 'list', 'show me', 'give me', 'can you', 'could you', 'I want to know', 'help me understand']`

**Logic**:
- Check if message ends with `?` → instant information request
- Check if message contains ANY of expanded keywords
- Check message length > 5 words → likely conversational, not selection

#### 1.2 Expand `_is_general_analysis_request()` keywords
**Current**: `['plot', 'chart', 'visualize', 'visualise', 'graph', 'distribution', 'map', 'analyze', 'analyse', 'run ', 'compute', 'show data', 'show me']`
**Add**: `['variable', 'variables', 'column', 'columns', 'data', 'dataset', 'statistics', 'stat', 'summary', 'explore', 'check']`

**Logic**:
- If user mentions "variable" or "data" + any analysis term → general analysis request
- If message length > 8 words → likely complex query, not simple selection

---

### ✅ Phase 2: Fix Execution Order (1 hour)

**Goal**: Ensure intent detection happens BEFORE slot resolution attempts

**Files to modify**:
- `app/data_analysis_v3/core/tpr_workflow_handler.py`

**Changes**:

#### 2.1 Reorder `handle_facility_selection()` logic
**Current order**:
1. Check `_is_information_request()` (line 728)
2. Check `_is_general_analysis_request()` (line 739)
3. Try `resolve_slot()` (line 747)
4. If no resolution → show explanation

**New order**:
1. **FIRST**: Check `_is_information_request()` → return explanation
2. **SECOND**: Check `_is_general_analysis_request()` → handoff to agent
3. **THIRD**: Try `resolve_slot()` with STRICT matching
4. **FOURTH**: If no exact match → Ask user to clarify with specific options (NOT give explanation)

**Key change**: Never fall back to canned explanation as a "helpful response". If we don't know what the user wants, ask them directly: "I didn't catch your selection. Please type one of: primary, secondary, tertiary, or all"

#### 2.2 Apply same reordering to `handle_age_group_selection()`
Same logic fix for age group stage

---

### ✅ Phase 3: Improve Agent Handoff (2 hours)

**Goal**: When user deviates, actually call the agent with proper context instead of showing facility comparison

**Files to modify**:
- `app/data_analysis_v3/core/tpr_workflow_handler.py`
- `app/data_analysis_v3/core/agent.py`

**Changes**:

#### 3.1 Fix `_handoff_to_agent()` to include full context
**Current** (line 1000-1016):
- Passes `user_query` and `workflow_context` to agent
- But agent doesn't know about available data variables!

**New logic**:
```python
def _handoff_to_agent(self, user_query: str, stage: str, valid_options: List[str]) -> Dict[str, Any]:
    from app.data_analysis_v3.core.agent import DataAnalysisAgent
    import asyncio

    agent = DataAnalysisAgent(self.session_id)

    # CRITICAL: Build rich context with actual data info
    workflow_context = {
        'stage': stage,
        'valid_options': valid_options,
        'in_tpr_workflow': True,
        'current_selections': self.tpr_selections,
        'data_columns': list(self.uploaded_data.columns) if self.uploaded_data is not None else [],
        'data_shape': self.uploaded_data.shape if self.uploaded_data is not None else None,
        'reminder': f"User is at {stage} stage. After answering, gently remind them to continue workflow by selecting from: {valid_options}"
    }

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(agent.analyze(user_query, workflow_context=workflow_context))
    finally:
        loop.close()

    # CRITICAL: Add gentle reminder to response
    if result.get('success') and result.get('message'):
        result['message'] += f"\n\n💡 **Ready to continue?** Please select: {', '.join(valid_options)}"

    return result
```

#### 3.2 Make agent aware it's in TPR workflow
Modify `agent.py` to check for `workflow_context['in_tpr_workflow']` and adjust its behavior:
- Still answer user's question fully
- But append gentle reminder about workflow continuation
- Use data from `workflow_context['data_columns']` to answer variable questions

---

### ✅ Phase 4: Handle Large Analysis Requests (1 hour)

**Goal**: Prevent timeout on "plot all variables" requests by intelligently limiting scope

**Files to modify**:
- `app/data_analysis_v3/core/agent.py`
- `app/data_analysis_v3/tools/python_tool.py`

**Changes**:

#### 4.1 Add request pre-processing in agent
Before executing Python tool, check:
- If user asks to "plot all variables" or "visualize everything"
- Count numeric columns in dataset
- If > 10 numeric columns → suggest specific subset instead

**Logic**:
```python
if "all variables" in user_query.lower() or "all columns" in user_query.lower():
    numeric_cols = df.select_dtypes(include='number').columns
    if len(numeric_cols) > 10:
        return {
            "success": True,
            "message": f"Your dataset has {len(numeric_cols)} numeric variables. Plotting all at once would take too long.\n\n**I can help you visualize specific variables**. Here are some key ones:\n\n{', '.join(numeric_cols[:10])}\n\nWhich would you like to see? Or tell me what aspect you're interested in (e.g., 'test results', 'geographic distribution', 'missing data patterns')"
        }
```

#### 4.2 Add timeout protection in Python tool
If plot generation takes > 30 seconds:
- Cancel operation
- Return partial results + suggestion to narrow scope

---

### ✅ Phase 5: Add Escape Hatches (30 minutes)

**Goal**: Give users explicit way to exit workflow or pause it

**Files to modify**:
- `app/data_analysis_v3/core/tpr_workflow_handler.py`

**Changes**:

#### 5.1 Add "pause workflow" command
Detect phrases:
- "pause", "stop", "wait", "hold on", "not now"
- Save workflow state
- Let user explore freely with agent
- Add "/resume tpr" command to continue

#### 5.2 Improve exit workflow message
Current message on "exit" is generic. Make it actionable:
```
"Pausing TPR workflow. Your selections are saved:
- State: Adamawa
- Facility: (pending)

You can now:
- Explore your data freely
- Ask any questions
- Resume TPR workflow by typing 'resume' or 'continue workflow'
```

---

## Testing Plan

After implementing fixes, test these scenarios:

### Test 1: Information Requests
- ✅ "tell me about the variables in my data"
- ✅ "what columns do I have?"
- ✅ "describe my dataset"
- **Expected**: Agent answers with data info + gentle reminder about workflow

### Test 2: Analysis Requests
- ✅ "plot the distribution for TPR"
- ✅ "show me missing values"
- ✅ "can you visualize test results?"
- **Expected**: Agent creates visualization + gentle reminder

### Test 3: Large Requests
- ✅ "plot all variables"
- ✅ "visualize everything in my dataset"
- **Expected**: Agent suggests subset instead of timing out

### Test 4: Workflow Continuation
- ✅ Ask question → Get answer → Select facility level
- **Expected**: Workflow resumes smoothly after deviation

### Test 5: Explicit Selection
- ✅ "primary" (exact keyword)
- ✅ "I want primary facilities" (contains keyword)
- **Expected**: Slot resolution works immediately

---

## Implementation Order

1. **Phase 1** (Strengthen detection) - Do this first, it's highest impact
2. **Phase 2** (Fix execution order) - Do this second, it's a prerequisite for everything else
3. **Phase 3** (Agent handoff) - Do this third, it enables true deviation
4. **Phase 4** (Large requests) - Do this fourth, it prevents timeout issues
5. **Phase 5** (Escape hatches) - Do this last, it's nice-to-have

**Estimated total time**: 5-6 hours

---

## Success Criteria

✅ User can ask "tell me about variables" → Gets actual answer (not facility comparison)
✅ User can request "plot TPR distribution" → Gets visualization (not workflow prompt)
✅ User can ask "plot all variables" → Gets smart suggestion (not timeout)
✅ Workflow still advances with exact keywords ("primary", "u5", etc.)
✅ Workflow reminds user to continue after answering deviation questions
✅ User can pause/resume workflow explicitly

---

## Rollback Plan

If fixes break workflow:
1. Restore from backup: `ChatMRPT_BEFORE_ARENA_FIX_20251006.tar.gz`
2. Keep strengthened keyword detection (Phase 1 only)
3. Roll back execution order changes (Phase 2)
4. Investigate what broke

---

## Notes for Future

**Architectural debt to address later**:
- TPR workflow handler is 1,600+ lines - needs refactoring into smaller modules
- Intent detection should use LLM classification, not keyword matching (more flexible)
- Agent handoff should be a first-class workflow state, not a hack
- Need unified "workflow context" object passed throughout the system
