# TPR Workflow: LLM-First Architecture Fix

**Date**: 2025-10-10
**Problem**: TPR workflow uses hardcoded keywords instead of leveraging the LLM properly

## Core Issue

The `TPRLanguageInterface` class exists with an LLM (gpt-4o-mini) but it's being **underutilized**:

1. **Current flow** (Keyword-first):
   ```
   User message
   → Hardcoded keyword check (_is_information_request)
   → If no match → Hardcoded keyword check (_is_general_analysis_request)
   → If no match → LLM slot resolution
   → If no match → Canned fallback response
   ```

2. **Intended flow** (LLM-first):
   ```
   User message
   → LLM classify_intent()
   → Route based on intent classification
   → Use keywords only for fast-path optimization
   ```

The docstring says "LLM-first" but implementation is "keyword-first with LLM fallback".

---

## Root Cause Analysis

### Problem 1: Intent Classification Too Limited
`TPRLanguageInterface.classify_intent()` only returns 4 intents:
- "start", "confirm", "question", "general"

But we need richer intents:
- "information_request" - User asking about options (explain differences, etc.)
- "analysis_request" - User wants to analyze data (plot variables, etc.)
- "facility_selection" - User making a facility choice
- "age_selection" - User making an age group choice
- "navigation" - User wants to go back, exit, check status
- "general_conversation" - User is just chatting

### Problem 2: Workflow Handler Bypasses LLM
`tpr_workflow_handler.py` has hardcoded keyword checks that run BEFORE the LLM:
```python
# Line 728
if self._is_information_request(message_lower):
    # Hardcoded keywords: ['why', 'what', 'how', 'help', 'explain'...]

# Line 739
if self._is_general_analysis_request(message_lower):
    # Hardcoded keywords: ['plot', 'chart', 'visualize'...]
```

These prevent the LLM from even being consulted!

### Problem 3: LLM Only Used for Slot Extraction
`resolve_slot()` uses the LLM, but only to extract "primary/secondary/tertiary" from user text.
It's never asked "what does the user want to do?"

---

## Solution: True LLM-First Architecture

### Phase 1: Enhance Intent Classification (2 hours)

**File**: `app/data_analysis_v3/core/tpr_language_interface.py`

#### 1.1 Expand Intent Taxonomy
Change from 4 intents to 7 intents:

**Current prompt** (line 85-87):
```python
"Classify the user's intent. Allowed intents: start, confirm, question, general. "
```

**New prompt**:
```python
"""You are assisting with a Test Positivity Rate (TPR) workflow.
Classify the user's intent into ONE of these categories:

1. **selection** - User is making a selection (facility level, age group, state)
   Examples: "primary", "I want primary facilities", "let's go with under 5"

2. **information_request** - User asking about options/explanations
   Examples: "explain the differences", "what are the options?", "tell me about the facilities"

3. **data_inquiry** - User asking about their uploaded data
   Examples: "what variables do I have?", "tell me about my data", "describe the columns"

4. **analysis_request** - User wants to analyze or visualize data
   Examples: "plot TPR distribution", "show missing values", "visualize test results"

5. **navigation** - User wants to go back, pause, exit, or check status
   Examples: "go back", "pause", "exit workflow", "where am I?"

6. **confirmation** - User confirming to proceed
   Examples: "yes", "continue", "let's go", "proceed"

7. **general** - Everything else (chitchat, unclear intent)

Current workflow stage: {stage}
User message: {message}

Respond with JSON:
{{
  "intent": one of the 7 intents above,
  "confidence": float 0-1,
  "rationale": short explanation,
  "extracted_value": if intent is 'selection', extract the choice (e.g., 'primary', 'u5')
}}
"""
```

#### 1.2 Add New IntentResult Fields
```python
@dataclass
class IntentResult:
    intent: str  # One of 7 intents above
    confidence: float
    rationale: Optional[str] = None
    extracted_value: Optional[str] = None  # NEW: For selections, extract the choice

    @property
    def is_confident(self) -> bool:
        return self.confidence >= 0.6
```

#### 1.3 Update classify_intent() Implementation
```python
def classify_intent(self, message: str, stage: str, context: Optional[Dict[str, Any]] = None) -> IntentResult:
    """Classify user intent within the TPR workflow using LLM-first approach."""

    # Fast-path: Check for exact keyword matches ONLY for common selections
    # This is for speed (20ms vs 2s), not intelligence
    if stage in ['facility_selection', 'age_selection']:
        exact_matches = self._check_exact_selection(message, stage)
        if exact_matches:
            return IntentResult(
                intent='selection',
                confidence=1.0,
                extracted_value=exact_matches,
                rationale='Exact keyword match'
            )

    # LLM-FIRST: Use LLM for all other cases
    if not self._llm:
        return self._baseline_intent(message, stage, context)

    # Call LLM with enhanced prompt
    try:
        llm_with_json = self._llm.bind(response_format={"type": "json_object"})
        reply = llm_with_json.invoke(
            self._enhanced_intent_prompt.format_messages(
                stage=stage or "unknown",
                message=message or "",
                context=json.dumps(context or {}, ensure_ascii=False)[:1200],
            )
        )

        payload = json.loads(reply.content)
        intent = payload.get("intent", "general")

        # Validate intent
        valid_intents = {
            'selection', 'information_request', 'data_inquiry',
            'analysis_request', 'navigation', 'confirmation', 'general'
        }
        if intent not in valid_intents:
            logger.warning(f"LLM returned invalid intent '{intent}', defaulting to 'general'")
            intent = 'general'

        return IntentResult(
            intent=intent,
            confidence=float(payload.get("confidence", 0.7)),
            rationale=payload.get("rationale"),
            extracted_value=payload.get("extracted_value")
        )

    except Exception as exc:
        logger.error(f"Intent classification failed: {exc}")
        return self._baseline_intent(message, stage, context)

def _check_exact_selection(self, message: str, stage: str) -> Optional[str]:
    """Fast-path check for exact selection keywords."""
    clean = message.lower().strip()

    if stage == 'facility_selection':
        exact_map = {'primary': 'primary', 'secondary': 'secondary',
                     'tertiary': 'tertiary', 'all': 'all'}
        return exact_map.get(clean)

    elif stage == 'age_selection':
        exact_map = {'u5': 'u5', 'o5': 'o5', 'pw': 'pw', 'all': 'all'}
        return exact_map.get(clean)

    return None
```

---

### Phase 2: Refactor Workflow Handler to Use LLM Classification (2 hours)

**File**: `app/data_analysis_v3/core/tpr_workflow_handler.py`

#### 2.1 Remove Hardcoded Keyword Checks
**Delete these methods**:
- `_is_information_request()` (line 922)
- `_is_general_analysis_request()` (line 930)

**Replace with LLM classification**:

#### 2.2 Update handle_facility_selection()
**Current logic** (line 702-815):
```python
def handle_facility_selection(self, user_query: str) -> Dict[str, Any]:
    # Hardcoded checks
    if self._is_information_request(message_lower):
        ...
    if self._is_general_analysis_request(message_lower):
        ...
    # Then slot resolution
    resolution = self.language.resolve_slot(...)
```

**New LLM-first logic**:
```python
def handle_facility_selection(self, user_query: str) -> Dict[str, Any]:
    """Handle facility selection with LLM-first intent classification."""
    logger.info(f"🔵 Facility selection - classifying intent for: '{user_query}'")

    # Get facility analysis for context
    state_for_analysis = self.tpr_selections.get('state', '')
    facility_analysis = self.tpr_analyzer.analyze_facility_levels(
        self.uploaded_data,
        state_for_analysis
    )

    # LLM-FIRST: Classify intent with rich context
    intent_result = self.language.classify_intent(
        message=user_query,
        stage='facility_selection',
        context={
            'current_stage': 'facility_selection',
            'valid_options': ['primary', 'secondary', 'tertiary', 'all'],
            'state': state_for_analysis,
            'facility_analysis': {
                'total_facilities': facility_analysis.get('total_facilities'),
                'levels': list(facility_analysis.get('levels', {}).keys())
            }
        }
    )

    logger.info(f"🎯 Intent classified as: {intent_result.intent} (confidence={intent_result.confidence:.2f})")
    logger.info(f"   Rationale: {intent_result.rationale}")

    # Route based on LLM-classified intent
    if intent_result.intent == 'information_request':
        logger.info("📚 User wants information about facility options")
        explanation = self._format_facility_explanation(facility_analysis)
        return {
            "success": True,
            "message": explanation,
            "session_id": self.session_id,
            "workflow": "tpr",
            "stage": "facility_selection"
        }

    elif intent_result.intent == 'data_inquiry':
        logger.info("🔍 User asking about their data - handoff to agent")
        return self._handoff_to_agent(
            user_query,
            stage='facility_selection',
            valid_options=['primary', 'secondary', 'tertiary', 'all'],
            context_type='data_inquiry'
        )

    elif intent_result.intent == 'analysis_request':
        logger.info("📊 User wants analysis - handoff to agent")
        return self._handoff_to_agent(
            user_query,
            stage='facility_selection',
            valid_options=['primary', 'secondary', 'tertiary', 'all'],
            context_type='analysis_request'
        )

    elif intent_result.intent == 'selection':
        logger.info(f"✅ User making selection: {intent_result.extracted_value}")

        # LLM already extracted the value!
        selected_level = intent_result.extracted_value

        if not selected_level:
            # LLM couldn't extract - ask user to clarify
            return {
                "success": True,
                "message": "I didn't catch which facility level you want. Please type one of: **primary**, **secondary**, **tertiary**, or **all**",
                "session_id": self.session_id,
                "workflow": "tpr",
                "stage": "facility_selection"
            }

        # Validate the selection
        if selected_level not in ['primary', 'secondary', 'tertiary', 'all']:
            return {
                "success": True,
                "message": f"I heard '{selected_level}' but that's not a valid option. Please choose: **primary**, **secondary**, **tertiary**, or **all**",
                "session_id": self.session_id,
                "workflow": "tpr",
                "stage": "facility_selection"
            }

        # Process the selection
        self.tpr_selections['facility_level'] = selected_level
        self.state_manager.save_tpr_selection('facility_level', selected_level)

        # Move to next stage
        self.current_stage = ConversationStage.TPR_AGE_GROUP
        self.state_manager.update_workflow_stage(self.current_stage)

        # Get age analysis and format response
        age_analysis = self.tpr_analyzer.analyze_age_groups(
            self.uploaded_data,
            state_for_analysis,
            selected_level
        )

        level_display = selected_level.replace('_', ' ').title()
        acknowledgment = f"Perfect! You've selected **{level_display}** facilities. "
        if age_analysis.get('total_tests'):
            acknowledgment += f"These facilities conducted {age_analysis['total_tests']:,} tests.\n\n"

        from ..core.formatters import MessageFormatter
        formatter = MessageFormatter(self.session_id)
        message = acknowledgment + formatter.format_age_group_selection(age_analysis)

        # Store age visualizations for on-demand access
        age_viz = self._build_age_group_visualizations(age_analysis)
        if age_viz:
            self.state_manager.update_state({
                'pending_visualizations': {
                    'age_group': age_viz,
                    'stage': 'age_selection'
                }
            })

        return {
            "success": True,
            "message": message,
            "session_id": self.session_id,
            "workflow": "tpr",
            "stage": "age_selection",
            "visualizations": None
        }

    elif intent_result.intent == 'navigation':
        logger.info("🧭 User wants to navigate - handle navigation command")
        return self.handle_navigation(user_query)

    else:  # general or low confidence
        logger.warning(f"❓ Unclear intent (confidence={intent_result.confidence:.2f})")
        return {
            "success": True,
            "message": f"I'm not sure what you'd like to do. Are you:\n\n"
                      f"- **Asking about the options?** (Say 'explain' or 'show charts')\n"
                      f"- **Asking about your data?** (I can help with that too!)\n"
                      f"- **Making a selection?** (Type: primary, secondary, tertiary, or all)\n\n"
                      f"What would you like?",
            "session_id": self.session_id,
            "workflow": "tpr",
            "stage": "facility_selection"
        }
```

#### 2.3 Apply Same Pattern to handle_age_group_selection()
Same LLM-first logic for age selection stage.

---

### Phase 3: Enhance Agent Handoff with Context (1 hour)

**File**: `app/data_analysis_v3/core/tpr_workflow_handler.py`

#### 3.1 Update _handoff_to_agent()
```python
def _handoff_to_agent(
    self,
    user_query: str,
    stage: str,
    valid_options: List[str],
    context_type: str = 'general'
) -> Dict[str, Any]:
    """Hand off to agent with rich context about workflow state and data."""
    from app.data_analysis_v3.core.agent import DataAnalysisAgent
    import asyncio

    agent = DataAnalysisAgent(self.session_id)

    # Build rich workflow context
    workflow_context = {
        'in_tpr_workflow': True,
        'stage': stage,
        'valid_options': valid_options,
        'current_selections': self.tpr_selections,
        'context_type': context_type,  # 'data_inquiry', 'analysis_request', 'general'

        # Data context
        'data_loaded': self.uploaded_data is not None,
        'data_columns': list(self.uploaded_data.columns) if self.uploaded_data is not None else [],
        'data_shape': {'rows': self.uploaded_data.shape[0], 'cols': self.uploaded_data.shape[1]} if self.uploaded_data is not None else None,

        # Workflow reminder
        'workflow_reminder': f"After helping the user, gently remind them they're in the TPR workflow at the {stage} stage. They can continue by selecting: {', '.join(valid_options)}"
    }

    # Call agent with rich context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            agent.analyze(user_query, workflow_context=workflow_context)
        )
    finally:
        loop.close()

    # Add workflow reminder to response
    if result.get('success') and result.get('message'):
        reminder = f"\n\n---\n\n💡 **Ready to continue the TPR workflow?** Select your facility level: {', '.join(valid_options)}"
        result['message'] += reminder
        result['workflow'] = 'tpr'
        result['stage'] = stage

    return result
```

---

### Phase 4: Handle Large Analysis Requests Intelligently (1 hour)

**File**: `app/data_analysis_v3/core/agent.py`

Add pre-processing logic before calling Python tool:

```python
async def analyze(self, user_query: str, workflow_context: Optional[Dict] = None):
    """Analyze with intelligent request preprocessing."""

    # Check for "plot all variables" type requests
    if any(phrase in user_query.lower() for phrase in ['all variables', 'all columns', 'everything']):
        # Check if this would be too expensive
        data_shape = workflow_context.get('data_shape') if workflow_context else None

        if data_shape and data_shape.get('cols', 0) > 10:
            # Too many columns - suggest subset
            columns = workflow_context.get('data_columns', [])
            numeric_cols = [c for c in columns if not any(x in c.lower() for x in ['name', 'id', 'state', 'lga', 'ward'])]

            suggestion = f"""Your dataset has **{data_shape['cols']} columns**. Plotting all at once would take too long and might timeout.

**I can help you visualize**:
- **Specific variables** - Tell me which ones (e.g., "TPR", "test results")
- **Variable groups** - Like "all test variables" or "all geographic columns"
- **Missing data patterns** - Show which columns have missing values
- **Key numeric variables** - Here are some: {', '.join(numeric_cols[:8])}

What aspect would you like to explore?"""

            return {
                "success": True,
                "message": suggestion,
                "session_id": self.session_id
            }

    # Continue with normal analysis
    return await self._original_analyze_logic(user_query, workflow_context)
```

---

## Implementation Order

1. **Phase 1** - Enhance intent classification (most critical, 2 hours)
2. **Phase 2** - Refactor workflow handler (prerequisite for everything, 2 hours)
3. **Phase 3** - Improve agent handoff (enables true deviation, 1 hour)
4. **Phase 4** - Handle large requests (prevents timeouts, 1 hour)

**Total**: ~6 hours

---

## Benefits of LLM-First Architecture

### ✅ No More Hardcoding
- **Before**: Add keyword for every new phrase users might say
- **After**: LLM understands intent naturally

### ✅ Better Understanding
- **Before**: "tell me about variables" → No keyword match → Falls through → Canned response
- **After**: "tell me about variables" → LLM classifies as "data_inquiry" → Agent answers

### ✅ Graceful Degradation
- **Before**: No match → Return confusing prompt
- **After**: Low confidence → Ask user to clarify in natural way

### ✅ Context-Aware
- **Before**: Keywords work the same everywhere
- **After**: LLM knows "explain" means different things at different stages

### ✅ Future-Proof
- **Before**: Every new capability needs new keywords
- **After**: Just update the intent taxonomy in the prompt

---

## Testing Plan

### Test 1: Data Inquiries
- ✅ "tell me about the variables in my data" → `data_inquiry` intent → Agent answers
- ✅ "what columns do I have?" → `data_inquiry` intent → Agent answers
- ✅ "describe my dataset" → `data_inquiry` intent → Agent answers

### Test 2: Analysis Requests
- ✅ "plot TPR distribution" → `analysis_request` intent → Agent creates viz
- ✅ "show missing values" → `analysis_request` intent → Agent analyzes
- ✅ "plot all variables" → Pre-processing catches → Suggests subset

### Test 3: Information Requests
- ✅ "explain the differences" → `information_request` intent → Shows facility comparison
- ✅ "what are my options?" → `information_request` intent → Lists options

### Test 4: Selections
- ✅ "primary" → Fast-path exact match → Advances workflow
- ✅ "I want primary facilities" → LLM extracts "primary" → Advances workflow
- ✅ "let's go with the primary level" → LLM extracts "primary" → Advances workflow

### Test 5: Ambiguous Cases
- ✅ "hmm not sure" → Low confidence → Asks user to clarify
- ✅ "maybe primary?" → Medium confidence + extracted "primary" → Confirms with user

---

## Success Criteria

✅ Zero hardcoded keyword lists in workflow handler
✅ LLM classifies intent for all user messages
✅ Intent classification has >90% accuracy on test cases
✅ Agent handoff includes full context about data
✅ Large analysis requests handled gracefully (no timeouts)
✅ Workflow still advances smoothly with clear selections
✅ Users can deviate naturally and return to workflow

---

## Rollback Plan

If LLM classification causes issues:
1. Restore from backup
2. Add fallback to keyword matching if LLM unavailable
3. Log all LLM classifications for debugging
4. Gradually tune the intent taxonomy

---

## Cost Analysis

**LLM calls per user interaction**:
- Intent classification: 1 call per message (~200 tokens)
- Using gpt-4o-mini: $0.150 per 1M input tokens
- Cost per message: ~$0.00003 (negligible)

**Benefits far outweigh costs**:
- Better UX = Higher user retention
- Less development time on keyword maintenance
- More natural interactions
