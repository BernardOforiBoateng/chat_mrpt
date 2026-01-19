"""
Tool Capabilities Definition for Semantic Routing

This module defines what each tool DOES (not keywords to match).
Used by the routing system to understand when tool execution is needed.
"""

TOOL_CAPABILITIES = {
    'describe_data': {
        'purpose': 'Describe uploaded data including column names, types, and statistics',
        'generates': 'Data overview with column information and summary statistics',
        'requires': 'Uploaded CSV data file',
        'execution_verbs': ['describe', 'tell', 'show', 'list', 'info'],
        'example_queries': [
            'tell me about the variables in my data',
            'describe my data',
            'show me the column names',
            'what variables do I have',
            'list the data columns'
        ]
    },

    'run_malaria_risk_analysis': {
        'purpose': 'Execute new malaria risk analysis calculations on uploaded data',
        'generates': 'New risk scores, vulnerability rankings, and analysis results',
        'requires': 'Uploaded CSV data with demographic/health indicators',
        'execution_verbs': ['run', 'execute', 'perform', 'start', 'calculate', 'analyze'],
        'example_queries': [
            'run the malaria risk analysis',
            'analyze my data',
            'perform risk assessment',
            'calculate vulnerability scores'
        ]
    },

    'create_vulnerability_map': {
        'purpose': 'Generate a new interactive HTML map showing vulnerability scores',
        'generates': 'Interactive choropleth map visualization',
        'requires': 'Completed analysis with risk scores',
        'execution_verbs': ['create', 'generate', 'plot', 'map', 'visualize'],
        'example_queries': [
            'create a vulnerability map',
            'show me the risk map',
            'plot vulnerability scores on map'
        ]
    },

    'create_box_plot': {
        'purpose': 'Generate new box plot visualization for statistical distributions',
        'generates': 'Box and whisker plot showing quartiles and outliers',
        'requires': 'Uploaded data with numeric variables',
        'execution_verbs': ['create', 'generate', 'plot', 'show'],
        'example_queries': [
            'create a box plot',
            'show statistical distribution',
            'plot quartiles'
        ]
    },

    'create_pca_map': {
        'purpose': 'Generate PCA (Principal Component Analysis) visualization map',
        'generates': 'Map showing PCA components and loadings',
        'requires': 'Completed PCA analysis',
        'execution_verbs': ['create', 'generate', 'plot', 'visualize'],
        'example_queries': [
            'show PCA results on map',
            'create principal component map',
            'visualize PCA analysis'
        ]
    },

    'variable_distribution': {
        'purpose': 'Create spatial distribution maps for any variable showing how it varies across wards',
        'generates': 'Interactive map showing the spatial distribution of a specified variable',
        'requires': 'Uploaded data with the variable to map',
        'execution_verbs': ['plot', 'map', 'show', 'visualize', 'display', 'create'],
        'example_queries': [
            'plot the evi variable distribution',
            'show me the distribution of pfpr',
            'map the rainfall variable',
            'visualize housing_quality across wards',
            'display the spatial distribution of elevation'
        ]
    },

    'create_settlement_map': {
        'purpose': 'Generate map showing settlement patterns and building footprints',
        'generates': 'Settlement classification map with building types',
        'requires': 'Settlement data or shapefile',
        'execution_verbs': ['create', 'generate', 'map', 'visualize'],
        'example_queries': [
            'show settlement patterns',
            'map building footprints',
            'visualize urban areas'
        ]
    },

    'show_settlement_statistics': {
        'purpose': 'Calculate and display settlement statistics',
        'generates': 'Statistical summary of settlement types and counts',
        'requires': 'Settlement data',
        'execution_verbs': ['show', 'calculate', 'display', 'get'],
        'example_queries': [
            'show settlement statistics',
            'get building counts',
            'display urban percentages'
        ]
    },

    'execute_data_query': {
        'purpose': 'Run queries on uploaded data to extract and filter specific information like rankings',
        'generates': 'Query results showing filtered data, rankings, or specific values',
        'requires': 'Uploaded data to query (and analysis results for rankings)',
        'execution_verbs': ['show', 'get', 'find', 'extract', 'list', 'filter', 'rank'],
        'example_queries': [
            'show me the top 10 highest risk wards',
            'list wards with TPR > 50',
            'find high risk areas',
            'get ward rankings from composite score',
            'show bottom 5 wards by vulnerability'
        ]
    },

    'execute_sql_query': {
        'purpose': 'Execute SQL queries on data for complex analysis',
        'generates': 'SQL query results',
        'requires': 'Data in queryable format',
        'execution_verbs': ['query', 'select', 'execute', 'run'],
        'example_queries': [
            'SELECT * FROM data WHERE risk > 0.5',
            'query wards by risk level',
            'run SQL analysis'
        ]
    },

    'run_data_quality_check': {
        'purpose': 'Perform new data quality assessment on uploaded files',
        'generates': 'Data quality report with issues and statistics',
        'requires': 'Uploaded data to check',
        'execution_verbs': ['check', 'assess', 'validate', 'verify', 'examine'],
        'example_queries': [
            'check data quality',
            'validate my data',
            'assess data completeness',
            'find data issues'
        ]
    },

    'explain_analysis_methodology': {
        'purpose': 'Generate explanation of analysis methods used',
        'generates': 'Detailed methodology explanation',
        'requires': 'Context about analysis type',
        'execution_verbs': ['explain', 'describe', 'detail'],
        'example_queries': [
            'explain the methodology',
            'how was this calculated',
            'describe analysis approach'
        ]
    },

    'plan_itn_distribution': {
        'purpose': 'Calculate optimal ITN (bed net) distribution plan',
        'generates': 'Distribution plan with net allocations per ward',
        'requires': 'Analysis results and net availability parameters',
        'execution_verbs': ['plan', 'calculate', 'distribute', 'allocate'],
        'example_queries': [
            'plan bed net distribution',
            'allocate ITNs to wards',
            'distribute 10000 nets optimally',
            'plan mosquito net campaign'
        ]
    },

    'generatecomprehensiveanalysissummary': {
        'purpose': 'Generate comprehensive summary of all analysis results',
        'generates': 'Complete analysis report with findings and recommendations',
        'requires': 'Completed analysis results',
        'execution_verbs': ['generate', 'create', 'summarize', 'compile'],
        'example_queries': [
            'generate comprehensive summary',
            'create analysis report',
            'summarize all findings'
        ]
    },

    'createhistogram': {
        'purpose': 'Create histogram visualization for data distribution',
        'generates': 'Histogram chart showing frequency distribution',
        'requires': 'Data with numeric variable to plot',
        'execution_verbs': ['create', 'plot', 'show', 'visualize'],
        'example_queries': [
            'create histogram of TPR values',
            'show frequency distribution',
            'plot data histogram'
        ]
    },

    'createscatterplot': {
        'purpose': 'Create scatter plot to show relationships between variables',
        'generates': 'Scatter plot visualization',
        'requires': 'Two numeric variables to compare',
        'execution_verbs': ['create', 'plot', 'show', 'compare'],
        'example_queries': [
            'create scatter plot of TPR vs rainfall',
            'plot relationship between variables',
            'show correlation scatter plot'
        ]
    },

    'createcorrelationheatmap': {
        'purpose': 'Create correlation heatmap showing relationships between all variables',
        'generates': 'Heatmap visualization of correlations',
        'requires': 'Multiple numeric variables',
        'execution_verbs': ['create', 'show', 'visualize', 'analyze'],
        'example_queries': [
            'show correlation heatmap',
            'analyze variable relationships',
            'create correlation matrix'
        ]
    },

    'createbarchart': {
        'purpose': 'Create bar chart for categorical comparisons',
        'generates': 'Bar chart visualization',
        'requires': 'Categorical and numeric data',
        'execution_verbs': ['create', 'plot', 'show', 'compare'],
        'example_queries': [
            'create bar chart of ward scores',
            'show comparison bar chart',
            'plot ward rankings as bars'
        ]
    },

    'createpiechart': {
        'purpose': 'Create pie chart showing proportions',
        'generates': 'Pie chart visualization',
        'requires': 'Categorical data with values',
        'execution_verbs': ['create', 'show', 'visualize'],
        'example_queries': [
            'create pie chart of risk categories',
            'show proportion breakdown',
            'visualize category distribution'
        ]
    },

    'createviolinplot': {
        'purpose': 'Create violin plot showing distribution shape',
        'generates': 'Violin plot visualization',
        'requires': 'Numeric data for distribution',
        'execution_verbs': ['create', 'plot', 'show'],
        'example_queries': [
            'create violin plot',
            'show distribution shape',
            'plot violin chart'
        ]
    },

    'createdensityplot': {
        'purpose': 'Create density plot for continuous distributions',
        'generates': 'Density plot visualization',
        'requires': 'Continuous numeric data',
        'execution_verbs': ['create', 'plot', 'show'],
        'example_queries': [
            'create density plot',
            'show probability density',
            'plot density distribution'
        ]
    },

    'createpairplot': {
        'purpose': 'Create pair plot matrix for multiple variables',
        'generates': 'Matrix of scatter plots',
        'requires': 'Multiple numeric variables',
        'execution_verbs': ['create', 'plot', 'show'],
        'example_queries': [
            'create pair plot',
            'show variable relationships',
            'plot pairwise comparisons'
        ]
    },

    'createregressionplot': {
        'purpose': 'Create regression plot with fitted line',
        'generates': 'Regression visualization with trend line',
        'requires': 'Two numeric variables',
        'execution_verbs': ['create', 'plot', 'fit', 'analyze'],
        'example_queries': [
            'create regression plot',
            'fit trend line',
            'analyze linear relationship'
        ]
    },

    'createqqplot': {
        'purpose': 'Create Q-Q plot for normality testing',
        'generates': 'Quantile-quantile plot',
        'requires': 'Numeric data for normality check',
        'execution_verbs': ['create', 'test', 'check', 'plot'],
        'example_queries': [
            'create Q-Q plot',
            'check normality',
            'test distribution'
        ]
    },

    'createinterventionmap': {
        'purpose': 'Create map showing intervention targeting',
        'generates': 'Map with intervention priorities',
        'requires': 'Analysis results and intervention criteria',
        'execution_verbs': ['create', 'map', 'show', 'plan'],
        'example_queries': [
            'create intervention map',
            'map intervention targets',
            'show priority areas for intervention'
        ]
    },

    'createurbanextentmap': {
        'purpose': 'Create map showing urban vs rural areas',
        'generates': 'Urban extent classification map',
        'requires': 'Settlement or urbanization data',
        'execution_verbs': ['create', 'map', 'show', 'classify'],
        'example_queries': [
            'create urban extent map',
            'show urban vs rural areas',
            'map urbanization'
        ]
    },

    'createdecisiontree': {
        'purpose': 'Create decision tree visualization for risk factors',
        'generates': 'Decision tree diagram',
        'requires': 'Risk factors and thresholds',
        'execution_verbs': ['create', 'build', 'generate', 'visualize'],
        'example_queries': [
            'create decision tree',
            'show risk decision paths',
            'build classification tree'
        ]
    },

    'create_vulnerability_map_comparison': {
        'purpose': 'Create side-by-side comparison of vulnerability maps',
        'generates': 'Comparison map showing multiple methods',
        'requires': 'Multiple analysis results to compare',
        'execution_verbs': ['compare', 'create', 'show', 'contrast'],
        'example_queries': [
            'compare vulnerability maps',
            'show PCA vs composite maps',
            'create comparison visualization'
        ]
    },

    'create_settlement_map': {
        'purpose': 'Create map showing settlement patterns',
        'generates': 'Settlement distribution map',
        'requires': 'Settlement data',
        'execution_verbs': ['create', 'map', 'show', 'visualize'],
        'example_queries': [
            'create settlement map',
            'show building footprints',
            'map settlement patterns'
        ]
    },

    'show_settlement_statistics': {
        'purpose': 'Calculate and show settlement statistics',
        'generates': 'Statistical summary of settlements',
        'requires': 'Settlement data',
        'execution_verbs': ['show', 'calculate', 'analyze', 'summarize'],
        'example_queries': [
            'show settlement statistics',
            'analyze building types',
            'summarize settlement data'
        ]
    }
}

def get_tool_capability(tool_name: str) -> dict:
    """Get capability description for a specific tool."""
    return TOOL_CAPABILITIES.get(tool_name, {})

def get_all_capabilities_summary() -> str:
    """Get a summary of all tool capabilities for routing context."""
    summary = []
    for tool_name, cap in TOOL_CAPABILITIES.items():
        summary.append(f"- {tool_name}: {cap['purpose']}")
    return "\n".join(summary)

def requires_tool_execution(message: str, context: dict) -> tuple[bool, str]:
    """
    Determine if a message requires tool execution based on semantic understanding.

    Returns:
        (requires_tool, reason)
    """
    message_lower = message.lower()

    # Check for execution verbs across all tools
    execution_verbs = set()
    for cap in TOOL_CAPABILITIES.values():
        execution_verbs.update(cap.get('execution_verbs', []))

    has_execution_verb = any(verb in message_lower for verb in execution_verbs)

    # Check if asking about existing results vs creating new ones
    explanation_patterns = ['what is', 'what does', 'explain', 'why is', 'how does', 'tell me about']
    is_explanation = any(pattern in message_lower for pattern in explanation_patterns)

    # If user has data and uses execution verb, likely needs tools
    if context.get('has_uploaded_files') and has_execution_verb and not is_explanation:
        return True, "Contains execution verb with uploaded data"

    # If asking for explanation of existing results, doesn't need tools
    if is_explanation and context.get('analysis_complete'):
        return False, "Asking for explanation of existing results"

    # Default based on context
    if context.get('has_uploaded_files') and not is_explanation:
        return True, "Has data and not asking for explanation"

    return False, "No execution needed"