# Tool #19 Fix - Step-by-Step Action Plan
**Date:** 2025-10-06
**Priority:** CRITICAL - System Not Using LangGraph Agent

---

## STEP 1: Diagnose Current AWS State (DO THIS FIRST)

### Option A: Using AWS Session Manager (Recommended)

1. Go to AWS Console → EC2 → Instances
2. Select instance `i-0994615951d0b9563` (3.21.167.170)
3. Click "Connect" → "Session Manager" → "Connect"
4. Run diagnostic commands:

```bash
# Check fallbacks configuration
grep -A 10 "fallbacks=" /home/ec2-user/ChatMRPT/app/core/request_interpreter.py

# Check if legacy methods still exist
grep -n "def _execute_data_query" /home/ec2-user/ChatMRPT/app/core/request_interpreter.py
grep -n "def _execute_sql_query" /home/ec2-user/ChatMRPT/app/core/request_interpreter.py

# Check tool_runner.py
ls -la /home/ec2-user/ChatMRPT/app/core/tool_runner.py
head -100 /home/ec2-user/ChatMRPT/app/core/tool_runner.py

# Check DataExplorationAgent
ls -la /home/ec2-user/ChatMRPT/app/data_analysis_v3/core/data_exploration_agent.py

# Check Tool #19 docstring
grep -A 25 "def _analyze_data_with_python" /home/ec2-user/ChatMRPT/app/core/request_interpreter.py
```

### Option B: Using SSH (If you have the key)

```bash
# SSH to instance 1
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@3.21.167.170

# Then run the same commands as above
```

### What We're Looking For

1. **Are legacy methods still in the code?**
   - If YES → They need to be deleted
   - If NO → Something else is exposing them

2. **What's in tool_runner.py?**
   - Does it auto-discover methods?
   - Does it use fallbacks parameter?
   - Does it have hardcoded tool lists?

3. **Does DataExplorationAgent exist?**
   - If YES → Good, we can use it
   - If NO → Major problem, need to investigate

4. **What does Tool #19 docstring say?**
   - Does it mention scipy, sklearn, ANOVA?
   - Or is it still vague like locally?

---

## STEP 2: Based on Diagnostic Results

### Scenario A: Legacy Methods Still Exist (Most Likely)

**Fix:**
1. Delete `_execute_data_query` method entirely
2. Delete `_execute_sql_query` method entirely
3. Delete `_run_data_quality_check` method if it exists
4. Remove schema generation code for these tools
5. Update Tool #19 docstring

**Commands:**
```bash
# Backup first
cp /home/ec2-user/ChatMRPT/app/core/request_interpreter.py /home/ec2-user/ChatMRPT/app/core/request_interpreter.py.backup_$(date +%Y%m%d_%H%M%S)

# Edit the file (I'll provide the exact edits after diagnostic)
nano /home/ec2-user/ChatMRPT/app/core/request_interpreter.py
```

### Scenario B: tool_runner.py Auto-Discovers Methods

**Fix:**
1. Modify tool_runner.py to exclude legacy methods
2. OR prefix legacy methods with `_DEPRECATED_`
3. Update Tool #19 docstring

### Scenario C: DataExplorationAgent Doesn't Exist

**Fix:**
1. Tool #19 won't work at all
2. Need to copy implementation from somewhere
3. Or revert to pure RequestInterpreter approach

---

## STEP 3: The Actual Fixes (After Diagnostic)

### Fix #1: Update Tool #19 Docstring

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

**New (Explicit):**
```python
"""
Execute custom Python analysis on user data via DataExplorationAgent.

Use this tool for ALL data analysis queries including:

STATISTICAL TESTS (scipy.stats):
- ANOVA tests (f_oneway, kruskal)
- t-tests (ttest_ind, ttest_rel, mannwhitneyu)
- Correlation tests (pearsonr, spearmanr)
- Chi-square tests (chi2_contingency)
- Normality tests (shapiro, kstest)

MACHINE LEARNING (sklearn):
- Clustering (KMeans, DBSCAN, AgglomerativeClustering)
- Dimensionality reduction (PCA, NMF, t-SNE)
- Regression (LinearRegression, LogisticRegression, RandomForest)
- Classification (DecisionTree, SVM, GradientBoosting)
- Preprocessing (StandardScaler, MinMaxScaler)

DATA ANALYSIS (pandas, numpy):
- Filtering, aggregation, groupby operations
- Custom calculations and transformations
- Statistical summaries (describe, quantile, etc.)

GEOSPATIAL ANALYSIS (geopandas):
- Spatial joins and overlays
- Distance calculations
- Coordinate transformations

VISUALIZATIONS (plotly):
- Interactive charts (scatter, bar, line, heatmap)
- Statistical plots (box, violin, histogram)
- Geospatial maps

Available libraries: pandas, numpy, scipy, sklearn, geopandas, plotly, matplotlib, seaborn

Args:
    session_id: Session identifier
    query: Natural language description of analysis to perform

Returns:
    Dict with response, visualizations, tools_used
"""
```

### Fix #2: Delete Legacy Methods

**File:** `/home/ec2-user/ChatMRPT/app/core/request_interpreter.py`

**Delete these entire methods:**
1. `def _execute_data_query` (lines ~979-1030)
2. `def _execute_sql_query` (lines ~1032-1054)
3. `def _run_data_quality_check` (if it exists)

**Delete schema generation code:**
1. Lines ~1718-1723 (execute_data_query schema)
2. Lines ~1725-1732 (execute_sql_query schema)

**Verify fallbacks are commented out:**
```python
# Lines 84-87 should look like:
self.tool_runner = ToolRunner(fallbacks={
    # 'execute_data_query': self._execute_data_query,  # REMOVED
    # 'execute_sql_query': self._execute_sql_query,    # REMOVED
    'explain_analysis_methodology': self._explain_analysis_methodology,
    ...
})
```

### Fix #3: Verify Tool #19 Implementation

**Check if Tool #19 method exists:**
```bash
grep -A 50 "def _analyze_data_with_python" /home/ec2-user/ChatMRPT/app/core/request_interpreter.py
```

**Should import and call DataExplorationAgent:**
```python
def _analyze_data_with_python(self, session_id: str, query: str) -> Dict[str, Any]:
    try:
        from app.data_analysis_v3.core.data_exploration_agent import DataExplorationAgent

        agent = DataExplorationAgent(session_id=session_id)
        result = agent.analyze_sync(query)

        return {
            'status': result.get('status', 'success'),
            'response': result.get('message', ''),
            'visualizations': result.get('visualizations', []),
            'tools_used': ['analyze_data_with_python'],
            'insights': result.get('insights', [])
        }
    except Exception as e:
        return {
            'status': 'error',
            'response': f'I encountered an error analyzing the data: {str(e)}',
            'tools_used': ['analyze_data_with_python']
        }
```

---

## STEP 4: Deploy to Both Instances

### Instance 1: 3.21.167.170

```bash
# After making changes, restart service
sudo systemctl restart chatmrpt

# Check logs
sudo journalctl -u chatmrpt -f
```

### Instance 2: 18.220.103.20

```bash
# Make SAME changes to instance 2
# Then restart
sudo systemctl restart chatmrpt
```

**CRITICAL:** Both instances must have identical code!

---

## STEP 5: Test the Fix

### Test Query 1: Simple ANOVA

```
POST /send_message_streaming
{
  "message": "Perform ANOVA to test if TPR differs across LGAs",
  "session_id": "be0bef7a-c877-45ca-9145-8e4ff462b0eb"
}
```

**Expected Result:**
- ✅ Tool selected: `analyze_data_with_python`
- ✅ Calls DataExplorationAgent
- ✅ Generates scipy.stats code
- ✅ Returns F-statistic and p-value

**NOT:**
- ❌ "Code contains potentially dangerous operations"

### Test Query 2: Linear Regression

```
POST /send_message_streaming
{
  "message": "Build a linear regression model to predict TPR from rainfall and soil_wetness",
  "session_id": "be0bef7a-c877-45ca-9145-8e4ff462b0eb"
}
```

**Expected Result:**
- ✅ Uses sklearn.LinearRegression
- ✅ Returns coefficients and R-squared

### Test Query 3: K-Means Clustering

```
POST /send_message_streaming
{
  "message": "Cluster wards into 3 groups based on TPR and rainfall",
  "session_id": "be0bef7a-c877-45ca-9145-8e4ff462b0eb"
}
```

**Expected Result:**
- ✅ Uses sklearn.KMeans
- ✅ Returns cluster assignments

---

## STEP 6: Add Logging to Verify Tool Selection

### Temporary Debug Logging

**File:** `/home/ec2-user/ChatMRPT/app/core/request_interpreter.py`

**Add after line ~480 (where tools are executed):**
```python
if function_name:
    logger.info(f"🎯 TOOL SELECTION DEBUG:")
    logger.info(f"  Selected Tool: {function_name}")
    logger.info(f"  User Query: {user_message[:100]}")
    logger.info(f"  Tool Docstring: {self.tools[function_name].__doc__[:200] if function_name in self.tools else 'N/A'}")
```

This will help us verify the LLM is selecting the right tool.

---

## STEP 7: If Still Failing

### Fallback Plan A: Force Tool #19 for Statistical Queries

Add routing logic in `process_message`:

```python
# Add before LLM tool selection
statistical_keywords = ['anova', 'regression', 'clustering', 'pca', 't-test', 'chi-square']
if any(keyword in user_message.lower() for keyword in statistical_keywords):
    logger.info(f"🎯 Auto-routing statistical query to Tool #19")
    return self._analyze_data_with_python(session_id, user_message)
```

### Fallback Plan B: Remove ConversationalDataAccess Entirely

If legacy tools keep getting called somehow, delete the service:

```bash
mv /home/ec2-user/ChatMRPT/app/services/conversational_data_access.py \
   /home/ec2-user/ChatMRPT/app/services/conversational_data_access.py.DISABLED
```

---

## Summary: What You Need to Do

1. **SSH to AWS instance 1** (3.21.167.170)
2. **Run diagnostic commands** from Step 1
3. **Share the output with me** so I can see current state
4. **I'll provide exact fixes** based on what we find
5. **Apply fixes to BOTH instances**
6. **Test with ANOVA query**
7. **Verify it works**

The key is: **Let's see what's actually on AWS first**, then we'll fix it precisely.

Ready to start? SSH to AWS and run the diagnostic commands.
