# LangGraph Liberation - Comprehensive Implementation Plan
**Date**: 2025-09-30
**Status**: READY FOR REVIEW
**Goal**: Free the LangGraph agent so it's active throughout ALL of ChatMRPT

---

## 🎯 Executive Summary

**What we're doing**: Removing bypass layers that prevent the LangGraph agent from handling messages, ensuring the agent is ALWAYS active regardless of workflow state.

**Why**: User wants the agent to be present throughout the entire user journey - during TPR workflow, risk analysis, ITN planning, general questions, etc. Users should be able to deviate from workflows anytime, and the agent should provide gentle reminders to return.

**How**: Delete TPR bypass logic, convert TPR workflow to a LangGraph tool, simplify agent.analyze() method, and preserve Track A improvements inside the tool.

---

## 📊 Complete ChatMRPT Architecture (Current State)

### **System Overview**

ChatMRPT has **TWO parallel systems**:

#### **System 1: Legacy Tool System** (Request Interpreter)
- **Entry Point**: `/send_message` route (analysis_routes.py)
- **Router**: Mistral 7B (local model) decides: "needs_tools" vs "can_answer"
- **When activated**: `routing_decision == "needs_tools"`
- **Handler**: RequestInterpreter.process_message()
- **Tools available**:
  - `run_malaria_risk_analysis` - Composite + PCA analysis
  - `run_itn_planning` - ITN/bed net distribution
  - `create_vulnerability_map` - Risk visualization
  - `execute_sql_query` - Data queries
  - And ~10 other tools
- **Characteristics**:
  - Uses GPT-4o
  - Function calling via OpenAI
  - Works well for risk analysis, ITN planning, visualizations
  - **NO workflow lock-in** - agent always active

#### **System 2: Data Analysis V3** (LangGraph Agent)
- **Entry Points**:
  - `/api/v1/data-analysis/chat` (data_analysis_v3_routes.py)
  - OR when TPR workflow is active
- **Handler**: DataAnalysisAgent (LangGraph)
- **Tools available**:
  - `analyze_data` - Python code execution tool
  - `tpr_analysis_tool` - TPR calculation
- **Characteristics**:
  - Uses GPT-4o
  - LangGraph ReACT pattern
  - Designed for flexible, multi-step analysis
  - **BUT**: Currently buried under bypass layers

---

### **Current Message Flow**

```
User sends message
    ↓
/send_message (analysis_routes.py:460)
    ↓
╔═══════════════════════════════════════════════════════════╗
║ BYPASS POINT #1: TPR Workflow Check (Lines 525-596)     ║
╚═══════════════════════════════════════════════════════════╝
    ↓ if session['tpr_workflow_active']:
    ├─→ TPRWorkflowRouter.route_message()
    │   └─→ [TPR response returned, NEVER reaches agent] ❌
    │
    └─→ else: Continue ✓
    ↓
Mistral Routing Decision (Lines 643-649)
    ├─→ "can_answer" → Arena mode (2 model comparison)
    │
    └─→ "needs_tools" → Request Interpreter (Legacy System)
        ↓
        RequestInterpreter.process_message()
        ↓
        [Risk analysis, ITN planning, visualizations work here] ✓
```

**Data Analysis V3 (LangGraph) Entry**:
```
User uploads TPR data in Data Analysis tab
    ↓
/api/v1/data-analysis/chat (data_analysis_v3_routes.py:316)
    ↓
agent = DataAnalysisAgent(session_id)
    ↓
agent.analyze(message)
    ↓
╔═══════════════════════════════════════════════════════════╗
║ BYPASS POINT #2: Agent-level TPR check (Lines 381-560)  ║
╚═══════════════════════════════════════════════════════════╝
    ↓ if state_manager.is_tpr_workflow_active():
    ├─→ TPRWorkflowHandler.extract_facility_level()
    │   ├─→ If keyword match found
    │   │   └─→ TPRWorkflowHandler.handle_facility_selection()
    │   │       └─→ [Returns result, NEVER reaches LangGraph] ❌
    │   └─→ If no match, check viz requests, questions, etc.
    │       └─→ [Handled directly, NEVER reaches LangGraph] ❌
    │
╔═══════════════════════════════════════════════════════════╗
║ BYPASS POINT #3: TPR Trigger Check (Lines 569-607)      ║
╚═══════════════════════════════════════════════════════════╝
    ↓ if any TPR trigger keyword:
    ├─→ TPRWorkflowHandler.start_workflow()
    │   └─→ [Returns welcome, NEVER reaches LangGraph] ❌
    │
    └─→ else: Finally... ✓
    ↓
╔═══════════════════════════════════════════════════════════╗
║ LangGraph Invocation (Line 688) ✓✓✓                     ║
╚═══════════════════════════════════════════════════════════╝
result = self.graph.invoke(input_state)
```

---

## 🔍 Complete Workflow Inventory

### **1. TPR (Test Positivity Rate) Workflow**

**Purpose**: Calculate malaria test positivity rates by facility type and age group

**Current Implementation**:
- **System**: Data Analysis V3 (LangGraph)
- **Bypass**: TPRWorkflowRouter (route-level) + TPRWorkflowHandler (agent-level)
- **Entry**: User uploads TPR data OR says "run tpr"
- **Stages**:
  1. Welcome (auto-detects TPR data, shows facility counts)
  2. Facility selection (primary/secondary/tertiary/all)
  3. Age group selection (u5/o5/pw/all)
  4. Calculation and results
- **Track A Improvements** (MUST PRESERVE):
  - Auto-detection of TPR data
  - Contextual welcome with data summary
  - 3-level fuzzy keyword matching
  - Proactive visualization offers
- **Problem**: Completely bypasses LangGraph agent during workflow

---

### **2. Risk Analysis Workflow**

**Purpose**: Malaria vulnerability assessment using Composite Score + PCA

**Current Implementation**:
- **System**: Legacy Tool System (Request Interpreter)
- **Tool**: `run_malaria_risk_analysis`
- **Entry**: User says "run analysis", "analyze my data", etc.
- **Steps**:
  1. User uploads CSV + shapefile
  2. User requests analysis
  3. Tool runs dual-method analysis (Composite + PCA)
  4. Creates rankings and visualizations
  5. Returns unified dataset
- **Characteristics**:
  - **Agent IS active** throughout (no bypass) ✓
  - User can ask questions during/after analysis ✓
  - Tool-based, not workflow-based ✓
- **No changes needed** - already works as desired

---

### **3. ITN (Bed Net) Distribution Planning**

**Purpose**: Allocate insecticide-treated nets based on risk rankings

**Current Implementation**:
- **System**: Legacy Tool System (Request Interpreter)
- **Tool**: `run_itn_planning`
- **Entry**: User says "plan bed nets", "ITN distribution", etc.
- **Requirements**: Risk analysis must be complete
- **Steps**:
  1. User completes risk analysis
  2. User requests ITN planning
  3. Tool uses rankings to allocate nets
  4. Returns allocation plan and maps
- **Characteristics**:
  - **Agent IS active** throughout (no bypass) ✓
  - User can ask questions during/after planning ✓
  - Tool-based, not workflow-based ✓
- **No changes needed** - already works as desired

---

### **4. Data Exploration / Questions**

**Purpose**: Answer user questions about malaria, their data, methodology

**Current Implementation**:
- **System**: Arena Mode (2-model comparison) OR Request Interpreter
- **Entry**: User asks a question
- **Routing**: Mistral decides "can_answer" or "needs_tools"
- **Characteristics**:
  - **Agent IS active** (Arena uses LLMs directly) ✓
  - Works for general knowledge questions ✓
- **No changes needed** - already works as desired

---

### **5. Visualization Creation**

**Purpose**: Create maps, charts, box plots, etc.

**Current Implementation**:
- **System**: Legacy Tool System (Request Interpreter)
- **Tools**: `create_vulnerability_map`, `create_box_plot`, `create_pca_map`, etc.
- **Entry**: User says "show map", "create chart", etc.
- **Characteristics**:
  - **Agent IS active** throughout (no bypass) ✓
  - User can request visualizations anytime ✓
- **No changes needed** - already works as desired

---

## 🚨 The Core Problem

**Only TPR workflow has bypass logic that locks users in.**

All other workflows/tools work correctly with the agent active throughout.

---

## 🎯 What Needs to Change

### **Goal**: Make TPR workflow work like the other tools

**Before** (Current):
```
User in TPR workflow:
  ↓
Message intercepted by TPRWorkflowRouter ❌
  ↓
Keyword matching happens (no agent reasoning) ❌
  ↓
If keyword matches → Direct response
If no match → Error or prompt for expected input ❌
  ↓
User is LOCKED into workflow (can't deviate) ❌
```

**After** (Desired):
```
User in TPR workflow:
  ↓
Message goes to LangGraph agent ✓
  ↓
Agent sees: workflow_stage = "TPR_FACILITY_LEVEL"
Agent sees: message = "show me a correlation matrix"
Agent reasons: "User wants viz, but workflow is active" ✓
  ↓
Agent calls: Visualization tool
Agent adds: "💡 *We're still working on TPR. Ready to pick a facility?*" ✓
  ↓
User response: "OK, primary"
  ↓
Agent sees: workflow_stage = "TPR_FACILITY_LEVEL"
Agent sees: message = "OK, primary"
Agent reasons: "User resuming TPR, fuzzy match 'primary'" ✓
  ↓
Agent calls: TPR tool with facility="primary"
Agent advances: workflow_stage = "TPR_AGE_GROUP"
Agent responds: "✓ Primary selected (321 facilities). Which age group?" ✓
```

---

## 📝 Detailed Changes Required

### **Phase 1: Remove Route-Level Bypass**

**File**: `app/web/routes/analysis_routes.py`

**Lines to DELETE**: 525-596 (72 lines)

**Current Code** (Lines 525-596):
```python
# Check for active TPR workflow FIRST
if session.get('tpr_workflow_active', False):
    logger.info(f"TPR workflow active for session {session_id}, routing to TPR handler")

    # Import TPR workflow router
    try:
        from ...tpr_module.integration.tpr_workflow_router import TPRWorkflowRouter

        # Get LLM manager for intent classification
        llm_manager = None
        if hasattr(current_app, 'services') and hasattr(current_app.services, 'llm_manager'):
            llm_manager = current_app.services.llm_manager

        # Create router and route the message
        router = TPRWorkflowRouter(session_id, llm_manager)
        tpr_result = router.route_message(user_message, dict(session))

        # Check if TPR router wants to transition to main interpreter
        if tpr_result.get('response') == '__DATA_UPLOADED__':
            # ... transition logic ...
        elif tpr_result.get('status') == 'tpr_to_main_transition':
            # ... transition logic ...
        else:
            # Format response for frontend
            formatted_response = {
                'status': tpr_result.get('status', 'success'),
                'message': tpr_result.get('response', ''),
                # ... etc ...
            }
            return jsonify(formatted_response)  # ← BYPASS!

    except Exception as e:
        logger.error(f"Error routing to TPR handler: {e}")
        # Fall through to normal processing if TPR routing fails
```

**Action**: DELETE entire block (lines 525-596)

**Result**: Messages will always reach Mistral routing decision instead of being intercepted by TPRWorkflowRouter.

---

### **Phase 2: Simplify Agent.analyze() Method**

**File**: `app/data_analysis_v3/core/agent.py`

**Lines to DELETE**: 381-607 (227 lines)

**Current Code Structure**:
```python
async def analyze(self, user_query: str) -> Dict[str, Any]:
    """Main entry point for analysis requests."""

    # ... setup code (lines 362-380) - KEEP

    # ============ DELETE START (Line 381) ============
    if state_manager.is_tpr_workflow_active():
        # 180 lines of TPR workflow bypass logic
        # - Keyword extraction
        # - Visualization request handling
        # - Question handling
        # - Direct returns (never reaching LangGraph)

    # Check for TPR triggers to START workflow
    tpr_triggers = ['run tpr', 'tpr analysis', ...]
    if any(tok in query_lc for tok in tpr_triggers):
        # 38 lines of trigger handling
        # - Initialize TPRWorkflowHandler
        # - Start workflow
        # - Return welcome (never reaching LangGraph)
    # ============ DELETE END (Line 607) ============

    # ... build input_state (lines 608-687) - KEEP

    # FINALLY: LangGraph (Line 688) - KEEP
    result = self.graph.invoke(input_state, {"recursion_limit": 10})

    # ... result processing (lines 689-750) - KEEP
```

**Action**: DELETE lines 381-607 (all bypass logic)

**Result**: All messages go straight to LangGraph invocation (line 688).

---

### **Phase 3: Convert TPR to LangGraph Tool**

**New File**: `app/data_analysis_v3/tools/tpr_workflow_langgraph_tool.py` (~300 lines)

**What it includes**:
1. **All Track A improvements**:
   - TPR data auto-detection
   - Contextual welcome generation
   - 3-level fuzzy keyword matching (exact → fuzzy → pattern)
   - Proactive visualization offers

2. **Workflow state management**:
   - Check current workflow stage from StateManager
   - Advance stage when user completes a step
   - Save state between messages

3. **Tool function for LangGraph**:
```python
@tool
async def tpr_workflow_step(
    session_id: str,
    action: str,  # "start", "select_facility", "select_age", "calculate"
    value: Optional[str] = None,  # facility level or age group
    context: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Execute one step of the TPR workflow.

    This tool manages the multi-step TPR analysis workflow:
    1. Start workflow (show welcome with data context)
    2. Select facility type (with fuzzy matching)
    3. Select age group (with fuzzy matching)
    4. Calculate TPR and return results

    The tool uses state management to track workflow progress and allows
    users to resume after deviations.

    Args:
        session_id: Session identifier
        action: The workflow action to perform
        value: The value for the action (facility level or age group)
        context: Additional context (data, state)

    Returns:
        Dict with response, stage, status, visualizations
    """
    handler = TPRWorkflowToolHandler(session_id)

    if action == "start":
        return handler.start_workflow()

    elif action == "select_facility":
        # Use fuzzy matching (Track A)
        matched_facility = handler.fuzzy_match_facility(value)
        if matched_facility:
            return handler.handle_facility_selection(matched_facility)
        else:
            return {
                "response": "I didn't understand that facility type. Please choose: primary, secondary, tertiary, or all",
                "stage": "TPR_FACILITY_LEVEL",
                "status": "awaiting_input"
            }

    elif action == "select_age":
        # Use fuzzy matching (Track A)
        matched_age = handler.fuzzy_match_age(value)
        if matched_age:
            return handler.handle_age_selection(matched_age)
        else:
            return {
                "response": "I didn't understand that age group. Please choose: u5, o5, pw, or all",
                "stage": "TPR_AGE_GROUP",
                "status": "awaiting_input"
            }

    elif action == "calculate":
        return handler.calculate_tpr()
```

4. **Helper class** (TPRWorkflowToolHandler):
   - Extracts all logic from TPRWorkflowHandler
   - Implements fuzzy matching
   - Generates contextual messages
   - Interacts with TPRAnalyzer for calculations

**Key Design Decision**: Single tool with multiple actions, NOT separate tools for each step. This keeps the agent's tool list manageable.

---

### **Phase 4: Update System Prompt**

**File**: `app/data_analysis_v3/prompts/system_prompt.py`

**Current System Prompt** (MAIN_SYSTEM_PROMPT):
```python
MAIN_SYSTEM_PROMPT = """You are a specialized data analysis assistant...
...existing instructions..."""
```

**Add Workflow Awareness**:
```python
MAIN_SYSTEM_PROMPT = """You are a specialized data analysis assistant...

## Workflow Management

You can guide users through structured workflows (like TPR analysis) while remaining flexible:

1. **Check workflow state**: If user is in a workflow, the state will show current stage
2. **Handle deviations gracefully**:
   - If user asks something unrelated to the active workflow, answer their question
   - After answering, provide a gentle reminder: "💡 *We're still working on [workflow]. Ready to continue?*"
   - NEVER force or block users from deviating
3. **Resume workflows naturally**:
   - If user seems to be resuming (e.g., "OK", "yes", "primary"), continue the workflow
   - If unclear, ask: "Would you like to continue with [workflow], or shall we explore something else?"

## TPR Workflow

When user's data contains TPR (test positivity rate) information, you can guide them through analysis:

**Steps**:
1. Welcome & facility selection
2. Age group selection
3. TPR calculation and results

**Tool to use**: `tpr_workflow_step`
- Action "start": Begin workflow
- Action "select_facility": User is selecting facility type (primary/secondary/tertiary/all)
- Action "select_age": User is selecting age group (u5/o5/pw/all)
- Action "calculate": Run TPR calculation

**Flexible matching**: The tool supports fuzzy matching - users can say "primary facilities", "kids under 5", "I want primary", etc.

**Example conversation**:
User: [uploads TPR data]
You: Detect TPR data, call tpr_workflow_step(action="start")
Tool returns welcome with options

User: "Wait, show me a correlation matrix"
You: [Create correlation matrix]
     "Here's your correlation matrix: [viz]
     💡 *We're still working on TPR analysis. You were selecting a facility type. Ready to continue?*"

User: "OK, primary"
You: Call tpr_workflow_step(action="select_facility", value="primary")
Tool returns: "✓ Primary selected. Which age group?"

User: "children under 5"
You: Call tpr_workflow_step(action="select_age", value="children under 5")
Tool returns: TPR results
```

---

### **Phase 5: Update Agent Initialization**

**File**: `app/data_analysis_v3/core/agent.py`

**Lines to MODIFY**: 34-83 (tool registration)

**Current Code**:
```python
def __init__(self, session_id: str):
    # ... LLM setup ...

    # Set up tools
    self.tools = [analyze_data]  # Only Python tool

    # Bind tools to LLM
    model_with_tools = self.llm.bind_tools(self.tools, tool_choice="auto")
```

**Modified Code**:
```python
def __init__(self, session_id: str):
    # ... LLM setup ...

    # Set up tools
    from ..tools.tpr_workflow_langgraph_tool import tpr_workflow_step
    self.tools = [
        analyze_data,        # Python code execution
        tpr_workflow_step    # TPR workflow management
    ]

    # Bind tools to LLM
    model_with_tools = self.llm.bind_tools(self.tools, tool_choice="auto")
```

---

## ⚠️ Pitfalls and Edge Cases

### **Pitfall #1: Track A Improvements Must Be Preserved**

**Risk**: Fuzzy matching, auto-detection, contextual welcome get lost

**Mitigation**:
- Move ALL Track A code into the new TPR tool
- Test fuzzy matching extensively
- Verify auto-detection still works
- Check welcome message includes data summary

**Test Cases**:
- User types "prinary" (typo) → Should match "primary" ✓
- User types "children under five" → Should match "u5" ✓
- User uploads TPR data → Should auto-detect and show contextual welcome ✓

---

### **Pitfall #2: State Management Across Deviations**

**Risk**: Workflow state lost when user deviates

**Mitigation**:
- StateManager persists workflow stage in Redis/file
- Agent checks state on EVERY message
- Tool reads state, doesn't rely on in-memory variables

**Test Cases**:
- User at facility selection → asks question → comes back → Should still be at facility selection ✓
- User closes browser → reopens → workflow state should persist ✓

---

### **Pitfall #3: Infinite Loops / Recursion**

**Risk**: Agent calls tool, tool returns "continue workflow", agent calls tool again, etc.

**Mitigation**:
- Tool returns CLEAR status: "complete", "awaiting_input", "error"
- Tool returns NEXT expected input in the response
- Agent knows when to stop (when tool returns "complete")

**Test Cases**:
- Workflow completes → Tool returns "complete" → Agent stops calling tool ✓
- User gives invalid input → Tool returns "awaiting_input" with prompt → Agent doesn't loop ✓

---

### **Pitfall #4: Two Systems Conflict**

**Risk**: Legacy system (RequestInterpreter) and LangGraph system both try to handle TPR

**Mitigation**:
- Remove TPRWorkflowRouter completely (Phase 1)
- Legacy system doesn't know about TPR workflow
- All TPR goes through Data Analysis V3 entry point

**Test Cases**:
- User uploads TPR in standard tab → Should route to Data Analysis V3 ✓
- User says "run tpr" in standard tab → Should route to Data Analysis V3 ✓

---

### **Pitfall #5: Frontend Expects Specific Response Format**

**Risk**: Frontend expects TPR responses in a certain structure, breaks when agent formats differently

**Mitigation**:
- Tool returns responses in SAME format as old TPRWorkflowHandler
- Agent passes through tool responses without reformatting
- Test frontend rendering of TPR responses

**Test Cases**:
- TPR welcome message renders correctly ✓
- Facility selection options show up ✓
- TPR results table displays ✓
- Download links work ✓

---

### **Pitfall #6: Performance / Latency**

**Risk**: Every message now goes through LangGraph (extra LLM call), increases latency

**Mitigation**:
- LangGraph adds ~1-2 seconds per message
- This is acceptable for better UX (agent always active)
- User won't notice if responses are still < 5 seconds

**Benchmark**:
- Current TPR bypass: ~0.5-1 second
- With LangGraph: ~2-3 seconds
- Acceptable trade-off for flexibility ✓

---

### **Pitfall #7: Agent Doesn't Detect Workflow Resumption**

**Risk**: User says "OK" or "primary" but agent doesn't know they're resuming TPR

**Mitigation**:
- System prompt teaches agent to check workflow state
- If state shows active workflow AND user message is short/keyword-like, agent assumes resumption
- If unclear, agent asks for clarification

**Test Cases**:
- User at facility selection → says "primary" → Agent resumes workflow ✓
- User at facility selection → says "tell me about malaria" → Agent answers question, reminds about workflow ✓

---

## 📋 Step-by-Step Implementation Plan

### **Step 1: Create TPR Tool (Safest First)**

**Why first**: Build the new tool BEFORE deleting old code

**Files to CREATE**:
- `app/data_analysis_v3/tools/tpr_workflow_langgraph_tool.py`

**What to include**:
1. Extract ALL code from TPRWorkflowHandler
2. Implement fuzzy matching (Track A)
3. Implement auto-detection (Track A)
4. Implement contextual welcome (Track A)
5. Create `@tool` function for LangGraph
6. Create helper class TPRWorkflowToolHandler
7. Add comprehensive docstrings
8. Include inline comments

**Testing**:
- Unit tests for fuzzy matching
- Unit tests for auto-detection
- Integration test with mock StateManager

**Time estimate**: 2-3 hours

---

### **Step 2: Update System Prompt**

**Files to MODIFY**:
- `app/data_analysis_v3/prompts/system_prompt.py`

**Changes**:
- Add workflow management instructions
- Add TPR workflow guidance
- Add example conversations
- Add gentle reminder templates

**Testing**:
- Visual inspection of prompt
- Test in playground (copy-paste prompt + user message, see if LLM responds correctly)

**Time estimate**: 30 minutes

---

### **Step 3: Update Agent Initialization**

**Files to MODIFY**:
- `app/data_analysis_v3/core/agent.py` (lines 34-83)

**Changes**:
- Import tpr_workflow_step tool
- Add to self.tools list

**Testing**:
- Start agent, verify 2 tools are registered
- Check agent can call TPR tool

**Time estimate**: 15 minutes

---

### **Step 4: Remove Agent-Level Bypass**

**Files to MODIFY**:
- `app/data_analysis_v3/core/agent.py` (lines 381-607)

**Changes**:
- DELETE 227 lines of bypass logic
- Verify LangGraph invocation (line 688) is now reached immediately after setup

**Before/After**:
```python
# BEFORE (complicated)
async def analyze(self, user_query: str):
    # setup (lines 362-380)

    # BYPASS LOGIC (lines 381-607) ← DELETE THIS
    if workflow_active:
        # 180 lines
    if tpr_triggers:
        # 38 lines

    # build input_state (lines 608-687)
    result = self.graph.invoke(input_state)  # Line 688
    # result processing (lines 689-750)

# AFTER (simple)
async def analyze(self, user_query: str):
    # setup (lines 362-380)

    # build input_state (lines 381-460)  # ← Line numbers shift down
    result = self.graph.invoke(input_state)  # ← Now at line 461
    # result processing (lines 462-523)
```

**Testing**:
- Agent still starts up
- Non-TPR messages still work
- TPR messages reach LangGraph

**Time estimate**: 30 minutes

---

### **Step 5: Remove Route-Level Bypass**

**Files to MODIFY**:
- `app/web/routes/analysis_routes.py` (lines 525-596)

**Changes**:
- DELETE 72 lines of TPR bypass
- Messages now always go to Mistral routing

**Before/After**:
```python
# BEFORE
@analysis_bp.route('/send_message', methods=['POST'])
def send_message():
    # ... get message ...

    # TPR BYPASS (lines 525-596) ← DELETE THIS
    if session.get('tpr_workflow_active'):
        router = TPRWorkflowRouter(...)
        return jsonify(tpr_result)  # ← Bypass!

    # Mistral routing (line 598+)
    routing_decision = route_with_mistral(message)
    # ...

# AFTER
@analysis_bp.route('/send_message', methods=['POST'])
def send_message():
    # ... get message ...

    # Mistral routing (line 526)  # ← Line numbers shift up
    routing_decision = route_with_mistral(message)
    # ...
```

**Testing**:
- Standard chat still works
- TPR messages route to Data Analysis V3

**Time estimate**: 15 minutes

---

### **Step 6: Test Complete Flow**

**Test Scenarios**:

**Test 1: TPR Workflow Happy Path**
```
1. User uploads TPR data
2. Agent detects TPR data, shows welcome
3. User types "primary"
4. Agent recognizes facility selection, calls TPR tool
5. Tool advances to age selection
6. User types "under 5 children"
7. Agent recognizes age selection, calls TPR tool
8. Tool calculates TPR, returns results
9. Agent shows results to user
```

**Test 2: TPR Workflow with Deviation**
```
1. User in TPR workflow at facility selection
2. User types "show me a correlation matrix"
3. Agent creates correlation matrix
4. Agent adds reminder: "💡 *We're still on TPR. Ready to pick a facility?*"
5. User types "yes, primary"
6. Agent resumes TPR workflow
```

**Test 3: TPR Workflow with Question**
```
1. User in TPR workflow at age selection
2. User types "what is TPR?"
3. Agent explains TPR
4. Agent adds reminder: "💡 *We're still selecting age group. Which one?*"
5. User types "pw"
6. Agent continues workflow
```

**Test 4: Multiple Deviations**
```
1. User in TPR at facility selection
2. User asks for data summary
3. Agent provides summary, reminder
4. User asks for histogram
5. Agent creates histogram, reminder
6. User types "OK, let's do primary"
7. Agent resumes TPR
```

**Test 5: Risk Analysis Still Works**
```
1. User uploads CSV + shapefile
2. User types "run analysis"
3. Request Interpreter handles it (legacy system)
4. Analysis completes
5. User can ask questions, plan ITN, etc.
```

**Time estimate**: 2 hours

---

### **Step 7: Deploy to AWS**

**Deployment Steps**:
1. Test locally first
2. Create deployment script
3. Deploy to both production instances
4. Verify on production
5. Monitor for errors

**Files to deploy**:
- `app/data_analysis_v3/tools/tpr_workflow_langgraph_tool.py` (new)
- `app/data_analysis_v3/prompts/system_prompt.py` (modified)
- `app/data_analysis_v3/core/agent.py` (modified - 227 lines deleted)
- `app/web/routes/analysis_routes.py` (modified - 72 lines deleted)

**Deployment script**:
```bash
#!/bin/bash
# deploy_langgraph_liberation.sh

INSTANCE1="3.21.167.170"
INSTANCE2="18.220.103.20"
KEY="/tmp/chatmrpt-key2.pem"

FILES=(
    "app/data_analysis_v3/tools/tpr_workflow_langgraph_tool.py"
    "app/data_analysis_v3/prompts/system_prompt.py"
    "app/data_analysis_v3/core/agent.py"
    "app/web/routes/analysis_routes.py"
)

echo "Deploying LangGraph Liberation to production..."

for ip in $INSTANCE1 $INSTANCE2; do
    echo "Deploying to $ip..."
    for file in "${FILES[@]}"; do
        scp -i "$KEY" "$file" "ec2-user@$ip:/home/ec2-user/ChatMRPT/$file"
    done
    ssh -i "$KEY" "ec2-user@$ip" 'sudo systemctl restart chatmrpt'
done

echo "✓ Deployment complete!"
```

**Time estimate**: 30 minutes

---

## ⏱️ Total Implementation Time

| Phase | Task | Time |
|-------|------|------|
| 1 | Create TPR tool | 2-3 hours |
| 2 | Update system prompt | 30 min |
| 3 | Update agent init | 15 min |
| 4 | Remove agent-level bypass | 30 min |
| 5 | Remove route-level bypass | 15 min |
| 6 | Testing | 2 hours |
| 7 | Deployment | 30 min |
| **Total** | **~6-7 hours** |

---

## ✅ Success Criteria

**The implementation is successful when**:

1. ✅ User can start TPR workflow and complete it (happy path works)
2. ✅ User can deviate from TPR workflow anytime (show charts, ask questions, etc.)
3. ✅ Agent provides gentle reminders when user deviates ("💡 *Still on TPR...*")
4. ✅ User can resume TPR workflow naturally ("OK, primary" after deviation)
5. ✅ Track A improvements preserved (fuzzy matching, auto-detection, contextual welcome)
6. ✅ Risk analysis workflow still works (legacy system unaffected)
7. ✅ ITN planning still works (legacy system unaffected)
8. ✅ General questions still work (Arena mode unaffected)
9. ✅ Agent is ALWAYS active (no more bypass layers)
10. ✅ Performance acceptable (< 5 seconds per response)

---

## 📊 Before/After Comparison

### **Before (Current)**

**User Experience**:
```
User: [uploads TPR data]
System: "Welcome! Which facilities?"

User: "Wait, show me a summary first"
System: "⚠️ Please select a facility type: primary, secondary, tertiary, or all"

User: "I want to see my data first!"
System: "⚠️ Please select a facility type..."

User: *frustrated* "primary"
System: "✓ Primary selected. Which age group?"
```

**Architecture**:
- 3 bypass layers (300+ lines of bypass code)
- User LOCKED into workflow
- Agent BYPASSED during TPR
- Rigid keyword matching
- No flexibility

### **After (Desired)**

**User Experience**:
```
User: [uploads TPR data]
Agent: "Welcome! Which facilities?"

User: "Wait, show me a summary first"
Agent: [Shows data summary]
       "💡 *We're still on TPR. Ready to pick a facility?*"

User: "Show me a correlation matrix too"
Agent: [Shows correlation matrix]
       "💡 *Ready to continue with facility selection?*"

User: "OK, primary"
Agent: "✓ Primary selected (321 facilities). Which age group?"
```

**Architecture**:
- 0 bypass layers (0 lines of bypass code)
- User FREE to explore
- Agent ACTIVE throughout
- Fuzzy matching + LLM reasoning
- Natural conversation

---

## 🎯 Implementation Priority

**Priority 1 (Must Have)**:
- Remove bypass layers ✓
- Create TPR tool ✓
- Update system prompt ✓
- Basic testing ✓

**Priority 2 (Should Have)**:
- Extensive testing (all scenarios) ✓
- Performance benchmarking ✓
- Error handling refinements ✓

**Priority 3 (Nice to Have)**:
- Enhanced reminder messages
- Proactive workflow suggestions
- Multi-workflow management (future)

---

## 🔄 Rollback Plan

**If something goes wrong**:

1. **Backup current code**:
   ```bash
   ssh ec2-user@$INSTANCE1 'cd ChatMRPT && tar -czf backup_before_liberation.tar.gz app/'
   ```

2. **Revert changes**:
   ```bash
   git checkout app/data_analysis_v3/core/agent.py
   git checkout app/web/routes/analysis_routes.py
   ```

3. **Redeploy old version**:
   ```bash
   ./deploy_to_production.sh
   ```

4. **Restore old behavior**: TPR bypass active, agent bypassed during workflow

---

## 📝 Summary

**What We're Doing**:
- Removing 300+ lines of bypass code that lock users into TPR workflow
- Converting TPR workflow to a LangGraph tool
- Ensuring agent is ALWAYS active throughout ChatMRPT
- Preserving all Track A improvements (fuzzy matching, auto-detection, contextual welcome)

**Why It Matters**:
- Users can deviate from workflows anytime
- Agent provides gentle reminders, not hard blocks
- Natural conversation flow
- Same experience across all workflows (TPR, risk analysis, ITN)

**Implementation Path**:
1. Build new TPR tool (safe, no deletions yet)
2. Update system prompt
3. Remove bypass layers (delete old code)
4. Test extensively
5. Deploy to production

**Time**: ~6-7 hours
**Risk**: Low (incremental changes, rollback available)
**Impact**: High (transforms user experience)

---

**Ready to proceed? ✅**
