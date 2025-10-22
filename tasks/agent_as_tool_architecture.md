# Agent as Tool Architecture

**Date**: 2025-10-04
**Concept**: Use DataExplorationAgent as a TOOL within RequestInterpreter

---

## The Insight

Instead of:
- Agent replaces RequestInterpreter ❌
- Agent runs parallel to RequestInterpreter ❌

Do this:
- **RequestInterpreter remains the orchestrator** ✅
- **Agent becomes Tool #19: Python execution** ✅

---

## Architecture

### Current State:
```
RequestInterpreter
├─ Tool 1: run_malaria_risk_analysis
├─ Tool 2: run_itn_planning
├─ Tool 3: create_vulnerability_map
├─ ...
└─ Tool 18: show_settlement_statistics

LLM chooses from 18 tools
If none fit → Conversational response (can't execute code)
```

### Proposed State:
```
RequestInterpreter
├─ Tool 1: run_malaria_risk_analysis
├─ Tool 2: run_itn_planning
├─ Tool 3: create_vulnerability_map
├─ ...
├─ Tool 18: show_settlement_statistics
└─ Tool 19: analyze_data_with_python ✨ (NEW)
         ↓
    Calls DataExplorationAgent
         ↓
    Executes Python code on df/gdf
         ↓
    Returns result
```

---

## Implementation

### Step 1: Create Tool Wrapper

**File**: `app/core/request_interpreter.py`

**Add to `_register_tools()` method**:

```python
def _register_tools(self):
    """Register actual Python functions as tools."""

    # ... existing 18 tools ...

    # NEW: Register Python execution tool
    self.tools['analyze_data_with_python'] = self._analyze_data_with_python

    logger.info(f"Registered {len(self.tools)} tools")

def _analyze_data_with_python(self, session_id: str, query: str) -> Dict[str, Any]:
    """
    Execute custom data analysis using Python on loaded datasets.

    Use this when user asks questions that require:
    - Querying specific data (e.g., "show me top 10 wards")
    - Custom calculations (e.g., "what's the correlation between X and Y")
    - Filtering data (e.g., "which wards have TPR > 0.5")
    - Custom visualizations
    - Geospatial queries

    This tool can access:
    - DataFrames (df) with all uploaded data
    - GeoDataFrames (gdf) with spatial boundaries
    - All pandas, numpy, geopandas operations

    Args:
        session_id: The session ID
        query: Natural language description of what analysis to perform

    Returns:
        Analysis result with answer and/or visualization
    """
    logger.info(f"🐍 PYTHON TOOL: analyze_data_with_python called")
    logger.info(f"  Session: {session_id}")
    logger.info(f"  Query: {query}")

    try:
        # Import the agent
        from app.data_analysis_v3.core.data_exploration_agent import DataExplorationAgent

        # Create agent instance
        agent = DataExplorationAgent(session_id=session_id)

        # Execute query via agent
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
            'data_returned': result.get('data_returned', False)
        }

    except Exception as e:
        logger.error(f"Error in analyze_data_with_python: {e}")
        return {
            'status': 'error',
            'response': f'I encountered an error analyzing the data: {str(e)}',
            'tools_used': ['analyze_data_with_python']
        }
```

**Lines Added**: ~60

---

### Step 2: Create DataExplorationAgent

**File**: `app/data_analysis_v3/core/data_exploration_agent.py`

```python
"""
Data Exploration Agent - Python execution on DataFrames and GeoDataFrames.

This agent is called BY RequestInterpreter when users ask questions
that require custom data analysis.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
import geopandas as gpd
import glob

from .agent import DataAnalysisAgent
from .encoding_handler import EncodingHandler

logger = logging.getLogger(__name__)


class DataExplorationAgent(DataAnalysisAgent):
    """
    Agent for exploring data with Python execution.

    Called by RequestInterpreter's analyze_data_with_python tool
    when users ask questions requiring custom analysis.

    Capabilities:
    - Query DataFrames with pandas
    - Geospatial queries with geopandas
    - Custom calculations
    - Custom visualizations
    """

    def __init__(self, session_id: str):
        super().__init__(session_id)
        logger.info(f"🔍 DataExplorationAgent initialized for session {session_id}")

    def _get_input_data(self) -> List[Dict[str, Any]]:
        """
        Load CSV + shapefile based on session state.

        Priority:
        1. Post-risk: unified_dataset.csv (has rankings)
        2. Post-TPR: raw_data.csv (has TPR + environment)
        3. Standard upload: raw_data.csv (user data)
        """
        input_data_list = []
        session_folder = f"instance/uploads/{self.session_id}"

        # Load CSV
        csv_file = self._determine_csv_file(session_folder)
        if csv_file:
            try:
                df = EncodingHandler.read_csv_with_encoding(csv_file)
                input_data_list.append({
                    'variable_name': 'df',
                    'data_description': f"Dataset with {len(df)} rows and {len(df.columns)} columns",
                    'data': df,
                    'columns': df.columns.tolist()
                })
                logger.info(f"✅ Loaded CSV: {os.path.basename(csv_file)} ({len(df)} rows)")
            except Exception as e:
                logger.error(f"Failed to load CSV {csv_file}: {e}")

        # Load shapefile if exists
        shapefile = self._find_shapefile(session_folder)
        if shapefile:
            try:
                gdf = gpd.read_file(shapefile)
                input_data_list.append({
                    'variable_name': 'gdf',
                    'data_description': f"Geospatial data with {len(gdf)} features",
                    'data': gdf,
                    'columns': gdf.columns.tolist(),
                    'is_spatial': True
                })
                logger.info(f"✅ Loaded shapefile: {len(gdf)} features")
            except Exception as e:
                logger.error(f"Failed to load shapefile {shapefile}: {e}")

        if not input_data_list:
            logger.warning(f"⚠️ No data loaded for session {self.session_id}")

        return input_data_list

    def _determine_csv_file(self, session_folder: str) -> Optional[str]:
        """Determine which CSV to load based on workflow phase."""

        # Post-risk: unified_dataset.csv
        if os.path.exists(f"{session_folder}/.analysis_complete"):
            unified = f"{session_folder}/unified_dataset.csv"
            if os.path.exists(unified):
                logger.info("📊 Phase: Post-Risk (unified_dataset.csv)")
                return unified

        # Post-TPR or Standard: raw_data.csv
        raw_data = f"{session_folder}/raw_data.csv"
        if os.path.exists(raw_data):
            if os.path.exists(f"{session_folder}/.tpr_complete"):
                logger.info("📊 Phase: Post-TPR (raw_data.csv)")
            else:
                logger.info("📊 Phase: Standard Upload (raw_data.csv)")
            return raw_data

        # Fallback: uploaded_data.csv
        uploaded = f"{session_folder}/uploaded_data.csv"
        if os.path.exists(uploaded):
            logger.info("📊 Phase: Fallback (uploaded_data.csv)")
            return uploaded

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

**Lines**: ~150

---

## How It Works

### Example 1: Simple Query

```
User: "Show me the top 10 wards by population"
    ↓
RequestInterpreter.process_message()
    ↓
LLM sees 19 tools, chooses: analyze_data_with_python
    ↓
Calls: _analyze_data_with_python(
    session_id="abc123",
    query="Show me the top 10 wards by population"
)
    ↓
Creates: DataExplorationAgent(session_id="abc123")
    ↓
Agent loads: df (from raw_data.csv)
    ↓
Agent's LLM writes Python: df.nlargest(10, 'population')
    ↓
Executes and returns result
    ↓
RequestInterpreter receives result
    ↓
User sees: Table with top 10 wards
```

### Example 2: Complex Tool

```
User: "Run the complete risk analysis"
    ↓
RequestInterpreter.process_message()
    ↓
LLM sees 19 tools, chooses: run_malaria_risk_analysis
    ↓
Calls pre-built tool (existing RI tool)
    ↓
Returns risk analysis results
    ↓
User sees: Risk maps + rankings
```

### Example 3: Mixed Usage

```
User: "What's the correlation between rainfall and TPR?"
    ↓
RequestInterpreter.process_message()
    ↓
LLM sees 19 tools, chooses: analyze_data_with_python
    ↓
Agent executes: df[['rainfall', 'TPR']].corr()
    ↓
Returns correlation matrix
    ↓
User sees: Correlation value
```

---

## Benefits

### ✅ RequestInterpreter Stays in Control
- All routing through one place
- All session management in one place
- All tool orchestration in one place

### ✅ Agent is Just Another Tool
- No complex routing logic
- No parallel paths
- No architecture changes

### ✅ LLM Makes Smart Decisions
- "Need pre-built analysis?" → Use run_malaria_risk_analysis
- "Need custom query?" → Use analyze_data_with_python
- Same brain, more options

### ✅ Minimal Code Changes
- Add 1 tool to RequestInterpreter (~60 lines)
- Create DataExplorationAgent (~150 lines)
- No routing changes needed
- Total: ~210 new lines

---

## What Changes

**MODIFY**:
1. `app/core/request_interpreter.py` (+60 lines)
   - Add `_analyze_data_with_python` tool method

**CREATE**:
1. `app/data_analysis_v3/core/data_exploration_agent.py` (~150 lines)
   - Agent that executes Python on data

**NO CHANGES**:
1. ✅ Routing logic in analysis_routes.py
2. ✅ All other RI tools
3. ✅ All other files

---

## Testing

```python
# Test 1: Agent as tool
response = request_interpreter.process_message(
    "Show me top 10 wards",
    session_id="test123"
)
assert 'analyze_data_with_python' in response['tools_used']
assert response['status'] == 'success'

# Test 2: Regular tools still work
response = request_interpreter.process_message(
    "Run risk analysis",
    session_id="test123"
)
assert 'run_malaria_risk_analysis' in response['tools_used']
assert response['status'] == 'success'

# Test 3: LLM chooses right tool
response = request_interpreter.process_message(
    "What's the average TPR?",
    session_id="test123"
)
assert 'analyze_data_with_python' in response['tools_used']  # LLM chose Python
```

---

## Rollback

If anything breaks:
```bash
# Revert request_interpreter.py
git checkout HEAD -- app/core/request_interpreter.py

# Remove agent file (doesn't affect anything)
rm app/data_analysis_v3/core/data_exploration_agent.py

# Restart
sudo systemctl restart chatmrpt
```

Zero risk - just removing one tool.

---

## Timeline

**Day 1** (2 hours):
- Create DataExplorationAgent
- Test locally

**Day 2** (1 hour):
- Add tool to RequestInterpreter
- Integration testing

**Day 3** (1 hour):
- Deploy to staging
- End-to-end testing

**Total**: 4 hours

---

## Conclusion

**This is the RIGHT architecture** ✅

Instead of:
- Agent replaces RI (too risky)
- Agent runs parallel to RI (complex routing)

We do:
- **Agent is Tool #19 in RI** (simple, safe, elegant)

RequestInterpreter remains the brain.
Agent is just a capability it can call.

Perfect! 🎯
