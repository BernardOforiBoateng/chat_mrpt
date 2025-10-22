# TPR Workflow Failures - Investigation & Fix Plan

**Date**: 2025-09-30
**Tests Failing**: 2/14 (TEST 3, TEST 13)
**Current Pass Rate**: 85.7%
**Target Pass Rate**: 100%

---

## Executive Summary

Two TPR workflow tests are failing due to **agent tool-calling issues**, not business logic problems. The TPR workflow infrastructure is correctly implemented, but the LangGraph agent isn't calling the `tpr_workflow_step` tool at the right times or with the right parameters.

**Core Problem**: The agent receives user messages like "calculate tpr" and "pregnant women" but fails to:
1. Recognize these as TPR workflow actions
2. Call the `tpr_workflow_step` tool with correct parameters
3. Preserve workflow state between steps

---

## TEST 3: TPR Auto-detection & Contextual Welcome

### Expected Behavior

1. User sends: `"calculate tpr"`
2. Agent recognizes TPR workflow intent
3. Agent calls: `tpr_workflow_step(session_id=X, action="start")`
4. Tool returns contextual welcome with:
   - Facility counts (e.g., "1,234 facilities, 567 wards, 89,456 tests")
   - Facility options: **primary**, **secondary**, **tertiary**, **all**
5. User sees comprehensive welcome message

**Test Validation Criteria**:
```python
expected_keywords=["facilities", "facility", "TPR", "primary", "secondary", "tertiary"]
```

### Current Behavior

**Response**: "It seems there was a hiccup in starting the TPR workflow. Let's try again. Could you specify which type of health facility you're interested in for the TPR calculation? You can choose from "primary", ..."

**Missing Keywords**: "facilities" (found: facility, TPR, primary, secondary, tertiary)

### Root Cause Analysis

#### Investigation Steps

1. **Read TPR workflow tool code** (`app/data_analysis_v3/tools/tpr_workflow_langgraph_tool.py`)
   - ✅ `start_workflow()` method DOES generate correct welcome message (lines 316-396)
   - ✅ Welcome message DOES include "facilities", counts, and all facility options
   - ✅ Tool returns proper response format

2. **Check agent system prompt** (need to verify)
   - ❓ Does agent know to call `tpr_workflow_step` for "calculate tpr"?
   - ❓ Is there a tool description that guides the agent?

3. **Review LangGraph agent tools list**
   - ❓ Is `tpr_workflow_step` registered in the agent's tool list?
   - ❓ Is tool description clear enough for agent to know when to call it?

#### Hypothesis

**Primary Hypothesis**: Agent isn't calling `tpr_workflow_step` tool at all when user says "calculate tpr"

**Evidence**:
- Response says "hiccup in starting the TPR workflow" (suggests error handling, not normal flow)
- Response manually lists facility options instead of using tool's contextual welcome
- Missing "facilities" plural form (tool uses "facilities", fallback uses "facility")

**Alternative Hypothesis**: Agent calls tool but gets an error, falls back to generic response

**Evidence**:
- "It seems there was a hiccup" suggests error recovery
- Response still knows to ask for facility selection (workflow context preserved)

#### Technical Deep Dive

**File**: `app/data_analysis_v3/tools/tpr_workflow_langgraph_tool.py`
**Method**: `start_workflow()` (lines 273-314)

```python
def start_workflow(self) -> Dict[str, Any]:
    """Start TPR workflow with contextual welcome."""
    # Load data
    df = self.load_data()
    if df is None:
        return {
            "response": "No data found. Please upload TPR data first.",
            "status": "error",
            "stage": "INITIAL"
        }

    # Auto-detect TPR data
    if not self.detect_tpr_data(df):
        return {
            "response": "This doesn't appear to be TPR data...",
            "status": "error",
            "stage": "INITIAL"
        }

    # Mark workflow as active
    self.state_manager.mark_tpr_workflow_active()

    # Generate contextual welcome
    welcome_message = self._generate_contextual_welcome(df)

    # Advance to facility selection stage
    self.state_manager.update_workflow_stage(ConversationStage.TPR_FACILITY_LEVEL)

    return {
        "response": welcome_message,
        "status": "success",
        "stage": "TPR_FACILITY_LEVEL",
        "workflow": "tpr"
    }
```

**Contextual Welcome** (lines 316-396):
```python
welcome = "# Welcome to ChatMRPT - Test Positivity Rate Analysis\n\n"
welcome += f"**Detected:** TPR data from your facilities\n"
welcome += f"**Coverage:** {total_facilities:,} facilities"
...
welcome += "**Your options:**\n"
welcome += "• **primary** ({count:,} facilities) - Community health centers\n"
welcome += "• **secondary** ({count:,} facilities) - District hospitals\n"
welcome += "• **tertiary** ({count:,} facilities) - Specialist centers\n"
welcome += "• **all** (or 4) - Combined analysis\n\n"
```

✅ **Conclusion**: The code is correct. The tool WILL return the right message IF called.

#### Problem Pinpointed

**Location**: LangGraph agent tool invocation logic

**Issue**: Agent receives "calculate tpr" but either:
1. Doesn't recognize it should call `tpr_workflow_step`
2. Calls it but handles error incorrectly
3. Gets blocked by state management issue

**Next Investigation Steps**:
1. Check `tpr_workflow_step` tool registration in agent
2. Review agent system prompt for TPR workflow instructions
3. Check agent logs for tool invocation attempts
4. Verify tool description and examples

---

## TEST 13: TPR Workflow Completion

### Expected Behavior

**Context**: After selecting facility="secondary" in TEST 12

1. User sends: `"pregnant women"`
2. Agent recognizes this as age group selection in TPR workflow
3. Agent calls: `tpr_workflow_step(session_id=X, action="select_age", value="pregnant women")`
4. Tool fuzzy-matches "pregnant women" → "pw"
5. Tool triggers TPR calculation with facility="secondary", age="pw"
6. User sees TPR results with:
   - Keywords: "TPR", "result", "pregnant", "calculated"
   - Ward-level TPR data
   - Visualization map

**Test Validation Criteria**:
```python
expected_keywords=["TPR", "result", "pregnant", "calculated"]
workflow_complete = "tpr" in response.get('response', '').lower()
```

### Current Behavior

**Response**: "The dataset includes several columns related to pregnant women:\n\n1. **Persons presenting with fever & tested by RDT Preg Women (PW)**: This column tracks the number of pregnant women who presented wit..."

**Missing Keywords**: "TPR", "result", "calculated" (found: "pregnant")

### Root Cause Analysis

#### Investigation Steps

1. **Read age group selection code** (`tpr_workflow_langgraph_tool.py` lines 660-682)
   - ✅ Fuzzy matching includes "pregnant", "pregnancy", "maternal", "women" → maps to "pw"
   - ✅ Handler calls `handle_age_group_selection(matched_age)` which triggers calculation
   - ✅ Calculation logic exists and should work

2. **Check workflow state persistence**
   - ❓ Is facility="secondary" selection from TEST 12 preserved?
   - ❓ Does TEST 13 start fresh or continue from TEST 12 state?

3. **Review test flow**
   - TEST 11: "let's do another tpr analysis" (starts new workflow)
   - TEST 12: "secndary facilitys" (selects facility)
   - TEST 13: "pregnant women" (should select age and calculate)

#### Hypothesis

**Primary Hypothesis**: Agent doesn't call `tpr_workflow_step` tool for "pregnant women"

**Evidence**:
- Response describes dataset columns (data exploration mode, not workflow mode)
- Response talks ABOUT pregnant women data, not TPR RESULTS for pregnant women
- No calculation keywords present ("TPR", "result", "calculated")

**Alternative Hypothesis**: Workflow state lost between TEST 12 and TEST 13

**Evidence**:
- TEST 11 starts new workflow
- TEST 12 selects facility
- TEST 13 might be treated as new conversation, not workflow continuation

#### Technical Deep Dive

**File**: `app/data_analysis_v3/tools/tpr_workflow_langgraph_tool.py`
**Method**: `fuzzy_match_age_group()` (lines 167-201)

```python
def fuzzy_match_age_group(self, query: str) -> Optional[str]:
    """Extract age group using 3-level fuzzy matching."""
    patterns = {
        'pw': [
            'pregnant', 'pregnancy', 'maternal', 'mother',
            'antenatal', 'expecting', 'gravid', 'prenatal', 'women'
        ],
        ...
    }

    # Check if ANY pattern keyword appears in query
    for group, keywords in patterns.items():
        for keyword in keywords:
            if keyword in query_clean:
                logger.info(f"✓ Pattern match: '{query_clean}' contains '{keyword}' → {group}")
                return group
```

✅ **Conclusion**: "pregnant women" WILL match to "pw" via pattern matching

**Method**: `handle_age_group_selection()` (lines 430-530)

```python
def handle_age_group_selection(self, age_group: str) -> Dict[str, Any]:
    """Handle age group selection and trigger TPR calculation."""

    # Store selection
    self.tpr_selections['age_group'] = age_group
    self.state_manager.update_tpr_selections(self.tpr_selections)

    # Advance to calculation stage
    self.state_manager.update_workflow_stage(ConversationStage.TPR_CALCULATING)

    # Perform TPR calculation
    result = self.calculate_tpr()

    return {
        "response": result['message'],
        "status": "success",
        "stage": "TPR_COMPLETE",
        "results": result.get('tpr_results'),
        "download_links": result.get('download_links')
    }
```

✅ **Conclusion**: If tool is called correctly, TPR will be calculated

#### Problem Pinpointed

**Location**: Agent doesn't recognize "pregnant women" should trigger tool call

**Issue**: Agent interprets "pregnant women" as:
- Data exploration question: "Tell me about pregnant women in the data"
- NOT as: "Select pregnant women for TPR calculation"

**Root Cause**: Agent lacks workflow context awareness

**Evidence**:
- Agent responds with column descriptions (exploration mode)
- Agent doesn't maintain workflow stage context
- Agent treats each message independently instead of as workflow step

---

## Comprehensive Root Cause Summary

### Core Issue: Agent Tool-Calling Logic

Both failing tests suffer from the same fundamental problem:

**The LangGraph agent doesn't reliably call the `tpr_workflow_step` tool when it should.**

#### Why This Happens

1. **Tool Description Insufficiency**
   - Tool may not have clear description of WHEN to call it
   - Examples may not cover all user input patterns
   - Agent prefers general conversation over structured tool calls

2. **Workflow State Awareness**
   - Agent doesn't maintain "I'm in TPR workflow" context
   - Each message processed independently
   - No "sticky" workflow mode to guide tool selection

3. **Ambiguous User Input**
   - "calculate tpr" could mean many things
   - "pregnant women" could be exploration or selection
   - Agent defaults to safer (exploration) interpretation

#### Why Previous Tests Pass

Tests that PASS have clearer tool-calling triggers:
- "show me a summary" → clear data exploration
- "show me a correlation heatmap" → clear visualization request
- "what columns are in my data?" → clear metadata request

These don't require workflow context - they're one-shot tool calls.

---

## Fix Plan

### Strategy

**Phase 1: Improve Tool Descriptions** (High Impact, Low Risk)
**Phase 2: Add Workflow State Awareness** (High Impact, Medium Risk)
**Phase 3: Enhance Agent System Prompt** (Medium Impact, Low Risk)

### Phase 1: Improve Tool Descriptions

#### Fix 1.1: Enhanced `tpr_workflow_step` Tool Description

**File**: `app/data_analysis_v3/tools/tpr_workflow_langgraph_tool.py`
**Line**: 576 (tool decorator)

**Current**:
```python
@tool
def tpr_workflow_step(
    session_id: str,
    action: str,
    value: str = ""
) -> Dict[str, Any]:
    """Execute a step in the TPR workflow (Test Positivity Rate analysis).
    ...
    """
```

**Problem**: Description doesn't clearly state WHEN to call this tool

**Fix**:
```python
@tool
def tpr_workflow_step(
    session_id: str,
    action: str,
    value: str = ""
) -> Dict[str, Any]:
    """Execute TPR workflow for malaria test positivity analysis.

    **WHEN TO CALL THIS TOOL**:
    - User wants to "calculate tpr", "run tpr", "analyze tpr", "tpr analysis"
    - User selects facility level: "primary", "secondary", "tertiary"
    - User selects age group: "under 5", "u5", "over 5", "o5", "pregnant", "pw"
    - You are in TPR workflow and user provides a selection

    **WORKFLOW STAGES**:
    1. Start: action="start" - Begins workflow with contextual welcome
    2. Facility: action="select_facility" value="primary|secondary|tertiary|all"
    3. Age: action="select_age" value="u5|o5|pw|all" (fuzzy matching supported)

    **CRITICAL**: Always call this tool for TPR-related requests, even if ambiguous.
    Natural language like "pregnant women" or "children" should trigger this tool
    when TPR workflow is active.

    Args:
        session_id: Current session identifier
        action: Workflow action to perform
            - "start": Begin TPR workflow
            - "select_facility": Select facility level (primary/secondary/tertiary/all)
            - "select_age": Select age group (u5/o5/pw/all - fuzzy matching enabled)
        value: The selection value (facility or age group) - natural language supported

    Returns:
        Dict with response, status, stage, and optional results

    Examples:
        # User: "calculate tpr" or "run tpr analysis"
        tpr_workflow_step(session_id="abc", action="start")

        # User: "primary facilities" or "1" or "community health centers"
        tpr_workflow_step(session_id="abc", action="select_facility", value="primary")

        # User: "pregnant women" or "maternal" or "pw"
        tpr_workflow_step(session_id="abc", action="select_age", value="pregnant women")

        # User: "children under 5" or "kids" or "u5"
        tpr_workflow_step(session_id="abc", action="select_age", value="children under 5")
    """
```

**Impact**: Directly tells agent when and how to call the tool

#### Fix 1.2: Add TPR Intent Keywords

**File**: `app/data_analysis_v3/core/agent.py`
**Location**: Agent initialization or system prompt

**Fix**: Add explicit TPR workflow triggers to agent's context

```python
TPR_WORKFLOW_TRIGGERS = [
    "calculate tpr",
    "run tpr",
    "tpr analysis",
    "test positivity",
    "positivity rate",
    "facility level",
    "age group",
    "pregnant women",
    "under 5",
    "children"
]
```

### Phase 2: Add Workflow State Awareness

#### Fix 2.1: Add Workflow State to Agent Context

**File**: `app/data_analysis_v3/core/agent.py`
**Method**: `analyze()` (line 388)

**Current**: Agent builds state without workflow context
**Fix**: Include workflow stage in every LLM call

```python
# In analyze() method, before creating input_state
workflow_stage = state_manager.get_workflow_stage()
tpr_active = state_manager.is_tpr_workflow_active()

# Add to input_state
input_state = {
    "messages": self.chat_history + [HumanMessage(content=user_query)],
    "session_id": self.session_id,
    "input_data": input_data_list,
    "workflow_active": tpr_active,  # NEW
    "workflow_stage": str(workflow_stage),  # NEW
    "tpr_selections": state_manager.get_tpr_selections() if tpr_active else {},  # NEW
    ...
}
```

#### Fix 2.2: Update Agent System Prompt

**File**: `app/data_analysis_v3/prompts/system_prompt.py` (or wherever agent prompt is defined)

**Add workflow awareness section**:

```
## Workflow State Management

You have access to workflow state in your context:
- `workflow_active`: True if user is in TPR workflow
- `workflow_stage`: Current stage (e.g., "TPR_FACILITY_LEVEL", "TPR_AGE_GROUP")
- `tpr_selections`: User's selections so far (facility_level, age_group)

**CRITICAL RULE**: When `workflow_active` is True:
1. Prioritize workflow progression over general conversation
2. Interpret user input as workflow selections, not exploration questions
3. Call `tpr_workflow_step` tool for ANY input that could be a selection
4. Examples:
   - User says "pregnant women" during TPR_AGE_GROUP stage → Call tool with action="select_age"
   - User says "secondary" during TPR_FACILITY_LEVEL stage → Call tool with action="select_facility"

When in doubt, assume user is answering the workflow question.
```

### Phase 3: Enhance Agent Reasoning

#### Fix 3.1: Add Workflow Decision Logic

**File**: `app/data_analysis_v3/core/agent.py`
**Location**: Before graph execution

**Add preprocessing step**:

```python
def analyze(self, user_query: str) -> Dict[str, Any]:
    """Main analysis method."""

    # Check workflow state
    state_manager = DataAnalysisStateManager(self.session_id)
    workflow_stage = state_manager.get_workflow_stage()

    # PREPROCESSING: Direct workflow routing
    if workflow_stage == ConversationStage.TPR_FACILITY_LEVEL:
        # User is expected to select facility
        # Any input should be treated as facility selection attempt
        logger.info(f"TPR workflow active at facility stage - routing to tool")

        from ..tools.tpr_workflow_langgraph_tool import tpr_workflow_step
        result = tpr_workflow_step(
            session_id=self.session_id,
            action="select_facility",
            value=user_query
        )

        if result.get('status') == 'success':
            return {
                "success": True,
                "message": result.get('response', ''),
                "visualizations": result.get('visualizations', []),
                "session_id": self.session_id
            }

    elif workflow_stage == ConversationStage.TPR_AGE_GROUP:
        # User is expected to select age group
        logger.info(f"TPR workflow active at age stage - routing to tool")

        from ..tools.tpr_workflow_langgraph_tool import tpr_workflow_step
        result = tpr_workflow_step(
            session_id=self.session_id,
            action="select_age",
            value=user_query
        )

        if result.get('status') == 'success':
            return {
                "success": True,
                "message": result.get('response', ''),
                "visualizations": result.get('visualizations', []),
                "session_id": self.session_id
            }

    # Continue with normal graph execution for non-workflow or start workflow cases
    ...
```

**Impact**: Direct routing bypasses agent decision-making for workflow steps

---

## Implementation Priority

### Critical Path (Must Fix for 100%)

1. ✅ **Fix 3.1** - Add workflow preprocessing logic
   - **Impact**: Directly solves TEST 13
   - **Risk**: Low (failover to normal flow if fails)
   - **Time**: 30 minutes

2. ✅ **Fix 1.1** - Enhanced tool description
   - **Impact**: Helps agent recognize TPR triggers
   - **Risk**: Very Low (just documentation)
   - **Time**: 15 minutes

3. ✅ **Fix 2.1** - Add workflow state to context
   - **Impact**: Gives agent awareness of workflow mode
   - **Risk**: Low (additive change)
   - **Time**: 20 minutes

### Nice to Have (Improves Robustness)

4. **Fix 2.2** - Update agent system prompt
   - **Impact**: Better agent reasoning
   - **Risk**: Medium (could confuse agent if poorly worded)
   - **Time**: 30 minutes

5. **Fix 1.2** - Add TPR intent keywords
   - **Impact**: Marginal (agent should infer from description)
   - **Risk**: Low
   - **Time**: 10 minutes

---

## Testing Strategy

### Unit Tests

1. **Test workflow preprocessing logic**
   ```python
   def test_workflow_preprocessing_facility():
       agent = DataAnalysisAgent(session_id="test")
       state_manager.update_workflow_stage(ConversationStage.TPR_FACILITY_LEVEL)

       result = agent.analyze("primary")
       assert result['success'] == True
       assert "facility" in result['message'].lower()
   ```

2. **Test workflow preprocessing age**
   ```python
   def test_workflow_preprocessing_age():
       agent = DataAnalysisAgent(session_id="test")
       state_manager.update_workflow_stage(ConversationStage.TPR_AGE_GROUP)

       result = agent.analyze("pregnant women")
       assert result['success'] == True
       assert "tpr" in result['message'].lower()
   ```

### Integration Tests

Rerun comprehensive test suite after each fix:

```bash
python tests/comprehensive_langgraph_test.py
```

**Target**: 14/14 tests passing (100%)

---

## Deployment Plan

### Step 1: Implement Fixes

1. Apply Fix 3.1 (workflow preprocessing)
2. Apply Fix 1.1 (tool description)
3. Apply Fix 2.1 (workflow state context)
4. Run local tests

### Step 2: Deploy to Production

```bash
# Deploy to both instances
for ip in 3.21.167.170 18.220.103.20; do
    scp -i /tmp/chatmrpt-key2.pem app/data_analysis_v3/core/agent.py ec2-user@$ip:/home/ec2-user/ChatMRPT/app/data_analysis_v3/core/
    scp -i /tmp/chatmrpt-key2.pem app/data_analysis_v3/tools/tpr_workflow_langgraph_tool.py ec2-user@$ip:/home/ec2-user/ChatMRPT/app/data_analysis_v3/tools/
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$ip 'sudo systemctl restart chatmrpt'
done
```

### Step 3: Verify in Production

```bash
python tests/comprehensive_langgraph_test.py
```

**Success Criteria**: 14/14 tests passing

---

## Risk Assessment

### Risks

1. **Workflow preprocessing might be too aggressive**
   - Mitigation: Only activate for specific workflow stages
   - Fallback: User can exit workflow with "exit" command

2. **State might not persist between requests**
   - Mitigation: File-based state management already in place
   - Verification: Check logs for state loading

3. **Tool description changes might confuse agent**
   - Mitigation: Keep description clear and example-heavy
   - Fallback: Revert to original description

### Rollback Plan

All changes are localized to 2 files:
- `app/data_analysis_v3/core/agent.py`
- `app/data_analysis_v3/tools/tpr_workflow_langgraph_tool.py`

Rollback: Restore from git history or backup files

---

## Success Metrics

- **TEST 3**: TPR Auto-detection
  - ✅ Response contains "facilities" (plural)
  - ✅ Response shows facility counts
  - ✅ Response lists primary, secondary, tertiary options

- **TEST 13**: TPR Workflow Completion
  - ✅ Response contains "TPR" keyword
  - ✅ Response contains "result" or "calculated"
  - ✅ Response shows TPR calculation results
  - ✅ No column descriptions (not exploration mode)

- **Overall**:
  - ✅ 14/14 tests passing (100%)
  - ✅ No regressions in currently passing tests

---

## Appendix: Code References

### Key Files

1. **Agent**: `app/data_analysis_v3/core/agent.py:388` - `analyze()` method
2. **TPR Tool**: `app/data_analysis_v3/tools/tpr_workflow_langgraph_tool.py:576` - Tool definition
3. **State Manager**: `app/data_analysis_v3/core/state_manager.py` - Workflow state
4. **Test Suite**: `tests/comprehensive_langgraph_test.py` - Integration tests

### Related Issues

- **LangGraph Liberation**: Successfully deployed (85.7% pass rate)
- **Async Handling**: Fixed in previous deployment
- **Session Management**: Working correctly

### Next Steps After Fix

1. Monitor production for edge cases
2. Add more workflow patterns (if needed)
3. Consider expanding preprocessing to other workflows
4. Document workflow patterns for future development
