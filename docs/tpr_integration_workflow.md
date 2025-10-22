# TPR Integration Workflow for ChatMRPT Data Analysis V3

## Overview
This document outlines the complete workflow for integrating Test Positivity Rate (TPR) analysis capabilities into the Data Analysis V3 system, enabling users to perform both standard data analysis and TPR-specific operations seamlessly.

## Core Philosophy
**"Best of Both Worlds"** - TPR detection adds capabilities without restricting standard data analysis features. Users can freely mix standard analysis with TPR-specific tools and seamlessly prepare data for risk analysis when ready.

## System Architecture

### High-Level Flow
```
Data Analysis V3 Tab:
[Upload Data] → [Detection] → [Enhanced Analysis Experience]
                                    ↓
                        • Standard Data Analysis Tools
                        • PLUS TPR-Specific Tools (if TPR detected)
                        • PLUS Risk Analysis Preparation (when ready)
```

### Component Architecture
```
app/
├── core/
│   ├── tpr_detector.py (NEW)              # Smart TPR data detection
│   └── request_interpreter.py (MODIFY)     # Enhanced context awareness
├── data_analysis_v3/
│   ├── core/
│   │   └── agent.py (MODIFY)              # TPR-aware agent behavior
│   ├── tools/
│   │   ├── tpr_calculation_tool.py (NEW)  # TPR calculation methods
│   │   ├── tpr_visualization_tool.py (NEW) # TPR-specific visualizations
│   │   ├── facility_analysis_tool.py (NEW) # Facility-level analysis
│   │   ├── testing_comparison_tool.py (NEW)# RDT vs Microscopy analysis
│   │   └── tpr_risk_preparation_tool.py (NEW) # Risk analysis bridge
│   └── prompts/
│       └── system_prompt.py (MODIFY)       # Enhanced with TPR guidance
└── web/
    └── routes/
        └── upload_routes.py (MODIFY)       # TPR detection on upload
```

## Detailed Workflow

### Phase 1: Upload and Detection

#### User Action
User uploads data file through Data Analysis V3 tab (e.g., `ad_Adamawa_State_TPR_LLIN_2024.xlsx`)

#### System Response
1. **File Reception**: Standard file upload handling
2. **TPR Detection**: 
   ```python
   is_tpr, tpr_info = TPRDetector.is_tpr_data(df)
   # Checks for: RDT columns, Microscopy columns, LLIN metrics, facility structure
   ```
3. **Tool Loading**:
   - Load all standard analysis tools
   - IF TPR detected: Add TPR-specific tools
   - Set context flags for agent awareness

#### User Experience
```
Agent: "I've analyzed your uploaded data and found Test Positivity Rate (TPR) indicators! 

Your data contains:
- 10,452 health facility records
- Testing data (RDT and Microscopy) 
- LLIN distribution metrics
- 246 unique wards across 21 LGAs

You can:
1. **Explore your data** - distributions, patterns, quality checks
2. **Calculate TPR metrics** - by ward, LGA, or facility level  
3. **Analyze trends** - temporal patterns, age groups, testing methods
4. **Prepare for risk analysis** - I can help merge environmental and demographic data

What would you like to explore first?"
```

### Phase 2: Mixed Analysis Mode

#### Available Operations
Users can freely mix standard and TPR-specific analyses:

##### Standard Analysis Operations
- Data exploration and summary statistics
- Distribution analysis
- Correlation analysis
- Missing data assessment
- Custom Python code execution
- General visualizations

##### TPR-Specific Operations (Additional)
- TPR calculation (multiple methods)
- Facility-level stratification
- Age group analysis
- Testing method comparison (RDT vs Microscopy)
- LLIN coverage analysis
- Temporal TPR trends

#### Example Interaction Flow
```
User: "Show me the distribution of all columns"
Agent: [Uses standard tool] "Here's the distribution analysis for all 20 columns..."

User: "Calculate TPR by ward"
Agent: [Uses TPR tool] "Calculating ward-level TPR using standard method...
        Average TPR: 35.2%
        Highest: 67% (Girei ward)
        Lowest: 12% (Yola North ward)"

User: "What's the correlation between TPR and LLIN coverage?"
Agent: [Uses both tools] "Analyzing correlation between TPR and LLIN coverage...
        Correlation coefficient: -0.38 (moderate negative)
        Wards with higher LLIN coverage show lower TPR rates."
```

### Phase 3: TPR Calculation Methods

#### Standard Method
- Formula: `TPR = (Positive Cases / Tested Cases) × 100`
- Uses: `max(RDT, Microscopy)` for both numerator and denominator
- Default for most scenarios

#### Age-Stratified Method
- Calculates separate TPR for: <5 years, ≥5 years, Pregnant Women
- Useful for targeted intervention planning
- Offered when complete age data available

#### Facility-Weighted Method
- Weights TPR by facility level (Primary, Secondary, Tertiary)
- Accounts for referral patterns and diagnostic capacity
- Suggested when facility level data present

#### Alternative Urban Method
- Formula: `TPR = (Positive Cases / OPD Attendance) × 100`
- Used for urban areas with TPR >50%
- Based on WHO recommendations for high-transmission settings

#### Smart Method Selection
```python
Decision Logic:
1. IF missing_data > 40% → Ask user about imputation
2. IF urban_area AND tpr > 50% → Suggest alternative method
3. IF complete_age_data → Offer age stratification
4. ELSE → Use standard method automatically
```

### Phase 4: Risk Analysis Preparation

#### Trigger Points
- User explicitly requests: "Prepare for risk analysis"
- After comprehensive TPR analysis completion
- When user asks about risk factors or vulnerability

#### Preparation Process
1. **Data Enhancement** (Preserves existing analyses)
   ```
   Current TPR Data (20 columns)
           ↓
   + Environmental Variables (8 columns)
   + Demographic Indicators (5 columns)
   + Geographic Boundaries
           ↓
   Enhanced Dataset (33+ columns)
   ```

2. **Environmental Variables Added**
   - Rainfall (annual, monthly averages)
   - Temperature (mean, min, max)
   - NDVI (vegetation index)
   - Urban percentage
   - Elevation
   - Distance to water bodies
   - Land cover type
   - Humidity index

3. **Demographic Variables Added**
   - Population density
   - Poverty rate
   - Literacy rate
   - Healthcare access index
   - Housing quality indicator

4. **File Creation**
   ```
   instance/uploads/{session_id}/
   ├── raw_data.csv              # For risk analysis pipeline
   ├── raw_shapefile.zip         # Geographic boundaries
   ├── enhanced_tpr_data.csv     # Complete enhanced dataset
   └── tpr_metadata.json         # Analysis metadata
   ```

#### User Experience
```
User: "Can we prepare this for risk analysis?"

Agent: "Absolutely! I'll prepare your data for risk analysis by:
        1. Keeping your current TPR calculations
        2. Adding environmental risk factors
        3. Merging demographic vulnerability indicators
        4. Including geographic boundaries
        
        This will create a comprehensive dataset while preserving all your analysis.
        Shall I proceed?"

User: "Yes"

Agent: "Data enhanced for risk analysis! 
        - Original: 20 variables
        - Enhanced: 45 variables
        - Wards ready: 246
        
        You can continue analyzing here or proceed to risk prioritization."
```

### Phase 5: Seamless Transition

#### Session State Management
```python
# Set flags for risk analysis pipeline
session['data_type'] = 'tpr_enhanced'
session['risk_analysis_ready'] = True
session['preserved_analyses'] = current_analyses
session['upload_type'] = 'csv_shapefile'  # Tricks system
```

#### Continuation Options
1. **Continue in Data Analysis**: User can keep exploring enhanced dataset
2. **Move to Risk Analysis**: System recognizes prepared data, starts risk pipeline
3. **Export Results**: Download enhanced dataset for external use

## Implementation Checklist

### Priority 1: Core Infrastructure
- [ ] Create `TPRDetector` class for data detection
- [ ] Update Data Analysis V3 agent with TPR awareness
- [ ] Modify system prompt with TPR guidelines
- [ ] Add TPR context to request interpreter

### Priority 2: TPR Tools Suite
- [ ] Implement `TPRCalculationTool` with all methods
- [ ] Create `TPRVisualizationTool` for specific charts
- [ ] Build `FacilityAnalysisTool` for facility stratification
- [ ] Develop `TestingComparisonTool` for RDT vs Microscopy

### Priority 3: Risk Analysis Bridge
- [ ] Create `TPRRiskPreparationTool`
- [ ] Implement environmental data extraction
- [ ] Connect demographic data sources
- [ ] Build shapefile extraction logic
- [ ] Set up session state management

### Priority 4: Testing & Refinement
- [ ] Test with all 37 state TPR files
- [ ] Validate calculation methods
- [ ] Ensure seamless transitions
- [ ] Handle edge cases and errors
- [ ] Performance optimization

## Key Design Principles

1. **Additive Enhancement**: TPR features add to, not replace, standard analysis
2. **Progressive Disclosure**: Reveal TPR features when relevant, not overwhelm
3. **Smart Defaults**: Make intelligent decisions while preserving user control
4. **Context Preservation**: Never lose user's analysis work during transitions
5. **Seamless Integration**: TPR→Risk pipeline feels natural and effortless

## Success Metrics

- User can perform standard analysis on TPR data without restrictions
- TPR-specific tools are discoverable but not intrusive
- Transition to risk analysis preserves all prior work
- System correctly detects TPR data 95%+ of the time
- Users can complete TPR→Risk workflow in under 5 interactions

## Example User Journeys

### Journey 1: Quick TPR Analysis
```
1. Upload → TPR detected
2. "Calculate TPR" → Results shown
3. "Export results" → Download CSV
Time: 2-3 interactions
```

### Journey 2: Exploratory Analysis
```
1. Upload → TPR detected
2. "Explore data" → Standard analysis
3. "Show correlations" → Mixed analysis
4. "Calculate TPR by facility" → TPR tool
5. "Compare methods" → Testing comparison
Time: 5-6 interactions
```

### Journey 3: Full Pipeline to Risk
```
1. Upload → TPR detected
2. "Analyze TPR" → TPR calculations
3. "Check quality" → Data assessment
4. "Prepare for risk" → Enhancement
5. "Start risk analysis" → Transition
Time: 4-5 interactions
```

## Notes for Developers

- TPR detection should be fast (<100ms) to not slow upload
- Tool loading should be dynamic based on data type
- Preserve all user-created variables during enhancement
- Environmental data extraction should cache results
- Session state must persist across worker processes
- Error handling should gracefully fall back to standard analysis

## Future Enhancements

1. **Multi-state Comparison**: Compare TPR across multiple states
2. **Temporal Analysis**: Trend analysis across time periods
3. **Automated Insights**: AI-generated observations about TPR patterns
4. **Custom Thresholds**: User-defined TPR risk categories
5. **Integration with Other Data**: Combine TPR with surveillance data

---

*Document Version: 1.0*
*Last Updated: January 2025*
*Author: ChatMRPT Development Team*