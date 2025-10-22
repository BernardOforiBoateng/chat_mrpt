# Implementation Plan: DataExplorationAgent as Tool #19

**Date**: 2025-10-04
**Status**: Ready for Implementation
**Estimated Effort**: 4-6 hours
**Risk Level**: Low

---

## Executive Summary

**Objective**: Add Python execution capability to RequestInterpreter by registering DataExplorationAgent as Tool #19 (`analyze_data_with_python`).

**Key Insight**: Instead of replacing or running parallel to RequestInterpreter, the agent becomes just another tool that the LLM can choose to call when users ask questions requiring custom data analysis.

**Strategic Vision**: Agent starts as Tool #19, gradually handles more queries over time, eventually becomes primary execution engine while complex pre-built tools remain for specialized tasks.

---

## Background & Context

### Current System Architecture

**RequestInterpreter** (`app/core/request_interpreter.py`):
- Orchestrates all user requests
- Has 18 registered tools (risk analysis, visualizations, SQL queries, etc.)
- Uses LLM (GPT-4o) to choose which tool to call
- Uses `LLMOrchestrator` + `ToolRunner` for execution

**How it works now:**
```
User: "Run the risk analysis"
    ↓
RequestInterpreter.process_message()
    ↓
orchestrator.run_with_tools(
    llm_manager,           # GPT-4o
    system_prompt,         # Instructions
    user_message,          # User query
    function_schemas,      # 18 tool descriptions
    tool_runner            # Executor
)
    ↓
GPT-4o chooses: run_malaria_risk_analysis
    ↓
tool_runner.execute("run_malaria_risk_analysis", args)
    ↓
Result returned
```

**Current Limitation:**
When users ask questions requiring custom analysis (e.g., "Show me top 10 wards by population"), the LLM has no tool that can execute Python code on the data. It can only:
1. Call a pre-built tool (if one exists)
2. Give a conversational response (can't actually query the data)

---

## Proposed Architecture

### Add Agent as Tool #19

**RequestInterpreter** gets a new tool:
```
Current Tools (18):
├─ run_malaria_risk_analysis
├─ run_itn_planning
├─ create_vulnerability_map
├─ execute_sql_query
├─ create_box_plot
├─ ... (13 more)

NEW Tool (19):
└─ analyze_data_with_python ✨
    ↓
    Calls DataExplorationAgent
    ↓
    Agent loads df/gdf from session
    ↓
    Agent's LLM writes Python code
    ↓
    Executes code and returns result
```

### How It Works

```
User: "Show me top 10 wards by population"
    ↓
RequestInterpreter.process_message()
    ↓
GPT-4o sees 19 tools:
  - run_malaria_risk_analysis? No
  - create_vulnerability_map? No
  - execute_sql_query? Maybe, but not ideal
  - analyze_data_with_python? YES! ✅
    ↓
Calls: analyze_data_with_python(
    session_id="abc123",
    query="Show me top 10 wards by population"
)
    ↓
Tool creates DataExplorationAgent instance
    ↓
Agent loads data (df from raw_data.csv)
    ↓
Agent's LLM writes: df.nlargest(10, 'population')
    ↓
Executes Python code
    ↓
Returns result to RequestInterpreter
    ↓
User sees: Table with top 10 wards
```

---

## Implementation Details

### Phase 1: Create DataExplorationAgent

**File**: `app/data_analysis_v3/core/data_exploration_agent.py` (NEW)

**Purpose**:
- Inherits from DataAnalysisAgent (reuses LangGraph setup)
- Loads CSV + shapefile based on session state
- Executes Python code on DataFrames/GeoDataFrames

**Key Methods**:

```python
class DataExplorationAgent(DataAnalysisAgent):
    """
    Agent for Python execution on user data.

    Called by RequestInterpreter's analyze_data_with_python tool.
    """

    def __init__(self, session_id: str):
        super().__init__(session_id)  # Inherits LangGraph setup

    def _get_input_data(self) -> List[Dict[str, Any]]:
        """
        Load data based on workflow phase:
        - Post-risk: unified_dataset.csv (has rankings)
        - Post-TPR: raw_data.csv (has TPR + environment)
        - Standard upload: raw_data.csv (user data)
        """
        # Determine CSV file
        csv_file = self._determine_csv_file(session_folder)

        # Load DataFrame
        df = pd.read_csv(csv_file)

        # Load shapefile if exists
        shapefile = self._find_shapefile(session_folder)
        if shapefile:
            gdf = gpd.read_file(shapefile)

        return [
            {'variable_name': 'df', 'data': df, ...},
            {'variable_name': 'gdf', 'data': gdf, ...}  # If shapefile exists
        ]

    def _determine_csv_file(self, session_folder: str):
        """
        Priority order:
        1. unified_dataset.csv (if .analysis_complete exists)
        2. raw_data.csv (if .tpr_complete or standard upload)
        3. uploaded_data.csv (fallback)
        """
        if os.path.exists(f"{session_folder}/.analysis_complete"):
            return f"{session_folder}/unified_dataset.csv"

        if os.path.exists(f"{session_folder}/raw_data.csv"):
            return f"{session_folder}/raw_data.csv"

        return f"{session_folder}/uploaded_data.csv"

    def _find_shapefile(self, session_folder: str):
        """Find shapefile in raw_shapefile.zip or shapefile/ directory."""
        # Check for raw_shapefile.zip
        # Check for shapefile/*.shp
        # Return path or None
```

**Lines**: ~150-200

---

### Phase 2: Register Tool in RequestInterpreter

**File**: `app/core/request_interpreter.py` (MODIFY)

**Changes**:

1. **Add to `_register_tools()` method** (line ~140):
```python
def _register_tools(self):
    """Register actual Python functions as tools."""

    # ... existing 18 tools ...

    # NEW: Python execution tool
    self.tools['analyze_data_with_python'] = self._analyze_data_with_python

    logger.info(f"Registered {len(self.tools)} tools")  # Now shows 19
```

2. **Add new tool method** (after existing tools, ~line 1500):
```python
def _analyze_data_with_python(self, session_id: str, query: str) -> Dict[str, Any]:
    """
    Execute custom Python analysis on user data.

    Use this tool when users ask questions requiring:
    - Custom data queries (e.g., "show top 10 wards by population")
    - Calculations (e.g., "what's the correlation between rainfall and TPR")
    - Filtering (e.g., "which wards have TPR > 0.5")
    - Custom visualizations
    - Geospatial queries

    This tool can access:
    - DataFrames (df) with uploaded data
    - GeoDataFrames (gdf) with spatial boundaries
    - All pandas, numpy, geopandas operations

    Args:
        session_id: Session identifier
        query: Natural language description of analysis to perform

    Returns:
        Dict with status, response, visualizations, code executed
    """
    logger.info(f"🐍 PYTHON TOOL: analyze_data_with_python called")
    logger.info(f"  Session: {session_id}")
    logger.info(f"  Query: {query[:100]}...")

    try:
        # Import agent
        from app.data_analysis_v3.core.data_exploration_agent import DataExplorationAgent

        # Create agent instance
        agent = DataExplorationAgent(session_id=session_id)

        # Execute query via agent (async)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(agent.analyze(query))
        finally:
            loop.close()

        # Format result for RequestInterpreter
        return {
            'status': 'success',
            'response': result.get('message', ''),
            'visualizations': result.get('visualizations', []),
            'tools_used': ['analyze_data_with_python'],
            'code_executed': result.get('code_executed', ''),
            'insights': result.get('insights', [])
        }

    except Exception as e:
        logger.error(f"Error in analyze_data_with_python: {e}", exc_info=True)
        return {
            'status': 'error',
            'response': f'I encountered an error analyzing the data: {str(e)}',
            'tools_used': ['analyze_data_with_python']
        }
```

**Lines Added**: ~60

---

## File Summary

### CREATE:
1. **`app/data_analysis_v3/core/data_exploration_agent.py`** (~150-200 lines)
   - DataExplorationAgent class
   - Inherits from DataAnalysisAgent
   - Loads CSV + shapefile based on session phase
   - Executes Python via inherited analyze_data tool

### MODIFY:
1. **`app/core/request_interpreter.py`** (+~60 lines)
   - Add tool registration in `_register_tools()`
   - Add `_analyze_data_with_python()` method

### NO CHANGES:
- ✅ All routing logic (analysis_routes.py)
- ✅ All existing tools (18 tools unchanged)
- ✅ LLMOrchestrator
- ✅ ToolRunner
- ✅ All other files

**Total New Code**: ~210-260 lines

---

## Testing Strategy

### Unit Tests

**File**: `tests/test_data_exploration_agent.py` (NEW)

```python
def test_agent_loads_correct_csv():
    """Test CSV selection based on workflow phase."""
    # Post-risk phase
    session_id = create_test_session_with_unified_dataset()
    agent = DataExplorationAgent(session_id)
    assert agent.csv_file == 'unified_dataset.csv'

    # Post-TPR phase
    session_id = create_test_session_with_tpr_complete()
    agent = DataExplorationAgent(session_id)
    assert agent.csv_file == 'raw_data.csv'

    # Standard upload
    session_id = create_test_session_standard_upload()
    agent = DataExplorationAgent(session_id)
    assert agent.csv_file == 'raw_data.csv'

def test_agent_loads_shapefile():
    """Test shapefile loading."""
    session_id = create_test_session_with_shapefile()
    agent = DataExplorationAgent(session_id)
    data = agent._get_input_data()

    assert len(data) == 2  # df + gdf
    assert data[0]['variable_name'] == 'df'
    assert data[1]['variable_name'] == 'gdf'
    assert data[1]['is_spatial'] == True

def test_agent_executes_python():
    """Test Python execution."""
    session_id = create_test_session_with_data()
    agent = DataExplorationAgent(session_id)

    result = agent.analyze("Show me the first 5 rows")

    assert result['success'] == True
    assert 'df.head(5)' in result.get('code_executed', '')
```

### Integration Tests

**File**: `tests/test_agent_as_tool.py` (NEW)

```python
def test_request_interpreter_calls_agent_tool():
    """Test RI can call analyze_data_with_python."""
    ri = RequestInterpreter()

    # Create test session with data
    session_id = create_test_session_with_data()

    # Send query that should use agent
    result = ri.process_message(
        "Show me the top 10 wards by population",
        session_id
    )

    assert result['status'] == 'success'
    assert 'analyze_data_with_python' in result['tools_used']
    assert len(result['response']) > 0

def test_llm_chooses_correct_tool():
    """Test LLM chooses agent vs pre-built tool correctly."""
    ri = RequestInterpreter()
    session_id = create_test_session_with_data()

    # Custom query → Should use agent
    result = ri.process_message(
        "What's the correlation between rainfall and elevation?",
        session_id
    )
    assert 'analyze_data_with_python' in result['tools_used']

    # Complex analysis → Should use pre-built tool
    result = ri.process_message(
        "Run the complete malaria risk analysis",
        session_id
    )
    assert 'run_malaria_risk_analysis' in result['tools_used']

def test_agent_tool_handles_errors():
    """Test error handling."""
    ri = RequestInterpreter()
    session_id = "invalid_session"

    result = ri.process_message(
        "Show me data",
        session_id
    )

    assert result['status'] == 'error'
    assert 'analyze_data_with_python' in result['tools_used']
```

### Manual Testing Checklist

- [ ] Standard upload → Ask "show top 10 wards" → Verify agent executes Python
- [ ] Post-TPR → Ask "which wards have TPR > 0.5" → Verify agent uses raw_data.csv
- [ ] Post-risk → Ask "show highest risk wards" → Verify agent uses unified_dataset.csv
- [ ] Pre-built tool request → Ask "run risk analysis" → Verify uses pre-built tool
- [ ] Error case → Invalid session → Verify graceful error handling
- [ ] Shapefile queries → Ask "show map of wards" → Verify gdf loaded

---

## Deployment Plan

### Development Environment (Local)

**Day 1** (2-3 hours):
1. Create `data_exploration_agent.py`
2. Implement CSV loading logic
3. Test locally with sample data
4. Verify inheritance from DataAnalysisAgent works

**Day 2** (1-2 hours):
1. Add tool to `request_interpreter.py`
2. Test tool registration
3. Test tool execution via RI
4. Run unit tests

**Day 3** (1 hour):
1. Integration testing
2. Test LLM tool selection
3. Fix any bugs

### Staging Deployment

**Backup First**:
```bash
# SSH to staging
ssh -i /tmp/chatmrpt-key2.pem ec2-user@18.117.115.217

# Backup current code
tar -czf ChatMRPT_pre_agent_tool_$(date +%Y%m%d_%H%M%S).tar.gz \
    ChatMRPT/app/core/request_interpreter.py \
    ChatMRPT/app/data_analysis_v3/
```

**Deploy**:
```bash
# Copy new files
scp -i /tmp/chatmrpt-key2.pem \
    app/data_analysis_v3/core/data_exploration_agent.py \
    ec2-user@18.117.115.217:~/ChatMRPT/app/data_analysis_v3/core/

scp -i /tmp/chatmrpt-key2.pem \
    app/core/request_interpreter.py \
    ec2-user@18.117.115.217:~/ChatMRPT/app/core/

# Restart service
ssh -i /tmp/chatmrpt-key2.pem ec2-user@18.117.115.217 \
    'sudo systemctl restart chatmrpt'

# Monitor logs
ssh -i /tmp/chatmrpt-key2.pem ec2-user@18.117.115.217 \
    'sudo journalctl -u chatmrpt -f'
```

**Test Staging**:
1. Upload test data
2. Send query: "Show me top 10 wards by population"
3. Verify agent tool is called
4. Check logs for any errors

### Production Deployment

**CRITICAL**: Deploy to BOTH production instances

**Production Instances**:
- Instance 1: `i-0994615951d0b9563` (3.21.167.170)
- Instance 2: `i-0f3b25b72f18a5037` (18.220.103.20)

**Backup First**:
```bash
# Backup both instances
for ip in 3.21.167.170 18.220.103.20; do
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$ip \
        "tar -czf ChatMRPT_pre_agent_tool_\$(date +%Y%m%d_%H%M%S).tar.gz \
         ChatMRPT/app/core/request_interpreter.py \
         ChatMRPT/app/data_analysis_v3/"
done
```

**Deploy to Both**:
```bash
# Deploy to all production instances
for ip in 3.21.167.170 18.220.103.20; do
    echo "Deploying to $ip..."

    # Copy files
    scp -i /tmp/chatmrpt-key2.pem \
        app/data_analysis_v3/core/data_exploration_agent.py \
        ec2-user@$ip:~/ChatMRPT/app/data_analysis_v3/core/

    scp -i /tmp/chatmrpt-key2.pem \
        app/core/request_interpreter.py \
        ec2-user@$ip:~/ChatMRPT/app/core/

    # Restart service
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$ip \
        'sudo systemctl restart chatmrpt'

    echo "✅ Deployed to $ip"
done
```

**Verify Production**:
```bash
# Check both instances are running
for ip in 3.21.167.170 18.220.103.20; do
    echo "Checking $ip..."
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$ip \
        'sudo systemctl status chatmrpt | head -10'
done
```

---

## Rollback Procedure

If anything goes wrong:

**Step 1: Revert RequestInterpreter**
```bash
# On affected instance
ssh -i /tmp/chatmrpt-key2.pem ec2-user@<IP>

# Restore from backup
cd ~/
tar -xzf ChatMRPT_pre_agent_tool_<timestamp>.tar.gz
cp ChatMRPT/app/core/request_interpreter.py \
   ChatMRPT_current/app/core/
```

**Step 2: Remove Agent File**
```bash
rm ~/ChatMRPT/app/data_analysis_v3/core/data_exploration_agent.py
```

**Step 3: Restart**
```bash
sudo systemctl restart chatmrpt
```

**Step 4: Verify**
```bash
sudo journalctl -u chatmrpt -f
# Check that system is working
```

**Recovery Time**: < 5 minutes

---

## Success Metrics

### Week 1 (Post-Deployment)
- [ ] Tool registered successfully (19 tools shown in logs)
- [ ] Agent tool called at least once per day
- [ ] No errors in agent execution
- [ ] Response times < 10 seconds for simple queries

### Month 1 (Adoption)
- [ ] Agent tool handles 10-20% of all queries
- [ ] User satisfaction maintained (no complaints)
- [ ] Zero critical errors from agent tool
- [ ] Identify which pre-built tools are now redundant

### Month 3 (Growth)
- [ ] Agent tool handles 40-60% of all queries
- [ ] Users prefer agent for custom queries
- [ ] Pre-built tools still used for complex workflows
- [ ] Plan deprecation of redundant simple tools

### Month 6 (Maturity)
- [ ] Agent tool handles 70-80% of all queries
- [ ] Deprecate redundant simple tools (SQL query, box plots, etc.)
- [ ] Keep only complex tools (risk analysis, ITN planning)
- [ ] Agent is proven reliable

---

## Tool Usage Tracking

**Add logging to track which tools are called**:

```python
# In request_interpreter.py
def _track_tool_usage(self, tool_name: str, session_id: str):
    """Track tool usage for metrics."""
    try:
        import json
        from datetime import datetime

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'tool_name': tool_name
        }

        # Append to metrics file
        with open('instance/tool_usage_metrics.jsonl', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        logger.debug(f"Failed to track tool usage: {e}")
```

**Analysis script** (`scripts/analyze_tool_usage.py`):
```python
import json
import pandas as pd
from collections import Counter

# Read metrics
with open('instance/tool_usage_metrics.jsonl') as f:
    data = [json.loads(line) for line in f]

df = pd.DataFrame(data)

# Count tool usage
tool_counts = Counter(df['tool_name'])

print("Tool Usage Statistics:")
print("=" * 50)
for tool, count in tool_counts.most_common():
    percentage = (count / len(df)) * 100
    print(f"{tool}: {count} ({percentage:.1f}%)")

# Agent vs pre-built tools
agent_count = tool_counts.get('analyze_data_with_python', 0)
total = len(df)
print(f"\nAgent handles: {agent_count}/{total} ({agent_count/total*100:.1f}%)")
```

---

## Evolution Path

### Phase 1: Introduction (Week 1)
```
Agent = Tool #19
Usage: 5-10% of queries
Status: Experimental
```

### Phase 2: Early Adoption (Months 1-2)
```
Agent usage grows to 30-40%
LLM learns when to use agent vs pre-built tools
Users start to prefer agent for custom queries
```

### Phase 3: Majority (Months 3-4)
```
Agent handles 60-70% of queries
Identify redundant pre-built tools:
  - execute_sql_query (agent can do this)
  - create_box_plot (agent can do this)
  - create_variable_distribution (agent can do this)
```

### Phase 4: Optimization (Months 5-6)
```
Deprecate redundant simple tools
Keep only complex tools:
  - run_malaria_risk_analysis
  - run_itn_planning
  - explain_analysis_methodology

Agent = Primary execution engine (80-90% of queries)
Pre-built tools = Specialized complex workflows (10-20%)
```

### Phase 5: Mature State (Year 1+)
```
RequestInterpreter evolved:
  - Orchestrator (routing, session management)
  - Agent tool (handles 90% of queries)
  - Complex tools (handles 10% specialized workflows)

Total tools: 5-7 (down from 19)
Maintenance effort: Reduced by 60%
Capability: Increased by 10x
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Agent fails to load data | Low | Medium | Graceful error handling, fallback to conversational |
| Agent writes bad Python code | Low | Low | LLM is good at Python, sandbox execution |
| Performance degradation | Low | Low | Agent adds ~1-2s overhead, acceptable for custom queries |
| Tool conflicts (LLM confused) | Medium | Low | Clear tool descriptions, monitor usage patterns |
| Production deployment issues | Low | Medium | Deploy to staging first, backup before production |
| User experience degradation | Low | Medium | Track metrics, rollback if needed |

**Overall Risk**: **Low** ✅

**Mitigation Strategy**: Phased rollout, monitoring, easy rollback.

---

## Questions & Answers

### Q1: Won't 19 tools confuse the LLM?
**A**: No. GPT-4o can handle 100+ tools easily. 19 is well within capacity. Plus, tool descriptions guide LLM to right choice.

### Q2: What if agent is slower than pre-built tools?
**A**: Agent adds ~1-2s overhead (LLM reasoning + code execution). For custom queries, this is acceptable trade-off for flexibility.

### Q3: Can we just remove all simple tools now?
**A**: No. Start with agent as additional option, prove reliability, then deprecate redundant tools gradually.

### Q4: What about streaming support?
**A**: Agent tool works with existing streaming infrastructure. RequestInterpreter already handles tool streaming.

### Q5: What if both instances get out of sync?
**A**: Deploy script ensures both instances updated. ALB will route to working instance if one fails.

### Q6: How do we know which tools to deprecate?
**A**: Track tool usage metrics for 3 months. Tools used < 5% are candidates for deprecation.

---

## Dependencies

### Code Dependencies
- DataAnalysisAgent (already exists in `app/data_analysis_v3/core/agent.py`)
- LangGraph (already installed)
- RequestInterpreter (existing)
- LLMOrchestrator (existing)
- ToolRunner (existing)

### Data Dependencies
- CSV files in `instance/uploads/{session_id}/`
- Shapefiles in `instance/uploads/{session_id}/shapefile/` or `raw_shapefile.zip`
- Flag files: `.tpr_complete`, `.analysis_complete`

### Infrastructure Dependencies
- AWS instances (production: 2 instances)
- Redis (session management)
- File system (session data storage)

---

## Next Steps

### Immediate (This Week)
1. ✅ Review this plan
2. Create `data_exploration_agent.py`
3. Test locally with sample data
4. Add tool to `request_interpreter.py`
5. Run unit tests
6. Deploy to staging

### Short-term (This Month)
1. Deploy to production
2. Monitor usage metrics
3. Gather user feedback
4. Fix any issues
5. Document learnings

### Long-term (Next 3-6 Months)
1. Track tool usage patterns
2. Identify redundant tools
3. Plan deprecation strategy
4. Optimize agent performance
5. Expand agent capabilities

---

## Conclusion

**This is a LOW-RISK, HIGH-VALUE enhancement** that:

✅ Adds Python execution to RequestInterpreter (Tool #19)
✅ Enables custom data queries users can't do today
✅ Requires minimal code changes (~210-260 lines)
✅ Doesn't break any existing functionality
✅ Sets foundation for long-term architecture evolution
✅ Easy to rollback if issues arise

**Strategic Impact**:
- Short-term: Better user experience for custom queries
- Medium-term: Agent handles majority of queries
- Long-term: Simplified architecture, reduced maintenance

**Recommendation**: **PROCEED** with implementation.

---

## Approval Checklist

Before implementation begins:
- [ ] Plan reviewed by technical lead
- [ ] Architecture approach approved
- [ ] Timeline acceptable
- [ ] Risk assessment reviewed
- [ ] Rollback procedure understood
- [ ] Success metrics agreed
- [ ] Resource allocation confirmed

**Once approved, proceed to implementation.**

---

## Contact & Support

**Implementation Questions**: Review code comments in created files
**Deployment Issues**: Check rollback procedure above
**Monitoring**: Check `sudo journalctl -u chatmrpt -f` on instances
**Metrics**: Run `python scripts/analyze_tool_usage.py` after Week 1

**Ready for Review!** 🚀
