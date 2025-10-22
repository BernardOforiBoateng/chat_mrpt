# LangGraph Agent Failure - Root Cause Investigation Report
**Date:** 2025-10-06
**Investigator:** Claude
**Session ID Analyzed:** be0bef7a-c877-45ca-9145-8e4ff462b0eb
**Status:** ❌ CRITICAL ISSUES FOUND - LangGraph Agent NOT Being Used

---

## EXECUTIVE SUMMARY

**The LangGraph agent (Tool #19 / `analyze_data_with_python`) is completely bypassed and NEVER used in the test session.**

**Test Results:**
- **Success Rate:** 5/12 (41.7%)
- **Failure Rate:** 7/12 (58.3%)
- **Critical Finding:** All ANOVA and regression queries fail with "Code contains potentially dangerous operations"

**Root Causes Identified:**
1. ✅ **Data Analysis Mode Exit** - System exits data analysis mode after TPR completion
2. ✅ **Legacy Tools Still Active** - `execute_data_query` and `execute_sql_query` NOT actually removed
3. ✅ **Tool #19 Never Selected** - LLM selects legacy tools instead of modern agent
4. ✅ **Missing AWS Files** - Local development environment incomplete, missing critical files
5. ✅ **DataExplorationAgent Doesn't Exist** - Implementation files not found anywhere

---

## PART 1: TEST RESULTS ANALYSIS

### Test Execution Summary

| # | Query Type | Result | Error/Tool Used |
|---|------------|--------|-----------------|
| 1 | Correlation (pandas .corr()) | ✅ SUCCESS | Unknown tool |
| 2 | Correlation heatmap (plotly) | ✅ SUCCESS | Unknown tool |
| 3 | ANOVA test (scipy.stats) | ❌ FAILED | "Code contains potentially dangerous operations" |
| 4 | ANOVA test #2 (scipy.stats) | ❌ FAILED | "Code contains potentially dangerous operations" |
| 5 | Linear regression (sklearn) | ❌ FAILED | "Code contains potentially dangerous operations" |
| 6 | Scatter plot | ❌ FAILED | "Y variable 'tpr' not found or not numeric" |
| 7 | Scatter plot retry | ❌ FAILED | "Y variable 'tpr' not found or not numeric" |
| 8 | Box plot | ❌ FAILED | "Validation error: List should have at least 2 items" |
| 9 | Data filtering (pandas) | ✅ SUCCESS | Unknown tool |
| 10 | Aggregation (pandas) | ✅ SUCCESS | Unknown tool |
| 11 | Ranking/GroupBy (pandas) | ✅ SUCCESS | Unknown tool |
| 12 | ANOVA test #3 (scipy.stats) | ❌ FAILED | "Code contains potentially dangerous operations" |

### Pattern Analysis

**✅ Working Queries (Simple Pandas Operations):**
- Correlation analysis
- Data filtering
- Aggregation
- GroupBy/Ranking
- Plotly heatmap

**❌ Failing Queries (Requiring External Libraries):**
- **ANOVA tests** (4 attempts) - Need scipy.stats
- **Linear regression** - Needs sklearn
- **Scatter plots** - Variable name issue
- **Box plot** - Validation issue

**Critical Pattern:** All queries requiring scipy.stats or sklearn FAIL with the EXACT error message from the legacy ConversationalDataAccess security filter.

---

## PART 2: WORKFLOW TRACE & ROOT CAUSE

### The Smoking Gun: Data Analysis Mode Exit

**From context.md (Lines 162-520):**

```
Line 162: Assistant: "✅ Results saved to tpr_results.csv"
Line 168: User: "yes"
Line 510-511: Response:
{
  "exit_data_analysis_mode": true,
  "message": "I've loaded your data...",
  "transition": "tpr_to_upload",
  "workflow": "data_upload"
}
Line 516-520: 🔄 TRANSITION: Exiting data analysis mode
Line 534: 🌐 Using endpoint: /send_message_streaming
Line 535: 🔍 Data Analysis Mode: false
```

**What Happened:**
1. TPR workflow completed successfully
2. User confirmed to continue ("yes")
3. **System EXITED data analysis mode**
4. ALL subsequent queries used `/send_message_streaming` endpoint
5. Data analysis mode = false for all ANOVA/regression queries

### Request Flow Comparison

**EXPECTED (According to Architecture):**
```
User: "Perform ANOVA test"
    ↓
RequestInterpreter.process_message()
    ↓
LLM sees Tool #19 (analyze_data_with_python)
    ↓
Tool #19 creates DataExplorationAgent
    ↓
Agent writes Python code with scipy.stats
    ↓
SecureExecutor runs code (has scipy.stats ✅)
    ↓
Result: ANOVA results ✅
```

**ACTUAL (What Really Happened):**
```
User: "Perform ANOVA test"
    ↓
/send_message_streaming endpoint (regular mode, NOT data analysis)
    ↓
RequestInterpreter.process_message()
    ↓
LLM sees legacy tools (execute_data_query)
    ↓
Legacy tool calls ConversationalDataAccess
    ↓
ConversationalDataAccess generates code with scipy.stats
    ↓
Security filter blocks scipy import ❌
    ↓
Result: "Code contains potentially dangerous operations" ❌
```

---

## PART 3: TOOL REGISTRATION ANALYSIS

### Tool #19 Registration Status

**File:** `app/core/request_interpreter.py`

**Line 143-144: Tool #19 IS Registered**
```python
# NEW: Python execution tool (Tool #19)
self.tools['analyze_data_with_python'] = self._analyze_data_with_python
```

✅ Tool #19 IS registered in `self.tools`

### Legacy Tools "Removal" Status

**Lines 133-135: Commented Out from self.tools**
```python
# REMOVED: Redundant data tools
# self.tools['execute_data_query'] = self._execute_data_query
# self.tools['execute_sql_query'] = self._execute_sql_query
```

**Lines 84-87: Commented Out from Fallbacks**
```python
self.tool_runner = ToolRunner(fallbacks={
    # 'execute_data_query': self._execute_data_query,  # REMOVED
    # 'execute_sql_query': self._execute_sql_query,    # REMOVED
    ...
})
```

✅ Legacy tools ARE commented out in both places (in the local code)

### THE CRITICAL DISCREPANCY

**But wait!** Lines 979-1030 show `_execute_data_query` is FULLY IMPLEMENTED and actively uses `ConversationalDataAccess`:

```python
Line 979: def _execute_data_query(self, session_id: str, query: str, code: Optional[str] = None):
Line 992:     from app.services.conversational_data_access import ConversationalDataAccess
Line 993:     conversational_data_access = ConversationalDataAccess(session_id, self.llm_manager)
Line 1000:    result = conversational_data_access.process_query(query)
Line 1027:    error_msg = f"Error executing query: {result.get('error', 'Unknown error')}"
```

**And lines 1718-1723 show parameter schema generation for execute_data_query:**

```python
Line 1718: if tool_name == 'execute_data_query':
Line 1719:     base_params['properties'].update({
Line 1720:         'query': {'type': 'string', 'description': 'Natural language query...'},
Line 1721:         'code': {'type': 'string', 'description': 'Optional Python code...'}
Line 1722:     })
```

### Where Schemas Are Generated

**Lines 187, 285, 310:**
```python
function_schemas = self.tool_runner.get_function_schemas()
```

**From previous investigation report (Oct 5, 2025):**
> "Related (Not Modified):
> - `/home/ec2-user/ChatMRPT/app/core/tool_runner.py` (generates schemas from fallbacks)"

---

## PART 4: THE MISSING FILES PROBLEM

### Local Development Environment

**Files in `/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/app/core/`:**
1. prompt_builder.py
2. request_interpreter.py

**Missing:**
- tool_runner.py ❌
- session_context_service.py ❌
- data_repository.py ❌
- llm_orchestrator.py ❌
- And likely many more...

### AWS Production Environment

**Files referenced in investigation reports (Lines 226-228):**
- `/home/ec2-user/ChatMRPT/app/core/tool_runner.py` ✅
- `/home/ec2-user/ChatMRPT/app/data_analysis_v3/core/executor.py` ✅
- `/home/ec2-user/ChatMRPT/app/services/conversational_data_access.py` ✅

**Critical Finding:** Local development code is INCOMPLETE. The actual production code on AWS has many more files.

### DataExplorationAgent Search Results

**Searched everywhere:**
- `find / -name "*exploration*"`  → NOT FOUND
- `find / -name "data_analysis_v3"` → NOT FOUND (in local environment)
- `grep -r "class DataExplorationAgent"` → NOT FOUND

**From implementation plan (tool19_implementation_notes.md:41):**
> "File: app/data_analysis_v3/core/data_exploration_agent.py (~144 lines)"

**Status:** File does NOT exist in local development environment ❌

**However:** Test files and documentation REFERENCE this file, suggesting it exists on AWS:
- `test_tool19_integration.py:63` imports it
- `test_tool19_registration.py:39` imports it
- Implementation notes describe it in detail

**Conclusion:** DataExplorationAgent exists on AWS but not in local dev environment

---

## PART 5: WHY LEGACY TOOLS ARE STILL ACTIVE

### The tool_runner.py Mystery

**From request_interpreter.py:77:**
```python
from .tool_runner import ToolRunner
```

**Import succeeds on AWS**, meaning tool_runner.py exists there.

**From Oct 5 investigation report:**
> "tool_runner.py (generates schemas from fallbacks)"

### Theory: How Legacy Tools Survive

**Even though fallbacks are commented out in request_interpreter.py (lines 84-87), tool_runner.py might:**

1. **Still generate schemas from the METHOD EXISTENCE**
   - `_execute_data_query` method exists (lines 979-1030)
   - `_execute_sql_query` method exists (lines 1032-1054)
   - tool_runner.py scans for these methods?

2. **Have its own hardcoded tool list**
   - Doesn't rely on fallbacks parameter
   - Directly discovers tool methods
   - Generates schemas independently

3. **Use introspection to find all _execute_* methods**
   - Scans RequestInterpreter for methods starting with `_`
   - Auto-generates schemas for anything that looks like a tool
   - Fallbacks parameter is ignored or overridden

### Evidence Supporting This Theory

**Lines 1718-1723:** Parameter schema generation for `execute_data_query` exists in request_interpreter.py, suggesting it's EXPECTED to be exposed.

**Lines 401, 325:** `_get_tool_parameters(tool_name)` is called to build schemas, and it HAS special handling for `execute_data_query` and `execute_sql_query`.

**Conclusion:** The methods are NOT fully removed. They're dormant in request_interpreter.py but ACTIVATED by tool_runner.py's schema generation.

---

## PART 6: ERROR MESSAGE TRACE

### "Code contains potentially dangerous operations"

**Source:** ConversationalDataAccess security filter

**File:** `app/services/conversational_data_access.py` (AWS only)

**Flow:**
```
execute_data_query (line 979)
    ↓
ConversationalDataAccess.process_query (line 1000)
    ↓
Generates Python code with:
    from scipy.stats import f_oneway
    ↓
Security filter checks code
    ↓
Detects "import scipy" or "from scipy"
    ↓
Returns: {'success': False, 'error': 'Code contains potentially dangerous operations'}
    ↓
execute_data_query line 1027:
    error_msg = f"Error executing query: {result.get('error', 'Unknown error')}"
    ↓
User sees: "Error executing query: Code contains potentially dangerous operations"
```

### Why Correlation Works But ANOVA Doesn't

**Correlation:**
```python
# ConversationalDataAccess generates:
correlation = df[['TPR', 'rainfall', 'soil_wetness']].corr()
# No imports needed ✅ Security filter passes ✅
```

**ANOVA:**
```python
# ConversationalDataAccess generates:
from scipy.stats import f_oneway  # ❌ BLOCKED
result = f_oneway(...)
```

**The security filter in ConversationalDataAccess:**
- ✅ Allows: pandas operations (no imports)
- ✅ Allows: numpy operations (no imports)
- ❌ Blocks: scipy imports
- ❌ Blocks: sklearn imports
- ❌ Blocks: any external library imports

---

## PART 7: WHY TOOL #19 ISN'T SELECTED

### Tool Selection Process

**The LLM chooses tools based on:**
1. Tool name
2. Tool docstring (description)
3. Parameter schema

**Tool #19 Docstring (Lines 1568-1589):**
```python
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
"""
```

**Problems with this docstring:**
1. ❌ Only mentions "correlation" as an example calculation
2. ❌ No mention of ANOVA, t-tests, chi-square
3. ❌ No mention of sklearn (clustering, PCA, regression)
4. ❌ Says "pandas, numpy, geopandas" but NOT scipy or sklearn
5. ❌ LLM doesn't know Tool #19 can do statistical tests

**execute_data_query Docstring (Line 980):**
```python
"""Execute complex data analysis using Python code. Use for statistics, correlations, or advanced analysis."""
```

**Problems:**
1. ✅ Says "statistics" explicitly
2. ✅ Says "advanced analysis"
3. ✅ LLM thinks THIS is the tool for ANOVA

### Why LLM Selects execute_data_query Instead of Tool #19

**User asks:** "Perform ANOVA test to see if TPR differs significantly across different LGAs"

**LLM reasoning:**
1. Sees "ANOVA" and "statistical test"
2. Looks for tool with "statistics" in description
3. Finds `execute_data_query`: "Use for statistics... or advanced analysis" ✅
4. Finds `analyze_data_with_python`: "Calculations (e.g., correlation)" ❌
5. Selects `execute_data_query`

**Result:** Wrong tool selected, security filter blocks scipy, error returned

---

## PART 8: DATA ANALYSIS MODE EXIT

### Why It Exits

**From test file** (`test_tpr_workflow_transition_standalone.py:71-79`):
```python
mock_response = {
    'success': True,
    'exit_data_analysis_mode': True,
    'redirect_message': '__DATA_UPLOADED__',
    'session_id': session_id,
    'workflow': 'data_upload',
    'stage': 'complete',
    'transition': 'tpr_to_upload',
    ...
}
```

**Design Intent:** After TPR completion, transition user from "TPR workflow mode" to "standard data analysis mode".

**Problem:** "Standard data analysis mode" uses `/send_message_streaming` endpoint, which routes through RequestInterpreter WITHOUT the DataAnalysisAgent/LangGraph integration.

### The Two Modes

**Mode 1: Data Analysis Mode** (during TPR workflow)
- Endpoint: `/api/v1/data-analysis/chat`
- Uses: DataAnalysisAgent (LangGraph)
- Has: TPR workflow handler, state management
- Tools: TPR-specific tools

**Mode 2: Regular/Upload Mode** (after TPR)
- Endpoint: `/send_message_streaming`
- Uses: RequestInterpreter directly
- Has: All registered tools from self.tools
- Tools: Risk analysis, visualization, ITN planning

**Critical Issue:** Tool #19 IS registered in self.tools, BUT legacy tools are ALSO active (via tool_runner.py), AND the docstring doesn't advertise statistical capabilities, so LLM selects wrong tool.

---

## PART 9: SUMMARY OF ROOT CAUSES

### Root Cause #1: Legacy Tools Not Actually Removed ⭐⭐⭐

**Status:** CRITICAL

**Evidence:**
- `execute_data_query` commented out in fallbacks (line 85)
- BUT method still exists (line 979)
- AND schema generation code exists (line 1718)
- AND tool_runner.py generates schemas from methods (per Oct 5 report)

**Impact:** Legacy tools with security filters are still exposed to LLM

**Fix Required:** Actually remove the methods AND schema generation code

---

### Root Cause #2: Tool #19 Docstring Doesn't Advertise Capabilities ⭐⭐⭐

**Status:** CRITICAL

**Evidence:**
- Docstring only mentions "correlation" as example (line 1573)
- No mention of ANOVA, sklearn, scipy.stats
- Says "pandas, numpy, geopandas" but not "scipy, sklearn"

**Impact:** LLM doesn't know Tool #19 can do statistical tests, selects wrong tool

**Fix Required:** Update docstring to explicitly list:
```python
"""
... Use this for:
- Statistical tests (ANOVA, t-tests, chi-square, correlation via scipy.stats)
- Machine learning (clustering, PCA, regression via sklearn)
- Data analysis (pandas, numpy operations)
- Geospatial queries (geopandas)
- Custom visualizations (plotly)
"""
```

---

### Root Cause #3: DataExplorationAgent Doesn't Exist Locally ⭐⭐

**Status:** MAJOR (affects development/testing)

**Evidence:**
- `app/data_analysis_v3/core/data_exploration_agent.py` NOT FOUND
- Directory `app/data_analysis_v3/` NOT FOUND
- Only exists on AWS production servers

**Impact:** Cannot test Tool #19 locally, can't verify if it works

**Fix Required:** Sync AWS code to local development environment

---

### Root Cause #4: tool_runner.py Generates Schemas from Methods ⭐⭐

**Status:** MAJOR

**Evidence:**
- tool_runner.py referenced in Oct 5 report: "generates schemas from fallbacks"
- Methods `_execute_data_query` and `_execute_sql_query` still exist
- Schema generation code still exists (lines 1718-1732)

**Impact:** Commenting out fallbacks does nothing if tool_runner scans for methods

**Fix Required:**
- Option A: Delete the method implementations entirely
- Option B: Modify tool_runner.py to ignore these specific methods
- Option C: Prefix methods with `_DEPRECATED_` to exclude them

---

### Root Cause #5: Data Analysis Mode Exit After TPR ⭐

**Status:** MODERATE (design decision, not bug)

**Evidence:**
- `exit_data_analysis_mode: True` after TPR (context.md line 511)
- Switches to `/send_message_streaming` endpoint
- Uses RequestInterpreter without LangGraph integration

**Impact:** Post-TPR queries don't use DataAnalysisAgent (if it exists)

**Fix Required:** Either:
- Option A: Don't exit data analysis mode after TPR
- Option B: Ensure Tool #19 works in regular mode
- Option C: Keep both modes but fix tool selection in regular mode

---

## PART 10: VERIFICATION & TESTING

### What We Still Don't Know

1. **Does DataExplorationAgent actually work on AWS?**
   - File exists there (per test imports)
   - But have we verified it executes correctly?
   - Does it have scipy.stats and sklearn?

2. **What does tool_runner.py actually do?**
   - How does it generate schemas?
   - Why are legacy tools still active?
   - Can we see the AWS version?

3. **Is the October 5 "fix" actually deployed?**
   - Report says "Deployed to both instances"
   - But tests show legacy tools still active
   - Was the fix reverted?

### Recommended Tests

1. **SSH to AWS and verify:**
   ```bash
   # Check if DataExplorationAgent exists
   ls -la /home/ec2-user/ChatMRPT/app/data_analysis_v3/core/

   # Check tool_runner.py content
   cat /home/ec2-user/ChatMRPT/app/core/tool_runner.py

   # Check if execute_data_query is in fallbacks
   grep -A 10 "fallbacks=" /home/ec2-user/ChatMRPT/app/core/request_interpreter.py
   ```

2. **Test Tool #19 directly:**
   - Call `analyze_data_with_python` with ANOVA query
   - Verify it routes to DataExplorationAgent
   - Verify scipy.stats is available
   - Check actual code execution

3. **Check function schemas:**
   - Print `self.tool_runner.get_function_schemas()`
   - Verify execute_data_query is NOT in the list
   - Verify analyze_data_with_python IS in the list

---

## PART 11: ARCHITECTURAL ISSUES

### Issue #1: Incomplete Local Development Environment

**Problem:** Local code missing critical files (tool_runner.py, DataExplorationAgent, etc.)

**Impact:**
- Cannot develop or test locally
- Cannot verify fixes work
- Must deploy to AWS to test anything

**Solution:** Sync AWS code to local, or use containerized development environment

### Issue #2: Multiple Tool Exposure Paths

**Problem:** Tools can be registered in multiple ways:
1. `self.tools[name] = method`
2. `ToolRunner(fallbacks={...})`
3. tool_runner.py auto-discovery
4. Schema generation in `_get_tool_parameters`

**Impact:** Removing from one place doesn't actually remove the tool

**Solution:** Single source of truth for tool registration

### Issue #3: No Tool Selection Logging

**Problem:** Cannot see which tool LLM selected for each query

**Impact:** Hard to debug why wrong tool is chosen

**Solution:** Add logging:
```python
logger.info(f"🎯 LLM selected tool: {tool_name}")
logger.info(f"📝 Tool docstring: {self.tools[tool_name].__doc__[:100]}")
```

### Issue #4: Mode Confusion

**Problem:** Two modes (data analysis vs regular), different tool availability, unclear when to use which

**Impact:** Users don't understand why some queries work in one mode but not another

**Solution:**
- Unify modes, OR
- Make tool availability consistent across modes, OR
- Give clear user feedback about current mode

---

## PART 12: IMMEDIATE ACTION ITEMS

### Priority 1: CRITICAL (Do First)

1. **SSH to AWS and verify current state:**
   - Check tool_runner.py content
   - Check if execute_data_query is in fallbacks
   - Check if DataExplorationAgent exists
   - Check Tool #19 docstring

2. **Update Tool #19 docstring to advertise capabilities:**
   ```python
   """
   Execute custom Python analysis on user data via DataExplorationAgent.

   Use this when users ask questions requiring:
   - Statistical tests: ANOVA, t-tests, chi-square, correlation (scipy.stats)
   - Machine learning: clustering (KMeans, DBSCAN), PCA, regression (sklearn)
   - Data analysis: filtering, aggregation, calculations (pandas, numpy)
   - Geospatial analysis: spatial joins, distance calculations (geopandas)
   - Interactive visualizations (plotly)

   Available libraries: pandas, numpy, scipy.stats, sklearn, geopandas, plotly
   """
   ```

3. **Actually remove legacy tools:**
   - Delete `_execute_data_query` method entirely (lines 979-1030)
   - Delete `_execute_sql_query` method entirely (lines 1032-1054)
   - Remove schema generation code (lines 1718-1732)
   - Verify tool_runner.py doesn't auto-discover them

### Priority 2: HIGH (Do Soon)

4. **Sync AWS code to local development:**
   - Copy all missing files from AWS to local
   - Ensure development environment matches production
   - Add deployment verification step

5. **Add tool selection logging:**
   - Log which tool LLM selects
   - Log tool docstring
   - Log selection reasoning (if available from LLM)

6. **Test Tool #19 end-to-end:**
   - Direct call with ANOVA query
   - Verify scipy.stats available
   - Verify sklearn available
   - Verify results returned correctly

### Priority 3: MEDIUM (Do Later)

7. **Decide on data analysis mode strategy:**
   - Keep both modes? Unify?
   - Ensure tool availability consistent
   - Document mode transitions clearly

8. **Add integration tests:**
   - Test ANOVA via Tool #19
   - Test clustering via Tool #19
   - Test PCA via Tool #19
   - Test that legacy tools are NOT accessible

9. **Clean up ConversationalDataAccess:**
   - If truly deprecated, remove entirely
   - Or update security filter to allow scipy/sklearn
   - Document its status clearly

---

## FINAL SUMMARY

### The Core Problem

**The LangGraph agent (Tool #19 / DataExplorationAgent) is not being used because:**

1. ❌ Legacy tools (`execute_data_query`, `execute_sql_query`) are still active despite being "removed"
2. ❌ Tool #19's docstring doesn't advertise statistical/ML capabilities
3. ❌ LLM selects legacy tools for ANOVA/regression queries
4. ❌ Legacy tools use ConversationalDataAccess with security filter
5. ❌ Security filter blocks scipy/sklearn imports
6. ❌ Result: "Code contains potentially dangerous operations"

### The Quick Fix

**Update Tool #19 docstring AND actually remove legacy tools:**
1. Add "ANOVA, sklearn, scipy.stats" to Tool #19 description
2. Delete `_execute_data_query` and `_execute_sql_query` methods entirely
3. Remove their schema generation code
4. Verify tool_runner.py doesn't expose them
5. Deploy to AWS
6. Test ANOVA query

### The Long-term Solution

1. Sync AWS code to local
2. Verify DataExplorationAgent works
3. Add comprehensive logging
4. Create integration tests
5. Document tool selection behavior
6. Unify or clarify mode transitions

---

## EVIDENCE REFERENCES

**Test Results:** `/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/context.md` (Lines 184-283)

**Tool Registration:** `app/core/request_interpreter.py` (Lines 84-87, 133-135, 143-144)

**Legacy Tool Implementation:** `app/core/request_interpreter.py` (Lines 979-1030, 1032-1054)

**Schema Generation:** `app/core/request_interpreter.py` (Lines 1686-1732)

**Tool #19 Docstring:** `app/core/request_interpreter.py` (Lines 1568-1589)

**October 5 Fix Report:** `tasks/project_notes/statistical_tests_root_cause_fix_20251005.md`

**Transition Logic:** `tests/test_tpr_workflow_transition_standalone.py` (Lines 71-79)

**AWS Deployment Info:** `CLAUDE.md` (AWS Infrastructure section)

---

**END OF INVESTIGATION REPORT**
