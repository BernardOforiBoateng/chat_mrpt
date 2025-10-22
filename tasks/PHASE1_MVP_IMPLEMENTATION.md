# Phase 1: MVP Implementation - Agent as Tool #19

**Date**: 2025-10-04
**Goal**: Get the basic plumbing working - worry about security/hardening later
**Effort**: 3-4 hours
**Focus**: Seamless integration with existing RequestInterpreter

---

## What We're Building (Simplified)

Add Tool #19 to RequestInterpreter that calls DataExplorationAgent for Python execution.

**Security, sandboxing, etc. = Phase 2 (later)**

---

## File Changes

### 1. CREATE: `app/data_analysis_v3/core/data_exploration_agent.py`

```python
"""
Data Exploration Agent - MVP for Tool #19 integration.

Simple Python execution on session data.
Security hardening in Phase 2.
"""

import os
import logging
import glob
from typing import List, Dict, Any, Optional
import pandas as pd
import geopandas as gpd

from .agent import DataAnalysisAgent
from .encoding_handler import EncodingHandler

logger = logging.getLogger(__name__)


class DataExplorationAgent(DataAnalysisAgent):
    """
    MVP: Simple Python execution on user data.

    Called by RequestInterpreter's analyze_data_with_python tool.
    Phase 1: Basic functionality
    Phase 2: Add sandbox, limits, security
    """

    def __init__(self, session_id: str):
        super().__init__(session_id)
        logger.info(f"🔍 DataExplorationAgent initialized for {session_id}")

    def analyze_sync(self, query: str) -> Dict[str, Any]:
        """
        Synchronous wrapper for tool calling.

        Args:
            query: User's query/question

        Returns:
            Dict with message, visualizations, etc.
        """
        import asyncio

        # Create event loop for async analyze
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self.analyze(query))
            return result
        finally:
            loop.close()

    def _get_input_data(self) -> List[Dict[str, Any]]:
        """
        Load CSV + shapefile from session folder.

        Priority:
        1. unified_dataset.csv (post-risk)
        2. raw_data.csv (post-TPR or standard upload)
        3. uploaded_data.csv (fallback)
        """
        input_data_list = []
        session_folder = f"instance/uploads/{self.session_id}"

        # Load CSV
        csv_file = self._find_csv(session_folder)
        if csv_file and os.path.exists(csv_file):
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

    def _find_csv(self, session_folder: str) -> Optional[str]:
        """Find CSV file in priority order."""

        # Priority 1: unified_dataset.csv (post-risk analysis)
        unified = f"{session_folder}/unified_dataset.csv"
        if os.path.exists(unified):
            logger.info("📊 Using unified_dataset.csv (post-risk)")
            return unified

        # Priority 2: raw_data.csv (post-TPR or standard upload)
        raw_data = f"{session_folder}/raw_data.csv"
        if os.path.exists(raw_data):
            logger.info("📊 Using raw_data.csv")
            return raw_data

        # Priority 3: uploaded_data.csv (fallback)
        uploaded = f"{session_folder}/uploaded_data.csv"
        if os.path.exists(uploaded):
            logger.info("📊 Using uploaded_data.csv (fallback)")
            return uploaded

        return None

    def _find_shapefile(self, session_folder: str) -> Optional[str]:
        """Find shapefile in session folder."""

        # Try raw_shapefile.zip (created by TPR workflow)
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

**Lines**: ~140

---

### 2. MODIFY: `app/core/request_interpreter.py`

**Change 1: Register Tool** (in `_register_tools()` method, around line 140):

```python
def _register_tools(self):
    """Register actual Python functions as tools - true py-sidebot style."""
    logger.info("Registering tools - py-sidebot pattern")

    # ... existing 18 tools ...

    # NEW: Tool #19 - Python execution via agent
    self.tools['analyze_data_with_python'] = self._analyze_data_with_python

    logger.info(f"Registered {len(self.tools)} tools")  # Now shows 19
```

**Change 2: Add Tool Method** (after existing tools, around line 1500):

```python
def _analyze_data_with_python(self, session_id: str, query: str) -> Dict[str, Any]:
    """
    Execute custom Python analysis on user data via DataExplorationAgent.

    Use this when users ask questions requiring:
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
        Dict with response, visualizations, tools_used (matching RI format)
    """
    logger.info(f"🐍 TOOL: analyze_data_with_python called")
    logger.info(f"  Session: {session_id}")
    logger.info(f"  Query: {query[:100]}...")

    try:
        # Import agent
        from app.data_analysis_v3.core.data_exploration_agent import DataExplorationAgent

        # Create agent instance
        agent = DataExplorationAgent(session_id=session_id)

        # Execute query (synchronous interface)
        result = agent.analyze_sync(query)

        # Format result to match RI tool contract
        # CRITICAL: RI expects 'response', agent returns 'message'
        return {
            'status': result.get('status', 'success'),
            'response': result.get('message', ''),  # Map 'message' to 'response'
            'visualizations': result.get('visualizations', []),
            'tools_used': ['analyze_data_with_python'],
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

## Key Points for Seamless Integration

### 1. Return Format Matches RI Contract ✅

Looking at existing tools, RI expects:
```python
{
    'status': 'success',
    'response': 'The answer...',  # ← NOT 'message'
    'visualizations': [...],
    'tools_used': ['tool_name']
}
```

Agent returns:
```python
{
    'status': 'success',
    'message': 'The answer...',  # ← Different field name
    'visualizations': [...]
}
```

**Solution**: Map `message` → `response` in the tool wrapper ✅

### 2. Async Handling ✅

Agent's `analyze()` is async, but RI tool must be sync.

**Solution**: Add `analyze_sync()` wrapper that handles event loop ✅

### 3. Data Loading ✅

Agent needs to find correct CSV based on workflow phase.

**Solution**: Priority order: unified → raw → uploaded ✅

### 4. Error Handling ✅

Tool must return error dict in RI format, not raise exceptions.

**Solution**: Try/catch in `_analyze_data_with_python` ✅

---

## Testing (Simplified for MVP)

### Manual Test 1: Standard Upload
```
1. Upload CSV + shapefile via standard upload
2. Send message: "Show me the first 5 rows"
3. Verify: Tool is called, agent loads data, returns result
4. Check logs for: "🐍 TOOL: analyze_data_with_python called"
```

### Manual Test 2: Post-TPR
```
1. Complete TPR workflow
2. Send message: "Which wards have TPR > 0.5?"
3. Verify: Agent loads raw_data.csv (has TPR column)
4. Check result contains actual ward names
```

### Manual Test 3: Error Handling
```
1. Send message with invalid session_id
2. Verify: Gets error dict with status='error'
3. Verify: No crash, graceful error message
```

### Manual Test 4: Tool Selection
```
1. Send message: "Run the risk analysis"
2. Verify: LLM chooses run_malaria_risk_analysis (NOT agent)
3. Send message: "Show me top 10 wards"
4. Verify: LLM chooses analyze_data_with_python (agent)
```

---

## Deployment

### Local Testing
```bash
# Activate venv
source chatmrpt_venv_new/bin/activate

# Create the agent file
# (copy code from above)

# Modify request_interpreter.py
# (add 2 changes from above)

# Test
python run.py

# Try in browser
# Upload data, ask: "Show me the first 5 rows"
```

### Staging
```bash
# Backup first
ssh -i /tmp/chatmrpt-key2.pem ec2-user@18.117.115.217
tar -czf ChatMRPT_pre_phase1_$(date +%Y%m%d_%H%M%S).tar.gz \
    ChatMRPT/app/core/request_interpreter.py \
    ChatMRPT/app/data_analysis_v3/

# Copy files
scp -i /tmp/chatmrpt-key2.pem \
    app/data_analysis_v3/core/data_exploration_agent.py \
    ec2-user@18.117.115.217:~/ChatMRPT/app/data_analysis_v3/core/

scp -i /tmp/chatmrpt-key2.pem \
    app/core/request_interpreter.py \
    ec2-user@18.117.115.217:~/ChatMRPT/app/core/

# Restart
ssh -i /tmp/chatmrpt-key2.pem ec2-user@18.117.115.217 \
    'sudo systemctl restart chatmrpt'

# Watch logs
ssh -i /tmp/chatmrpt-key2.pem ec2-user@18.117.115.217 \
    'sudo journalctl -u chatmrpt -f | grep -E "TOOL:|analyze_data_with_python"'
```

### Production (Both Instances)
```bash
# Only after staging works!
for ip in 3.21.167.170 18.220.103.20; do
    echo "Deploying to $ip..."
    # Same steps as staging
done
```

---

## Rollback (If Needed)

```bash
# Revert request_interpreter.py
cd ~/
tar -xzf ChatMRPT_pre_phase1_*.tar.gz
cp ChatMRPT/app/core/request_interpreter.py ChatMRPT_current/app/core/

# Remove agent file
rm ~/ChatMRPT/app/data_analysis_v3/core/data_exploration_agent.py

# Restart
sudo systemctl restart chatmrpt
```

**Recovery Time**: < 2 minutes

---

## What We're NOT Doing (Phase 2)

- ❌ Sandbox/security hardening
- ❌ Resource limits (memory, CPU, time)
- ❌ Code whitelisting
- ❌ Feature flags
- ❌ SessionDataResolver abstraction
- ❌ Comprehensive unit tests
- ❌ Caching strategy

**Phase 1 Goal**: Get it working, prove the integration works.

**Phase 2 Goal**: Harden security, add limits, production-ready.

---

## Success Criteria (Phase 1)

- [ ] Tool #19 registered (logs show "Registered 19 tools")
- [ ] Agent can be called from RI
- [ ] Agent loads data successfully
- [ ] Agent executes Python code
- [ ] Results returned in correct format
- [ ] No crashes or deadlocks
- [ ] Works on standard upload, post-TPR, post-risk

---

## Next Steps After Phase 1

Once basic integration works:

**Phase 2** (Security & Hardening):
1. Add sandbox for code execution
2. Add resource limits
3. Add feature flag
4. Add SessionDataResolver
5. Add comprehensive tests
6. Add monitoring/metrics

**Phase 3** (Optimization):
1. Add caching
2. Optimize data loading
3. Add streaming support
4. Performance tuning

---

## Questions Answered

### Q: "Where to point to?"
**A**: Tool points to `app.data_analysis_v3.core.data_exploration_agent.DataExplorationAgent`

### Q: "What codes to register?"
**A**: Add 1 line in `_register_tools()`: `self.tools['analyze_data_with_python'] = self._analyze_data_with_python`

### Q: "How to make it seamless?"
**A**:
- Return format matches RI (`response` not `message`)
- Sync wrapper handles async (`analyze_sync()`)
- Error handling returns dict, doesn't raise

---

## Ready to Implement?

**Files to create/modify**:
1. CREATE: `app/data_analysis_v3/core/data_exploration_agent.py` (~140 lines)
2. MODIFY: `app/core/request_interpreter.py` (+60 lines)

**Total new code**: ~200 lines

**Estimated time**: 2-3 hours

**Risk**: Low (easy rollback)

**Value**: High (enables custom queries immediately)

---

**Let's build Phase 1!** 🚀

Security and hardening come in Phase 2 after we prove the integration works.
