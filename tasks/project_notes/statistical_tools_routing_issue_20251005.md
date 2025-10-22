# Statistical Tools Routing Issue Investigation
**Date:** 2025-10-05
**Status:** ✅ Fixed and Deployed

## Problem Summary

After removing legacy tools (`execute_data_query`, `execute_sql_query`), statistical queries show inconsistent behavior:

**✅ Working:**
- Correlation analysis → Creates heatmap correctly

**❌ Failing:**
- ANOVA test → Asks for clarification instead of executing
- Clustering (K-Means) → Creates correlation heatmap instead
- PCA analysis → Runs full malaria risk analysis instead

## Root Cause: Tool Description Mismatch

### The Problem

The LLM chooses tools based on their docstrings (function descriptions). There are **3 tools** the LLM can see:

### Tool #1: `analyze_data_with_python` (DataExplorationAgent)
**Location:** `app/core/request_interpreter.py:1567-1589`

**Docstring:**
```python
"""
Execute custom Python analysis on user data via DataExplorationAgent.

Use this when users ask questions requiring:
- Custom data queries (e.g., "show top 10 wards by population")
- Calculations (e.g., "what's the correlation between rainfall and TPR")  # ← ONLY mentions correlation!
- Filtering (e.g., "which wards have TPR > 0.5")
- Custom visualizations
- Geospatial queries

This tool can access:
- DataFrames (df) with uploaded data
- GeoDataFrames (gdf) with spatial boundaries
- All pandas, numpy, geopandas operations  # ← No mention of scipy.stats or sklearn!
"""
```

**Actual Capabilities (via SecureExecutor):**
- ✅ scipy.stats (ANOVA, t-tests, chi-square, correlation, etc.)
- ✅ sklearn (clustering, PCA, regression, etc.)
- ✅ pandas, numpy, geopandas
- ✅ plotly visualizations

**Problem:** Docstring is too vague! Only mentions "correlation" as an example. Doesn't advertise statistical tests or machine learning.

### Tool #2: `run_malaria_risk_analysis`
**Location:** `app/core/request_interpreter.py:654-657`

**Docstring:**
```python
"""
Run complete dual-method malaria risk analysis (composite scoring + PCA).  # ← Explicitly mentions PCA!
Use ONLY when analysis has NOT been run yet. DO NOT use if analysis is already complete.
For ITN planning after analysis, use run_itn_planning instead.
"""
```

**Problem:** Mentions "PCA" explicitly, so LLM selects this for "perform PCA" queries!

### Tool #3: `explain_analysis_methodology`
**Location:** `app/core/request_interpreter.py:1088-1089`

**Docstring:**
```python
"""
Explain how malaria risk analysis methodologies work (composite scoring, PCA, or both).  # ← Also mentions PCA!
"""
```

**Problem:** Also mentions "PCA", could be selected for PCA-related queries.

## Why Correlation Works

The `analyze_data_with_python` docstring has this example (line 1573):
> "Calculations (e.g., "what's the correlation between rainfall and TPR")"

**Result:** LLM sees "correlation" in user query → sees "correlation" in docstring → selects correct tool ✅

## Why PCA/Clustering/ANOVA Fail

1. **User asks:** "Perform PCA on environmental variables"
2. **LLM searches docstrings for "PCA":**
   - `analyze_data_with_python`: No mention of "PCA" ❌
   - `run_malaria_risk_analysis`: "composite scoring + PCA" ✅
3. **LLM selects:** `run_malaria_risk_analysis` (wrong tool!)
4. **Result:** Runs full risk analysis instead of PCA

Same issue with clustering and ANOVA - they're not mentioned in `analyze_data_with_python` description.

## Tool Selection Logic Flow

```
User Query: "Perform ANOVA test"
    ↓
LLM checks all tool docstrings for match
    ↓
analyze_data_with_python:
  - Mentions "correlation" ❌
  - Mentions "calculations" (vague) ❌
  - No match for "ANOVA"
    ↓
run_malaria_risk_analysis:
  - Mentions "analysis" ✅ (weak match)
  - Might select this or ask for clarification
    ↓
LLM: Confused, asks user for clarification
```

```
User Query: "Cluster wards into 3 groups"
    ↓
LLM checks all tool docstrings for match
    ↓
analyze_data_with_python:
  - Mentions "correlation" (weak match on "analysis") ✅
  - Best available match (but wrong interpretation)
    ↓
LLM: Selects analyze_data_with_python
    ↓
Agent generates correlation code instead of clustering
    ↓
Result: Correlation heatmap instead of clusters
```

```
User Query: "Perform PCA analysis"
    ↓
LLM checks all tool docstrings for match
    ↓
analyze_data_with_python:
  - No mention of "PCA" ❌
    ↓
run_malaria_risk_analysis:
  - Explicitly mentions "PCA" ✅✅
    ↓
LLM: Selects run_malaria_risk_analysis
    ↓
Result: Full risk analysis instead of PCA
```

## The Fix

Update `_analyze_data_with_python` docstring to explicitly mention statistical and ML capabilities:

**Current (Vague):**
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

**Proposed (Explicit):**
```python
"""
Execute Python analysis on user data including statistical tests and machine learning.

Use this for:
- Statistical tests (correlation, ANOVA, t-tests, chi-square, regression)
- Machine learning (clustering, PCA, classification, dimensionality reduction)
- Data queries (filter, aggregate, top N, statistics)
- Custom calculations and transformations
- Visualizations (charts, plots, heatmaps)
- Geospatial analysis

Available libraries:
- scipy.stats: All statistical tests (f_oneway, ttest_ind, pearsonr, chi2_contingency, etc.)
- sklearn: Clustering (KMeans, DBSCAN), PCA, regression, preprocessing
- pandas, numpy: Data manipulation
- geopandas: Geospatial operations
- plotly: Interactive visualizations

Examples:
- "Perform ANOVA test for TPR across facility levels"
- "Cluster wards into 3 groups based on environmental variables"
- "Run PCA on rainfall, soil_wetness, and distance_to_waterbodies"
- "Calculate correlation between TPR and all environmental factors"
- "Build linear regression model to predict TPR"

DO NOT use run_malaria_risk_analysis for statistical queries - use this tool instead.
"""
```

## Why This Will Work

1. **Explicit capability listing**: LLM sees "ANOVA", "clustering", "PCA" in docstring
2. **Library documentation**: Mentions scipy.stats and sklearn explicitly
3. **Clear examples**: Shows actual statistical test use cases
4. **Direct guidance**: "DO NOT use run_malaria_risk_analysis for statistical queries"

## Implementation Plan

1. Update `_analyze_data_with_python` docstring in `request_interpreter.py`
2. Optionally update `run_malaria_risk_analysis` docstring to reinforce:
   ```
   "Run complete dual-method malaria risk analysis (composite scoring + PCA).
   Use ONLY for full risk assessment workflow.
   For individual statistical tests (ANOVA, PCA, clustering), use analyze_data_with_python instead."
   ```
3. Test all 5 statistical queries from `test_queries_ml_stats.txt`
4. Deploy to both production instances

## Solution Implemented: System Prompt Approach (Better!)

**Decision:** After discussion, we chose to add guidance to the **system prompt** instead of updating individual tool docstrings.

**Why System Prompt is Better:**
- ✅ LLM sees system prompt when selecting tools
- ✅ One central place to document tool capabilities
- ✅ Easier to maintain (change once, not per-tool)
- ✅ Can provide nuanced guidance about when to use what tool
- ✅ Less redundancy across codebase

**File Modified:**
- `/home/ec2-user/ChatMRPT/app/core/prompt_builder.py` (lines 222-264)

**Changes Made:**
Added "Tool Selection Guide" section to system prompt with:
1. Explicit list of statistical tests available in `analyze_data_with_python`
2. Machine learning algorithms available
3. Pre-loaded libraries (scipy.stats, sklearn, etc.)
4. Clear examples: "Perform ANOVA" → Use analyze_data_with_python
5. Explicit negative guidance: "Do NOT use run_malaria_risk_analysis for individual tests"

## Expected Results After Fix

**Query** → **Tool Selected** → **Result**

1. "Correlation analysis" → `analyze_data_with_python` → ✅ Correlation heatmap
2. "ANOVA test" → `analyze_data_with_python` → ✅ ANOVA results with p-value
3. "K-Means clustering" → `analyze_data_with_python` → ✅ Cluster assignments
4. "PCA analysis" → `analyze_data_with_python` → ✅ PCA components and variance
5. "Linear regression" → `analyze_data_with_python` → ✅ Regression coefficients

All queries will consistently use the correct tool (DataExplorationAgent → SecureExecutor with scipy.stats + sklearn).

## Technical Insight

**Key Learning:** Tool selection is purely based on semantic matching between user query and tool docstrings. If capabilities aren't explicitly documented in the docstring, the LLM cannot know about them, even if the underlying code supports them.

**Architecture Pattern:** When exposing tools to LLM:
1. Document ALL capabilities in the docstring
2. Include specific examples for each capability type
3. List available libraries/imports
4. Provide negative guidance (what NOT to use tool for)
5. Use keywords that users are likely to use in queries

## Deployment

**Deployed to:**
- Instance 1: 3.21.167.170 ✅
- Instance 2: 18.220.103.20 ✅

**Deployment Command:**
```bash
for ip in 3.21.167.170 18.220.103.20; do
    scp -i ~/.ssh/chatmrpt-key.pem app/core/prompt_builder.py ec2-user@$ip:/home/ec2-user/ChatMRPT/app/core/
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$ip 'sudo systemctl restart chatmrpt'
done
```

**Both services restarted successfully.**

## Related Files

**Modified (Oct 5):**
1. `app/core/request_interpreter.py` (lines 84-91) - Removed legacy tools from fallbacks
2. `app/core/prompt_builder.py` (lines 222-264) - Added statistical tool guidance to system prompt

**Related (No Changes):**
- `app/data_analysis_v3/core/executor.py` (has scipy.stats + sklearn)
- `app/data_analysis_v3/core/data_exploration_agent.py` (executes Python code)
- `app/core/tool_runner.py` (generates schemas from docstrings)
