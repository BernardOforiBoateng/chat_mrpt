# LangGraph Agent Test Results Analysis
**Date:** 2025-10-06
**Session ID:** be0bef7a-c877-45ca-9145-8e4ff462b0eb
**Status:** Investigation in Progress

---

## Test Execution Summary

### Test Queries and Results

| # | Query | Result | Error Message |
|---|-------|--------|---------------|
| 1 | "What is the correlation between TPR and rainfall? Also show correlation with soil_wetness and distance_to_waterbodies." | ✅ SUCCESS | - |
| 2 | "Create a correlation heatmap for all numeric variables" | ✅ SUCCESS | - |
| 3 | "Perform an ANOVA test to see if TPR differs significantly across different LGAs. Show me the F-statistic and p-value." | ❌ FAILED | "Error executing query: Code contains potentially dangerous operations" |
| 4 | "Is there a significant difference in TPR across urban categories? Group wards into 'High Urban' (>40%) and 'Low Urban' (<=40%) and run ANOVA." | ❌ FAILED | "Error executing query: Code contains potentially dangerous operations" |
| 5 | "Build a linear regression model to predict TPR from rainfall and soil_wetness. What are the coefficients and R-squared value?" | ❌ FAILED | "Error executing query: Code contains potentially dangerous operations" |
| 6 | "Create a scatter plot of TPR vs rainfall, colored by LGA." | ❌ FAILED | "Y variable 'tpr' not found or not numeric." |
| 7 | "Create a scatter plot of tpr vs rainfall, colored by LGA." (retry with lowercase) | ❌ FAILED | "Y variable 'tpr' not found or not numeric." |
| 8 | "Make a box plot showing TPR distribution for each LGA." | ❌ FAILED | "Tool execution failed: 1 validation error for CreateBoxPlotGrid variables List should have at least 2 items" |
| 9 | "Show me the top 10 wards by TPR that have rainfall > 27700000." | ✅ SUCCESS | - |
| 10 | "Find all wards where distance_to_waterbodies is 0 (adjacent to water). How many are there and what's their average TPR?" | ✅ SUCCESS | - |
| 11 | "Which LGA has the highest average TPR? Show all LGAs ranked by average TPR." | ✅ SUCCESS | - |
| 12 | "Perform ANOVA to test if TPR differs across LGAs" | ❌ FAILED | "Error executing query: Code contains potentially dangerous operations" |

**Success Rate:** 5/12 (41.7%)
**Failure Rate:** 7/12 (58.3%)

---

## Pattern Analysis

### ✅ Working Queries (5)
1. **Correlation analysis** (simple pandas `.corr()`)
2. **Correlation heatmap** (plotly visualization)
3. **Data filtering** ("top 10 wards by TPR with condition")
4. **Aggregation with condition** ("wards where distance_to_waterbodies is 0")
5. **Ranking/GroupBy** ("LGAs ranked by average TPR")

**Common Pattern:**
- Simple pandas operations (filtering, aggregation, correlation)
- No external library imports required (scipy, sklearn)
- Visualization using plotly (heatmap worked)

### ❌ Failing Queries (7)

#### Type 1: "Code contains potentially dangerous operations" (4 queries)
- **ANOVA test #1** - Test across LGAs with F-statistic and p-value
- **ANOVA test #2** - Test across urban categories
- **Linear regression** - Predict TPR from environmental variables
- **ANOVA test #3** - Simple ANOVA across LGAs

**Common Pattern:**
- Requires scipy.stats (ANOVA: `f_oneway`)
- Requires sklearn (Linear regression: `LinearRegression`)
- Security filter blocking imports

#### Type 2: Variable not found (2 queries)
- **Scatter plot #1** - "Y variable 'tpr' not found or not numeric"
- **Scatter plot #2** - Same error (tried lowercase 'tpr')

**Possible Issues:**
- Case sensitivity (TPR vs tpr)
- Column name mismatch
- Tool doesn't have access to correct dataframe

#### Type 3: Validation error (1 query)
- **Box plot** - "List should have at least 2 items after validation, not 1"

**Issue:**
- Tool expects 2+ variables, only got 1 (TPR)
- Tool-specific validation rule

---

## CRITICAL FINDING: Data Analysis Mode Exit

### Workflow Trace (from context.md)

**Line 162-169: TPR Workflow Completion**
```
Assistant: ✅ Results saved to tpr_results.csv
📍 TPR Map Visualization created: tpr_distribution_map.html
✅ Data prepared for risk analysis (environmental variables added)

Ready to continue? Say 'continue' or 'yes'...

You: yes
```

**Line 510-511: System Response**
```json
{
  "exit_data_analysis_mode": true,
  "message": "I've loaded your data from your region. It has 226 rows and 14 columns...",
  "session_id": "be0bef7a-c877-45ca-9145-8e4ff462b0eb",
  "stage": "complete",
  "success": true,
  "transition": "tpr_to_upload",
  "workflow": "data_upload"
}
```

**Line 516-520: Mode Transition**
```
🔄 TRANSITION: Exiting data analysis mode
🔄 TRANSITION: Message to display: I've loaded your data from your region...
```

**Line 533-535: Subsequent Query Routing**
```
🎯 FRONTEND: Endpoint Selection
  🌐 Using endpoint: /send_message_streaming
  🔍 Data Analysis Mode: false
```

### The Problem

**After TPR workflow completion, the system:**
1. ✅ Sets `exit_data_analysis_mode: true`
2. ✅ Transitions to `workflow: "data_upload"`
3. ✅ Exits data analysis mode
4. ❌ **All subsequent queries use `/send_message_streaming` endpoint**
5. ❌ **Queries go through RequestInterpreter's OLD tools, NOT LangGraph agent**

**This means:**
- Tool #19 (`analyze_data_with_python` → DataExplorationAgent) is NEVER called
- Legacy tools are being used instead
- ANOVA/regression fails because legacy `execute_data_query` blocks scipy imports
- The LangGraph agent is completely bypassed

---

## Request Flow Analysis

### Expected Flow (according to architecture)
```
User Query
    ↓
RequestInterpreter.process_message()
    ↓
LLM selects Tool #19 (analyze_data_with_python)
    ↓
DataExplorationAgent created
    ↓
LangGraph agent writes Python code
    ↓
SecureExecutor executes (has scipy.stats, sklearn)
    ↓
Results returned
```

### Actual Flow (from logs)
```
User Query
    ↓
/send_message_streaming endpoint (NOT /api/v1/data-analysis/chat)
    ↓
RequestInterpreter.process_message()
    ↓
LLM selects legacy tool (execute_data_query or similar)
    ↓
Legacy tool execution (NO scipy.stats, NO sklearn)
    ↓
Security filter blocks imports → ERROR
```

---

## Key Questions for Investigation

### 1. Why was data analysis mode exited?
- **File:** Unknown (need to find transition logic)
- **Question:** Why does TPR completion trigger `exit_data_analysis_mode: true`?
- **Expected:** Should stay in data analysis mode for post-TPR queries

### 2. Which endpoint handles queries in regular mode?
- **Observed:** `/send_message_streaming`
- **Question:** Does this endpoint have access to Tool #19?
- **File:** Need to find route handler

### 3. Which tools are actually being called?
- **Correlation queries:** Unknown tool (works, so probably simple tool)
- **ANOVA queries:** Definitely NOT Tool #19 (gets "dangerous operations" error)
- **Question:** How to determine which tool the LLM selected?

### 4. Where is Tool #19 registered?
- **Known:** `app/core/request_interpreter.py:143` (from previous investigation)
- **Question:** Is it accessible from `/send_message_streaming` endpoint?

### 5. Is DataExplorationAgent even imported/used?
- **File:** `app/data_analysis_v3/core/data_exploration_agent.py` (supposedly)
- **Question:** Does this file exist? Is it functional?

---

## Next Steps

1. **Find the endpoint handler** for `/send_message_streaming`
2. **Trace Tool #19 availability** in that endpoint
3. **Locate transition logic** that exits data analysis mode after TPR
4. **Find DataExplorationAgent** implementation
5. **Examine tool selection logs** to see which tool LLM picks
6. **Identify security filter** that blocks scipy imports

---

## Hypotheses

### Hypothesis 1: Tool #19 Not Available in Regular Mode
- **Evidence:** Queries use `/send_message_streaming`, not data analysis endpoint
- **Impact:** Tool #19 only available in data analysis mode, which was exited
- **Test:** Check if Tool #19 is registered in regular RequestInterpreter

### Hypothesis 2: Data Analysis Mode Shouldn't Exit After TPR
- **Evidence:** `exit_data_analysis_mode: true` in response
- **Impact:** Removes access to advanced analysis tools
- **Test:** Find why TPR completion triggers mode exit

### Hypothesis 3: Legacy Tools Still Active
- **Evidence:** "Code contains potentially dangerous operations" (legacy error)
- **Impact:** LLM selecting legacy tools over Tool #19
- **Test:** Check if legacy tools were actually removed from fallbacks

### Hypothesis 4: Tool #19 Docstring Still Vague
- **Evidence:** From previous investigation report
- **Impact:** LLM doesn't know Tool #19 can do ANOVA/regression
- **Test:** Check current docstring of `_analyze_data_with_python`

---

## Status: Investigation Phase 1 Complete

**Findings:**
1. ✅ LangGraph agent (Tool #19) is NOT being used at all
2. ✅ System exits data analysis mode after TPR workflow
3. ✅ Queries route to `/send_message_streaming` (regular mode)
4. ✅ Legacy tools are handling queries, failing on scipy/sklearn imports
5. ⏳ Need to find why mode transition occurs
6. ⏳ Need to verify Tool #19 availability in regular mode
7. ⏳ Need to locate actual DataExplorationAgent code

**Next:** Deep dive into code to understand routing and tool availability.
