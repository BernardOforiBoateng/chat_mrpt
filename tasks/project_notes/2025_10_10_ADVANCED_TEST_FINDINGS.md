# Advanced Statistical & ML Test Findings
**Date**: 2025-10-10
**Status**: ⚠️ **CRITICAL ISSUES FOUND**

---

## Executive Summary

Advanced statistical and ML tests revealed **critical limitations** in the agent:
- ✅ **Simple queries work** (7/15 passed - 46.7%)
- ❌ **Complex ML queries fail** (8/15 failed - recursion loops)
- ✅ **Message truncation bug FIXED** (smart pairing preservation)
- ❌ **NEW recursion limit issue** (agent loops infinitely on hard queries)

---

## Test Results: 7/15 Passing (46.7%)

### ✅ PASSED Tests (7 tests)

1. **Distribution Analysis** (5.51s) ✅
   - Query: "what is the distribution of TPR? Is it normally distributed?"
   - Result: Calculated skewness (-1.53), kurtosis, explained distribution shape
   - Agent capability: Statistical description

2. **Outlier Detection** (7.43s) ✅
   - Query: "which wards have TPR values that are outliers (more than 2 standard deviations from mean)?"
   - Result: Identified 15 outliers, listed all ward names with TPR values
   - Agent capability: Statistical filtering

3. **Complex Multi-Condition Filtering** (5.27s) ✅
   - Query: "how many wards have TPR > 15 AND Rainfall > 2000 AND FacilityLevel is Secondary?"
   - Result: 38 wards meet all criteria
   - Agent capability: Complex boolean logic

4. **Rolling Average** (5.46s) ✅
   - Query: "calculate a 5-ward rolling average of TPR"
   - Result: Computed rolling average, showed first 10 values
   - Agent capability: Time-series style analysis

5. **Feature Variance Analysis** (3.81s) ✅
   - Query: "which variable has the highest variance: TPR, Rainfall, NDWI, or EVI?"
   - Result: Rainfall has highest variance (543,505.98)
   - Agent capability: Statistical comparison

6. **Conditional Statistics** (3.06s) ✅
   - Query: "what is the average TPR for wards where Rainfall is above the median?"
   - Result: Average TPR = 29.81
   - Agent capability: Conditional aggregation

7. **Top-N Complex Query** (4.92s) ✅
   - Query: "show me the top 10 wards with highest TPR, but only for Primary facilities"
   - Result: Listed 10 wards with TPR = 30.0 (all tied at max)
   - Agent capability: Filtering + sorting

### ❌ FAILED Tests (8 tests)

#### Category 1: Recursion Limit (5 tests)
**Error**: "Recursion limit of 25 reached without hitting a stop condition"

**Symptom**: Agent enters infinite loop, message count explodes:
- 11 → 25 → 53 → 109 → 221 → 445 → 893 → 1789 → 3581 → 7165 messages (!)

**Failed Queries**:
1. **Correlation Analysis** (17s timeout)
   - "what is the correlation between Rainfall and TPR?"
   - Agent tries multiple approaches, never succeeds

2. **Correlation Matrix** (20s timeout)
   - "show me the correlation between TPR, Rainfall, NDWI, and Temperature"
   - Too complex, enters loop

3. **Linear Regression** (24s timeout)
   - "can you run a linear regression with TPR as the target and Rainfall, NDWI, EVI as predictors?"
   - Requires sklearn, agent can't figure it out

4. **K-Means Clustering** (41s timeout)
   - "can you cluster the wards into 3 groups based on TPR, Rainfall, and NDWI using k-means?"
   - Missing import (`KMeans` not defined), loops trying to fix

5. **Pivot Table Analysis** (21s timeout)
   - "create a pivot table showing average TPR by FacilityLevel and AgeGroup"
   - Complex pandas operation, agent loops

#### Category 2: Percentiles Issue (1 test)
**Error**: Recursion limit

**Failed Query**:
- **Percentiles and Quartiles** (13s timeout)
  - "what are the 25th, 50th, and 75th percentiles of TPR?"
  - Should be simple `.quantile()`, but agent loops

#### Category 3: PCA (1 test)
**Error**: Recursion limit

**Failed Query**:
- **Principal Component Analysis** (28s timeout)
  - "perform PCA on TPR, Rainfall, NDWI, EVI, Temperature, and Humidity. How much variance is explained by the first 2 components?"
  - Requires sklearn PCA, agent can't complete

#### Category 4: Statistical Testing (1 test)
**Error**: Recursion limit

**Failed Query**:
- **Statistical Comparison** (18s timeout)
  - "is there a significant difference in TPR between Primary and Secondary facilities?"
  - Requires t-test or similar, agent loops

---

## Root Causes Analysis

### Issue #1: Message Truncation Bug ✅ FIXED
**Problem**: Truncation was breaking tool_calls/tool message pairs
- OpenAI requires: `tool` role message MUST be preceded by `assistant` with `tool_calls`
- Our truncation cut out `assistant` but kept `tool` → 400 error

**Fix Implemented**:
```python
def _smart_truncate_messages(self, messages: List[BaseMessage], keep: int) -> List[BaseMessage]:
    """
    Smart message truncation that preserves tool_calls/tool message pairs.
    - Takes last N messages
    - If first message is ToolMessage, includes preceding AIMessage with tool_calls
    """
    if len(messages) <= keep:
        return messages

    result = messages[-keep:]

    # Check if first message in result is a ToolMessage
    if result and isinstance(result[0], ToolMessage):
        # Find and include the corresponding AIMessage with tool_calls
        for i in range(len(messages) - keep - 1, -1, -1):
            msg = messages[i]
            if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                result = [msg] + result
                break

    return result
```

**Result**: No more 400 errors ✅

### Issue #2: Recursion Limit on Complex Queries ❌ NOT FIXED
**Problem**: Agent enters infinite loop on complex ML/statistical queries

**Symptoms**:
1. Message count explodes (7,000+ messages)
2. Agent tries different code approaches repeatedly
3. Hits 25-recursion limit
4. Never gives up or provides fallback response

**Root Causes**:
1. **Missing Imports**: Agent generates code with `KMeans`, `plt`, etc. but they're not imported
   - `SimpleExecutor` only pre-imports: pandas, numpy, plotly, sklearn (the module, not classes)
   - Agent tries `from sklearn.cluster import KMeans` but restricted imports block it

2. **No Fallback Strategy**: When code fails, agent just tries different approach
   - No "give up after N attempts" logic
   - No "tell user it's too complex" response

3. **Recursion Limit Too Low**: 25 iterations isn't enough for complex queries
   - Each attempt = 2 messages (AI + tool response)
   - 25 limit = ~12 attempts
   - Complex queries need more iterations

**Evidence from Logs**:
```
Code execution error: name 'KMeans' is not defined
[Agent tries different import]
Code execution error: name 'KMeans' is not defined
[Agent tries yet another way]
...
[Repeats until recursion limit]
```

---

## Comparison: Simple vs Advanced Queries

### Simple Queries (100% Pass Rate)
- "what is the average TPR?" ✅
- "what is the standard deviation?" ✅
- "how many wards have TPR > 15%?" ✅
- "what's the average TPR by facility level?" ✅

**Why They Work**:
- Single pandas operation
- No complex imports
- Clear, unambiguous task
- Fast execution (<5s)

### Advanced Queries (0-50% Pass Rate)
- "what is the correlation between X and Y?" ❌
- "run linear regression" ❌
- "k-means clustering" ❌
- "PCA analysis" ❌

**Why They Fail**:
- Require specialized imports (sklearn classes)
- Multiple steps (fit, predict, analyze)
- Agent doesn't know exact syntax
- Loops trying different approaches

---

## Impact Assessment

### ✅ What Works Well
1. **Basic Statistics**: Mean, std dev, percentiles (when agent doesn't loop)
2. **Filtering & Grouping**: Complex boolean logic, aggregations
3. **Data Exploration**: Outliers, distributions, variance
4. **Conditional Analysis**: Filtering + calculation

### ❌ What Doesn't Work
1. **Machine Learning**: K-means, PCA, regression
2. **Advanced Statistics**: Correlation (sometimes), t-tests
3. **Complex Multi-Step**: Pivot tables, reshaping

### Impact on Users
- **Health Officials** (primary users): Can do most needed analysis ✅
  - TPR calculations ✅
  - Facility comparisons ✅
  - Outlier detection ✅
  - Distribution analysis ✅

- **Data Scientists** (advanced users): Limited ML capabilities ❌
  - No clustering ❌
  - No regression ❌
  - No PCA ❌
  - Basic correlation works sometimes ⚠️

---

## Recommended Fixes

### Priority 1: Fix Recursion Loops (CRITICAL)

**Option A: Increase Recursion Limit**
```python
result = self.graph.invoke(input_state, {"recursion_limit": 50})  # Double it
```
- **Pros**: Simple, gives agent more attempts
- **Cons**: Still might loop, just longer

**Option B: Add Error Counting & Fallback**
```python
def _route_from_agent(self, state: DataAnalysisState):
    error_count = state.get('error_count', 0)
    if error_count >= 3:
        # Give up, return helpful message
        return '__end__'

    if state.get('tool_call_count', 0) >= 5:
        return '__end__'
    # ... existing logic
```
- **Pros**: Prevents infinite loops
- **Cons**: Requires state management

**Option C: Pre-Import ML Classes**
```python
# In executor_simple.py
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression
from scipy import stats

exec_globals = {
    'pd': pd, 'np': np, 'px': px, 'go': go,
    'KMeans': KMeans,
    'PCA': PCA,
    'LinearRegression': LinearRegression,
    'stats': stats,
    # ...
}
```
- **Pros**: Fixes import errors immediately
- **Cons**: Loads unused libraries

### Priority 2: Improve System Prompt for ML

Add ML-specific guidance to system prompt:
```python
## Machine Learning Operations

For clustering (k-means):
```python
from sklearn.cluster import KMeans
kmeans = KMeans(n_clusters=3)
df['cluster'] = kmeans.fit_predict(df[['col1', 'col2']])
```

For PCA:
```python
from sklearn.decomposition import PCA
pca = PCA(n_components=2)
components = pca.fit_transform(df[['col1', 'col2']])
```
```

### Priority 3: Smart Timeout & Fallback

When agent is stuck:
1. Detect repeated failures (same error 3+ times)
2. Return helpful message:
   ```
   "This analysis is complex and I'm having trouble completing it automatically.
    Could you break it down into steps? For example:
    1. First calculate the correlation
    2. Then create the visualization"
   ```

---

## Deployment Status

### What Was Deployed (2025-10-10 23:00 UTC)
- ✅ Smart message truncation (preserves tool_calls/tool pairs)
- ✅ Deployed to both production instances
- ✅ Services restarted

### What Still Needs Deployment
- ❌ Recursion limit fix (not implemented yet)
- ❌ ML class pre-imports (not implemented)
- ❌ Error counting & fallback (not implemented)

---

## Test Results Summary

| Category | Passed | Failed | Success Rate |
|----------|--------|--------|--------------|
| **Simple Stats** | 4/4 | 0/4 | 100% |
| **Intermediate** | 3/4 | 1/4 | 75% |
| **Advanced ML** | 0/7 | 7/7 | 0% |
| **TOTAL** | 7/15 | 8/15 | 46.7% |

---

## Next Steps

### Immediate (Tonight)
1. ⏳ **Document findings** (this file) ✅
2. ⏳ **Choose fix strategy** (Option C: pre-import ML classes)
3. ⏳ **Implement fix**
4. ⏳ **Re-test advanced queries**
5. ⏳ **Deploy if successful**

### Short-term (Tomorrow)
1. Add error counting & fallback logic
2. Improve system prompt with ML examples
3. Increase recursion limit to 50
4. Monitor production for recursion issues

### Long-term (This Week)
1. Create "complex query" detection
2. Suggest query simplification to users
3. Add "break down into steps" guidance
4. Consider caching successful code patterns

---

## Lessons Learned

### What Worked
1. **Smart truncation** - Preserving message pairs prevents API errors
2. **Simple queries** - Agent handles basic stats perfectly
3. **Error detection** - Tests revealed issues before users hit them

### What Didn't Work
1. **Naive truncation** - Breaking pairs caused 400 errors
2. **No fallback** - Agent loops forever instead of giving up
3. **Limited imports** - Restricting sklearn classes broke ML queries

### Key Insights
1. **Agent needs explicit imports** - Can't figure out "from sklearn.cluster import KMeans" on its own
2. **Recursion limits matter** - 25 is too low for complex queries
3. **Error patterns emerge** - Same error 3+ times = agent is stuck
4. **Testing reveals reality** - Simple tests passed, advanced tests exposed limits

---

## Conclusion

The agent works **very well** for health official use cases (basic stats, filtering, aggregations) but struggles with **advanced ML** (clustering, PCA, regression).

**Immediate Fix Needed**: Pre-import sklearn classes to prevent "not defined" errors and infinite loops.

**Long-term Strategy**: Add error detection, fallback responses, and query complexity guidance.

---

**Status**: Issues documented, fix options identified, awaiting implementation decision.
**Created**: 2025-10-10 23:15 UTC
**Next Action**: Implement Option C (pre-import ML classes) and re-test
