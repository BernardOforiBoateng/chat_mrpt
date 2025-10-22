# Tool #19 Analysis & Improvement Plan

**Date**: 2025-10-05
**Status**: Production Analysis - Tool #19 Working ✅
**Based On**: Real conversation data + browser console logs

---

## EXECUTIVE SUMMARY

**✅ Tool #19 is working successfully in production!**

However, analysis reveals three key areas for improvement:
1. **Response Formatting** - Inconsistent markdown, poor readability
2. **Redundant Tools** - Several tools now obsolete with Tool #19
3. **Agent Enhancements** - Data schema awareness, better error handling

---

## 1. RESPONSE FORMATTING ANALYSIS

### Current Issues (from actual conversation)

#### Issue #1: Bullet Points Run Together
**Location**: contxt.md:207-209

**Current Output**:
```
Results:

• WardCode: ADSDSA04 - StateCode: AD - LGACode: 2001 - WardName: Dilli - LGA: Demsa - State: Adamawa - GeopoliticalZone: North-East - TPR: 86.900 - Total_Tested: 2030 - Total_Positive: 1764 - distance_to_waterbodies: 2779.000 - rainfall: 27798692.000 - soil_wetness: 0.526 - urban_percentage: 28.727 • WardCode: ADSDSA03 - StateCode: AD - LGACode: 2001 - WardName: Demsa - LGA: Demsa - State: Adamawa...
```

**Problems**:
- No line breaks between bullet points
- Runs together as one massive paragraph
- Very hard to read
- Missing vertical spacing

**Desired Output**:
```
Results:

• **Dilli** (Ward Code: ADSDSA04)
  - State: Adamawa (North-East)
  - TPR: 86.9%
  - Tested: 2,030 | Positive: 1,764
  - Soil Wetness: 0.526 | Rainfall: 27,798,692
  - Urban: 28.7%

• **Demsa** (Ward Code: ADSDSA03)
  - State: Adamawa (North-East)
  - TPR: 62.5%
  - Tested: 4,058 | Positive: 2,537
  - Soil Wetness: 0.526 | Rainfall: 27,798,692
  - Urban: 57.5%
```

#### Issue #2: Inconsistent Category Headers
**Location**: contxt.md:221-232

**Current Output**:
```
Your dataset contains 14 variables:

Health Indicators: • TPR

Environmental Factors: • distance_to_waterbodies • rainfall • soil_wetness

Socioeconomic Variables: • urban_percentage
```

**Problems**:
- Category headers on same line as bullets
- No clear separation
- Inconsistent formatting

**Desired Output**:
```
Your dataset contains 14 variables:

**Health Indicators**
• TPR

**Environmental Factors**
• distance_to_waterbodies
• rainfall
• soil_wetness

**Socioeconomic Variables**
• urban_percentage

**Geographic Identifiers**
• WardCode, StateCode, LGACode
• WardName, LGA, State

**Other Variables**
• GeopoliticalZone
• Total_Tested, Total_Positive
```

#### Issue #3: Statistics Lack Structure
**Location**: contxt.md:239

**Current Output**:
```
Mean TPR: 71.3782 Median TPR: 72.9800 Min TPR: 36.2300 Max TPR: 91.5200 Standard Deviation of TPR: 11.0327
```

**Problems**:
- All on one line
- No formatting
- Hard to scan

**Desired Output**:
```
**TPR Statistics**

| Metric | Value |
|--------|-------|
| Mean | 71.38 |
| Median | 72.98 |
| Min | 36.23 |
| Max | 91.52 |
| Std Dev | 11.03 |
```

#### Issue #4: Raw DataFrame Output
**Location**: contxt.md:343-346

**Current Output**:
```
WardName distance_to_ref 0 Dilli 61.5679 1 Demsa 53.3829 2 Nassarawo Demsa 38.8607 3 Kpasham 41.9735 4 Borrong 65.1018 .. ... ... 221 Makama A 59.0361 222 Mbamba 64.3466 223 Adarawo 60.5771 224 Ngurore 49.0066 225 Makama B 57.2055

[226 rows x 2 columns]
```

**Problems**:
- Raw pandas DataFrame.__str__() output
- Not user-friendly
- Index numbers shown (0, 1, 2...)
- "[226 rows x 2 columns]" is technical

**Desired Output**:
```
**Ward Distances from Reference Point (9.0, 12.0)**

Showing top 10 closest wards:

| Ward | Distance (km) |
|------|---------------|
| Nassarawo Demsa | 38.86 |
| Kpasham | 41.97 |
| Ngurore | 49.01 |
| Demsa | 53.38 |
| Makama B | 57.21 |
| Makama A | 59.04 |
| Adarawo | 60.58 |
| Dilli | 61.57 |
| Mbamba | 64.35 |
| Borrong | 65.10 |

*Total: 226 wards analyzed*
```

#### Issue #5: "Analysis completed successfully" with no output
**Location**: contxt.md:325

**Current Output**:
```
Analysis completed successfully.
```

**Problems**:
- Says "completed" but shows no result
- User has no idea what the coefficient of variation actually is
- Unhelpful

**Desired Output**:
```
**Coefficient of Variation Analysis**

Coefficient of Variation for composite_score: **0.248** (24.8%)

*Interpretation:* This indicates moderate variability in risk scores across wards. Values between 15-30% suggest reasonable consistency with some spread.
```

#### Issue #6: Long Paragraphs Without Breaks
**Location**: contxt.md:277-288

**Current Output**:
```
Cleaned your data - Fixed ward name mismatches and filled missing values using neighboring areas
Selected 5 risk factors - Based on North East's malaria patterns
Normalized everything - Put all variables on the same 0-1 scale for fair comparison
Ran statistical tests - Checked if your data is suitable for advanced pattern analysis
Calculated risk scores using both methods: • Composite Score: Simple average of all risk factors (transparent and easy to understand) • PCA Score: Statistical method that finds hidden patterns in your data
Ranked all wards - From highest to lowest risk for intervention planning
Behind the Scenes - Statistical Testing: I ran two tests...
```

**Problems**:
- Wall of text
- Hard to scan
- No visual hierarchy
- Bullets mixed with explanations

**Desired Output**:
```
**Analysis Complete!** ✅ I've ranked all 226 wards by malaria risk.

**What I Did:**

1. **Data Cleaning**
   - Fixed ward name mismatches
   - Filled missing values using neighboring areas

2. **Variable Selection**
   - Selected 5 key risk factors
   - Based on North East's malaria patterns

3. **Normalization**
   - Put all variables on 0-1 scale
   - Ensures fair comparison

4. **Statistical Testing**
   - KMO Test: 0.523 ✓ (adequate relationships)
   - Bartlett's Test: p < 0.001 ✓ (significant patterns)

5. **Risk Scoring (Dual Method)**
   - **Composite Score**: Simple average (transparent, easy to understand)
   - **PCA Score**: Statistical patterns (advanced analysis)

6. **Ward Ranking**
   - Ranked from highest to lowest risk
   - Ready for intervention planning

---

**Next Steps:**
• Plan ITN/bed net distribution
• View highest risk wards
• Compare methods visually
• Export results
```

### Summary of Formatting Issues

| Issue | Current State | Impact | Priority |
|-------|---------------|--------|----------|
| Bullet points run together | No line breaks | Very hard to read | **HIGH** |
| Inconsistent headers | Mixed formatting | Confusing structure | **HIGH** |
| Statistics on one line | No table format | Hard to scan | **MEDIUM** |
| Raw DataFrame output | Technical format | Not user-friendly | **HIGH** |
| Empty "success" messages | No actual result | Unhelpful | **MEDIUM** |
| Long paragraphs | No breaks | Poor readability | **HIGH** |
| Missing tables | Text-only | Hard to compare values | **MEDIUM** |

---

## 2. REDUNDANT TOOLS ANALYSIS

### Tools Now Redundant (Can be Removed)

Based on actual conversation showing Tool #19 handling these queries:

#### ✅ CONFIRMED REDUNDANT

**1. execute_data_query**
- **Original Purpose**: Generic data queries
- **Evidence**: "Show me the first 10 rows" handled by Tool #19
- **Replacement**: Tool #19 handles all data queries
- **Action**: **REMOVE** ✅

**2. execute_sql_query**
- **Original Purpose**: SQL queries on data
- **Evidence**: "List all wards in Demsa LGA sorted by TPR" handled by Tool #19
- **Note**: Line 350 shows SQL error ("Referenced column 'latitude' not found")
  - This means SQL tool was called but failed
  - Tool #19 should have been used instead
- **Replacement**: Tool #19 can do SQL-equivalent operations via pandas
- **Action**: **REMOVE** ✅

**3. run_data_quality_check**
- **Original Purpose**: Check for missing values, duplicates, etc.
- **Evidence**: Tool #19 can run `df.info()`, `df.describe()`, `df.isnull().sum()`
- **Replacement**: Tool #19 with appropriate query
- **Action**: **REMOVE** ✅

#### 🤔 POSSIBLY REDUNDANT (Need More Testing)

**4. create_box_plot**
- **Original Purpose**: Create box plots for distributions
- **Evidence**: Tool #19 created scatter plot, histogram successfully
- **Concern**: Dedicated viz tools might be faster/more consistent
- **Action**: **TEST** - If Tool #19 creates good box plots, remove

**5. create_decision_tree**
- **Original Purpose**: Create decision tree visualizations
- **Evidence**: Tool #19 has plotting capabilities
- **Concern**: Decision trees might need specialized formatting
- **Action**: **TEST** - Verify Tool #19 can create interpretable trees

**6. create_composite_score_maps**
- **Original Purpose**: Specialized map visualizations
- **Evidence**: Not tested in conversation
- **Concern**: Geospatial maps might need dedicated tool
- **Action**: **KEEP FOR NOW** - Specialized geospatial visualization

### Tools to KEEP (Still Valuable)

**Essential Workflow Tools:**

**1. run_malaria_risk_analysis** ✅ KEEP
- **Reason**: Complex multi-step workflow
- **Functions**:
  - Zone detection
  - Variable selection by zone
  - Dual-method scoring (Composite + PCA)
  - 26-model ensemble
  - Statistical testing (KMO, Bartlett)
  - Risk categorization
- **Why Tool #19 can't replace**: Requires domain-specific logic, pre-built algorithms
- **Evidence**: Conversation shows this completed successfully (contxt.md:269-289)

**2. run_itn_planning** ✅ KEEP
- **Reason**: Complex allocation algorithm
- **Functions**:
  - Population-based allocation
  - Urban/rural prioritization
  - Coverage calculations
  - Optimization logic
- **Why Tool #19 can't replace**: Requires intervention planning domain knowledge
- **Evidence**: Successfully planned 2M net distribution (contxt.md:408-434)

**3. create_vulnerability_map** ✅ KEEP
- **Reason**: Specialized geospatial visualization
- **Functions**:
  - Choropleth maps with proper color scales
  - Risk category overlays
  - Ward boundary rendering
  - Interactive tooltips
- **Why Tool #19 can't replace**: Geospatial visualization requires specialized libraries
- **Note**: Might be integrated into Tool #19 later, but keep separate for now

**4. create_variable_distribution** ✅ KEEP
- **Reason**: Specialized map creation
- **Evidence**: "Plot me the map distribution for rainfall variable" (contxt.md:250)
- **Functions**:
  - Spatial distribution mapping
  - Variable-specific color scales
  - Summary statistics overlay
- **Why Tool #19 can't replace**: Geospatial + statistical visualization combo
- **Note**: Could eventually merge with Tool #19's plotting capabilities

**5. create_settlement_map** ✅ KEEP
- **Reason**: Specialized for settlement data
- **Functions**:
  - Building classification overlays
  - Settlement type visualization
  - Large geospatial file handling (436MB dataset)
- **Why Tool #19 can't replace**: Specialized data format

**6. show_settlement_statistics** ✅ KEEP
- **Reason**: Specialized for settlement analytics
- **Functions**:
  - Settlement type aggregation
  - Coverage statistics
  - Building count summaries
- **Why Tool #19 can't replace**: Specialized data source

**7. explain_analysis_methodology** ✅ KEEP
- **Reason**: Educational/knowledge tool
- **Functions**:
  - Explains PCA vs Composite
  - Describes risk factors
  - Methodology documentation
- **Why Tool #19 can't replace**: Knowledge-based, not data-based

### Tools List Summary

| Tool Name | Status | Reason |
|-----------|--------|--------|
| analyze_data_with_python | ✅ KEEP | **This is Tool #19** |
| run_malaria_risk_analysis | ✅ KEEP | Complex workflow with domain logic |
| run_itn_planning | ✅ KEEP | Specialized allocation algorithm |
| create_vulnerability_map | ✅ KEEP | Geospatial visualization |
| create_variable_distribution | ✅ KEEP | Spatial distribution maps |
| create_settlement_map | ✅ KEEP | Settlement data visualization |
| show_settlement_statistics | ✅ KEEP | Settlement analytics |
| explain_analysis_methodology | ✅ KEEP | Educational content |
| execute_data_query | ❌ REMOVE | Tool #19 handles this |
| execute_sql_query | ❌ REMOVE | Tool #19 handles this |
| run_data_quality_check | ❌ REMOVE | Tool #19 handles this |
| create_box_plot | 🤔 TEST | Might be redundant |
| create_decision_tree | 🤔 TEST | Might be redundant |
| create_pca_map | 🤔 TEST | Might merge with vulnerability map |
| create_urban_extent_map | 🤔 TEST | Might be redundant |

**Tool Count:**
- **Current**: 19 tools (after adding Tool #19)
- **After Cleanup**: ~12-15 tools (remove 3-7 redundant ones)
- **Future Goal**: 8-10 essential tools

---

## 3. AGENT ENHANCEMENT OPPORTUNITIES

### Enhancement #1: Better Data Schema Awareness

**Problem Identified**: contxt.md:350
```
Error executing SQL: Referenced column "latitude" not found in FROM clause!
LINE 1: SELECT WardName FROM df WHERE ABS(latitude - 9.4) <= 0.5
```

**Issue**:
- Agent tried to query `latitude` column
- Column doesn't exist in dataset
- Error is technical, not user-friendly

**Root Cause**:
- Agent doesn't inspect available columns before generating code
- Makes assumptions about data structure
- No schema validation

**Proposed Enhancement**:

```python
class DataExplorationAgent(DataAnalysisAgent):
    def _get_input_data(self) -> List[Dict[str, Any]]:
        # ... existing code ...

        # NEW: Add schema information to context
        if csv_file and os.path.exists(csv_file):
            df = EncodingHandler.read_csv_with_encoding(csv_file)

            # Build rich schema description
            schema_info = {
                'columns': df.columns.tolist(),
                'dtypes': df.dtypes.to_dict(),
                'sample': df.head(3).to_dict('records'),  # Show example rows
                'numeric_columns': df.select_dtypes(include=[np.number]).columns.tolist(),
                'categorical_columns': df.select_dtypes(include=['object']).columns.tolist(),
                'shape': df.shape
            }

            input_data_list.append({
                'variable_name': 'df',
                'data_description': f"Dataset with {len(df)} rows and {len(df.columns)} columns",
                'data': df,
                'columns': df.columns.tolist(),
                'schema': schema_info  # NEW: Rich schema metadata
            })
```

**System Prompt Enhancement**:
```python
SYSTEM_PROMPT_ADDITION = """
IMPORTANT: Before generating any code, check the available columns in the dataset.

Available columns are provided in the schema metadata.

If a user asks about a column that doesn't exist:
1. Check for similarly named columns (e.g., 'lat' for 'latitude', 'centroid_lat' for 'latitude')
2. Suggest the closest match
3. Ask for clarification

Example:
User: "Which wards are within 0.5 degrees latitude of 9.4?"
You should check: Does 'latitude' column exist?
If not: "I don't see a 'latitude' column. However, I found 'centroid_lat'. Should I use that instead?"
"""
```

**Better Error Messages**:
Instead of:
```
Error executing SQL: Referenced column "latitude" not found
```

Show:
```
I couldn't find a 'latitude' column in your data.

**Available geographic columns:**
• centroid_lat (latitude of ward centroid)
• centroid_lon (longitude of ward centroid)
• WardCode, LGA, State

Did you mean to use 'centroid_lat' instead?

I can help you find wards near latitude 9.4 using this column. Would you like me to proceed?
```

### Enhancement #2: Better Result Formatting

**Problem**: Tool #19 returns raw outputs (DataFrames, lists, etc.)

**Current Behavior** (from agent code):
```python
# Agent executes Python code, returns whatever the code outputs
result = execute_python_code(code)
return {'message': str(result), 'status': 'success'}
```

**Enhancement**: Add formatting layer

```python
class DataExplorationAgent(DataAnalysisAgent):
    def _format_result(self, result: Any, query: str) -> str:
        """Format result for user-friendly display."""

        # DataFrame formatting
        if isinstance(result, pd.DataFrame):
            return self._format_dataframe(result, query)

        # Series formatting
        elif isinstance(result, pd.Series):
            return self._format_series(result, query)

        # Numeric results
        elif isinstance(result, (int, float)):
            return self._format_numeric(result, query)

        # Dict/List formatting
        elif isinstance(result, (dict, list)):
            return self._format_collection(result, query)

        # Default
        else:
            return str(result)

    def _format_dataframe(self, df: pd.DataFrame, query: str) -> str:
        """Format DataFrame as markdown table."""

        # If too many rows, show top N
        if len(df) > 10:
            display_df = df.head(10)
            footer = f"\n\n*Showing first 10 of {len(df)} rows*"
        else:
            display_df = df
            footer = ""

        # Create markdown table
        table = display_df.to_markdown(index=False, floatfmt=".2f")

        # Add header
        header = f"**Results**\n\n"

        return header + table + footer
```

### Enhancement #3: Smart Query Intent Detection

**Problem**: Sometimes Tool #19 is called when a specialized tool would be better

**Example**:
- User: "Plot me the map distribution for rainfall"
- Tool #19 might struggle with geospatial visualization
- `create_variable_distribution` would be perfect

**Enhancement**: Add routing hints in system prompt

```python
ROUTING_HINTS = """
When to delegate to specialized tools:

1. **Geospatial Maps** → Use create_variable_distribution or create_vulnerability_map
   - Keywords: "map", "spatial distribution", "geographic"
   - Example: "Plot rainfall distribution map" → create_variable_distribution

2. **Risk Analysis** → Use run_malaria_risk_analysis
   - Keywords: "risk analysis", "rank wards", "vulnerability assessment"
   - Example: "Run risk analysis" → run_malaria_risk_analysis

3. **ITN Planning** → Use run_itn_planning
   - Keywords: "distribute nets", "ITN allocation", "bed net planning"
   - Example: "Plan net distribution" → run_itn_planning

4. **Simple Data Queries** → YOU handle this (Tool #19)
   - Keywords: "show", "list", "calculate", "correlation", "statistics"
   - Example: "Show top 10 wards" → YOU do this

When in doubt, handle it yourself (Tool #19). Only delegate if there's a clear better tool.
```

### Enhancement #4: Pagination for Large Results

**Problem**: contxt.md:305
```
Found 20 results. Showing first 5:
• Rumde, 0.79, 1
• Gereng, 0.75, 2
...
Use a more specific query to narrow down results.
```

**Issue**:
- Says "Found 20" but only shows 5
- Confusing message "Use more specific query"
- User wanted all 20, not 5

**Enhancement**:

```python
def _handle_large_results(self, df: pd.DataFrame, limit: int = 20) -> str:
    """Handle pagination for large result sets."""

    total = len(df)

    if total == 0:
        return "No results found."

    if total <= limit:
        # Show all
        return self._format_dataframe(df, "")

    else:
        # Show first N with option to see more
        preview = self._format_dataframe(df.head(limit), "")

        footer = f"""

---

**Showing first {limit} of {total} results.**

To see more:
• "Show me the next {limit}" (for next page)
• "Show all results" (to see everything)
• "Export to file" (to download full results)
"""

        return preview + footer
```

### Enhancement #5: Visualization Quality Control

**Problem**: Tool #19 creates visualizations but quality varies

**Current**: Agent generates matplotlib/plotly code, output quality inconsistent

**Enhancement**: Standardized visualization templates

```python
class DataExplorationAgent(DataAnalysisAgent):
    VISUALIZATION_TEMPLATES = {
        'scatter': """
import plotly.express as px

fig = px.scatter(
    df,
    x='{x_col}',
    y='{y_col}',
    title='{title}',
    labels={{'{x_col}': '{x_label}', '{y_col}': '{y_label}'}},
    template='plotly_white',
    hover_data=['WardName'] if 'WardName' in df.columns else None
)
fig.update_layout(
    font=dict(size=12),
    title_font_size=16,
    xaxis_title_font_size=14,
    yaxis_title_font_size=14
)
fig.show()
""",

        'histogram': """
import plotly.express as px

fig = px.histogram(
    df,
    x='{x_col}',
    nbins=30,
    title='{title}',
    labels={{'{x_col}': '{x_label}'}},
    template='plotly_white'
)
fig.update_layout(
    font=dict(size=12),
    title_font_size=16,
    xaxis_title_font_size=14,
    yaxis_title_font_size=14
)
fig.show()
"""
    }
```

### Enhancement #6: Add Explanatory Context

**Problem**: contxt.md:330
```
Interquartile Range of pca_score: 0.8263
```

**Issue**: Just a number, no context

**Enhancement**: Add interpretation

```python
def _add_interpretation(self, metric: str, value: float) -> str:
    """Add explanatory context to statistical results."""

    interpretations = {
        'iqr': lambda v: f"""
**Interquartile Range (IQR): {v:.4f}**

*What this means:*
The IQR is {v:.4f}, which represents the spread of the middle 50% of your data.

- **Low IQR (<0.5)**: Data is tightly clustered
- **Medium IQR (0.5-1.0)**: Moderate spread ✓ (your case)
- **High IQR (>1.0)**: Wide spread, high variability

This suggests your PCA scores have moderate variability across wards.
""",

        'coefficient_of_variation': lambda v: f"""
**Coefficient of Variation: {v:.3f}** ({v*100:.1f}%)

*What this means:*
The CV is {v*100:.1f}%, indicating the relative variability.

- **Low (<15%)**: Very consistent
- **Medium (15-30%)**: Moderate variability ✓ (your case)
- **High (>30%)**: High variability

Your data shows reasonable consistency with some natural variation.
"""
    }

    return interpretations.get(metric, lambda v: str(v))(value)
```

---

## 4. IMPLEMENTATION PRIORITY

### Phase 1: Critical Formatting Fixes (Week 1)

**Impact**: HIGH | **Effort**: MEDIUM | **Priority**: 🔴 URGENT

**What to Fix**:
1. ✅ Fix bullet point line breaks
2. ✅ Add proper section headers with spacing
3. ✅ Format DataFrames as markdown tables
4. ✅ Add interpretations to numeric results
5. ✅ Structure long paragraphs with headings

**Where to Fix**:
- `app/data_analysis_v3/core/formatters.py` (create if doesn't exist)
- `app/data_analysis_v3/core/agent.py` (add formatting layer)
- `app/core/request_interpreter.py` (_analyze_data_with_python return formatting)

### Phase 2: Remove Redundant Tools (Week 2)

**Impact**: MEDIUM | **Effort**: LOW | **Priority**: 🟡 HIGH

**What to Remove**:
1. ✅ execute_data_query
2. ✅ execute_sql_query
3. ✅ run_data_quality_check

**Where to Modify**:
- `app/core/request_interpreter.py` (remove from _register_tools())
- Tool runner cleanup

**Testing Required**:
- Verify Tool #19 handles all queries these tools used to handle
- Check no existing workflows break

### Phase 3: Agent Enhancements (Week 3-4)

**Impact**: HIGH | **Effort**: HIGH | **Priority**: 🟢 MEDIUM

**What to Add**:
1. ✅ Data schema awareness
2. ✅ Better error messages with suggestions
3. ✅ Result pagination
4. ✅ Visualization templates
5. ✅ Interpretive context for statistics

**Where to Modify**:
- `app/data_analysis_v3/core/data_exploration_agent.py`
- `app/data_analysis_v3/prompts/system_prompt.py`

---

## 5. SPECIFIC CODE LOCATIONS TO MODIFY

### Formatting Fixes

**File**: `app/data_analysis_v3/core/formatters.py` (CREATE NEW)
```python
class ResponseFormatter:
    """Format agent responses for user-friendly display."""

    @staticmethod
    def format_dataframe(df: pd.DataFrame, title: str = None) -> str:
        """Format DataFrame as markdown table with proper spacing."""
        ...

    @staticmethod
    def format_statistics(stats: dict) -> str:
        """Format statistics as markdown table."""
        ...

    @staticmethod
    def format_list_results(items: list, title: str = None) -> str:
        """Format list with proper bullets and spacing."""
        ...
```

**File**: `app/data_analysis_v3/core/agent.py` (MODIFY)
```python
# Line ~200 (after analyze() returns result)
from .formatters import ResponseFormatter

def analyze(self, query: str) -> Dict[str, Any]:
    # ... existing code ...

    # NEW: Format result before returning
    if 'message' in result:
        result['message'] = ResponseFormatter.format_response(
            result['message'],
            result.get('result_type', 'text')
        )

    return result
```

### Tool Removal

**File**: `app/core/request_interpreter.py` (MODIFY)
```python
# Line ~140: _register_tools()

# REMOVE these lines:
# self.tools['execute_data_query'] = self._execute_data_query
# self.tools['execute_sql_query'] = self._execute_sql_query
# self.tools['run_data_quality_check'] = self._run_data_quality_check

# Keep these:
self.tools['run_malaria_risk_analysis'] = self._run_malaria_risk_analysis
self.tools['create_vulnerability_map'] = self._create_vulnerability_map
# ... other essential tools ...
self.tools['analyze_data_with_python'] = self._analyze_data_with_python  # Tool #19
```

### Agent Enhancements

**File**: `app/data_analysis_v3/core/data_exploration_agent.py` (MODIFY)
```python
# Add after __init__()
def _validate_column_exists(self, column: str, df: pd.DataFrame) -> tuple[bool, str]:
    """Check if column exists, suggest alternatives if not."""
    if column in df.columns:
        return True, column

    # Find similar columns
    from difflib import get_close_matches
    suggestions = get_close_matches(column, df.columns, n=3, cutoff=0.6)

    if suggestions:
        return False, f"Column '{column}' not found. Did you mean: {', '.join(suggestions)}?"
    else:
        return False, f"Column '{column}' not found. Available columns: {', '.join(df.columns)}"
```

**File**: `app/data_analysis_v3/prompts/system_prompt.py` (MODIFY)
```python
# Add to existing MAIN_SYSTEM_PROMPT

COLUMN_VALIDATION_SECTION = """
IMPORTANT: Always validate columns before using them in code.

Before generating code that references a column:
1. Check if it exists in df.columns
2. If not, check for similar names
3. Ask user for clarification if unsure

Example:
User asks: "Filter by latitude > 9.0"
You should:
- Check: 'latitude' in df.columns?
- If no: Look for 'centroid_lat', 'lat', etc.
- Respond: "I found 'centroid_lat' instead of 'latitude'. Should I use that?"
"""
```

---

## 6. TESTING PLAN

### Test 1: Formatting Improvements
```
Query: "Show me the first 10 rows"
Expected: Proper markdown table with clear headers
Verify: No bullet points run together
```

### Test 2: Statistics Formatting
```
Query: "Show me basic statistics for TPR"
Expected: Formatted table with labels
Verify: Not all on one line
```

### Test 3: DataFrame Pagination
```
Query: "Show me all wards sorted by TPR"
Expected: First 20 with "see more" option
Verify: Clear indication of total count
```

### Test 4: Error Handling
```
Query: "Filter by latitude > 9.0"
Expected: Suggestion to use 'centroid_lat'
Verify: Helpful error message, not technical SQL error
```

### Test 5: Redundant Tool Removal
```
Query: "Run a SQL query to get wards in Demsa"
Expected: Tool #19 handles it (not execute_sql_query)
Verify: Check logs - should show analyze_data_with_python
```

---

## 7. SUCCESS METRICS

**Formatting**:
- ✅ No more run-together bullet points
- ✅ All DataFrames shown as markdown tables
- ✅ Statistics formatted with clear labels
- ✅ Proper vertical spacing between sections

**Tool Reduction**:
- ✅ Remove 3 redundant tools minimum
- ✅ Tool count: 19 → 16 (or lower)
- ✅ No functionality lost

**Agent Quality**:
- ✅ Better error messages (no raw SQL errors)
- ✅ Column suggestions when names don't match
- ✅ Interpretive context for statistics
- ✅ Pagination for large results

**User Experience**:
- ✅ Faster response times (fewer tools = less routing overhead)
- ✅ More readable outputs
- ✅ Fewer "I don't understand" errors

---

## 8. ROLLOUT STRATEGY

### Week 1: Formatting Fixes
1. Create formatters.py
2. Integrate into agent.py
3. Test locally
4. Deploy to production
5. Monitor user feedback

### Week 2: Tool Removal
1. Remove execute_data_query
2. Remove execute_sql_query
3. Remove run_data_quality_check
4. Update tool descriptions
5. Test all query types still work
6. Deploy to production

### Week 3-4: Agent Enhancements
1. Add schema awareness
2. Add column validation
3. Add result pagination
4. Add interpretation layer
5. Test edge cases
6. Deploy to production

---

**Analysis Complete!** Ready to proceed with implementation plan.
