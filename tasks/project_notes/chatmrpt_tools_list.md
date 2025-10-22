# Complete List of ChatMRPT Tools
**Date**: 2025-01-18

## Tools Registered in RequestInterpreter (`app/core/request_interpreter.py`)

### 1. Analysis Tools
- **`run_malaria_risk_analysis`** - Main analysis tool that runs complete malaria risk assessment
  - Note: Composite and PCA analysis tools disabled to prevent confusion

### 2. Visualization Tools
- **`create_vulnerability_map`** - Creates vulnerability/risk maps
- **`create_box_plot`** - Generates box plot visualizations
- **`create_pca_map`** - Creates PCA-based risk maps
- **`create_variable_distribution`** - Shows distribution of variables

### 3. Settlement Visualization Tools
- **`create_settlement_map`** - Creates settlement footprint maps
- **`show_settlement_statistics`** - Displays settlement statistics

### 4. Data Tools
- **`execute_data_query`** - Executes data queries
- **`execute_sql_query`** - Runs SQL queries on data
- **`run_data_quality_check`** - Checks data quality

### 5. Explanation Tools
- **`explain_analysis_methodology`** - Explains analysis methods used

### 6. ITN Planning Tool
- **`run_itn_planning`** - Plans bed net distribution based on risk

**Total: 12 active tools registered**

## Data Analysis V3 Tools (`app/data_analysis_v3/tools/`)

### 1. Python Analysis Tool
- **`analyze_data`** (python_tool.py) - Executes Python code for data analysis
  - Main tool for LangGraph data analysis mode
  - Used when user selects Option 1 after upload

### 2. TPR Analysis Tool
- **`analyze_tpr_data`** (tpr_analysis_tool.py) - Specialized TPR data analysis
  - Handles Test Positivity Rate calculations
  - Used when user selects Option 2 (TPR workflow)
  - Actions: analyze, calculate_tpr, prepare_for_risk

## Physical Tool Files (`app/tools/`)

### Core Tool Files:
1. **complete_analysis_tools.py** - Main malaria risk analysis
2. **visualization_charts_tools.py** - Chart visualizations
3. **visualization_maps_tools.py** - Map visualizations
4. **variable_distribution.py** - Variable distribution analysis
5. **settlement_visualization_tools.py** - Settlement maps
6. **settlement_validation_tools.py** - Settlement validation
7. **settlement_intervention_tools.py** - Settlement-based interventions
8. **itn_planning_tools.py** - ITN/bed net distribution planning
9. **export_tools.py** - Export functionality
10. **methodology_explanation_tools.py** - Method explanations
11. **custom_analysis_parser.py** - Custom analysis parsing
12. **chatmrpt_help_tool.py** - Help system
13. **base.py** - Base tool classes

## Arena vs Tool Routing Decision Points

### Current Routing Logic (from `analysis_routes.py`):

1. **Mistral decides routing** based on:
   - Message content analysis
   - Session context (data loaded?)
   - Specific triggers

2. **Routes to TOOLS when**:
   - Analysis triggers: "run analysis", "perform analysis", "analyze my data"
   - Visualization keywords: "plot", "map", "chart", "visualize", "graph"
   - Ranking queries: "top", "highest", "lowest", "rank", "list wards"
   - Data queries: "check data quality", "summarize", "what variables"
   - ITN planning: "bed net", "ITN", "intervention", "mosquito net"

3. **Routes to ARENA when**:
   - General greetings: "hi", "hello", "hey"
   - Knowledge questions: "what is", "how does", "explain"
   - No data uploaded and asking general questions
   - Small talk

## Problem Areas Where Arena Gets Triggered Instead of Tools

Based on the routing logic, these scenarios might incorrectly go to Arena:

1. **Ambiguous requests** without specific keywords
   - "Show me the results" (no specific tool keyword)
   - "What did you find?" (could be interpreted as knowledge question)

2. **Follow-up questions** after analysis
   - "Why is this ward ranked high?" (has "why" - knowledge trigger)
   - "Tell me more about this" (has "tell me about" - knowledge trigger)

3. **Mixed intent messages**
   - "Hi, can you run the analysis?" (greeting first might confuse)
   - "Thanks, now plot the map" (gratitude might trigger conversational)

4. **Typos or variations** not in trigger list
   - "analize the data" (typo)
   - "do the risk assessment" (not exact match)

## Recommendations to Fix

1. **Expand trigger keywords** for tools
2. **Check for tool context** in follow-ups
3. **Prioritize tool routing** when data is loaded
4. **Add fallback checking** for common typos
5. **Consider session state** more strongly (if analysis_complete, bias toward tools)