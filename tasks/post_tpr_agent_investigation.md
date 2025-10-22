# Post-TPR Agent Feasibility Investigation

**Date**: 2025-10-04
**Objective**: Investigate feasibility of creating a second LangGraph agent to handle post-TPR requests with access to CSV + shapefile data

---

## Executive Summary

**Verdict: HIGHLY FEASIBLE** ✅

This is a **small architectural enhancement**, not a major rewrite. The infrastructure already exists, and we can replicate the proven TPR agent pattern with minimal changes.

**Estimated Effort**: 2-3 hours implementation + 1 hour testing
**Risk Level**: Low (we're replicating proven code)
**Code Changes**: ~300-400 new lines + ~100 lines modifications

---

## Current Architecture Overview

### Existing Flow

```
User Upload
    ↓
┌─────────────────────────────────────────────────┐
│ UPLOAD PATHS                                     │
│                                                  │
│ 1. Standard Upload (csv_shapefile)              │
│    - Stores: raw_data.csv + raw_shapefile.zip   │
│    - Sets: csv_loaded=True, shapefile_loaded=True│
│    - Goes to: RequestInterpreter (NO agent!)    │
│                                                  │
│ 2. TPR Upload (tpr_excel)                       │
│    - Stores: uploaded_data.csv                  │
│    - Goes to: DataAnalysisAgent (LangGraph)     │
│    - Runs TPR workflow                          │
│    - Creates: raw_data.csv + raw_shapefile.zip  │
│                                                  │
└─────────────────────────────────────────────────┘
    ↓
analysis_routes.py (Flask endpoint)
    ↓
┌─────────────────┐
│ Standard Upload │ → RequestInterpreter (Simple router)
│ (csv_shapefile) │    - NO agent intelligence
│                 │    - Only pre-built tools
│                 │    - raw_data.csv + raw_shapefile.zip exist
│                 │    - NO conversational queries
└─────────────────┘

┌─────────────────┐
│ TPR Phase       │ → DataAnalysisAgent (LangGraph)
│ (Phase 1)       │    - analyze_data (Python tool)
│                 │    - analyze_tpr_data (TPR-specific tool)
└─────────────────┘
    ↓ (.tpr_complete + .risk_ready flags)
    ↓
┌─────────────────┐
│ Post-TPR        │ → RequestInterpreter (Simple router)
│ (Phase 2-3)     │    - Calls tools via _run_malaria_risk_analysis()
│                 │    - Calls tools via _run_itn_planning()
│                 │    - NO access to actual data
│                 │    - raw_data.csv + raw_shapefile.zip exist
└─────────────────┘
```

### Key Files

1. **Current TPR Agent** (`app/data_analysis_v3/core/agent.py`)
   - Lines: 851
   - Tools: `analyze_data`, `analyze_tpr_data`
   - Data access: CSV only (`raw_data.csv`, `uploaded_data.csv`)
   - LLM: OpenAI GPT-4o
   - Framework: LangGraph + LangChain

2. **Request Interpreter** (`app/core/request_interpreter.py`)
   - Lines: 1,600+
   - Role: Simple router/orchestrator
   - Tools: Calls pre-built tools as functions
   - Data access: Only via file paths (no direct DataFrame access)
   - Intelligence: No LLM - just keyword matching

---

## Proposed Architecture

### New Flow

```
User Upload
    ↓
┌─────────────────────────────────────────────────┐
│ UPLOAD PATHS (UNCHANGED)                        │
│                                                  │
│ 1. Standard Upload (csv_shapefile)              │
│    - Stores: raw_data.csv + raw_shapefile.zip   │
│    - Goes to: PostTPRAgent ✨ (NEW!)            │
│                                                  │
│ 2. TPR Upload (tpr_excel)                       │
│    - Stores: uploaded_data.csv                  │
│    - Goes to: DataAnalysisAgent (TPR workflow)  │
│                                                  │
└─────────────────────────────────────────────────┘
    ↓
analysis_routes.py (Flask endpoint)
    ↓
┌─────────────────┐
│ Standard Upload │ → PostTPRAgent ✨ (NEW!)
│ (csv_shapefile) │    - analyze_data (Python tool)
│                 │    - Access to raw_data.csv + raw_shapefile.zip
│                 │    - Conversational queries
│                 │    - Custom analysis
│                 │    - Can call pre-built tools if needed
└─────────────────┘

┌─────────────────┐
│ TPR Phase       │ → DataAnalysisAgent (existing)
│ (Phase 1)       │    - analyze_data (Python tool)
│                 │    - analyze_tpr_data (TPR-specific tool)
└─────────────────┘
    ↓ (.tpr_complete + .risk_ready flags)
    ↓
┌─────────────────┐
│ Post-TPR Phase  │ → PostTPRAgent ✨ (NEW!)
│ (Phase 2)       │    - analyze_data (Python tool - inherited)
│                 │    - Access to raw_data.csv + raw_shapefile.zip
│                 │    - Conversational queries
│                 │    - Custom analysis
│                 │    - Can call run_malaria_risk_analysis if needed
└─────────────────┘
    ↓ (.analysis_complete flag)
    ↓
┌─────────────────┐
│ Post-Risk Phase │ → PostTPRAgent ✨ (same agent, different context)
│ (Phase 3)       │    - analyze_data (Python tool - inherited)
│                 │    - Access to unified_dataset.csv + shapefile
│                 │    - ITN planning queries
│                 │    - Advanced analysis
│                 │    - Can call run_itn_planning if needed
└─────────────────┘
```

**KEY INSIGHT**: The PostTPRAgent serves **THREE use cases**:
1. **Standard Upload** (csv_shapefile) - Immediate conversational access to uploaded data
2. **Post-TPR** (after TPR workflow completes) - Query TPR results + environmental data
3. **Post-Risk** (after risk analysis completes) - Query rankings + plan interventions

---

## Proposed Implementation

### 1. New Agent Class

**File**: `app/data_analysis_v3/core/post_tpr_agent.py` (NEW)

**Structure**:
```python
class PostTPRAgent(DataAnalysisAgent):
    """
    Agent for handling post-TPR requests with shapefile + CSV access.
    Inherits from DataAnalysisAgent but with enhanced data loading.
    """

    def __init__(self, session_id: str):
        super().__init__(session_id)  # Inherit all LangGraph setup

        # Override data loading to include shapefiles
        self.has_shapefile = self._check_shapefile_exists()

    def _get_input_data(self) -> List[Dict[str, Any]]:
        """
        ENHANCED: Load both CSV and shapefile data.

        Priority order:
        1. Post-risk: unified_dataset.csv (if .analysis_complete exists)
        2. Post-TPR: raw_data.csv (if .risk_ready exists)
        3. Fallback: uploaded_data.csv
        """
        input_data_list = []
        session_folder = f"instance/uploads/{self.session_id}"

        # Determine which CSV to load based on workflow phase
        csv_file = self._determine_csv_file(session_folder)

        # Load CSV
        if csv_file:
            df = pd.read_csv(csv_file)
            input_data_list.append({
                'variable_name': 'df',
                'data_description': f"Dataset with {len(df)} rows",
                'data': df,
                'columns': df.columns.tolist()
            })

        # Load shapefile (if exists)
        shapefile_path = self._find_shapefile(session_folder)
        if shapefile_path:
            gdf = gpd.read_file(shapefile_path)
            input_data_list.append({
                'variable_name': 'gdf',
                'data_description': f"Geospatial data with {len(gdf)} features",
                'data': gdf,
                'columns': gdf.columns.tolist(),
                'is_spatial': True
            })

        return input_data_list

    def _determine_csv_file(self, session_folder: str) -> Optional[str]:
        """Determine which CSV to load based on workflow phase."""

        # Phase 3 (Post-Risk): unified_dataset.csv
        if os.path.exists(f"{session_folder}/.analysis_complete"):
            unified_path = f"{session_folder}/unified_dataset.csv"
            if os.path.exists(unified_path):
                logger.info("📊 Loading unified_dataset.csv (Phase 3: Post-Risk)")
                return unified_path

        # Phase 2 (Post-TPR): raw_data.csv
        if os.path.exists(f"{session_folder}/.risk_ready"):
            raw_data_path = f"{session_folder}/raw_data.csv"
            if os.path.exists(raw_data_path):
                logger.info("📊 Loading raw_data.csv (Phase 2: Post-TPR)")
                return raw_data_path

        # Fallback: uploaded_data.csv
        uploaded_path = f"{session_folder}/uploaded_data.csv"
        if os.path.exists(uploaded_path):
            logger.info("📊 Loading uploaded_data.csv (Fallback)")
            return uploaded_path

        return None

    def _find_shapefile(self, session_folder: str) -> Optional[str]:
        """Find shapefile in session folder."""

        # Try raw_shapefile.zip first (created by TPR workflow)
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

**Key Features**:
- **Inheritance**: Reuses all LangGraph setup from `DataAnalysisAgent`
- **Context-aware loading**: Automatically selects right CSV based on flags
- **Shapefile support**: Loads geospatial data as `gdf` variable
- **Phase detection**: Knows whether it's in Post-TPR or Post-Risk phase

---

### 2. Routing Logic

**File**: `app/web/routes/analysis_routes.py` (MODIFY)

**Changes** (around line 831):

```python
# BEFORE
elif use_tools and (session.get('use_data_analysis_v3', False) or session.get('data_analysis_active', False)):
    # Route to Data Analysis V3 agent (LangGraph)
    from app.data_analysis_v3.core.agent import DataAnalysisAgent
    agent = DataAnalysisAgent(session_id=session_id)
    result = loop.run_until_complete(agent.analyze(user_message))

# AFTER
elif use_tools and (session.get('use_data_analysis_v3', False) or session.get('data_analysis_active', False)):
    # Determine which agent to use based on workflow phase
    session_folder = f"instance/uploads/{session_id}"

    # Check workflow phase
    tpr_complete = os.path.exists(f"{session_folder}/.tpr_complete")
    has_standard_upload = (session.get('upload_type') == 'csv_shapefile' and
                          session.get('csv_loaded') and
                          session.get('shapefile_loaded'))

    # Use PostTPRAgent for: Standard uploads, Post-TPR, Post-Risk
    if tpr_complete or has_standard_upload:
        logger.info("🎯 Routing to Post-TPR Agent (with data access)")
        from app.data_analysis_v3.core.post_tpr_agent import PostTPRAgent
        agent = PostTPRAgent(session_id=session_id)
    else:
        # TPR Phase only: Use standard TPR workflow agent
        logger.info("🎯 Routing to TPR Agent (workflow)")
        from app.data_analysis_v3.core.agent import DataAnalysisAgent
        agent = DataAnalysisAgent(session_id=session_id)

    result = loop.run_until_complete(agent.analyze(user_message))
```

**Lines changed**: ~15-20 lines

**Key Change**: Now routes **standard uploads** (csv_shapefile) to PostTPRAgent!

---

### 3. Enhanced System Prompt

**File**: `app/data_analysis_v3/prompts/post_tpr_system_prompt.py` (NEW)

```python
"""
System prompt for Post-TPR Agent with enhanced capabilities.
Extends the base system prompt with geospatial awareness.
"""

from .system_prompt import MAIN_SYSTEM_PROMPT

POST_TPR_SYSTEM_PROMPT = MAIN_SYSTEM_PROMPT + """

## ENHANCED CAPABILITIES (Post-TPR Phase)

You now have access to BOTH tabular and geospatial data:

1. **DataFrame (df)**:
   - Contains all numerical data (TPR, environmental variables, rankings)
   - Use pandas for analysis

2. **GeoDataFrame (gdf)**:
   - Contains spatial geometries for wards
   - Use geopandas for spatial operations
   - Can create maps, calculate distances, spatial joins

## AVAILABLE OPERATIONS

**Spatial Analysis**:
- Buffer analysis: `gdf.buffer(distance)`
- Spatial joins: `gpd.sjoin(gdf1, gdf2)`
- Distance calculations: `gdf.distance(other)`
- Centroid extraction: `gdf.centroid`

**Visualization**:
- Choropleth maps: `gdf.plot(column='variable', cmap='viridis')`
- Interactive maps: Use folium or plotly
- Overlay maps: Combine TPR + environmental layers

**Custom Queries**:
- SQL-like queries on df: `df.query("TPR > 0.5")`
- Spatial filtering: `gdf[gdf.within(boundary)]`
- Aggregations: `df.groupby('ward').agg({'TPR': 'mean'})`

## WORKFLOW CONTEXT

You are in the POST-TPR phase. The user has completed:
1. ✅ TPR analysis with ward-level calculations
2. ✅ Data preparation with environmental variables

You should:
- Answer questions about TPR patterns
- Perform custom spatial analysis
- Create visualizations on demand
- Help user understand data before running risk analysis
"""
```

---

### 4. Tool Integration

**No changes needed!** ✅

The new agent inherits `analyze_data` tool from parent class, which already supports:
- Python code execution
- DataFrame operations
- GeoDataFrame operations (via geopandas import)
- Visualization generation

---

## Integration Points

### 1. Data Loading (Automatic)

**Current**:
```python
# TPR Agent loads only CSV
file_patterns = [
    'uploaded_data.csv',
    'raw_data.csv'
]
```

**New**:
```python
# Post-TPR Agent loads CSV + shapefile
csv_file = determine_csv_file()  # Phase-aware
shapefile = find_shapefile()      # Automatic detection

input_data = [
    {'variable_name': 'df', 'data': pd.read_csv(csv_file)},
    {'variable_name': 'gdf', 'data': gpd.read_file(shapefile)}
]
```

### 2. Phase Detection (Flag-based)

```python
# Phase 1 (Standard Upload): csv_shapefile + data files exist
if session.get('upload_type') == 'csv_shapefile':
    use_post_tpr_agent = True
    load_csv = 'raw_data.csv'
    load_shapefile = 'raw_shapefile.zip'

# Phase 2 (Post-TPR): .tpr_complete + .risk_ready
if os.path.exists('.tpr_complete'):
    use_post_tpr_agent = True
    load_csv = 'raw_data.csv'
    load_shapefile = 'raw_shapefile.zip'

# Phase 3 (Post-Risk): .analysis_complete
if os.path.exists('.analysis_complete'):
    use_post_tpr_agent = True  # Same agent!
    load_csv = 'unified_dataset.csv'
    load_shapefile = 'raw_shapefile.zip'  # Same shapefile
```

### 3. Fallback Handling

**What if agent can't answer?**
- Agent can still call tools via RequestInterpreter
- Use tool calling: `run_malaria_risk_analysis(session_id)`
- Seamless transition to existing pipeline

---

## Benefits of This Approach

### ✅ Reuses Proven Code
- Inherits from working `DataAnalysisAgent`
- Uses same LangGraph setup (2-node pattern)
- Same LLM (OpenAI GPT-4o)
- Same Python execution tool

### ✅ Context-Aware Data Loading
- Automatically loads correct CSV based on phase
- No manual file selection needed
- Handles Standard Upload, Post-TPR, and Post-Risk phases

### ✅ Handles "Outside Tool" Requests
- User asks: "How many wards have TPR > 0.5?"
  - Agent: Executes Python code directly
  - No need for pre-built tool
- User asks: "Show me wards with high rainfall"
  - Agent: Creates custom visualization
  - No hardcoded map types

### ✅ **MASSIVE VALUE FOR STANDARD UPLOADS** 🚀
**This is the game-changer!**

**Before** (Current):
- Standard upload (csv_shapefile) → RequestInterpreter
- NO conversational queries
- NO custom analysis
- NO access to data
- Only pre-built tools work

**After** (With PostTPRAgent):
- Standard upload (csv_shapefile) → PostTPRAgent
- ✅ "Show me the top 10 wards by population"
- ✅ "Create a map of rainfall distribution"
- ✅ "What's the correlation between elevation and temperature?"
- ✅ "Filter wards where urban_extent > 50%"
- ✅ Can still call pre-built tools when needed

**Users get conversational data analysis immediately after upload!**

### ✅ Preserves Existing Tools
- `run_malaria_risk_analysis` still works
- `run_itn_planning` still works
- Agent can call them if needed

### ✅ Minimal Changes
- **New files**: 1 (`post_tpr_agent.py` ~200 lines)
- **Modified files**: 1 (`analysis_routes.py` ~20 lines)
- **New system prompt**: 1 (`post_tpr_system_prompt.py` ~100 lines)
- **Total new code**: ~320 lines

---

## Risks & Mitigations

### Risk 1: Data Loading Confusion
**Issue**: Agent might load wrong CSV/shapefile
**Mitigation**: Flag-based detection with clear logging
**Test**: Create unit tests for each phase

### Risk 2: Shapefile Format Issues
**Issue**: Shapefiles might be in different formats
**Mitigation**: Support both .zip and .shp directory
**Test**: Test with actual session data

### Risk 3: Performance
**Issue**: Loading shapefile might be slow
**Mitigation**: Use lazy loading (only load if needed)
**Test**: Benchmark with real shapefiles

### Risk 4: Tool Conflicts
**Issue**: Agent might conflict with RequestInterpreter
**Mitigation**: Clear routing logic based on flags
**Test**: End-to-end workflow testing

---

## Testing Strategy

### Unit Tests

```python
def test_post_tpr_agent_csv_selection():
    """Test that agent loads correct CSV based on phase."""

    # Phase 2: Post-TPR
    session_folder = create_test_session_with_tpr_complete()
    agent = PostTPRAgent('test_session')
    assert agent.csv_file == 'raw_data.csv'

    # Phase 3: Post-Risk
    add_analysis_complete_flag(session_folder)
    agent = PostTPRAgent('test_session')
    assert agent.csv_file == 'unified_dataset.csv'

def test_post_tpr_agent_shapefile_loading():
    """Test shapefile loading."""

    session_folder = create_test_session_with_shapefile()
    agent = PostTPRAgent('test_session')
    data = agent._get_input_data()

    assert len(data) == 2  # df + gdf
    assert data[1]['variable_name'] == 'gdf'
    assert data[1]['is_spatial'] == True
```

### Integration Tests

```python
def test_post_tpr_workflow():
    """Test complete Post-TPR workflow."""

    # 1. Complete TPR workflow
    complete_tpr_workflow('test_session')

    # 2. Send message to Post-TPR agent
    response = send_message(
        session_id='test_session',
        message='How many wards have TPR greater than 0.5?'
    )

    # 3. Verify agent used PostTPRAgent
    assert response['agent_type'] == 'PostTPRAgent'
    assert 'df' in response['data_variables']
    assert 'gdf' in response['data_variables']

    # 4. Verify answer is correct
    assert 'wards' in response['message'].lower()
```

---

## Implementation Plan

### Phase 1: Core Agent (1-2 hours)
1. Create `post_tpr_agent.py`
2. Implement `_get_input_data()` override
3. Add phase detection logic
4. Test CSV loading

### Phase 2: Shapefile Integration (1 hour)
1. Add shapefile detection
2. Load as GeoDataFrame
3. Test with sample data
4. Handle edge cases (missing shapefile)

### Phase 3: Routing (30 min)
1. Modify `analysis_routes.py`
2. Add flag-based routing
3. Test routing logic

### Phase 4: System Prompt (30 min)
1. Create enhanced system prompt
2. Document spatial capabilities
3. Add examples

### Phase 5: Testing (1 hour)
1. Unit tests for data loading
2. Integration tests for workflow
3. End-to-end testing with real data

**Total**: ~4 hours

---

## Example Usage

### Scenario 1: Standard Upload (NEW! 🎉)

```
User uploads: raw_data.csv + raw_shapefile.zip (standard upload)
User: "Show me the top 10 wards by population"

PostTPRAgent:
- Detects: standard upload (csv_shapefile)
- Loads: raw_data.csv + raw_shapefile.zip
- Executes: df.nlargest(10, 'population')[['ward_name', 'population']]
- Returns: Table with top 10 wards
```

### Scenario 2: Standard Upload - Spatial Query (NEW! 🎉)

```
User: "Create a map showing rainfall distribution"

PostTPRAgent:
- Loads: raw_data.csv + raw_shapefile.zip
- Executes:
  import folium
  gdf.plot(column='rainfall', cmap='Blues', legend=True)
- Returns: Interactive choropleth map
```

### Scenario 3: Post-TPR Query

```
User: "Which wards have the highest TPR?"

PostTPRAgent:
- Detects: .tpr_complete flag exists
- Loads: raw_data.csv (has TPR column)
- Executes: df.nlargest(10, 'TPR')[['ward', 'TPR']]
- Returns: "Top 10 wards by TPR: ..."
```

### Scenario 4: Spatial Query

```
User: "Show me a map of wards with TPR > 0.5"

PostTPRAgent:
- Loads raw_data.csv + raw_shapefile.zip
- Executes:
  high_tpr = gdf[gdf['TPR'] > 0.5]
  high_tpr.plot(column='TPR', cmap='Reds')
- Returns: Interactive map
```

### Scenario 5: Custom Analysis

```
User: "What's the correlation between rainfall and TPR?"

PostTPRAgent:
- Loads raw_data.csv
- Executes:
  correlation = df[['rainfall', 'TPR']].corr()
  print(correlation)
- Returns: Correlation matrix + interpretation
```

### Scenario 6: Tool Handoff

```
User: "Run the risk analysis now"

PostTPRAgent:
- Recognizes this needs pre-built tool
- Calls: run_malaria_risk_analysis(session_id)
- Hands off to RequestInterpreter
- Returns: Risk analysis results
```

---

## Comparison: Before vs After

### Before (Current)

**Standard Upload (csv_shapefile)**:
- ❌ No conversational queries on data
- ❌ No custom analysis
- ❌ No spatial queries
- ❌ Only pre-built tools work
- ❌ RequestInterpreter has no intelligence
- ❌ **Users can't explore their data!**

**Post-TPR (after TPR workflow)**:
- ❌ No conversational queries on TPR results
- ❌ No custom analysis
- ❌ No spatial queries
- ❌ Only pre-built tools work

**What works**:
- ✅ TPR workflow (Phase 1)
- ✅ Pre-built risk analysis tool
- ✅ Pre-built ITN planning tool

### After (Proposed)

**Standard Upload (csv_shapefile)** 🚀:
- ✅ **Conversational queries immediately after upload**
- ✅ Custom analysis on demand
- ✅ Spatial queries with shapefile
- ✅ Intelligent agent with context
- ✅ Can still call pre-built tools
- ✅ **Users can explore data naturally!**

**Post-TPR (after TPR workflow)** 🚀:
- ✅ Answer any question about TPR results
- ✅ Custom analysis on TPR + environmental data
- ✅ Spatial queries with wards
- ✅ Intelligent agent with context
- ✅ Seamless tool integration

**Post-Risk (after risk analysis)** 🚀:
- ✅ Query unified dataset with rankings
- ✅ Custom ITN planning scenarios
- ✅ Advanced spatial analysis
- ✅ Interactive exploration

**Still works**:
- ✅ TPR workflow (unchanged)
- ✅ Pre-built risk analysis tool
- ✅ Pre-built ITN planning tool

---

## Questions & Answers

### Q1: Why not modify existing DataAnalysisAgent?
**A**: Keep TPR agent focused. Post-TPR has different needs (shapefile access, different CSV files). Separation of concerns.

### Q2: Why inherit instead of creating new agent from scratch?
**A**: Reuse proven code. LangGraph setup is complex (51 lines). Tools work. No need to reinvent.

### Q3: What if user asks something agent can't answer?
**A**: Agent can call tools! It has access to `run_malaria_risk_analysis()` via tool calling. Best of both worlds.

### Q4: Performance impact?
**A**: Minimal. Only loads shapefile if exists. CSV loading same as before. GeoDataFrame loading ~100-500ms for typical wards.

### Q5: How does it know which CSV to load?
**A**: Flag-based + session detection:
- `upload_type == 'csv_shapefile'` → `raw_data.csv` (standard upload)
- `.tpr_complete` → `raw_data.csv` (post-TPR)
- `.analysis_complete` → `unified_dataset.csv` (post-risk)
- Neither → `uploaded_data.csv` (fallback)

### Q6: What if shapefile doesn't exist?
**A**: Agent works fine without it! Only loads if available. User just won't get spatial features.

---

## Conclusion

**This is a SMALL, SAFE enhancement** that:
- Reuses proven code (inheritance)
- Adds minimal new code (~315 lines)
- Provides huge value (conversational analysis)
- Low risk (well-tested pattern)
- Clear implementation path (4 hours)

**Recommendation**: ✅ **Proceed with implementation**

The architecture is sound, the pattern is proven, and the value is high. This is exactly the right way to enhance the system without breaking existing functionality.

---

## Next Steps

1. ✅ Review this investigation
2. Get approval to proceed
3. Create `post_tpr_agent.py`
4. Test with sample data
5. Integrate with routing
6. Deploy and monitor

**Ready when you are!** 🚀
