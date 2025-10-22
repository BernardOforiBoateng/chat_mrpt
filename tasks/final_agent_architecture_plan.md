# Final Architecture Plan: DataExplorationAgent Integration

**Date**: 2025-10-04
**Status**: Deep Analysis Complete
**Recommendation**: PROCEED with careful integration

---

## Executive Summary

After deep analysis of RequestInterpreter and current routing, here's the safest integration plan:

**✅ Create `DataExplorationAgent` as PARALLEL PATH to RequestInterpreter, NOT as replacement**

**Key Insight**: RequestInterpreter and DataExplorationAgent serve DIFFERENT purposes:
- **Request Interpreter**: Pre-built tools + orchestration (risk analysis, ITN planning, visualizations)
- **DataExplorationAgent**: Conversational data queries (Python execution, custom analysis)

They are **complementary**, not competitive.

---

## Current Architecture (DETAILED)

### Routing Flow (analysis_routes.py line 831-895)

```python
User Message
    ↓
┌─────────────────────────────────────────────────────┐
│ 1. Check if use_tools + use_data_analysis_v3        │
│    YES → DataAnalysisAgent (TPR workflow)           │
│    NO  → Continue to step 2                         │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ 2. Otherwise → RequestInterpreter                   │
│    - process_message()                              │
│    - Calls tools via orchestrator + tool_runner     │
│    - Returns tool results                           │
└─────────────────────────────────────────────────────┘
```

### RequestInterpreter Responsibilities (CRITICAL - DO NOT BREAK)

**1. Tool Registry** (18 tools):
- `run_malaria_risk_analysis` - Dual-method analysis
- `run_itn_planning` - ITN distribution
- `create_vulnerability_map` - Choropleth maps
- `create_box_plot`, `create_pca_map`, `create_variable_distribution`
- `create_urban_extent_map`, `create_decision_tree`, `create_composite_score_maps`
- `create_settlement_map`, `show_settlement_statistics`
- `execute_data_query`, `execute_sql_query`, `run_data_quality_check`
- `explain_analysis_methodology`

**2. Orchestration Components**:
- `tool_runner` - Executes tools, builds function schemas
- `orchestrator` - LLM tool calling loop
- `prompt_builder` - System prompt construction
- `context_service` - Session context management
- `data_repo` - Data repository access

**3. Special Workflows**:
- Permission workflows
- Fork detection
- Data upload handling
- Conversational fallback (no data loaded)

**4. Session Management**:
- Loads CSV data into memory
- Checks flags (`.analysis_complete`, `.risk_ready`, etc.)
- Updates session state

**5. Streaming Support**:
- `process_message_streaming()` - Server-sent events
- Tool execution with streaming responses

### Why We CANNOT Deprecate RequestInterpreter

1. **Essential Tool Execution**: All pre-built analysis tools live here
2. **Complex Orchestration**: Manages LLM → tool selection → execution loop
3. **Session State**: Handles data loading, context building
4. **Streaming**: Critical for UX
5. **Special Workflows**: Permission handling, forks, etc.

---

## Proposed Architecture (SAFE INTEGRATION)

### New Routing Flow

```python
User Message
    ↓
analysis_routes.py (line ~831)
    ↓
┌─────────────────────────────────────────────────────┐
│ Step 1: Determine Routing Path                      │
│                                                      │
│ Check flags:                                        │
│ - use_data_analysis_v3                              │
│ - upload_type                                       │
│ - .tpr_complete                                     │
│ - csv_loaded + shapefile_loaded                     │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Path A: TPR Workflow (EXISTING)                     │
│                                                      │
│ If: use_data_analysis_v3 AND NOT .tpr_complete      │
│   → DataAnalysisAgent                               │
│   → TPR workflow with analyze_tpr_data tool         │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Path B: Data Exploration (NEW) ✨                   │
│                                                      │
│ If: Standard upload OR Post-TPR OR Post-Risk        │
│   Conditions:                                       │
│   - upload_type == 'csv_shapefile' AND data_loaded  │
│   - .tpr_complete exists                            │
│   - .analysis_complete exists                       │
│                                                      │
│   → DataExplorationAgent                            │
│   → Conversational queries with Python execution    │
│   → Can call RequestInterpreter tools if needed     │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Path C: Tool-Based Analysis (EXISTING)              │
│                                                      │
│ If: None of the above                               │
│   → RequestInterpreter                              │
│   → Pre-built tools                                 │
│   → Complex orchestration                           │
└─────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Create DataExplorationAgent

**File**: `app/data_analysis_v3/core/data_exploration_agent.py`

**Structure**:
```python
from .agent import DataAnalysisAgent

class DataExplorationAgent(DataAnalysisAgent):
    """
    Conversational data exploration agent.

    Handles:
    - Standard uploads (csv_shapefile)
    - Post-TPR queries
    - Post-risk queries

    Capabilities:
    - Python code execution on DataFrames
    - Geospatial queries on GeoDataFrames
    - Custom visualizations
    - Can call RequestInterpreter tools when needed
    """

    def __init__(self, session_id: str):
        super().__init__(session_id)
        # All LangGraph setup inherited

    def _get_input_data(self) -> List[Dict[str, Any]]:
        """
        ENHANCED: Load CSV + shapefile based on workflow phase.

        Priority:
        1. Post-risk: unified_dataset.csv
        2. Post-TPR: raw_data.csv
        3. Standard upload: raw_data.csv
        """
        input_data_list = []
        session_folder = f"instance/uploads/{self.session_id}"

        # Determine CSV file
        csv_file = self._determine_csv_file(session_folder)
        if csv_file and os.path.exists(csv_file):
            df = EncodingHandler.read_csv_with_encoding(csv_file)
            input_data_list.append({
                'variable_name': 'df',
                'data_description': f"Dataset with {len(df)} rows",
                'data': df,
                'columns': df.columns.tolist()
            })

        # Load shapefile if exists
        shapefile = self._find_shapefile(session_folder)
        if shapefile:
            gdf = gpd.read_file(shapefile)
            input_data_list.append({
                'variable_name': 'gdf',
                'data_description': f"Geospatial data with {len(gdf)} features",
                'data': gdf,
                'columns': gdf.columns.tolist(),
                'is_spatial': True
            })

        return input_data_list

    def _determine_csv_file(self, session_folder: str) -> Optional[str]:
        """Determine which CSV to load based on flags."""

        # Post-risk: unified_dataset.csv
        if os.path.exists(f"{session_folder}/.analysis_complete"):
            unified = f"{session_folder}/unified_dataset.csv"
            if os.path.exists(unified):
                logger.info("📊 Loading unified_dataset.csv (Post-Risk)")
                return unified

        # Post-TPR or standard upload: raw_data.csv
        raw_data = f"{session_folder}/raw_data.csv"
        if os.path.exists(raw_data):
            if os.path.exists(f"{session_folder}/.tpr_complete"):
                logger.info("📊 Loading raw_data.csv (Post-TPR)")
            else:
                logger.info("📊 Loading raw_data.csv (Standard Upload)")
            return raw_data

        # Fallback
        uploaded = f"{session_folder}/uploaded_data.csv"
        if os.path.exists(uploaded):
            logger.info("📊 Loading uploaded_data.csv (Fallback)")
            return uploaded

        return None

    def _find_shapefile(self, session_folder: str) -> Optional[str]:
        """Find shapefile in session folder."""
        # Try raw_shapefile.zip first
        shapefile_zip = f"{session_folder}/raw_shapefile.zip"
        if os.path.exists(shapefile_zip):
            return shapefile_zip

        # Try shapefile directory
        shapefile_dir = f"{session_folder}/shapefile"
        if os.path.exists(shapefile_dir):
            shp_files = glob.glob(f"{shapefile_dir}/*.shp")
            if shp_files:
                return shp_files[0]

        return None
```

**Lines**: ~250

---

### Phase 2: Update Routing Logic

**File**: `app/web/routes/analysis_routes.py` (line ~831-895)

**Current Code**:
```python
elif use_tools and (session.get('use_data_analysis_v3', False) or session.get('data_analysis_active', False)):
    # Route to Data Analysis V3 agent
    agent = DataAnalysisAgent(session_id=session_id)
    result = loop.run_until_complete(agent.analyze(user_message))
else:
    # RequestInterpreter fallback
    response = request_interpreter.process_message(user_message, session_id)
```

**New Code**:
```python
elif use_tools and (session.get('use_data_analysis_v3', False) or session.get('data_analysis_active', False)):
    # ENHANCED ROUTING: Choose between TPR agent and Exploration agent

    session_folder = f"instance/uploads/{session_id}"

    # Detect workflow phase
    tpr_complete = os.path.exists(f"{session_folder}/.tpr_complete")
    analysis_complete = os.path.exists(f"{session_folder}/.analysis_complete")
    has_standard_upload = (
        session.get('upload_type') == 'csv_shapefile' and
        session.get('csv_loaded') and
        session.get('shapefile_loaded')
    )

    # Route to DataExplorationAgent for: Standard uploads, Post-TPR, Post-Risk
    use_exploration_agent = (
        has_standard_upload or
        tpr_complete or
        analysis_complete
    )

    if use_exploration_agent:
        logger.info(f"🔍 Routing to DataExplorationAgent for session {session_id}")
        logger.info(f"   Phase: {'Standard Upload' if has_standard_upload else 'Post-TPR' if tpr_complete and not analysis_complete else 'Post-Risk'}")

        from app.data_analysis_v3.core.data_exploration_agent import DataExplorationAgent
        agent = DataExplorationAgent(session_id=session_id)
    else:
        logger.info(f"🎯 Routing to DataAnalysisAgent (TPR workflow) for session {session_id}")
        from app.data_analysis_v3.core.agent import DataAnalysisAgent
        agent = DataAnalysisAgent(session_id=session_id)

    # Process with chosen agent
    result = loop.run_until_complete(agent.analyze(user_message))

    # Format response...

elif use_tools:
    # RequestInterpreter for non-agent paths
    logger.info(f"🔧 Routing to RequestInterpreter for session {session_id}")
    response = request_interpreter.process_message(
        user_message,
        session_id,
        is_data_analysis=is_data_analysis,
        tab_context=tab_context
    )
else:
    # Arena or other paths...
```

**Lines Changed**: ~40 lines

---

### Phase 3: Agent Can Call RequestInterpreter Tools (Optional Enhancement)

If user asks for something requiring pre-built tools (e.g., "run the risk analysis"), the agent could:

**Option A: Return helpful message**
```
Agent: "I'll run the comprehensive risk analysis for you."
[Agent doesn't have that tool, returns message]
User sees response, clicks button to run analysis
```

**Option B: Add tool wrappers** (Future enhancement)
```python
@tool
def run_risk_analysis(session_id: str):
    """Run the complete malaria risk analysis."""
    from flask import current_app
    ri = current_app.services.request_interpreter
    return ri._run_malaria_risk_analysis(session_id)

class DataExplorationAgent(DataAnalysisAgent):
    def __init__(self, session_id):
        super().__init__(session_id)

        # Add risk analysis tool
        self.tools.append(run_risk_analysis)
```

**Recommendation**: Start with Option A (simple), add Option B later if needed.

---

## Files to Create/Modify

### CREATE:
1. `app/data_analysis_v3/core/data_exploration_agent.py` (~250 lines)
   - Inherits from DataAnalysisAgent
   - Overrides `_get_input_data()`
   - Adds `_determine_csv_file()`, `_find_shapefile()`

2. `app/data_analysis_v3/prompts/data_exploration_system_prompt.py` (~100 lines)
   - Extends base system prompt
   - Adds geospatial awareness
   - Documents available operations

### MODIFY:
1. `app/web/routes/analysis_routes.py` (line ~831-895, ~40 lines changed)
   - Enhanced routing logic
   - Phase detection
   - Agent selection

### NO CHANGES:
1. ✅ `app/core/request_interpreter.py` - **UNTOUCHED**
2. ✅ `app/data_analysis_v3/core/agent.py` - **UNTOUCHED**
3. ✅ All other files - **UNTOUCHED**

---

## Testing Strategy

### Unit Tests
```python
def test_exploration_agent_csv_selection():
    # Test CSV selection logic
    assert agent._determine_csv_file(folder_with_unified) == 'unified_dataset.csv'
    assert agent._determine_csv_file(folder_with_raw) == 'raw_data.csv'

def test_exploration_agent_shapefile_loading():
    # Test shapefile detection
    agent = DataExplorationAgent('test_session')
    data = agent._get_input_data()
    assert any(d['variable_name'] == 'gdf' for d in data)
```

### Integration Tests
```python
def test_standard_upload_routes_to_exploration_agent(client):
    # Upload CSV + shapefile
    upload_both_files(client, 'test.csv', 'test.zip')

    # Send message
    response = client.post('/send_message', json={'message': 'Show top 10 wards'})

    # Verify used DataExplorationAgent
    assert 'DataExplorationAgent' in response.logs
    assert response.json['status'] == 'success'

def test_post_tpr_routes_to_exploration_agent(client):
    # Complete TPR workflow
    complete_tpr_workflow(client)

    # Send message
    response = client.post('/send_message', json={'message': 'Which wards have highest TPR?'})

    # Verify used DataExplorationAgent
    assert 'DataExplorationAgent' in response.logs
```

### Manual Testing Checklist
- [ ] Standard upload → Can query data immediately
- [ ] TPR workflow → Routes to DataAnalysisAgent during TPR
- [ ] Post-TPR → Routes to DataExplorationAgent, can query TPR results
- [ ] Post-risk → Routes to DataExplorationAgent, can query rankings
- [ ] Tool requests → RequestInterpreter still works
- [ ] Edge cases → Missing shapefile, corrupted CSV

---

## Rollback Plan

If anything breaks:

1. **Revert routing change** in `analysis_routes.py`
   ```bash
   git checkout HEAD -- app/web/routes/analysis_routes.py
   ```

2. **Remove new agent file** (doesn't affect existing code)
   ```bash
   rm app/data_analysis_v3/core/data_exploration_agent.py
   ```

3. **Restart server**
   ```bash
   sudo systemctl restart chatmrpt
   ```

System returns to current state. Zero risk.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Routing logic breaks | Low | High | Comprehensive testing, easy rollback |
| Agent fails to load data | Medium | Medium | Graceful error handling, fallback to RI |
| Conflicts with RI | Low | High | They're parallel paths, no overlap |
| Performance degradation | Low | Low | Agent uses same LangGraph pattern |
| Session flag issues | Medium | Medium | Flag detection is simple, well-tested |

**Overall Risk**: **LOW** ✅

---

## Timeline

**Day 1 (2-3 hours)**:
- Create `data_exploration_agent.py`
- Test locally with sample data
- Verify CSV + shapefile loading

**Day 2 (1-2 hours)**:
- Update routing in `analysis_routes.py`
- Add logging for debugging
- Local integration testing

**Day 3 (1-2 hours)**:
- Deploy to staging
- End-to-end testing
- Performance monitoring

**Day 4 (1 hour)**:
- Deploy to production
- Monitor logs
- User testing

**Total**: 5-8 hours

---

## Success Criteria

✅ **Standard uploads** get conversational data access immediately
✅ **Post-TPR** users can query TPR results naturally
✅ **Post-risk** users can explore rankings and plan ITN
✅ **RequestInterpreter** continues to work unchanged
✅ **TPR workflow** continues to work unchanged
✅ **No breaking changes** to existing functionality
✅ **Performance** remains same or improves

---

## Conclusion

**PROCEED with this plan** ✅

This is a **safe, minimal integration** that:
- Adds massive value (conversational data exploration)
- Doesn't touch RequestInterpreter (zero risk to existing tools)
- Uses proven pattern (inherits from DataAnalysisAgent)
- Easy to test and rollback
- Clear separation of concerns

**RequestInterpreter** remains essential for pre-built tools and orchestration.
**DataExplorationAgent** adds conversational flexibility.

They complement each other perfectly.

---

## Next Steps

1. ✅ Review this plan
2. Get approval
3. Create `data_exploration_agent.py`
4. Test locally
5. Update routing
6. Deploy and monitor

**Ready to proceed!** 🚀
