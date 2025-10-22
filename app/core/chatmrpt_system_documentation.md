# ChatMRPT Complete System Documentation
## The Definitive Technical Manual for Arena Model Intelligence

---

# SECTION 1: SYSTEM IDENTITY & ARCHITECTURE

## What is ChatMRPT?
**Chat-based Malaria Risk Prioritization Tool** - An AI-powered conversational platform that transforms complex geospatial and health data into actionable malaria intervention strategies for Nigerian health officials.

## Core Architecture
```
User Interface (React + Flask)
    ↓
Chat Interface (/send_message)
    ↓
Request Interpreter (Mistral routing)
    ↓
Tool Execution Layer (16 specialized tools)
    ↓
Analysis Engine (Composite/PCA/TPR)
    ↓
Visualization Generator (Maps/Charts)
    ↓
Response Formatter
    ↓
User Interface Update
```

## Session Management
- **Session ID**: UUID generated on first visit
- **Storage**: `instance/uploads/{session_id}/`
- **Persistence**: File-based for cross-worker compatibility
- **Workers**: 6 Gunicorn workers for concurrent users

---

# SECTION 2: COMPLETE TOOL CATALOG

## 2.1 DATA ANALYSIS TOOLS

### RunMalariaRiskAnalysis
**File**: `app/tools/complete_analysis_tools.py`
**Class**: `RunMalariaRiskAnalysis(DataAnalysisTool)`
**Purpose**: Orchestrates complete malaria risk assessment
**Triggers**:
- "analyze my data"
- "run complete analysis"
- "perform risk assessment"
**Process**:
1. Loads uploaded data
2. Detects geopolitical zone
3. Selects appropriate variables
4. Runs composite scoring
5. Runs PCA analysis
6. Generates all visualizations
7. Creates rankings
**Outputs**:
- `analysis_complete.csv`
- `composite_scores.csv`
- `pca_results.csv`
- `ward_rankings.csv`

### GenerateComprehensiveAnalysisSummary
**File**: `app/tools/complete_analysis_tools.py`
**Purpose**: Creates executive summary of analysis
**Outputs**:
- Key findings
- Top 10 high-risk wards
- Bottom 10 low-risk wards
- Statistical insights
- Recommendations

### DescribeData
**File**: `app/tools/data_description_tools.py`
**Class**: `DescribeData(BaseTool)`
**Purpose**: Statistical overview of uploaded data
**Provides**:
- Column count and types
- Missing data percentage
- Descriptive statistics (mean, std, quartiles)
- Data quality score
- Variable correlations

## 2.2 VISUALIZATION MAP TOOLS

### CreateVulnerabilityMap
**File**: `app/tools/visualization_maps_tools.py`
**Purpose**: Choropleth map of risk levels
**Parameters**:
```python
{
    "variable": "composite_score",  # Column to visualize
    "color_scheme": "Reds",        # Color palette
    "n_classes": 5,                 # Number of classes
    "classification": "quantiles"   # Classification method
}
```
**Output**: Interactive Folium HTML map

### CreatePCAMap
**Purpose**: Visualizes PCA component scores
**Parameters**:
```python
{
    "component_number": 1,  # PC1, PC2, etc.
    "show_loadings": True   # Show variable contributions
}
```

### CreateInterventionMap
**Purpose**: Targeted intervention recommendations
**Parameters**:
```python
{
    "intervention_type": "ITN",  # ITN/IRS/SMC
    "priority_threshold": 0.7    # Risk threshold
}
```

### CreateCompositeScoreMaps
**Purpose**: Multiple maps for different risk dimensions
**Generates**:
- Overall risk map
- Environmental risk map
- Socioeconomic risk map
- Health system risk map

### CreateUrbanExtentMap
**Purpose**: Urban vs rural classification visualization
**Data Source**: Settlement footprint analysis

## 2.3 VISUALIZATION CHART TOOLS

### CreateHistogram
**Parameters**:
```python
{
    "variable": "pfpr",
    "bins": 20,
    "show_kde": True  # Kernel density estimate
}
```

### CreateBoxPlot
**Purpose**: Distribution comparison across groups
**Parameters**:
```python
{
    "variables": ["pfpr", "tpr", "rainfall"],
    "group_by": "State"  # Optional grouping
}
```

### CreateScatterPlot
**Purpose**: Bivariate relationships
**Parameters**:
```python
{
    "x_variable": "rainfall",
    "y_variable": "pfpr",
    "size_variable": "population",  # Optional
    "color_variable": "State"       # Optional
}
```

### CreateCorrelationHeatmap
**Purpose**: Variable correlation matrix
**Shows**: Pearson correlations between all numeric variables

### CreateBarChart
**Types Available**:
- Simple bar chart
- Grouped bar chart (CreateGroupedBarChart)
- Stacked bar chart (CreateStackedBarChart)
- Lollipop chart (CreateLollipopChart)

### CreatePieChart / CreateDonutChart
**Purpose**: Proportional distribution
**Parameters**:
```python
{
    "variable": "risk_category",
    "top_n": 10  # Show top N categories
}
```

### Statistical Plots
- **CreateQQPlot**: Normality assessment
- **CreateResidualPlot**: Model diagnostics
- **CreateRegressionPlot**: Linear relationships
- **CreatePairPlot**: All pairwise relationships

### Spatial Plots
- **CreateBubbleMap**: Size-encoded spatial data
- **CreateCoordinatePlot**: X,Y coordinate visualization

## 2.4 INTERVENTION PLANNING TOOLS

### PlanITNDistribution
**File**: `app/tools/itn_planning_tools.py`
**Purpose**: Optimizes bed net distribution
**Algorithm**:
1. Calculates need based on population
2. Factors in current coverage
3. Prioritizes by risk score
4. Respects budget constraints
**Parameters**:
```python
{
    "coverage_target": 80,      # Percentage
    "nets_per_household": 2,     # Standard allocation
    "budget_limit": 1000000     # Optional constraint
}
```
**Output**: Distribution plan with ward priorities

### ExportITNResults
**File**: `app/tools/export_tools.py`
**Purpose**: Exports intervention plans
**Formats**: Excel, CSV, JSON
**Includes**:
- Ward allocations
- Budget breakdown
- Coverage projections
- Implementation timeline

## 2.5 SPECIALIZED ANALYSIS TOOLS

### VariableDistribution
**File**: `app/tools/variable_distribution.py`
**Purpose**: Deep dive into variable patterns
**Analysis**:
- Shapiro-Wilk normality test
- Skewness and kurtosis
- Outlier detection
- Transformation recommendations

### ExplainAnalysisMethodology
**File**: `app/tools/methodology_explanation_tools.py`
**Purpose**: Plain-language method explanations
**Covers**:
- Composite scoring methodology
- PCA interpretation
- Variable selection rationale
- Statistical assumptions

## 2.6 SETTLEMENT TOOLS

### CreateSettlementAnalysisMap
**File**: `app/tools/settlement_intervention_tools.py`
**Purpose**: Settlement-level risk analysis
**Uses**: Building footprint data from Kano

### CreateInterventionTargetingMap
**Purpose**: Micro-targeting interventions
**Resolution**: Individual settlement level

## 2.7 HELP & SYSTEM TOOLS

### ChatMRPTHelpTool
**File**: `app/tools/chatmrpt_help_tool.py`
**Purpose**: Context-aware help provision
**Features**:
- Detects user's current step
- Provides relevant examples
- Suggests next actions
- Troubleshooting guidance

---

# SECTION 3: USER INTERFACE COMPONENTS

## 3.1 MAIN LAYOUT

### Header Section
```html
<div class="header">
    <div class="logo">ChatMRPT</div>
    <div class="nav-menu">
        <button id="survey-button">Survey</button>
        <button id="help-button">Help</button>
        <button id="settings-button">Settings</button>
    </div>
</div>
```

### Left Sidebar
```html
<div class="sidebar-left">
    <!-- Upload Section -->
    <div class="upload-section">
        <h3>Data Upload</h3>
        <button id="upload-csv">Upload CSV</button>
        <button id="upload-shapefile">Upload Shapefile</button>
        <button id="upload-both">Upload Both</button>
        <div class="upload-status"></div>
    </div>

    <!-- Analysis Options (appears after upload) -->
    <div class="analysis-options" style="display:none;">
        <h3>Analysis</h3>
        <button id="run-composite">Composite Analysis</button>
        <button id="run-pca">PCA Analysis</button>
        <button id="configure">Configure Parameters</button>
    </div>

    <!-- Results Actions (appears after analysis) -->
    <div class="results-actions" style="display:none;">
        <h3>Results</h3>
        <button id="download-results">Download CSV</button>
        <button id="generate-report">Generate Report</button>
        <button id="share-results">Share</button>
    </div>
</div>
```

### Main Chat Area
```html
<div class="chat-container">
    <div class="messages-area" id="messages">
        <!-- Messages appear here -->
    </div>

    <div class="suggestions-panel" id="suggestions">
        <div class="suggestions-header">
            <span>Suggested Actions</span>
            <button id="toggle-suggestions">Hide</button>
        </div>
        <div class="suggestions-list">
            <!-- Dynamic suggestions -->
        </div>
    </div>

    <div class="input-area">
        <textarea id="user-input" placeholder="Ask a question or describe what you want to do..."></textarea>
        <button id="send-message">Send</button>
        <button id="voice-input">🎤</button>
    </div>
</div>
```

### Right Panel
```html
<div class="right-panel">
    <!-- Data Preview (after upload) -->
    <div class="data-preview" style="display:none;">
        <h3>Data Preview</h3>
        <div class="data-stats">
            <p>Rows: <span id="row-count"></span></p>
            <p>Columns: <span id="col-count"></span></p>
            <p>Zone: <span id="detected-zone"></span></p>
        </div>
        <table class="preview-table">
            <!-- First 5 rows -->
        </table>
    </div>

    <!-- Results Summary (after analysis) -->
    <div class="results-summary" style="display:none;">
        <h3>Key Findings</h3>
        <div class="findings-list"></div>
    </div>

    <!-- Embedded Visualizations -->
    <div class="viz-container" id="current-viz">
        <!-- Maps/charts display here -->
    </div>
</div>
```

## 3.2 BUTTON BEHAVIORS

### Upload CSV Button
**ID**: `upload-csv`
**Action**: Opens file picker (accept: .csv, .xlsx, .xls)
**Process**:
1. User selects file
2. Client-side validation
3. POST to `/upload_both_files`
4. Progress bar shows
5. Success/error message
6. Data preview updates

### Upload Shapefile Button
**ID**: `upload-shapefile`
**Action**: Opens file picker (accept: .zip)
**Requirements**: ZIP containing .shp, .dbf, .shx files

### Run Analysis Buttons
**Composite**: Quick analysis with equal weights
**PCA**: Statistical dimensionality reduction
**Both trigger**: `/run_analysis` endpoint

### Download Results
**Generates**: ZIP file containing:
- Raw data
- Cleaned data
- Analysis results
- All visualizations
- Summary report

---

# SECTION 4: API ENDPOINTS & ROUTES

## 4.1 UPLOAD ENDPOINTS

### POST /upload_both_files
**Purpose**: Main file upload handler
**Request**:
```javascript
FormData: {
    csv_file: File,
    shapefile: File
}
```
**Response**:
```json
{
    "status": "success",
    "upload_type": "full_dataset",
    "session_id": "uuid",
    "csv_info": {...},
    "shapefile_info": {...},
    "detected_zone": "North_West",
    "next_steps": ["Run analysis", "Preview data"]
}
```

### POST /validate_data
**Purpose**: Pre-upload validation
**Validates**:
- File format
- Required columns
- Data types
- Geographic alignment

### GET /get_data_requirements
**Returns**:
```json
{
    "required_columns": ["WardName", "StateCode"],
    "optional_columns": ["Population", "pfpr", "rainfall"],
    "file_formats": ["csv", "xlsx"],
    "max_file_size": "32MB"
}
```

## 4.2 ANALYSIS ENDPOINTS

### POST /send_message
**Purpose**: Main chat interaction endpoint
**Request**:
```json
{
    "message": "Show me high risk areas",
    "context": {
        "session_id": "uuid",
        "has_data": true,
        "analysis_complete": true
    }
}
```
**Response**:
```json
{
    "response": "The highest risk wards are...",
    "visualizations": ["risk_map_12345.html"],
    "suggestions": [
        {
            "text": "View detailed statistics",
            "reason": "Get quantitative insights",
            "priority": "high"
        }
    ],
    "tools_used": ["CreateVulnerabilityMap"],
    "status": "complete"
}
```

### POST /run_analysis
**Triggers**: Complete analysis pipeline
**Parameters**:
```json
{
    "analysis_type": "composite|pca|both",
    "variables": ["auto"|list],
    "weights": {"var1": 0.3, "var2": 0.7}
}
```

### POST /toggle_suggestions
**Purpose**: Show/hide suggestions panel
**Persists**: In session state

## 4.3 VISUALIZATION ENDPOINTS

### GET /serve_viz_file/<filename>
**Purpose**: Serves generated visualizations
**Path**: `instance/uploads/{session_id}/visualizations/`
**Types**: HTML (maps/charts), PNG (static charts)

### POST /explain_visualization
**Purpose**: AI explanation of visualization
**Request**:
```json
{
    "viz_file": "risk_map_12345.html",
    "question": "What does this show?"
}
```

### GET /list_visualizations
**Returns**: All available visualizations for session

## 4.4 REPORT ENDPOINTS

### GET /generate_report
**Parameters**:
```
?format=docx|pdf|html
&sections=summary,methodology,results,recommendations
```
**Generates**: Comprehensive analysis report

### POST /customize_report
**Purpose**: Configure report sections
**Options**:
- Include/exclude sections
- Add custom text
- Select visualizations
- Choose statistics

## 4.5 TPR SPECIFIC ENDPOINTS

### POST /upload_tpr_data
**Accepts**: NMEP Excel format
**Validates**: Required sheets and columns

### POST /calculate_tpr
**Parameters**:
```json
{
    "state": "Kano",
    "period": "Q1-Q3",
    "aggregation": "ward|lga"
}
```

### GET /tpr_results
**Returns**: Calculated TPR with trends

---

# SECTION 5: WORKFLOWS & USER JOURNEYS

## 5.1 STANDARD RISK ANALYSIS WORKFLOW

### Step 1: Data Preparation
**User Action**: Prepares CSV with ward data
**Required Columns**:
- WardName (text)
- StateCode (text)
- Numeric indicators (at least 2)

### Step 2: Upload Process
```
1. Click "Upload CSV" → Select file
2. Click "Upload Shapefile" → Select ZIP
3. System validates files
4. Shows preview if successful
5. Displays detected zone
```

### Step 3: Analysis Configuration
**Automatic**:
- Zone detection
- Variable selection
- Data cleaning

**Optional**:
- Custom variable selection
- Weight adjustment
- Parameter tuning

### Step 4: Analysis Execution
```
1. Click "Run Analysis"
2. Progress indicator shows
3. Backend processes:
   - Data normalization
   - Composite scoring
   - PCA computation
   - Ranking generation
4. Completion notification
```

### Step 5: Results Exploration
**Available Actions**:
- View risk map
- Check rankings table
- See statistical summary
- Request specific insights
- Generate visualizations
- Export results

## 5.2 CONVERSATIONAL WORKFLOW

### Natural Language Interaction
```
User: "I have malaria data for Kano"
Bot: "Great! Please upload your data files."
[User uploads]
Bot: "I've detected Kano State data with 127 wards. Ready to analyze?"
User: "Yes, what are the high risk areas?"
Bot: [Runs analysis automatically]
Bot: "Analysis complete. The top 10 high-risk wards are:
     1. Dala - Score: 0.89
     2. Fagge - Score: 0.85
     ..."
User: "Show this on a map"
Bot: [Generates and displays map]
User: "Focus on areas near water"
Bot: [Filters for distance_to_water < 1km, updates map]
```

## 5.3 TPR WORKFLOW

### Excel Upload Path
```
1. Upload NMEP Excel file
2. System detects TPR format
3. Select state from dropdown
4. Choose time period
5. Click "Calculate TPR"
6. View results:
   - TPR by ward table
   - Temporal trends
   - Geographic distribution
7. Generate Word report
```

## 5.4 ERROR RECOVERY WORKFLOWS

### Upload Error Recovery
```
Error: "Missing required column: WardName"
Solution:
1. Show column mapping interface
2. User maps their column to WardName
3. Retry validation
4. Continue if successful
```

### Analysis Error Recovery
```
Error: "Insufficient numeric variables"
Solution:
1. Show available columns
2. Explain minimum requirements
3. Suggest data enrichment
4. Offer to proceed with available data
```

---

# SECTION 6: SESSION & STATE MANAGEMENT

## 6.1 SESSION VARIABLES

### Core Session State
```python
session = {
    # Identity
    'session_id': 'uuid-v4-string',
    'created_at': '2024-01-20T10:30:00',

    # Upload State
    'upload_complete': False,
    'csv_loaded': False,
    'csv_filename': 'kano_wards.csv',
    'shapefile_loaded': False,
    'shapefile_filename': 'kano_boundaries.zip',

    # Data State
    'detected_zone': 'North_West',
    'detected_state': 'Kano',
    'row_count': 127,
    'column_count': 15,
    'available_variables': [...],
    'selected_variables': [...],

    # Analysis State
    'analysis_complete': False,
    'analysis_type': 'composite',
    'analysis_timestamp': '2024-01-20T10:35:00',
    'results_generated': ['rankings', 'map', 'chart'],

    # UI State
    'suggestions_visible': True,
    'current_workflow_step': 'results',
    'last_action': 'run_analysis',

    # Interaction History
    'message_count': 5,
    'tools_used': ['RunMalariaRiskAnalysis', 'CreateVulnerabilityMap'],
    'errors_encountered': []
}
```

## 6.2 FILE SYSTEM STRUCTURE

### Session Directory Layout
```
instance/uploads/{session_id}/
├── raw_data.csv                 # Original upload
├── raw_shapefile.zip            # Original shapefile
├── shapefile/                   # Extracted shapefile
│   ├── boundaries.shp
│   ├── boundaries.dbf
│   ├── boundaries.shx
│   └── boundaries.prj
├── cleaned_data.csv             # Processed data
├── analysis_results/
│   ├── composite_scores.csv    # Composite analysis
│   ├── pca_results.csv         # PCA output
│   ├── pca_components.csv      # Component loadings
│   ├── rankings.csv            # Ward rankings
│   └── statistics.json         # Summary stats
├── visualizations/
│   ├── risk_map_*.html         # Interactive maps
│   ├── histogram_*.html        # Distribution charts
│   ├── scatter_*.html          # Relationship plots
│   └── correlation_*.html      # Correlation matrix
├── reports/
│   ├── summary.docx            # Word report
│   ├── technical_report.pdf    # Detailed PDF
│   └── presentation.pptx       # Slides
└── exports/
    ├── results_package.zip      # All results
    └── itn_plan.xlsx           # Intervention plan
```

## 6.3 STATE TRANSITIONS

### Workflow State Machine
```
INITIAL → UPLOADING → DATA_READY → ANALYZING → RESULTS_READY → COMPLETE
           ↓            ↓            ↓            ↓
         ERROR        ERROR        ERROR        ERROR
           ↓            ↓            ↓            ↓
        RECOVERY     RECOVERY     RECOVERY     RECOVERY
```

### State Transition Rules
- **INITIAL → UPLOADING**: File upload initiated
- **UPLOADING → DATA_READY**: Valid files uploaded
- **DATA_READY → ANALYZING**: Analysis triggered
- **ANALYZING → RESULTS_READY**: Analysis complete
- **Any → ERROR**: Validation/processing failure
- **ERROR → RECOVERY**: Error handled, retry available

---

# SECTION 7: ERROR HANDLING & RECOVERY

## 7.1 ERROR TAXONOMY

### Upload Errors
```python
UPLOAD_ERRORS = {
    'NO_FILE': "No file selected",
    'INVALID_FORMAT': "File must be CSV or Excel",
    'TOO_LARGE': "File exceeds 32MB limit",
    'CORRUPT_FILE': "File appears corrupted",
    'MISSING_COLUMNS': "Required columns not found",
    'EMPTY_FILE': "File contains no data"
}
```

### Data Errors
```python
DATA_ERRORS = {
    'NO_NUMERIC': "No numeric variables found",
    'INSUFFICIENT_DATA': "Too many missing values (>50%)",
    'ZERO_VARIANCE': "Variable has no variation",
    'MISMATCHED_WARDS': "Ward names don't match shapefile",
    'INVALID_GEOMETRY': "Shapefile geometry corrupted"
}
```

### Analysis Errors
```python
ANALYSIS_ERRORS = {
    'INSUFFICIENT_VARIABLES': "Need at least 2 variables",
    'MEMORY_ERROR': "Dataset too large for analysis",
    'CONVERGENCE_FAILURE': "PCA failed to converge",
    'INVALID_PARAMETERS': "Analysis parameters invalid"
}
```

## 7.2 ERROR RECOVERY STRATEGIES

### Automatic Recovery
```python
def auto_recover(error_type, session):
    if error_type == 'MISSING_COLUMNS':
        # Try fuzzy matching
        return fuzzy_match_columns(session)

    elif error_type == 'INSUFFICIENT_DATA':
        # Use available data with warning
        return proceed_with_warning(session)

    elif error_type == 'ZERO_VARIANCE':
        # Remove constant variables
        return filter_valid_variables(session)
```

### User-Guided Recovery
```python
def guide_recovery(error_type, session):
    if error_type == 'MISMATCHED_WARDS':
        return {
            'action': 'show_mapping_interface',
            'message': 'Help us match your ward names',
            'options': suggest_ward_matches(session)
        }
```

---

# SECTION 8: ARENA MODEL INTEGRATION POINTS

## 8.1 KNOWLEDGE INJECTION POINTS

### System Prompt Template
```python
ARENA_SYSTEM_KNOWLEDGE = """
You are an expert on ChatMRPT, a malaria risk analysis platform.

SYSTEM CAPABILITIES:
{list_all_tools()}

CURRENT USER STATE:
{get_session_state()}

AVAILABLE ACTIONS:
{get_available_actions()}

USER HISTORY:
{get_interaction_history()}

Provide specific, actionable guidance based on the user's current context.
"""
```

### Context Builder
```python
def build_arena_context(session):
    return {
        'tools': get_available_tools(session),
        'state': get_current_state(session),
        'data': get_data_summary(session),
        'results': get_results_summary(session),
        'errors': get_recent_errors(session),
        'suggestions': generate_suggestions(session)
    }
```

## 8.2 ARENA MODEL ROLES

### Model Specializations
```python
MODEL_ROLES = {
    'mistral': {
        'role': 'Workflow Navigator',
        'expertise': ['routing', 'state_tracking', 'next_steps'],
        'prompt_style': 'concise_technical'
    },
    'gpt-4': {
        'role': 'Analysis Expert',
        'expertise': ['statistics', 'interpretation', 'insights'],
        'prompt_style': 'detailed_analytical'
    },
    'claude': {
        'role': 'Domain Specialist',
        'expertise': ['malaria', 'nigeria', 'interventions'],
        'prompt_style': 'comprehensive_contextual'
    },
    'llama': {
        'role': 'Quick Assistant',
        'expertise': ['ui_help', 'simple_queries', 'navigation'],
        'prompt_style': 'brief_helpful'
    },
    'gemini': {
        'role': 'Visualization Guide',
        'expertise': ['maps', 'charts', 'visual_interpretation'],
        'prompt_style': 'visual_descriptive'
    }
}
```

## 8.3 PROMPT ENGINEERING

### Tool-Aware Prompting
```python
def create_tool_aware_prompt(query, context):
    return f"""
    User Query: {query}

    Available Tools:
    {format_tools_with_descriptions()}

    Current Data:
    - Files: {context['files']}
    - Variables: {context['variables']}
    - Analysis Status: {context['status']}

    Determine:
    1. Can this be answered with current data?
    2. Which tool(s) should be used?
    3. What parameters are needed?
    4. What's the expected output?

    Respond with specific tool calls or explanations.
    """
```

### Dynamic Suggestion Generation
```python
def generate_intelligent_suggestions(session):
    prompt = f"""
    Given this session state:
    {json.dumps(session, indent=2)}

    What are the 5 most relevant next actions?
    Consider:
    - What the user has already done
    - What they haven't explored yet
    - Common workflow patterns
    - Their apparent goal

    Format each suggestion as:
    - Action: [specific command/click]
    - Reason: [why this is relevant]
    - Priority: [high/medium/low]
    """
    return query_arena_model(prompt)
```

---

# SECTION 9: ADVANCED FEATURES

## 9.1 MULTI-MODEL CONSENSUS

### Consensus Algorithm
```python
def get_consensus_response(query, context):
    responses = {}

    # Query all models
    for model in ARENA_MODELS:
        responses[model] = query_model(model, query, context)

    # Weight by expertise
    weighted_responses = weight_by_expertise(responses, query_type)

    # Synthesize
    return synthesize_responses(weighted_responses)
```

## 9.2 LEARNING & ADAPTATION

### Success Pattern Tracking
```python
SUCCESS_PATTERNS = {
    'workflow_sequences': track_successful_paths(),
    'helpful_suggestions': track_followed_suggestions(),
    'effective_tools': track_tool_usage_success(),
    'query_resolutions': track_query_satisfaction()
}
```

### Prompt Optimization
```python
def optimize_prompts(success_data):
    # Analyze what works
    effective_patterns = analyze_success_patterns(success_data)

    # Update prompts
    for pattern in effective_patterns:
        update_prompt_template(pattern)
```

---

# SECTION 10: QUICK REFERENCE

## Common User Intents → System Actions

| User Says | System Does |
|-----------|-------------|
| "Analyze my data" | Runs complete analysis pipeline |
| "Show high risk areas" | Creates vulnerability map |
| "What does this mean?" | Explains current visualization |
| "Compare wards" | Creates comparison chart |
| "Download results" | Generates results package |
| "Help me understand PCA" | Explains methodology |
| "Plan ITN distribution" | Runs ITN planning tool |
| "Show correlations" | Creates correlation heatmap |
| "Focus on water access" | Filters by water distance |
| "Generate report" | Creates Word document |

## Tool Trigger Patterns

| Pattern | Tool | Parameters |
|---------|------|------------|
| "map", "show", "spatial" | CreateVulnerabilityMap | variable, color_scheme |
| "histogram", "distribution" | CreateHistogram | variable, bins |
| "scatter", "relationship" | CreateScatterPlot | x_var, y_var |
| "ranking", "top", "bottom" | GenerateRankings | n_top, sort_order |
| "explain", "what", "how" | ExplainMethodology | analysis_type |
| "ITN", "nets", "distribution" | PlanITNDistribution | coverage_target |

## Error → Solution Mapping

| Error | Quick Solution |
|-------|---------------|
| No file selected | Prompt upload |
| Missing WardName | Column mapping |
| No numeric variables | Check data types |
| Analysis failed | Validate inputs |
| Map not showing | Check shapefile |
| Results empty | Rerun analysis |

---

END OF DOCUMENTATION

This documentation serves as the complete knowledge base for arena models to understand and guide users through ChatMRPT.