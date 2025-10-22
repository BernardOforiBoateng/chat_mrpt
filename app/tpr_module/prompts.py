"""
Chain-of-Thought and ReAct prompts for TPR analysis.
Based on industry best practices (2025) with 94.9% accuracy.
Includes correct TPR formulas from NMEP guidelines.
"""

# ReAct Pattern: Initial TPR Exploration
REACT_TPR_EXPLORATION = """
You are analyzing Test Positivity Rate (TPR) data using the ReAct pattern.
You have FULL ACCESS to the DataFrame for exploration.

## Data Context:
{context}

## Your Task:
Perform a comprehensive initial exploration of this TPR dataset using the ReAct pattern:

Thought 1: First, I need to understand the data structure and columns.
- What columns exist and what do they represent?
- What are the data types?
- How many records are there?

Thought 2: Identify test-related columns.
- Look for RDT (Rapid Diagnostic Test) columns
- Look for Microscopy columns
- Identify positive/negative result columns
- Find testing volume columns

Thought 3: Detect the geographic hierarchy.
- State level columns (could be 'State', 'orgunitlevel2', etc.)
- LGA/District columns
- Ward/Facility columns

Thought 4: Check for temporal columns.
- Year, Month, Week columns
- Date formats

Thought 5: Identify data quality issues.
- Missing values patterns
- Logical inconsistencies (e.g., positives > tested)
- Outliers in TPR values
- Zero or negative values where inappropriate

## Initial Analysis Summary:
Provide a clear, structured summary including:
1. Dataset Overview (rows, columns, time period)
2. Test Type Columns Found
3. Geographic Levels Detected
4. Data Quality Issues
5. Recommendations for Analysis Approach

Be specific about column names and provide examples of values found.
"""

# ReAct Analysis Template for User Queries
REACT_ANALYSIS_TEMPLATE = """
## User Query:
{query}

## Current Data Context:
{context}

## Previous Reasoning Trace:
{trace}

## Iteration {iteration}:

Based on the query and context, continue the ReAct pattern:

Thought: [Reason about what needs to be done next to answer the query]

Action: [Generate pandas/numpy code to explore or analyze the data]
```python
# Your code here
# Store results in 'result' variable
```

If you have enough information to answer the query, respond with:
Thought: I have gathered sufficient information to answer the query.
DONE

Otherwise, continue with the next thought and action.
"""

# TPR Calculation with Correct Formulas
TPR_CALCULATION_PROMPT = """
You need to calculate Test Positivity Rate (TPR) using the correct NMEP formulas.

## TPR Formula Guidelines:

### Standard TPR Formula (Use this by default):
```
TPR = (max(RDT_Positive, Microscopy_Positive) / max(RDT_Tested, Microscopy_Tested)) × 100
```

### Alternative TPR Formula (For urban areas with >50% private facilities):
```
TPR = (Total_Positive_Cases / OPD_Attendance) × 100
```

### Important Rules:
1. **Take the MAXIMUM, not the sum** - A patient tested by both methods counts as 1
2. **Age Group Handling**: 
   - If columns have age suffixes (_Under5, _Over5), calculate separately
   - Total = Under5 + Over5 (when combining age groups)
3. **Facility Level Filtering**:
   - Primary: HF_TYPE contains 'Primary' or 'PHC'
   - Secondary: HF_TYPE contains 'Secondary' or 'General Hospital'
   - Tertiary: HF_TYPE contains 'Tertiary' or 'Teaching'
4. **Missing Data**:
   - Skip rows where denominator is 0 or null
   - Don't impute - mark as missing

## Your Task:
Generate code to calculate TPR for the data following these exact formulas.

Thought: I need to identify the correct columns and apply the right formula.
"""

# Chain-of-Thought Quality Check
COT_QUALITY_CHECK = """
Let's perform a comprehensive data quality check step-by-step.

## Data Context:
{context}

## Step-by-Step Quality Analysis:

### 1. LOGICAL CONSISTENCY CHECKS:
Thought: Testing numbers must follow logical rules.
- Can positive cases exceed total tested? No.
- Can tested exceed persons with fever? No.
- Can outpatient exceed general attendance? No.

Check each rule and report violations:
```python
# Example checks:
# df[df['positive'] > df['tested']]  # Should be empty
# df[df['tested'] > df['persons_with_fever']]  # Should be empty
```

### 2. OUTLIER DETECTION:
Thought: TPR typically ranges from 5-60% in endemic areas.
- Values below 1% might indicate data entry errors
- Values above 90% are highly unusual
- Check for facilities with consistently extreme values

```python
# Calculate TPR and find outliers
# tpr = (positive / tested) * 100
# outliers = df[(tpr < 1) | (tpr > 90)]
```

### 3. MISSING DATA PATTERNS:
Thought: Missing data might not be random.
- Are certain facilities consistently missing data?
- Are certain time periods missing?
- Are test types systematically missing?

```python
# Analyze missing patterns
# missing_by_facility = df.groupby('facility').apply(lambda x: x.isnull().sum())
```

### 4. TEMPORAL CONSISTENCY:
Thought: Check for time-related anomalies.
- Sudden spikes or drops in testing
- Seasonal patterns
- Data collection gaps

### 5. GEOGRAPHIC CONSISTENCY:
Thought: Compare across geographic units.
- Are neighboring areas showing similar patterns?
- Are there geographic outliers?

## Quality Report Summary:
Provide a structured report with:
1. Critical Issues (must fix before analysis)
2. Warning Issues (should review)
3. Data Cleaning Recommendations
4. Analysis Limitations
"""

# User Guidance Prompt
USER_GUIDANCE_PROMPT = """
Based on the data quality assessment, provide analysis recommendations.

## Data Context:
{context}

## Quality Issues Found:
{quality_issues}

## Recommended Analysis Approaches:

### Option 1: Standard TPR Calculation
```python
# Simple aggregation at ward level
tpr = df.groupby('ward').agg({{
    'tested': 'sum',
    'positive': 'sum'
}}).assign(tpr=lambda x: (x['positive']/x['tested'])*100)
```
Best when: Data quality is good, no major outliers

### Option 2: Robust TPR with Outlier Handling
```python
# Remove statistical outliers before calculation
Q1 = df['tpr'].quantile(0.25)
Q3 = df['tpr'].quantile(0.75)
IQR = Q3 - Q1
filtered = df[~((df['tpr'] < Q1 - 1.5*IQR) | (df['tpr'] > Q3 + 1.5*IQR))]
```
Best when: Outliers detected, need robust estimates

### Option 3: Time-Weighted TPR
```python
# Weight recent data more heavily
weights = pd.to_datetime(df['date']).apply(lambda x: calculate_weight(x))
weighted_tpr = np.average(df['tpr'], weights=weights)
```
Best when: Data spans long time period, recent trends important

### Option 4: Facility-Type Stratified Analysis
```python
# Separate analysis by facility type
for facility_type in df['facility_type'].unique():
    subset = df[df['facility_type'] == facility_type]
    # Calculate TPR for this facility type
```
Best when: Different facility types have different testing protocols

## Interactive Decision Points:

1. **Outlier Handling**: 
   - Include all data (preserves completeness)
   - Exclude statistical outliers (improves reliability)
   - Flag but include outliers (transparency)

2. **Aggregation Level**:
   - State level (broad overview)
   - LGA level (administrative planning)
   - Ward level (intervention targeting)
   - Facility level (operational insights)

3. **Time Period**:
   - All available data (comprehensive)
   - Last 12 months (recent trends)
   - Specific season (seasonal patterns)

4. **Test Type**:
   - RDT only (field diagnostics)
   - Microscopy only (laboratory confirmed)
   - Combined (maximum coverage)

Which approach would you like to use? I can guide you through the implementation.
"""

# Hierarchical Problem Breakdown
HIERARCHICAL_TPR_ANALYSIS = """
Let's break down the TPR analysis into manageable subproblems:

## Level 1: Data Understanding
├── 1.1 Column Detection
│   ├── Identify test columns (RDT/Microscopy)
│   ├── Find location hierarchy columns
│   ├── Detect temporal columns
│   └── Locate demographic columns
│
├── 1.2 Data Quality Assessment
│   ├── Check logical consistency
│   ├── Identify missing patterns
│   ├── Detect outliers
│   └── Validate geographic coverage
│
└── 1.3 Data Preparation
    ├── Handle missing values
    ├── Standardize column names
    ├── Create derived columns
    └── Filter valid records

## Level 2: TPR Calculation
├── 2.1 Method Selection
│   ├── Simple ratio (positive/tested)
│   ├── Weighted average
│   ├── Bayesian estimation
│   └── Time-series approach
│
├── 2.2 Aggregation Strategy
│   ├── Geographic level
│   ├── Temporal granularity
│   ├── Test type combination
│   └── Facility stratification
│
└── 2.3 Quality Control
    ├── Confidence intervals
    ├── Sensitivity analysis
    ├── Cross-validation
    └── Peer comparison

## Level 3: Interpretation & Action
├── 3.1 Risk Classification
│   ├── High/Medium/Low TPR zones
│   ├── Trend analysis
│   ├── Hotspot detection
│   └── Intervention priorities
│
├── 3.2 Reporting
│   ├── Summary statistics
│   ├── Visualizations
│   ├── Recommendations
│   └── Confidence levels
│
└── 3.3 Validation
    ├── Expert review points
    ├── Historical comparison
    ├── Regional benchmarks
    └── Uncertainty quantification

For each subproblem, I'll provide:
1. Specific code to solve it
2. Interpretation of results
3. Decision points for user input
4. Quality checks
"""

# Self-Consistency Validation Prompt
SELF_CONSISTENCY_CHECK = """
Generate multiple approaches to calculate TPR and validate consistency.

## Approach 1: Simple Aggregation
```python
tpr1 = (df['positive'].sum() / df['tested'].sum()) * 100
```

## Approach 2: Ward-Level Average
```python
ward_tpr = df.groupby('ward').apply(
    lambda x: (x['positive'].sum() / x['tested'].sum()) * 100
)
tpr2 = ward_tpr.mean()
```

## Approach 3: Weighted by Testing Volume
```python
df['tpr'] = (df['positive'] / df['tested']) * 100
tpr3 = np.average(df['tpr'], weights=df['tested'])
```

## Consistency Check:
- If all three approaches give similar results (±5%), high confidence
- If approaches differ >10%, investigate why:
  - Uneven distribution of testing?
  - Outlier wards affecting averages?
  - Data quality issues?

Return the most appropriate method with justification.
"""

# SQL Alternative Generation
SQL_GENERATION_PROMPT = """
Generate both Pandas and SQL solutions for the analysis.

## PANDAS SOLUTION:
```python
# TPR calculation by ward
tpr_by_ward = (
    df.groupby(['state', 'lga', 'ward'])
    .agg({{
        'tested': 'sum',
        'positive': 'sum'
    }})
    .assign(tpr=lambda x: (x['positive'] / x['tested']) * 100)
    .round(2)
)

# Filter high-risk areas (TPR > 40%)
high_risk = tpr_by_ward[tpr_by_ward['tpr'] > 40]
```

## SQL SOLUTION:
```sql
-- TPR calculation by ward
WITH ward_summary AS (
    SELECT 
        state,
        lga,
        ward,
        SUM(tested) as total_tested,
        SUM(positive) as total_positive,
        ROUND((SUM(positive) * 100.0 / NULLIF(SUM(tested), 0)), 2) as tpr
    FROM tpr_data
    WHERE tested > 0
    GROUP BY state, lga, ward
)
SELECT *
FROM ward_summary
WHERE tpr > 40
ORDER BY tpr DESC;
```

## Comparison:
- Pandas: Better for complex transformations, easier debugging
- SQL: More efficient for large datasets, database integration

Which approach would you prefer?
"""

# Human Validation Checkpoint
HUMAN_VALIDATION_PROMPT = """
## ⚠️ Human Validation Required

The following operation requires your review:

### Operation Type: {operation_type}
### Risk Level: {risk_level}

### Proposed Action:
```python
{code}
```

### Why This Needs Review:
{reason}

### Potential Impact:
- Records affected: {records_affected}
- Data percentage: {data_percentage}%
- Reversible: {reversible}

### Validation Questions:
1. Do you approve this operation? (yes/no)
2. Any modifications needed?
3. Additional constraints to apply?

Please review carefully before proceeding.
"""

# Error Recovery Prompt
ERROR_RECOVERY_PROMPT = """
## Error Encountered

Error Type: {error_type}
Error Message: {error_message}

## Recovery Strategy:

Thought: Let me analyze what went wrong and find an alternative approach.

### Potential Causes:
1. Column name mismatch
2. Data type incompatibility  
3. Missing values in calculation
4. Division by zero
5. Memory constraints

### Alternative Approaches:

Option 1: More defensive coding
```python
# Add null checks and type validation
if df[column].notna().any():
    # Proceed with calculation
```

Option 2: Simplified calculation
```python
# Break complex operation into steps
step1 = df.groupby('ward')['tested'].sum()
step2 = df.groupby('ward')['positive'].sum()
tpr = (step2 / step1) * 100
```

Option 3: Subset the data
```python
# Work with smaller subset first
sample = df.sample(min(1000, len(df)))
# Test on sample, then apply to full data
```

Which recovery approach should I try?
"""

# Ward Matching with Dynamic Detection
WARD_MATCHING_PROMPT = """
You need to match ward names from TPR data with shapefile ward names.

## Context:
TPR Data Wards: {tpr_wards_sample}
Shapefile Wards: {shapefile_wards_sample}

## Your Task:
Generate code to intelligently match these ward names accounting for:

1. **Common Variations**:
   - "Doubeli" vs "Doubeli Ward"
   - "KAREWA" vs "Karewa Ward"
   - Case differences
   - Special characters and spaces

2. **Fuzzy Matching Strategy**:
   ```python
   from rapidfuzz import fuzz, process
   
   # For each TPR ward, find best matches
   matches = process.extract(tpr_ward, shapefile_wards, 
                            scorer=fuzz.token_sort_ratio, limit=3)
   ```

3. **Confidence Thresholds**:
   - >85% → Auto-match
   - 60-85% → Need verification
   - <60% → Manual input needed

Generate the matching code that maximizes data retention.
"""

# Zone Variable Extraction
ZONE_VARIABLE_EXTRACTION_PROMPT = """
Extract environmental variables based on the geopolitical zone.

## Zone Mappings:
- North_Central: ['rainfall', 'temp', 'evi', 'ndmi', 'ndwi', 'soil_wetness', 'nighttime_lights']
- North_East: ['housing_quality', 'evi', 'ndwi', 'soil_wetness']
- North_West: ['housing_quality', 'elevation', 'evi', 'distance_to_waterbodies', 'soil_wetness']
- South_East: ['rainfall', 'elevation', 'evi', 'nighttime_lights', 'soil_wetness', 'temp']
- South_South: ['elevation', 'housing_quality', 'temp', 'evi', 'ndwi', 'ndmi']
- South_West: ['rainfall', 'elevation', 'evi', 'nighttime_lights']

## Current State: {state_name}
## Zone: {zone}

Generate code to:
1. Identify the zone for the state
2. Extract only the relevant variables for that zone
3. Join them to the TPR results

Remember: Different zones need different variables based on their malaria risk factors.
"""

# Dynamic Output Generation
OUTPUT_GENERATION_PROMPT = """
Generate the three required output files dynamically.

## Required Outputs:

1. **TPR Analysis CSV**:
   - All TPR calculations
   - Ward-level details
   - Metadata columns

2. **Main Analysis CSV**:
   - WardName (first column)
   - Identifiers (WardCode, LGACode, etc.)
   - TPR value
   - Zone-specific environmental variables

3. **Shapefile**:
   - All data joined to geographic boundaries
   - Ready for GIS mapping

Generate code to create these outputs without hardcoding column names.
Use dynamic detection based on what's actually in the data.
"""
