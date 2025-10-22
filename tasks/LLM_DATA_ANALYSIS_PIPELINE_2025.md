# LLM-Powered Data Analysis Pipeline - Complete Redesign Plan
## From TPR Module to General-Purpose Exploratory Data Analysis

### Executive Summary
Transform the existing TPR (Test Positivity Rate) module into a comprehensive, LLM-powered data analysis pipeline that enables users to perform exploratory data analysis through natural language. The system will give the LLM full access to data with code execution capabilities, supporting CSV, Excel (XLSX/XLS), and SQL operations.

### Architecture Overview

```
User → Natural Language Query → LLM Agent → Code Generation → Sandbox Execution → Results/Visualization
         ↑                                       ↓
         └─────── Iterative Refinement ←─────────┘
```

## Industry Standards & Best Practices (2024-2025)

### 1. Core Technologies
- **PandasAI**: Conversational data analysis with privacy controls
- **E2B Sandbox**: Secure code execution environment
- **LangChain**: Agent orchestration and tool management
- **Scikit-LLM**: Integration of LLMs with traditional ML workflows
- **Code Interpreter Pattern**: OpenAI's Advanced Data Analysis approach

### 2. Security & Privacy
- **Sandboxed Execution**: Isolated Docker/E2B environment for code execution
- **Privacy Mode**: Option to not send data content to LLM (only schemas)
- **Resource Limits**: CPU, memory, and execution time constraints
- **File System Isolation**: Restricted access to system files

### 3. Data Science Stack Integration
```python
SUPPORTED_LIBRARIES = {
    'pandas': 'Data manipulation and analysis',
    'numpy': 'Numerical computing',
    'scikit-learn': 'Machine learning algorithms',
    'matplotlib': 'Static visualizations',
    'seaborn': 'Statistical data visualization',
    'plotly': 'Interactive visualizations',
    'scipy': 'Scientific computing',
    'statsmodels': 'Statistical modeling',
    'sqlalchemy': 'SQL database interaction',
    'openpyxl': 'Excel file operations',
    'xlrd': 'Legacy Excel support'
}
```

## Implementation Plan

### Phase 1: Remove TPR Complexity (Week 1)

#### Files to Remove
```
app/tpr_module/                    # Entire TPR module
├── __init__.py
├── data/
│   ├── nmep_parser.py            # Rigid NMEP format parser
│   └── tpr_processor.py          # TPR-specific processing
├── integration/
│   ├── __init__.py
│   └── llm_tpr_handler.py        # TPR-specific LLM handler
├── output/
│   └── output_generator.py       # TPR report generator
├── conversation.py               # TPR conversation flow
├── prompts.py                    # TPR-specific prompts
└── sandbox.py                    # TPR testing

app/web/routes/tpr_routes.py      # TPR-specific routes
app/web/routes/tpr_react_routes.py # TPR React routes
```

#### Files to Modify
```python
# app/static/js/modules/upload/file-uploader.js
# Remove lines 850-870 (TPR verification and refresh logic)
# Remove verifyTPRSessionState() function
# Remove TPR-specific upload handlers

# app/web/routes/__init__.py
# Remove TPR blueprint registration

# app/services/container.py
# Remove TPR service initialization
```

### Phase 2: Build Core Data Analysis Engine (Week 1-2)

#### 2.1 Create Flexible Data Handler
```python
# app/data_analysis/core/data_handler.py
class UniversalDataHandler:
    """
    Handles all data formats with automatic detection
    """
    
    SUPPORTED_FORMATS = {
        '.csv': 'pandas.read_csv',
        '.xlsx': 'pandas.read_excel',
        '.xls': 'pandas.read_excel',
        '.json': 'pandas.read_json',
        '.parquet': 'pandas.read_parquet',
        '.feather': 'pandas.read_feather',
        '.sql': 'sqlalchemy connection'
    }
    
    def load_data(self, file_path, **kwargs):
        """Automatically detect and load data"""
        
    def get_data_profile(self):
        """Return schema, stats, dtypes for LLM context"""
        
    def prepare_llm_context(self, privacy_mode=False):
        """Prepare data context for LLM"""
```

#### 2.2 Code Execution Sandbox
```python
# app/data_analysis/sandbox/executor.py
class SecureCodeExecutor:
    """
    Secure sandbox for LLM-generated code execution
    """
    
    def __init__(self):
        self.sandbox_config = {
            'timeout': 30,  # seconds
            'memory_limit': '512MB',
            'cpu_limit': 1,
            'allowed_imports': SUPPORTED_LIBRARIES.keys(),
            'filesystem_access': 'readonly',
            'network_access': False
        }
    
    def execute_code(self, code: str, context: dict):
        """Execute code in sandbox with data context"""
        
    def validate_code(self, code: str):
        """Pre-execution validation and sanitization"""
```

### Phase 3: LLM Integration with Smart Prompts (Week 2)

#### 3.1 Advanced Prompt Templates
```python
# app/data_analysis/prompts/templates.py

SYSTEM_PROMPT = """You are an expert data analyst with access to a comprehensive Python environment.

## Your Capabilities:
- Full access to pandas, numpy, scikit-learn, matplotlib, seaborn, plotly
- Can perform exploratory data analysis (EDA)
- Can build machine learning models
- Can create visualizations
- Can perform statistical tests
- Can clean and transform data

## Data Context:
{data_context}

## Output Format:
1. **Thought Process**: Brief explanation of approach
2. **Code**: Python code to execute
3. **Interpretation**: What the results mean

## Best Practices:
- Always check data shape and dtypes first
- Handle missing values appropriately
- Use appropriate visualizations for data types
- Provide statistical significance when relevant
- Suggest next steps for analysis
"""

ANALYSIS_PATTERNS = {
    'eda': """
    Perform comprehensive exploratory data analysis:
    1. Data shape and info
    2. Missing value analysis
    3. Distribution of numerical features
    4. Correlation analysis
    5. Outlier detection
    6. Feature relationships
    """,
    
    'ml_pipeline': """
    Build a machine learning pipeline:
    1. Data preprocessing
    2. Feature engineering
    3. Model selection
    4. Cross-validation
    5. Performance metrics
    6. Feature importance
    """,
    
    'statistical': """
    Perform statistical analysis:
    1. Descriptive statistics
    2. Hypothesis testing
    3. ANOVA/Chi-square tests
    4. Regression analysis
    5. Time series analysis (if applicable)
    """
}
```

#### 3.2 Dynamic Tool Generation
```python
# app/data_analysis/agents/analyst.py
class DataAnalystAgent:
    """
    LLM-powered data analyst with dynamic tool generation
    """
    
    def __init__(self, llm_manager):
        self.llm = llm_manager
        self.executor = SecureCodeExecutor()
        self.conversation_history = []
    
    async def analyze(self, query: str, data_context: dict):
        """
        Main analysis entry point
        """
        # Generate analysis plan
        plan = await self._generate_analysis_plan(query, data_context)
        
        # Execute iteratively
        results = []
        for step in plan:
            code = await self._generate_code(step, data_context)
            result = await self.executor.execute_code(code, data_context)
            results.append(result)
            
            # Update context with results
            data_context['previous_results'] = results
        
        return self._format_response(results)
    
    async def _generate_code(self, task: str, context: dict):
        """Generate executable Python code for task"""
        
    async def _handle_errors(self, error: str, code: str):
        """Self-healing: fix code based on error"""
```

### Phase 4: Frontend Redesign (Week 2-3)

#### 4.1 New Upload Interface
```javascript
// app/static/js/modules/data_analysis/upload.js
class DataAnalysisUploader {
    constructor() {
        this.supportedFormats = ['.csv', '.xlsx', '.xls', '.json'];
        this.maxFileSize = 100 * 1024 * 1024; // 100MB
    }
    
    async handleUpload(file) {
        // No page refresh!
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/data-analysis/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        this.displayDataProfile(result.profile);
        this.enableAnalysisChat();
    }
    
    displayDataProfile(profile) {
        // Show data shape, columns, types, preview
    }
}
```

#### 4.2 Interactive Analysis Interface
```javascript
// app/static/js/modules/data_analysis/chat.js
class DataAnalysisChat {
    constructor() {
        this.analysisHistory = [];
        this.currentDataset = null;
    }
    
    async sendAnalysisRequest(query) {
        // Stream results with code and visualizations
        const response = await fetch('/api/data-analysis/analyze', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                query: query,
                dataset_id: this.currentDataset,
                mode: 'exploratory'  // or 'ml', 'statistical'
            })
        });
        
        // Handle streaming response
        const reader = response.body.getReader();
        await this.handleStreamingResponse(reader);
    }
    
    async handleStreamingResponse(reader) {
        // Display code execution in real-time
        // Show intermediate results
        // Render visualizations dynamically
    }
}
```

### Phase 5: Advanced Features (Week 3)

#### 5.1 Multi-Dataset Analysis
```python
# app/data_analysis/core/multi_dataset.py
class MultiDatasetAnalyzer:
    """Handle analysis across multiple uploaded datasets"""
    
    def join_datasets(self, datasets: list, join_config: dict):
        """Intelligent joining based on common columns"""
    
    def cross_dataset_analysis(self, query: str):
        """Analyze relationships across datasets"""
```

#### 5.2 Automated Insights Generation
```python
# app/data_analysis/insights/generator.py
class InsightGenerator:
    """Automatically generate insights from data"""
    
    def generate_insights(self, data):
        insights = []
        
        # Statistical anomalies
        insights.extend(self._find_anomalies(data))
        
        # Correlations
        insights.extend(self._find_correlations(data))
        
        # Trends
        insights.extend(self._find_trends(data))
        
        # ML-based patterns
        insights.extend(self._find_patterns(data))
        
        return insights
```

#### 5.3 Export and Reporting
```python
# app/data_analysis/export/reporter.py
class AnalysisReporter:
    """Generate comprehensive analysis reports"""
    
    def generate_report(self, analysis_session):
        """Create PDF/HTML report with all analysis"""
    
    def export_code_notebook(self, analysis_session):
        """Export as Jupyter notebook"""
    
    def export_dashboard(self, analysis_session):
        """Create interactive dashboard"""
```

## Migration Strategy

### Week 1: Foundation
1. Back up existing codebase
2. Remove TPR modules
3. Implement basic data handler
4. Set up code sandbox

### Week 2: Core Features
1. Integrate LLM with code generation
2. Implement streaming responses
3. Create analysis templates
4. Test with sample datasets

### Week 3: Polish & Deploy
1. Add advanced features
2. Comprehensive testing
3. Documentation
4. Gradual rollout

## Testing Strategy

```python
# tests/test_data_analysis.py
def test_csv_upload_and_analysis():
    """Test basic CSV analysis workflow"""
    
def test_excel_multiple_sheets():
    """Test Excel with multiple sheets"""
    
def test_code_sandbox_security():
    """Ensure malicious code is blocked"""
    
def test_llm_code_generation():
    """Test code generation quality"""
    
def test_visualization_generation():
    """Test chart creation"""
    
def test_ml_pipeline():
    """Test end-to-end ML workflow"""
```

## Configuration

```python
# app/config/data_analysis.py
DATA_ANALYSIS_CONFIG = {
    'max_file_size_mb': 100,
    'sandbox_timeout_seconds': 30,
    'max_memory_mb': 512,
    'allowed_libraries': SUPPORTED_LIBRARIES.keys(),
    'privacy_mode': False,  # Don't send data to LLM
    'cache_results': True,
    'auto_insights': True,
    'streaming_enabled': True,
    'visualization_backend': 'plotly',  # or 'matplotlib'
    'llm_model': 'qwen3-8b',
    'llm_temperature': 0.3,
    'max_iterations': 5,  # For self-healing code
}
```

## Success Metrics

1. **User Experience**
   - No page refreshes
   - < 2s response time for simple queries
   - Streaming responses for long analyses

2. **Analysis Quality**
   - 95% code execution success rate
   - Meaningful insights generation
   - Appropriate visualization selection

3. **Security**
   - Zero code escapes from sandbox
   - No data leaks to LLM (in privacy mode)
   - Resource limits enforced

4. **Flexibility**
   - Support 10+ file formats
   - Handle datasets up to 100MB
   - Work with any tabular data structure

## Conclusion

This redesign transforms the rigid TPR module into a flexible, powerful, LLM-driven data analysis platform that democratizes data science while maintaining security and performance. The system leverages 2024-2025 best practices including sandboxed execution, privacy controls, and intelligent code generation to provide a ChatGPT-like experience for data analysis.