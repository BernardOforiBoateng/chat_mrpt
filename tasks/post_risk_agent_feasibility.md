# Post-Risk Analysis Agent - Feasibility Investigation

**Date**: October 4, 2025
**Investigator**: Claude
**Status**: ✅ HIGHLY FEASIBLE - Minor Changes Required

---

## Executive Summary

**Goal**: Create a second LangGraph agent (similar to DataAnalysisAgent) that:
1. Activates AFTER risk analysis completes (`.analysis_complete` flag exists)
2. Has access to `unified_dataset.csv` (master file with rankings) AND shapefile
3. Handles any ad-hoc queries outside the standard workflow
4. Uses same proven LangGraph architecture

**Verdict**: **HIGHLY FEASIBLE** with minimal architectural changes

---

## Current Architecture Analysis

### Phase 1: DataAnalysisAgent (TPR Workflow)
**Location**: `app/data_analysis_v3/core/agent.py` (851 lines)

**Capabilities**:
- LangGraph orchestrator with OpenAI gpt-4o
- Python execution tool (`analyze_data`)
- TPR analysis tool (`analyze_tpr_data`)
- File-based state management

**Data Access** (Lines 176-223):
```python
# Loads CSV from these patterns (IN ORDER):
1. data_analysis.csv
2. raw_data.csv
3. unified_dataset.csv  # ← Already checks for this!
4. uploaded_data.csv
```

**Current Limitation**: NO shapefile access (only CSV)

### Phase 2-3: RequestInterpreter (Risk & ITN)
**Location**: `app/core/request_interpreter.py`

**Capabilities**:
- Simple state machine (deterministic routing)
- Calls tools directly (no LLM)
- File validation only

**Data Access**:
- Reads flag files (`.analysis_complete`, `.risk_ready`)
- Loads CSVs but can't query them intelligently
- NO conversational ability

---

## Key Files and Data Flow

### Critical Data Files
```
instance/uploads/{session_id}/
├── Phase 1: TPR Workflow
│   ├── uploaded_data.csv (user upload)
│   ├── tpr_results.csv (TPR calculations)
│   ├── .tpr_complete (flag)
│   └── raw_shapefile.zip ⭐ CREATED HERE (line 1110-1126 of tpr_analysis_tool.py)
│
├── Phase 1→2 Transition
│   ├── raw_data.csv (TPR + environmental variables)
│   └── .risk_ready (flag)
│
├── Phase 2: Risk Analysis
│   ├── unified_dataset.csv ⭐ MASTER FILE (all data + rankings)
│   │   - Original columns preserved
│   │   - composite_rank (1 = highest risk)
│   │   - pca_rank
│   │   - overall_rank
│   ├── vulnerability_map_composite.html
│   ├── vulnerability_map_pca.html
│   └── .analysis_complete ⭐ ACTIVATION FLAG
│
└── Phase 3: ITN Planning
    ├── itn_distribution_plan.csv
    └── itn_allocation_map.html
```

### Shapefile Creation
**Location**: `app/data_analysis_v3/tpr_analysis_tool.py:1110-1126`

```python
# Create raw_shapefile.zip
logger.info("📦 Creating shapefile package...")
try:
    # Ensure shapefile has same columns as CSV
    for col in final_df.columns:
        if col not in merged_gdf.columns:
            merged_gdf[col] = final_df[col]

    shapefile_path = create_shapefile_package(merged_gdf, session_folder)
    logger.info(f"✅ Created raw_shapefile.zip")
```

**Key Insight**: Shapefile is already created during TPR phase! We just need to load it.

---

## Proposed Solution: PostRiskAgent

### 1. Architecture (95% Same as DataAnalysisAgent)

**New File**: `app/data_analysis_v3/core/post_risk_agent.py` (~600 lines)

**Components to Replicate**:
```python
class PostRiskAgent:
    """
    LangGraph agent for post-risk analysis queries.
    Activates AFTER .analysis_complete flag is set.
    Has access to unified_dataset.csv + shapefile.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id

        # Same LLM setup as DataAnalysisAgent
        self.llm = ChatOpenAI(
            model="gpt-4o",
            api_key=os.environ.get('OPENAI_API_KEY'),
            temperature=0.7,
            max_tokens=2000,
            timeout=50
        )

        # NEW: Tools for post-risk queries
        self.tools = [
            analyze_data,           # Python execution (reuse existing)
            query_unified_data,     # NEW: SQL queries on unified_dataset
            visualize_variable,     # NEW: Choropleth maps
            export_filtered_data    # NEW: Export subsets
        ]

        # Same graph structure
        self.graph = self._build_graph()
```

### 2. Key Differences from DataAnalysisAgent

| Component | DataAnalysisAgent | PostRiskAgent |
|-----------|-------------------|---------------|
| **Activation** | After upload, before workflow | After `.analysis_complete` flag |
| **CSV File** | `uploaded_data.csv`, `raw_data.csv` | `unified_dataset.csv` (master) |
| **Shapefile** | ❌ None | ✅ `raw_shapefile.zip` |
| **System Prompt** | "TPR workflow assistant" | "Risk analysis assistant" |
| **Tools** | `analyze_data`, `analyze_tpr_data` | `analyze_data`, `query_unified_data`, `visualize_variable` |
| **Use Cases** | TPR workflow navigation | Ad-hoc queries, custom visualizations |

### 3. Data Loading Changes

**Current** (`agent.py:176-223`):
```python
def _get_input_data(self) -> List[Dict[str, Any]]:
    """Load uploaded data and prepare for agent."""
    file_patterns = [
        'data_analysis.csv',
        'raw_data.csv',
        'unified_dataset.csv',  # ← Already here!
        'uploaded_data.csv'
    ]
    # Load first match...
```

**New** (`post_risk_agent.py`):
```python
def _get_input_data(self) -> List[Dict[str, Any]]:
    """Load unified dataset + shapefile for post-risk queries."""
    input_data_list = []
    session_folder = f"instance/uploads/{self.session_id}"

    # 1. Load unified_dataset.csv (REQUIRED)
    csv_path = os.path.join(session_folder, 'unified_dataset.csv')
    if not os.path.exists(csv_path):
        raise FileNotFoundError("unified_dataset.csv not found. Risk analysis must complete first.")

    df = EncodingHandler.read_csv_with_encoding(csv_path)

    # 2. Load shapefile (OPTIONAL but recommended)
    shapefile_path = os.path.join(session_folder, 'raw_shapefile.zip')
    gdf = None
    if os.path.exists(shapefile_path):
        import geopandas as gpd
        gdf = gpd.read_file(f"zip://{shapefile_path}")
        logger.info(f"✅ Loaded shapefile with {len(gdf)} features")
    else:
        logger.warning("⚠️ Shapefile not found - spatial queries unavailable")

    # 3. Prepare data object
    data_obj = {
        'variable_name': 'df',
        'data_description': f"Unified dataset with {len(df)} wards, {len(df.columns)} columns (includes TPR, environmental data, and risk rankings)",
        'data': df,
        'columns': df.columns.tolist(),
        'shapefile': gdf,  # NEW: Include shapefile
        'has_rankings': all(col in df.columns for col in ['composite_rank', 'pca_rank', 'overall_rank'])
    }

    input_data_list.append(data_obj)
    return input_data_list
```

### 4. System Prompt Changes

**Current** (`prompts/system_prompt.py`):
```python
MAIN_SYSTEM_PROMPT = """
## Role
You are a data analysis assistant specializing in malaria data and TPR (Test Positivity Rate) analysis.
...
```

**New** (`prompts/post_risk_system_prompt.py`):
```python
POST_RISK_SYSTEM_PROMPT = """
## Role
You are a malaria risk analysis assistant with access to completed risk assessment data.

## Available Data
- **unified_dataset.csv**: Complete ward-level data with:
  - Original TPR data (Total_Tested, Total_Positive, TPR)
  - Environmental variables (rainfall, NDWI, NDMI, soil_wetness, EVI, elevation, etc.)
  - Risk rankings:
    - `composite_rank` (1 = highest risk, equal-weighted scoring)
    - `pca_rank` (PCA-based ranking)
    - `overall_rank` (average of both methods)
- **Shapefile**: Geographic boundaries for spatial queries and mapping

## Core Capabilities
1. **Query Rankings**: "Show me top 10 high-risk wards"
2. **Filter Data**: "Which wards have TPR > 15% and composite_rank < 20?"
3. **Custom Visualizations**: "Create a map of rainfall distribution"
4. **Statistical Analysis**: "What's the correlation between TPR and elevation?"
5. **Export Subsets**: "Export wards in top 50 composite_rank as CSV"

## Tools Available
- `analyze_data`: Execute Python code (pandas, numpy, plotly)
- `query_unified_data`: SQL queries on the dataset
- `visualize_variable`: Create choropleth maps for any variable
- `export_filtered_data`: Export filtered subsets

## Important Notes
- Risk analysis is COMPLETE - all rankings are final
- You can answer ANY question about the data
- Always check column names with df.columns before querying
- Shapefile enables spatial queries (if available)
```

### 5. Integration Point (Routing Logic)

**Where to Add**: `app/web/routes/data_analysis_v3_routes.py:665-681`

**Current**:
```python
else:
    # NO WORKFLOW ACTIVE → Pure agent
    logger.info(f"[BRIDGE] No TPR workflow → Routing to pure Agent")

    from app.data_analysis_v3.core.agent import DataAnalysisAgent
    agent = DataAnalysisAgent(session_id)

    async def run_analysis():
        return await agent.analyze(message)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(run_analysis())
        return jsonify(result)
    finally:
        loop.close()
```

**New** (ADD BEFORE above block):
```python
# ============================================================
# NEW: Check if risk analysis is complete
# ============================================================
import os
analysis_complete_flag = os.path.join(f"instance/uploads/{session_id}", '.analysis_complete')
unified_dataset_path = os.path.join(f"instance/uploads/{session_id}", 'unified_dataset.csv')

if os.path.exists(analysis_complete_flag) and os.path.exists(unified_dataset_path):
    # Risk analysis complete → Use PostRiskAgent
    logger.info(f"[BRIDGE] Risk analysis complete → Routing to PostRiskAgent")

    from app.data_analysis_v3.core.post_risk_agent import PostRiskAgent
    agent = PostRiskAgent(session_id)

    async def run_post_risk_analysis():
        return await agent.analyze(message)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(run_post_risk_analysis())
        return jsonify(result)
    finally:
        loop.close()
else:
    # NO WORKFLOW ACTIVE → Pure DataAnalysisAgent
    logger.info(f"[BRIDGE] No TPR workflow → Routing to pure Agent")
    # ... existing code ...
```

---

## Required New Tools

### 1. Query Unified Data Tool
**File**: `app/data_analysis_v3/tools/query_unified_data_tool.py`

```python
@tool
def query_unified_data(
    graph_state: Annotated[dict, InjectedState],
    sql_query: str
) -> str:
    """
    Execute SQL query on unified_dataset.csv using DuckDB.

    Args:
        sql_query: SQL query (e.g., "SELECT * FROM df WHERE composite_rank < 10 ORDER BY TPR DESC")

    Returns:
        Query results as formatted string
    """
    import duckdb

    # Get dataframe from state
    df = graph_state['input_data'][0]['data']

    # Execute query
    result = duckdb.query(sql_query).to_df()

    return result.to_string()
```

### 2. Visualize Variable Tool
**File**: `app/data_analysis_v3/tools/visualize_variable_tool.py`

```python
@tool
def visualize_variable(
    graph_state: Annotated[dict, InjectedState],
    variable: str,
    title: str = None
) -> Dict[str, Any]:
    """
    Create choropleth map for any variable in unified_dataset.

    Args:
        variable: Column name to visualize (e.g., 'TPR', 'composite_rank', 'rainfall')
        title: Optional custom title

    Returns:
        Visualization info with web_path
    """
    import folium
    import geopandas as gpd

    session_id = graph_state['session_id']
    gdf = graph_state['input_data'][0]['shapefile']
    df = graph_state['input_data'][0]['data']

    # Merge data with shapefile
    merged = gdf.merge(df, on='WardCode')

    # Create choropleth
    # ... (similar to existing visualization code)

    return {
        'web_path': f'/static/visualizations/{filename}',
        'title': title or f'{variable} Distribution'
    }
```

---

## Feasibility Assessment

### ✅ What Makes This Easy

1. **Proven Architecture**: DataAnalysisAgent already works perfectly
   - LangGraph setup proven
   - OpenAI gpt-4o integration tested
   - Python tool execution working
   - State management solid

2. **Data Already Available**:
   - `unified_dataset.csv` created by risk analysis ✅
   - `raw_shapefile.zip` created during TPR phase ✅
   - Flag files (`.analysis_complete`) already in place ✅

3. **Minimal Code Changes**:
   - ~600 lines for PostRiskAgent (copy-paste 80% from DataAnalysisAgent)
   - ~150 lines for new tools (query_unified_data, visualize_variable)
   - ~30 lines routing logic in data_analysis_v3_routes.py
   - **Total: ~780 new lines of code**

4. **No Breaking Changes**:
   - Doesn't affect existing workflow
   - Only activates AFTER risk analysis complete
   - Falls back to DataAnalysisAgent if no unified_dataset

### ⚠️ Minor Challenges

1. **Shapefile Loading**:
   - Need to add `import geopandas as gpd`
   - Handle case where shapefile doesn't exist
   - **Solution**: Make shapefile optional, gracefully degrade

2. **Tool Registration**:
   - Need to create 2 new LangChain tools
   - **Solution**: Follow exact pattern from `python_tool.py`

3. **System Prompt Tuning**:
   - Need different prompt for post-risk queries
   - **Solution**: Create separate `POST_RISK_SYSTEM_PROMPT`

4. **Testing**:
   - Need to test with actual unified_dataset.csv
   - **Solution**: Use existing test sessions from production

---

## File Structure

```
app/data_analysis_v3/
├── core/
│   ├── agent.py (existing - 851 lines)
│   ├── post_risk_agent.py (NEW - ~600 lines) ⭐
│   ├── state.py (existing)
│   └── ...
├── tools/
│   ├── python_tool.py (existing)
│   ├── tpr_analysis_tool.py (existing)
│   ├── query_unified_data_tool.py (NEW - ~100 lines) ⭐
│   └── visualize_variable_tool.py (NEW - ~150 lines) ⭐
├── prompts/
│   ├── system_prompt.py (existing)
│   └── post_risk_system_prompt.py (NEW - ~80 lines) ⭐
└── ...

app/web/routes/
└── data_analysis_v3_routes.py (MODIFY - add ~30 lines) ⭐
```

**Total New Files**: 3
**Modified Files**: 1
**Total New Code**: ~860 lines

---

## Use Cases Enabled

Once PostRiskAgent is implemented, users can ask:

### 1. Ranking Queries
- "Show me the top 20 highest risk wards"
- "Which wards are ranked below 50 in composite scoring?"
- "Compare composite_rank and pca_rank - which wards differ the most?"

### 2. Data Filtering
- "Find all wards with TPR > 15% AND composite_rank < 30"
- "Show me high-risk wards in Kumbotso LGA"
- "Which wards have high rainfall but low TPR?"

### 3. Custom Visualizations
- "Create a map showing rainfall distribution"
- "Visualize the relationship between elevation and TPR"
- "Show me a choropleth of NDWI values"

### 4. Statistical Analysis
- "What's the correlation between environmental variables and TPR?"
- "Run PCA on just the environmental variables"
- "Calculate summary statistics for top 50 ranked wards"

### 5. Export and Download
- "Export top 100 wards as CSV"
- "Give me an Excel file with wards ranked 1-50"
- "Download shapefile filtered to composite_rank < 100"

---

## Implementation Complexity

### Estimation

| Task | Complexity | Time Estimate | Risk Level |
|------|-----------|---------------|------------|
| Create PostRiskAgent class | Low | 2-3 hours | 🟢 Low |
| Implement data loading (CSV + shapefile) | Low | 1 hour | 🟢 Low |
| Create query_unified_data tool | Low | 1 hour | 🟢 Low |
| Create visualize_variable tool | Medium | 2 hours | 🟡 Medium |
| Write POST_RISK_SYSTEM_PROMPT | Low | 30 min | 🟢 Low |
| Add routing logic | Low | 30 min | 🟢 Low |
| Testing with real data | Medium | 2 hours | 🟡 Medium |
| Bug fixes and refinement | Medium | 2 hours | 🟡 Medium |

**Total Estimated Time**: 11-12 hours (1.5 days)

### Risk Mitigation

1. **Testing Strategy**:
   - Test with existing production sessions that have `unified_dataset.csv`
   - Start with CSV-only (no shapefile) to ensure basic functionality
   - Add shapefile support incrementally

2. **Fallback Plan**:
   - If PostRiskAgent fails, fall back to DataAnalysisAgent
   - Graceful degradation if shapefile missing

3. **Incremental Rollout**:
   - Phase 1: CSV queries only (SQL tool)
   - Phase 2: Add Python tool
   - Phase 3: Add shapefile support and visualizations

---

## Recommended Approach

### Option A: Separate PostRiskAgent (RECOMMENDED ✅)
**Pros**:
- Clean separation of concerns
- Easy to maintain and debug
- Can evolve independently
- No risk to existing DataAnalysisAgent

**Cons**:
- ~600 lines of duplicated code
- Need to keep both agents in sync for core features

### Option B: Extend DataAnalysisAgent with Modes
**Pros**:
- Single codebase
- Reuse all existing code

**Cons**:
- Makes agent.py even larger (1400+ lines)
- Complexity in mode switching
- Higher risk of breaking existing functionality

### Option C: Create UnifiedConversationalAgent
**Pros**:
- Single agent handles entire lifecycle
- Most elegant solution long-term

**Cons**:
- Major architectural change
- High risk
- 3-4 days of work

**Verdict**: **Option A (Separate PostRiskAgent)** is the best balance of:
- Low risk
- Fast implementation
- Clean architecture
- Easy rollback if needed

---

## Placement Decision

### Recommended Location
```
app/data_analysis_v3/core/post_risk_agent.py
```

### Rationale
1. **Consistent Structure**: Matches existing `agent.py` location
2. **Logical Grouping**: Part of Data Analysis V3 module
3. **Import Clarity**: Easy to import alongside DataAnalysisAgent
4. **Discoverability**: Developers know where to find it

### Alternative Considered
```
app/core/post_risk_agent.py
```
- ❌ Breaks consistency (all agents should be in data_analysis_v3/)
- ❌ Harder to find
- ❌ Doesn't leverage existing infrastructure

---

## Next Steps (If Approved)

1. **Create Plan** (30 min)
   - Detailed task breakdown in `tasks/todo.md`
   - Define acceptance criteria

2. **Create PostRiskAgent** (3 hours)
   - Copy agent.py structure
   - Modify data loading for unified_dataset + shapefile
   - Update system prompt

3. **Create Tools** (3 hours)
   - `query_unified_data_tool.py`
   - `visualize_variable_tool.py`

4. **Add Routing** (30 min)
   - Modify `data_analysis_v3_routes.py`
   - Add flag detection logic

5. **Testing** (4 hours)
   - Test with production sessions
   - Verify CSV loading
   - Test shapefile integration
   - Validate visualizations

6. **Documentation** (1 hour)
   - Update `CLAUDE.md`
   - Add docstrings
   - Create usage examples

**Total**: ~12 hours (1.5 days)

---

## Conclusion

✅ **HIGHLY FEASIBLE**

Creating a PostRiskAgent is:
- **Low Risk**: Proven architecture, no breaking changes
- **Fast**: 1.5 days of focused work
- **High Value**: Enables powerful ad-hoc queries after risk analysis
- **Clean**: Separate agent maintains code clarity

The architecture is sound, the data is already available, and the implementation follows established patterns. This is a straightforward extension of the existing system with minimal complexity.

**Recommendation**: Proceed with implementation using Option A (Separate PostRiskAgent).
