# TPR Data Test Questions for ChatMRPT Agent

## Test Categories & Expected Capabilities

### 1. **Data Understanding & Exploration**
- Agent should automatically detect data structure
- Provide clear summaries without technical jargon
- Handle large datasets (337,774 rows) efficiently
- Understand hierarchical geography (State → LGA → Ward → Facility)

### 2. **Calculation Capabilities**
- Calculate test positivity rates: (Positive cases / Total tested) × 100
- Aggregate data at different geographic levels
- Handle missing data appropriately
- Perform time-series calculations

### 3. **Visualization Generation**
- Create choropleth maps for geographic data
- Generate time-series plots for trends
- Build comparison charts (bar, scatter, heatmaps)
- Interactive visualizations with Plotly

### 4. **Insight Generation**
- Identify high-risk areas automatically
- Detect trends and patterns
- Provide actionable recommendations
- Prioritize interventions based on data

### 5. **Multi-dimensional Analysis**
- Combine multiple indicators (TPR + LLIN coverage)
- Stratify by age groups and pregnancy status
- Geographic and temporal analysis together
- Risk scoring and ranking

## Test Scenarios by User Persona

### Public Health Official
"I need to know which states require immediate malaria intervention based on current data"
Expected: Risk ranking, hotspot identification, resource requirements

### Program Manager
"Show me LLIN distribution effectiveness and gaps"
Expected: Coverage analysis, correlation with outcomes, distribution recommendations

### Epidemiologist
"Analyze seasonal patterns and predict next quarter's malaria burden"
Expected: Trend analysis, seasonality detection, forecasting

### Policy Maker
"Give me an executive summary of the malaria situation across Nigeria"
Expected: High-level insights, key metrics, strategic recommendations

### Field Coordinator
"Which specific wards in my state need urgent attention?"
Expected: Ward-level analysis, specific locations, operational guidance

## Success Criteria

1. **Accuracy**: Calculations match manual verification
2. **Speed**: Responds within 30 seconds for basic queries
3. **Completeness**: Addresses all aspects of the question
4. **Clarity**: Non-technical language for non-technical users
5. **Actionability**: Provides specific, implementable recommendations
6. **Visualization**: Generates appropriate, informative charts
7. **Context**: Understands malaria domain context
8. **Scale**: Handles state-level and national-level analysis

## Edge Cases to Test

1. Missing data handling: "What if some facilities didn't report?"
2. Data quality: "Show me which facilities have suspicious data"
3. Zero values: "Which areas have no malaria cases?"
4. Outliers: "Identify unusual spikes in the data"
5. Comparison periods: "Compare this month to same month last year"

## Integration Tests

1. Upload state file → Ask for analysis → Get visualization
2. Upload multiple states → Compare → Get recommendations  
3. Ask follow-up questions → Maintain context → Deeper analysis
4. Request specific formats → Export results → Share findings
5. Switch between tabs → Maintain session → Continue analysis

## Performance Benchmarks

- Small state file (3K rows): < 10 seconds
- Medium state file (10K rows): < 20 seconds  
- Large state file (22K rows): < 30 seconds
- Full national data (337K rows): < 60 seconds
- Visualization generation: < 5 seconds
- Map rendering: < 10 seconds

## Domain-Specific Intelligence Tests

1. "Why might test positivity be high but case numbers low?"
2. "What's the relationship between rainfall and malaria transmission?"
3. "How does urbanization affect malaria patterns?"
4. "What interventions would you recommend for states with high TPR but good LLIN coverage?"
5. "Explain the difference between RDT and microscopy results"

These questions will thoroughly test whether ChatMRPT can:
- Handle real-world messy data
- Provide valuable insights to different user types
- Generate appropriate visualizations
- Make data-driven recommendations
- Maintain context across conversations
- Scale from ward-level to national analysis