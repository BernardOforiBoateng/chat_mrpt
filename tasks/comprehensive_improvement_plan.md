# ChatMRPT Comprehensive Improvement Plan
**Date**: 2025-09-30
**Goal**: Transform ChatMRPT from functional to delightful while freeing the LangGraph agent to be truly powerful

---

## Executive Summary

### Current State
- **Technically Solid**: 8/10 - Architecture works, analysis is robust
- **User Experience**: 5/10 - Functional but frustrating, keyword-dependent
- **Agent Capabilities**: 6/10 - Powerful but buried under routing layers, tightly coupled to TPR

### Target State
- **User Experience**: 9/10 - Conversational, helpful, guides users naturally
- **Agent Capabilities**: 9/10 - Autonomous, powerful, can handle complex multi-step tasks
- **Architecture**: Clean separation between workflow orchestration and AI reasoning

### Implementation Approach
**Three-Track Parallel Development**:
1. **Track A: User Experience (UX)** - Immediate user-facing improvements
2. **Track B: Agent Liberation** - Free agent from routing complexity
3. **Track C: Agent Enhancement** - Make agent truly intelligent

---

## Track A: User Experience Improvements
**Goal**: Make ChatMRPT feel conversational and helpful
**Timeline**: 1 week
**Risk**: Low - No architectural changes

### Phase A1: Transform First Impressions (Day 1-2)

#### A1.1: Contextual Welcome Message
**File**: `app/data_analysis_v3/core/agent.py:795-847`

**Current Problem**:
```python
summary = "📊 **Your data has been uploaded successfully!**\n\n"
summary += "You can now freely explore your data..."
```
User reaction: "Wait, what do I do now?"

**Solution**:
```python
def _generate_tpr_welcome(self, data_info: Dict) -> str:
    """Generate contextual welcome based on detected data type"""

    message = "# Welcome to ChatMRPT - Malaria Risk Analysis\n\n"

    # Detected TPR data
    if data_info.get('is_tpr_data'):
        message += "**What I see:** Test Positivity Rate data from your facilities\n"
        message += f"**Coverage:** {data_info['total_facilities']:,} facilities, "
        message += f"{data_info['total_tests']:,} tests conducted\n\n"

        message += "**What we'll do together** (3-5 minutes):\n"
        message += "1. 📊 Calculate TPR by facility type and age group\n"
        message += "2. 🗺️ Map high-risk areas across wards\n"
        message += "3. 📈 Combine with environmental factors\n"
        message += "4. 🎯 Prioritize wards for intervention\n\n"

        message += "**Let's start!** Which health facilities should we analyze?\n\n"
        message += self._format_facility_options(data_info)
    else:
        # Generic data analysis
        message += "I can help you analyze this dataset. What would you like to explore?\n"
        message += "Examples: 'Show summary statistics', 'Find correlations', 'Create visualizations'"

    return message

def _format_facility_options(self, data_info: Dict) -> str:
    """Format options with data-driven context"""
    options = "**Your options:**\n"

    # Show actual counts from data
    if data_info.get('facility_counts'):
        counts = data_info['facility_counts']
        options += f"• **primary** ({counts['primary']:,} facilities) - Community health centers\n"
        options += f"• **secondary** ({counts['secondary']:,} facilities) - District hospitals\n"
        options += f"• **tertiary** ({counts['tertiary']:,} facilities) - Specialist centers\n"
        options += f"• **all** ({counts['total']:,} facilities) - Combined analysis\n\n"
    else:
        options += "• **primary** - Community health centers (basic care)\n"
        options += "• **secondary** - District hospitals (general medicine)\n"
        options += "• **tertiary** - Specialist centers (advanced care)\n"
        options += "• **all** - Combined analysis across all levels\n\n"

    options += "💡 Not sure? Ask me 'What's the difference?' or type your choice."
    return options
```

**Impact**: Users immediately understand what's happening and what to do

**Testing**:
- Upload TPR data → Should show TPR workflow intro
- Upload generic CSV → Should show analysis options
- Check that facility counts are accurate

---

#### A1.2: Fuzzy Keyword Matching
**File**: `app/data_analysis_v3/core/tpr_workflow_handler.py:1439, 1461`

**Current Problem**:
```
User: "I want primary facilities"
Agent: "⚠️ I didn't understand. Please enter: primary, secondary, tertiary, or all"
```

**Solution - Three-Level Matching**:
```python
def extract_facility_level(self, query: str) -> Optional[str]:
    """
    Extract facility level with three-level matching:
    1. Exact keyword match (fast)
    2. Fuzzy string matching (handles typos)
    3. Pattern/phrase matching (handles variations)
    """
    query_clean = query.lower().strip()

    # Level 1: Exact match (fast path - 20ms)
    exact_keywords = {
        'primary': 'primary', '1': 'primary', 'one': 'primary',
        'secondary': 'secondary', '2': 'secondary', 'two': 'secondary',
        'tertiary': 'tertiary', '3': 'tertiary', 'three': 'tertiary',
        'all': 'all', '4': 'all', 'four': 'all', 'every': 'all'
    }

    if query_clean in exact_keywords:
        logger.info(f"Exact match: '{query_clean}' → {exact_keywords[query_clean]}")
        return exact_keywords[query_clean]

    # Level 2: Fuzzy match (handles typos - 50ms)
    from difflib import get_close_matches
    close_matches = get_close_matches(query_clean, exact_keywords.keys(), n=1, cutoff=0.75)

    if close_matches:
        matched_key = close_matches[0]
        result = exact_keywords[matched_key]
        logger.info(f"Fuzzy match: '{query_clean}' → '{matched_key}' → {result}")
        return result

    # Level 3: Pattern/phrase matching (handles "I want X", "let's do X" - 100ms)
    patterns = {
        'primary': [
            'primary', 'basic', 'community', 'first level', 'phc',
            'health center', 'clinic', 'local', 'ward level'
        ],
        'secondary': [
            'secondary', 'district', 'general hospital', 'second level',
            'cottage hospital', 'comprehensive', 'lga'
        ],
        'tertiary': [
            'tertiary', 'specialist', 'teaching hospital', 'third level',
            'referral', 'federal medical', 'university hospital'
        ],
        'all': [
            'all', 'every', 'combined', 'everything', 'total',
            'across all', 'all levels', 'complete'
        ]
    }

    # Check if ANY pattern keyword appears in query
    for level, keywords in patterns.items():
        for keyword in keywords:
            if keyword in query_clean:
                logger.info(f"Pattern match: '{query_clean}' contains '{keyword}' → {level}")
                return level

    # No match - return None (will trigger helpful error message)
    logger.info(f"No match found for: '{query_clean}'")
    return None


def extract_age_group(self, query: str) -> Optional[str]:
    """Extract age group with same three-level matching"""
    query_clean = query.lower().strip()

    # Level 1: Exact match
    exact_keywords = {
        'u5': 'u5', '1': 'u5', 'one': 'u5',
        'o5': 'o5', '2': 'o5', 'two': 'o5',
        'pw': 'pw', '3': 'pw', 'three': 'pw',
        'all': 'all', '4': 'all', 'four': 'all'
    }

    if query_clean in exact_keywords:
        return exact_keywords[query_clean]

    # Level 2: Fuzzy match
    from difflib import get_close_matches
    close_matches = get_close_matches(query_clean, exact_keywords.keys(), n=1, cutoff=0.75)
    if close_matches:
        return exact_keywords[close_matches[0]]

    # Level 3: Pattern matching
    patterns = {
        'u5': [
            'under 5', 'under five', 'u5', 'under-5', 'children',
            'kids', 'infant', 'toddler', 'young', 'pediatric'
        ],
        'o5': [
            'over 5', 'over five', 'o5', 'over-5', 'adult',
            'older', 'above 5', 'above five', 'grown'
        ],
        'pw': [
            'pregnant', 'pregnancy', 'maternal', 'mother',
            'antenatal', 'expecting', 'gravid', 'prenatal'
        ],
        'all': [
            'all', 'every', 'combined', 'everything', 'total',
            'all ages', 'everyone', 'complete'
        ]
    }

    for group, keywords in patterns.items():
        for keyword in keywords:
            if keyword in query_clean:
                return group

    return None
```

**Impact**:
- "I want primary" ✓
- "let's analyze basic facilities" ✓
- "primary health centers" ✓
- "1" ✓
- "prinary" (typo) ✓

**Testing**:
- Try 20+ variations per keyword
- Ensure no false positives
- Verify fuzzy match doesn't match wrong option

---

#### A1.3: Proactive Visualization Offers
**File**: `app/data_analysis_v3/core/tpr_workflow_handler.py:637, 723`

**Current Problem**: User doesn't know charts exist

**Solution**:
```python
def _format_facility_selection_message(self, analysis: Dict) -> str:
    """Format facility selection with proactive viz offer"""

    message = "Now, which health facility level would you like to analyze?\n\n"

    # Show options with data-driven counts
    message += self._format_facility_options_with_counts(analysis)
    message += "\n"

    # PROACTIVE OFFER - Make it obvious
    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    message += "💡 **Need help deciding?**\n"
    message += "I have **2 interactive charts** ready:\n"
    message += "  📊 Chart 1: Facility distribution by level\n"
    message += "  📈 Chart 2: Test volumes (RDT vs Microscopy)\n\n"
    message += "Say **'show charts'** or **'show data'** to see them\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    message += "Type your choice or ask questions."

    return message


def _format_age_group_selection_message(self, analysis: Dict) -> str:
    """Format age group selection with proactive viz offer"""

    facility = analysis.get('facility_level', 'selected facilities')

    message = f"Good! {facility.title()} facilities selected.\n\n"
    message += "Now, which age group should we focus on?\n\n"

    # Show options
    message += "**Your options:**\n"
    message += "• **u5** (or 1) - Children under 5 years\n"
    message += "• **o5** (or 2) - Everyone 5 years and older\n"
    message += "• **pw** (or 3) - Pregnant women\n"
    message += "• **all** (or 4) - All age groups combined\n\n"

    # PROACTIVE OFFER
    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    message += "💡 **Want to see the data first?**\n"
    message += "I have **2 charts** showing:\n"
    message += "  📊 Test volumes by age group\n"
    message += "  📈 Positivity rate comparisons\n\n"
    message += "Say **'show charts'** to see them\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    message += "Type your choice or ask questions."

    return message
```

**Impact**: Users know help is available, explore data before deciding

---

#### A1.4: Smart Error Messages with Suggestions
**File**: `app/data_analysis_v3/core/tpr_workflow_handler.py:840-863`

**Current Problem**: Repeats same message when confused

**Solution**:
```python
def handle_facility_selection(self, user_query: str) -> Dict:
    """Handle facility selection with intelligent error recovery"""

    # Try to extract facility level
    extracted = self.extract_facility_level(user_query)

    if extracted:
        # Success! Process the selection
        return self._process_facility_selection(extracted)

    # No match - provide intelligent help
    return self._generate_helpful_facility_error(user_query)


def _generate_helpful_facility_error(self, user_query: str) -> Dict:
    """Generate context-aware error message with suggestions"""

    query_lower = user_query.lower().strip()

    # Case 1: User is asking a question
    question_words = ['what', 'why', 'how', 'explain', 'mean', 'difference', 'tell me']
    if any(q in query_lower for q in question_words):
        message = "Let me explain the facility levels:\n\n"
        message += "**Primary** = Basic health posts and clinics\n"
        message += "  • Usually in rural areas\n"
        message += "  • First point of contact\n"
        message += "  • Example: Community Health Center\n\n"
        message += "**Secondary** = District-level hospitals\n"
        message += "  • General medical and surgical care\n"
        message += "  • Laboratory and X-ray facilities\n"
        message += "  • Example: General Hospital\n\n"
        message += "**Tertiary** = Specialist referral centers\n"
        message += "  • Advanced medical care\n"
        message += "  • Teaching hospitals\n"
        message += "  • Example: Federal Medical Center\n\n"
        message += "Which level would you like to analyze? (primary/secondary/tertiary/all)"

        return {"success": True, "message": message, "workflow": "tpr", ...}

    # Case 2: User made a typo or close match
    from difflib import get_close_matches
    valid_options = ['primary', 'secondary', 'tertiary', 'all']
    close_matches = get_close_matches(query_lower, valid_options, n=1, cutoff=0.5)

    if close_matches:
        suggestion = close_matches[0]
        message = f"**Did you mean '{suggestion}'?**\n\n"
        message += f"If yes, just type **'{suggestion}'** to confirm.\n\n"
        message += f"Or choose from: **primary**, **secondary**, **tertiary**, **all**\n\n"
        message += "💡 Tip: You can also ask me 'What is secondary?' to learn more."

        return {"success": True, "message": message, "workflow": "tpr", ...}

    # Case 3: Generic unclear input
    message = "I didn't quite catch that. Let me help:\n\n"
    message += "**Quick options:**\n"
    message += "• Type **primary**, **secondary**, **tertiary**, or **all**\n"
    message += "• Or just type the number: **1**, **2**, **3**, or **4**\n\n"
    message += "**Need more info?**\n"
    message += "• Ask: 'What's the difference between them?'\n"
    message += "• Say: 'Show me the data' to see facility distribution\n\n"
    message += "What would you like to do?"

    return {"success": True, "message": message, "workflow": "tpr", ...}
```

**Impact**: Helpful instead of frustrating, guides user to success

---

### Phase A2: Progressive Enhancement (Day 3-4)

#### A2.1: Add Progress Indicators
**File**: `app/data_analysis_v3/tools/tpr_analysis_tool.py:896-900`

**Current Problem**: 3-5 seconds of silence during TPR calculation

**Solution**:
```python
# In analyze_tpr_data tool
try:
    logger.info(f"Calculating TPR - Age: {age_group}, Method: {test_method}, Facilities: {facility_level}")

    # ADD PROGRESS INDICATOR
    progress_message = f"🔄 **Calculating TPR...**\n"
    progress_message += f"• Processing {len(df)} facility records\n"
    progress_message += f"• Analyzing {test_method} test data\n"
    progress_message += f"• Aggregating by ward level\n"
    progress_message += "This will take 10-15 seconds..."

    # Return progress immediately (if streaming available)
    yield {"status": "progress", "message": progress_message}

    # Then do actual calculation
    tpr_results = calculate_ward_tpr(df,
                                    age_group=age_group,
                                    test_method=test_method,
                                    facility_level=facility_level)

except Exception as e:
    # Error handling
```

**Impact**: Users know something is happening, not frozen

---

#### A2.2: Improve TPR Completion Message
**File**: `app/data_analysis_v3/core/formatters.py:161-185`

**Current**:
```python
message = tool_output  # Just dumps tool output
```

**Improved**:
```python
def format_tpr_completion(self, tpr_results: Dict, state_name: str) -> str:
    """Format TPR completion with clear next steps"""

    message = "## ✅ TPR Analysis Complete!\n\n"

    # Key findings (data-driven)
    message += "**Key Findings:**\n"
    message += f"• Average TPR: **{tpr_results['mean_tpr']:.1f}%** across {tpr_results['total_wards']} wards\n"
    message += f"• Highest risk: **{tpr_results['max_ward']}** ({tpr_results['max_tpr']:.1f}% TPR)\n"
    message += f"• Total tests: **{tpr_results['total_tested']:,}** ({tpr_results['total_positive']:,} positive)\n\n"

    # Show top 3 high-risk wards
    if tpr_results.get('high_risk_wards'):
        message += "**Top Priority Wards:**\n"
        for i, ward in enumerate(tpr_results['high_risk_wards'][:3], 1):
            message += f"{i}. {ward['WardName']}: {ward['TPR']:.1f}% TPR\n"
        message += "\n"

    # Show map availability
    if tpr_results.get('map_created'):
        message += "📍 **Interactive map created** showing TPR distribution\n\n"

    # Clear next step
    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    message += "## 🎯 Next Step: Comprehensive Risk Assessment\n\n"
    message += "**What happens next:**\n"
    message += "I'll combine your TPR data with:\n"
    message += "• Environmental factors (rainfall, vegetation)\n"
    message += "• Infrastructure data (housing quality, urban extent)\n"
    message += "• Geographic features (elevation, water proximity)\n\n"
    message += "This will give you **complete vulnerability rankings** for ITN distribution.\n\n"
    message += "**Ready to continue?** Say **'yes'** or **'continue'** when ready.\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    message += "💡 Or ask me questions about these TPR results first."

    return message
```

**Impact**: Clear understanding of what was done, what comes next

---

## Track B: Agent Liberation
**Goal**: Free the LangGraph agent from routing complexity
**Timeline**: 1 week (parallel with Track A)
**Risk**: Medium - Architectural changes but well-scoped

### Phase B1: Extract TPR Logic from Agent (Day 1-3)

#### B1.1: Create Dedicated TPR Router
**New File**: `app/data_analysis_v3/core/tpr_router.py`

**Purpose**: Handle ALL TPR routing logic outside the agent

```python
"""
TPR Router - Handles TPR workflow routing separately from agent
"""
import logging
from typing import Dict, Any, Optional
from .state_manager import DataAnalysisStateManager, ConversationStage
from .tpr_workflow_handler import TPRWorkflowHandler
from .tpr_data_analyzer import TPRDataAnalyzer

logger = logging.getLogger(__name__)


class TPRRouter:
    """
    Dedicated router for TPR workflow.
    Separates TPR orchestration from general agent logic.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state_manager = DataAnalysisStateManager(session_id)
        self.tpr_analyzer = TPRDataAnalyzer()
        self.tpr_handler = None  # Lazy init

    def should_handle(self, user_query: str) -> bool:
        """Check if this query should be routed to TPR workflow"""

        # Check if TPR workflow is active
        if self.state_manager.is_tpr_workflow_active():
            return True

        # Check for TPR trigger words
        tpr_triggers = [
            'tpr', 'test positivity', 'positivity rate',
            'calculate tpr', 'start tpr', 'run tpr'
        ]
        query_lower = user_query.lower()
        if any(trigger in query_lower for trigger in tpr_triggers):
            return True

        return False

    def route(self, user_query: str, data: Any) -> Optional[Dict]:
        """
        Route query through TPR workflow if applicable.
        Returns None if query should go to general agent.
        """

        if not self.should_handle(user_query):
            return None

        # Initialize handler if needed
        if self.tpr_handler is None:
            self.tpr_handler = TPRWorkflowHandler(
                self.session_id,
                self.state_manager,
                self.tpr_analyzer
            )
            self.tpr_handler.set_data(data)
            self.tpr_handler.load_state_from_manager()

        # Get current stage
        stage = self.tpr_handler.current_stage

        # KEYWORD-FIRST APPROACH
        extracted_value = None

        if stage == ConversationStage.TPR_STATE_SELECTION:
            return self.tpr_handler.handle_state_selection(user_query)

        elif stage == ConversationStage.TPR_COMPLETED_AWAITING_CONFIRMATION:
            result = self.tpr_handler.handle_risk_analysis_confirmation(user_query)
            if result.get('requires_ai'):
                # User asked a question - return None to let agent handle
                return None
            return result

        elif stage == ConversationStage.TPR_FACILITY_LEVEL:
            extracted_value = self.tpr_handler.extract_facility_level(user_query)
            if extracted_value:
                return self.tpr_handler.handle_facility_selection(user_query)

        elif stage == ConversationStage.TPR_AGE_GROUP:
            extracted_value = self.tpr_handler.extract_age_group(user_query)
            if extracted_value:
                return self.tpr_handler.handle_age_group_selection(user_query)

        # Check for visualization requests
        if self._is_viz_request(user_query):
            return self._handle_viz_request(stage)

        # No keyword match - return None to let agent handle with context
        return None

    def _is_viz_request(self, query: str) -> bool:
        """Check if user is requesting visualizations"""
        viz_keywords = ['show', 'chart', 'visual', 'graph', 'data', 'see']
        query_lower = query.lower()
        return sum(1 for kw in viz_keywords if kw in query_lower) >= 2

    def _handle_viz_request(self, stage: ConversationStage) -> Dict:
        """Handle visualization request"""
        pending_viz = self.tpr_handler.get_pending_visualizations()

        if pending_viz:
            if stage == ConversationStage.TPR_FACILITY_LEVEL:
                message = "Here are the facility insights:\n\n"
                message += "**Chart 1:** Facility distribution\n"
                message += "**Chart 2:** Test volumes by type\n\n"
                message += "Based on this, which level? (primary/secondary/tertiary/all)"
            else:
                message = "Here's the data you requested:"

            return {
                "success": True,
                "message": message,
                "session_id": self.session_id,
                "workflow": "tpr",
                "stage": stage.value,
                "visualizations": pending_viz
            }

        return None

    def get_context_for_agent(self) -> Optional[str]:
        """
        Get TPR context to pass to agent if query should be handled by AI.
        This allows agent to answer questions about TPR workflow.
        """
        if not self.state_manager.is_tpr_workflow_active():
            return None

        stage = self.state_manager.get_workflow_stage()
        valid_keywords = self.tpr_handler.get_valid_keywords_for_stage(stage) if self.tpr_handler else []

        context = f"[TPR Context: User is in TPR workflow at {stage.value}. "
        context += f"Valid keywords: {valid_keywords}. "
        context += "If user asks a question, answer it and guide them to use keywords.]"

        return context
```

**Impact**: Agent is no longer polluted with TPR-specific logic

---

#### B1.2: Simplify Agent.analyze()
**File**: `app/data_analysis_v3/core/agent.py:362-560`

**Current**: 192 lines of TPR-specific logic

**After Refactor**:
```python
async def analyze(self, user_query: str) -> Dict[str, Any]:
    """
    Main entry point - now clean and focused on AI reasoning
    """
    logger.info(f"[DEBUG] analyze() called with query: {user_query[:100]}")

    # NEW: Try TPR router first
    from .tpr_router import TPRRouter
    tpr_router = TPRRouter(self.session_id)

    # Load data if needed
    data = self._load_session_data()

    # Route to TPR if applicable
    tpr_result = tpr_router.route(user_query, data)
    if tpr_result:
        return tpr_result

    # Get TPR context if in workflow (for AI to understand)
    tpr_context = tpr_router.get_context_for_agent()
    if tpr_context:
        user_query = user_query + "\n\n" + tpr_context

    # Check for TPR→Risk transition
    transition_response = self._check_tpr_transition(user_query)
    if transition_response:
        return transition_response

    # NOW INVOKE LANGGRAPH (clean, no TPR coupling)
    input_data_list = self._prepare_input_data()

    input_state = {
        "messages": self.chat_history + [HumanMessage(content=user_query)],
        "session_id": self.session_id,
        "input_data": input_data_list,
        "current_variables": {},
        "output_plots": [],
        "insights": [],
        "errors": [],
        "tool_call_count": 0
    }

    try:
        result = self.graph.invoke(input_state, {"recursion_limit": 10})
        return self._format_result(result)
    except Exception as e:
        logger.error(f"Graph execution failed: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "session_id": self.session_id
        }
```

**Before**: 851 lines (192 lines of TPR logic)
**After**: ~700 lines (TPR logic extracted)

**Impact**: Agent code is focused on AI reasoning, not workflow orchestration

---

### Phase B2: Make All Tools Available to Agent (Day 4-5)

#### B2.1: Create Tool Registry
**New File**: `app/data_analysis_v3/core/tool_registry.py`

```python
"""
Central registry for ALL ChatMRPT tools accessible to LangGraph agent
"""
from typing import List, Dict, Any
from langchain_core.tools import BaseTool
import logging

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry of all tools available to the agent"""

    @staticmethod
    def get_all_tools(session_id: str, context: Dict[str, Any]) -> List[BaseTool]:
        """
        Get all tools based on session context.
        Tools are conditionally included based on what data is available.
        """
        tools = []

        # 1. ALWAYS AVAILABLE: General data analysis
        from ..tools.python_tool import analyze_data
        tools.append(analyze_data)

        # 2. CONDITIONAL: TPR analysis (if TPR data detected)
        if context.get('has_tpr_data'):
            from ..tools.tpr_analysis_tool import analyze_tpr_data
            tools.append(analyze_tpr_data)
            logger.info("Added TPR analysis tool (TPR data detected)")

        # 3. CONDITIONAL: Risk analysis (if raw_data.csv exists)
        if context.get('risk_ready'):
            risk_tool = ToolRegistry._create_risk_analysis_tool(session_id)
            tools.append(risk_tool)
            logger.info("Added risk analysis tool (data prepared)")

        # 4. CONDITIONAL: ITN planning (if analysis complete)
        if context.get('analysis_complete'):
            itn_tool = ToolRegistry._create_itn_planning_tool(session_id)
            tools.append(itn_tool)
            logger.info("Added ITN planning tool (analysis complete)")

        # 5. ALWAYS AVAILABLE: Visualization tools
        viz_tools = ToolRegistry._get_visualization_tools(session_id)
        tools.extend(viz_tools)

        logger.info(f"Tool registry: {len(tools)} tools available")
        return tools

    @staticmethod
    def _create_risk_analysis_tool(session_id: str) -> BaseTool:
        """Create risk analysis tool as a LangChain tool"""
        from langchain_core.tools import tool

        @tool
        def run_risk_analysis(
            composite_variables: str = None,
            pca_variables: str = None
        ) -> str:
            """
            Run dual-method malaria risk analysis (Composite + PCA).
            Analyzes ward-level vulnerability using TPR and environmental data.
            Creates vulnerability rankings and interactive maps.

            Args:
                composite_variables: Comma-separated list of variables for composite (optional)
                pca_variables: Comma-separated list for PCA (optional)
            """
            from app.core.request_interpreter import RequestInterpreter
            from app.services.container import ServiceContainer

            # Initialize RequestInterpreter
            container = ServiceContainer()
            interpreter = RequestInterpreter(
                container.llm_manager,
                container.data_service,
                container.analysis_service,
                container.visualization_service
            )

            # Parse variables
            comp_vars = composite_variables.split(',') if composite_variables else None
            pca_vars = pca_variables.split(',') if pca_variables else None

            # Call the actual tool
            result = interpreter._run_malaria_risk_analysis(
                session_id=session_id,
                variables=comp_vars or pca_vars
            )

            if isinstance(result, dict):
                return result.get('response', str(result))
            return str(result)

        return run_risk_analysis

    @staticmethod
    def _create_itn_planning_tool(session_id: str) -> BaseTool:
        """Create ITN planning tool as a LangChain tool"""
        from langchain_core.tools import tool

        @tool
        def plan_itn_distribution(
            total_nets: int = 10000,
            avg_household_size: float = 5.0,
            urban_threshold: float = 30.0,
            method: str = 'composite'
        ) -> str:
            """
            Plan ITN (bed net) distribution based on vulnerability rankings.
            Allocates nets to high-risk wards proportionally.

            Args:
                total_nets: Total nets available for distribution
                avg_household_size: Average household size for calculations
                urban_threshold: Urban % threshold for allocation
                method: Ranking method ('composite' or 'pca')
            """
            from app.core.request_interpreter import RequestInterpreter
            from app.services.container import ServiceContainer

            container = ServiceContainer()
            interpreter = RequestInterpreter(
                container.llm_manager,
                container.data_service,
                container.analysis_service,
                container.visualization_service
            )

            result = interpreter._run_itn_planning(
                session_id=session_id,
                total_nets=total_nets,
                avg_household_size=avg_household_size,
                urban_threshold=urban_threshold,
                method=method
            )

            if isinstance(result, dict):
                return result.get('response', str(result))
            return str(result)

        return plan_itn_distribution

    @staticmethod
    def _get_visualization_tools(session_id: str) -> List[BaseTool]:
        """Get visualization creation tools"""
        # Can add viz tools here if needed
        return []
```

---

#### B2.2: Update Agent to Use Tool Registry
**File**: `app/data_analysis_v3/core/agent.py:54-58`

**Current**:
```python
# Set up tools - conditionally add TPR tool if TPR data detected
self.tools = [analyze_data]
self._check_and_add_tpr_tool()
```

**After**:
```python
# Get all available tools from registry
from .tool_registry import ToolRegistry

session_context = self._get_session_context()
self.tools = ToolRegistry.get_all_tools(self.session_id, session_context)

logger.info(f"Agent initialized with {len(self.tools)} tools")
```

**Impact**: Agent can now see and use ALL tools (risk analysis, ITN planning, etc.)

---

## Track C: Agent Enhancement
**Goal**: Make the agent truly intelligent and autonomous
**Timeline**: 1-2 weeks (after Tracks A & B)
**Risk**: Medium-High - New capabilities

### Phase C1: Multi-Turn Reasoning (Week 2, Day 1-3)

#### C1.1: Add ReACT-Style Reasoning Loop
**New File**: `app/data_analysis_v3/core/reasoning_engine.py`

```python
"""
Multi-turn reasoning engine for complex queries
"""
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class ReasoningEngine:
    """
    Enables agent to break down complex queries into steps.
    Uses ReACT pattern: Reason → Act → Observe → Reason
    """

    def __init__(self, agent, max_turns: int = 5):
        self.agent = agent
        self.max_turns = max_turns

    async def solve_complex_query(self, user_query: str) -> Dict[str, Any]:
        """
        Solve complex query through iterative reasoning.

        Example complex query:
        "Show me the top 10 wards by TPR, create a map, and export to Excel"

        This requires multiple steps:
        1. Calculate TPR
        2. Get top 10
        3. Create map
        4. Export
        """

        logger.info(f"Starting multi-turn reasoning for: {user_query[:100]}")

        # Step 1: Ask agent to create a plan
        plan = await self._create_plan(user_query)
        logger.info(f"Plan created: {len(plan['steps'])} steps")

        # Step 2: Execute plan step by step
        results = []
        context = {}

        for i, step in enumerate(plan['steps'], 1):
            if i > self.max_turns:
                logger.warning(f"Max turns ({self.max_turns}) reached")
                break

            logger.info(f"Executing step {i}/{len(plan['steps'])}: {step['action']}")

            # Execute step with accumulated context
            step_result = await self._execute_step(step, context)
            results.append(step_result)

            # Update context with results
            context.update(step_result.get('context', {}))

            # Check if step failed
            if not step_result.get('success'):
                # Try to recover or abort
                recovery = await self._attempt_recovery(step, step_result, context)
                if recovery:
                    results.append(recovery)
                    context.update(recovery.get('context', {}))
                else:
                    logger.error(f"Step {i} failed, aborting")
                    break

        # Step 3: Synthesize final answer
        final_answer = await self._synthesize_answer(user_query, plan, results)

        return final_answer

    async def _create_plan(self, user_query: str) -> Dict:
        """Ask agent to break query into steps"""

        planning_prompt = f"""
        Break this query into executable steps:
        "{user_query}"

        Return a JSON plan with:
        {{
            "steps": [
                {{"action": "step description", "tool": "tool_name", "params": {{...}}}},
                ...
            ]
        }}

        Available tools: {[tool.name for tool in self.agent.tools]}
        """

        # Get plan from LLM
        plan_response = await self.agent.llm.ainvoke(planning_prompt)

        # Parse JSON plan
        import json
        try:
            plan = json.loads(plan_response.content)
        except:
            # Fallback: simple 1-step plan
            plan = {"steps": [{"action": user_query, "tool": "analyze_data", "params": {}}]}

        return plan

    async def _execute_step(self, step: Dict, context: Dict) -> Dict:
        """Execute a single step"""

        # Build step query with context
        step_query = step['action']
        if context:
            step_query += f"\n\nContext from previous steps: {context}"

        # Execute through agent
        result = await self.agent.analyze(step_query)

        return {
            "success": result.get('success', True),
            "output": result.get('message', ''),
            "context": {
                "step_action": step['action'],
                "tool_used": step.get('tool'),
                **result
            }
        }

    async def _attempt_recovery(self, step: Dict, error: Dict, context: Dict) -> Dict:
        """Try to recover from step failure"""

        recovery_prompt = f"""
        Step failed: {step['action']}
        Error: {error}

        Available context: {context}

        Can you suggest an alternative approach or fix?
        """

        recovery = await self.agent.llm.ainvoke(recovery_prompt)

        # Try alternative approach if suggested
        if "try" in recovery.content.lower():
            # Extract alternative and attempt
            pass

        return None

    async def _synthesize_answer(self, original_query: str, plan: Dict, results: List[Dict]) -> Dict:
        """Synthesize final answer from all steps"""

        synthesis_prompt = f"""
        Original query: {original_query}

        Plan executed:
        {plan}

        Results from each step:
        {results}

        Synthesize a coherent final answer that addresses the original query.
        Include all relevant visualizations and data.
        """

        final_answer = await self.agent.llm.ainvoke(synthesis_prompt)

        return {
            "success": True,
            "message": final_answer.content,
            "visualizations": self._collect_visualizations(results),
            "steps_executed": len(results),
            "session_id": self.agent.session_id
        }

    def _collect_visualizations(self, results: List[Dict]) -> List:
        """Collect all visualizations from step results"""
        all_viz = []
        for result in results:
            if result.get('visualizations'):
                all_viz.extend(result['visualizations'])
        return all_viz
```

**Impact**: Agent can now handle "Show top 10 wards, create map, export to Excel" in one request

---

### Phase C2: Self-Correction & Learning (Week 2, Day 4-5)

#### C2.1: Add Error Recovery
**File**: `app/data_analysis_v3/core/agent.py` - Add to `_agent_node()`

```python
def _agent_node(self, state: DataAnalysisState) -> DataAnalysisState:
    """
    Agent node with error recovery.
    If tool fails, agent reflects and tries alternative.
    """

    # Invoke model
    response = self.model.invoke(state)

    # Check if there were errors in previous tool calls
    if state.get('errors'):
        last_error = state['errors'][-1]

        # Add error reflection to messages
        reflection_msg = f"""
        The previous tool call failed with error:
        {last_error}

        Please:
        1. Analyze why it failed
        2. Try a different approach
        3. If data is missing, explain what's needed
        """

        # Re-invoke with reflection
        reflection_response = self.model.invoke({
            **state,
            "messages": state["messages"] + [HumanMessage(content=reflection_msg)]
        })

        return {
            **state,
            "messages": state["messages"] + [reflection_response],
            "tool_call_count": state.get("tool_call_count", 0) + 1
        }

    return {
        **state,
        "messages": state["messages"] + [response],
        "tool_call_count": state.get("tool_call_count", 0) + 1
    }
```

**Impact**: Agent doesn't give up on first error, tries alternatives

---

## Implementation Timeline

### Week 1: Parallel Development
```
Day 1-2:  Track A (A1.1-A1.2) + Track B (B1.1)
Day 3-4:  Track A (A1.3-A1.4) + Track B (B1.2)
Day 5:    Track A (A2.1-A2.2) + Track B (B2.1-B2.2)
Weekend:  Testing & Integration
```

### Week 2: Enhancement & Polish
```
Day 1-3:  Track C (C1.1) - Multi-turn reasoning
Day 4-5:  Track C (C2.1) - Error recovery
Weekend:  Full system testing
```

---

## Success Metrics

### User Experience (Track A)
- [ ] Keyword match success rate: 60% → 95%
- [ ] User completes TPR workflow: 50% → 85%
- [ ] User views visualizations: 20% → 70%
- [ ] Average time to complete workflow: 8 min → 4 min

### Agent Capabilities (Track B+C)
- [ ] Agent code size: 851 lines → <700 lines
- [ ] Tools available to agent: 2 → 6+
- [ ] Can handle complex queries: No → Yes
- [ ] Self-correction rate: 0% → 80%

### System Health
- [ ] No increase in response latency
- [ ] No increase in error rates
- [ ] All existing functionality preserved
- [ ] AWS deployment successful

---

## Testing Strategy

### Phase Testing (After Each Phase)
1. Unit tests for new functions
2. Manual testing of user flows
3. Comparison with previous behavior

### Integration Testing (End of Each Track)
1. Full TPR workflow (Track A)
2. Agent tool usage (Track B)
3. Complex query handling (Track C)

### End-to-End Testing (After Week 2)
1. New user onboarding flow
2. Complete analysis pipeline (TPR → Risk → ITN)
3. Edge cases and error scenarios
4. Load testing on AWS

---

## Rollback Plan

### Immediate Rollback
If critical issues arise:
```bash
# Restore from pre-investigation backup
ssh ec2-user@3.21.167.170
cd /home/ec2-user
tar -xzf ChatMRPT_pre_investigation_20250930_205142.tar.gz
sudo systemctl restart chatmrpt
```

### Granular Rollback
Each track is independent:
- Track A issues: Revert UX changes only
- Track B issues: Revert agent refactor
- Track C issues: Disable new features

---

## Risk Mitigation

### High-Risk Changes
1. **Agent refactoring (Track B)**: Extensive testing before deployment
2. **Tool registry**: Validate all tools still work
3. **Multi-turn reasoning**: Start with opt-in flag

### Medium-Risk Changes
1. **Fuzzy matching**: Test with 100+ variations
2. **TPR router**: Ensure no regression in current flow

### Low-Risk Changes
1. **Welcome messages**: Pure UI, easy to revert
2. **Progress indicators**: Additive only

---

## Post-Implementation Tasks

### Documentation Updates
- [ ] Update CLAUDE.md with new architecture
- [ ] Document new agent capabilities
- [ ] Create user guide for improved UX

### Monitoring
- [ ] Add metrics for keyword match success
- [ ] Track agent tool usage
- [ ] Monitor error recovery attempts

### Future Enhancements
- [ ] Semantic memory (conversation history)
- [ ] Proactive suggestions
- [ ] Multi-language support
- [ ] Voice interface

---

## Conclusion

This comprehensive plan transforms ChatMRPT from **functional** to **delightful** while making the LangGraph agent truly powerful and autonomous.

**Key Benefits:**
✅ Users feel guided, not confused
✅ Conversational instead of keyword-dependent
✅ Agent can handle complex multi-step tasks
✅ Clean architecture enables future enhancements
✅ All phases deliver independent value

**Ready to start implementation!**
