# ChatMRPT Data Analysis Pipeline Architecture
## Transform from TPR-specific to General Purpose EDA System

## Executive Summary
This document outlines the transformation of ChatMRPT from a TPR-specific system to a comprehensive Exploratory Data Analysis (EDA) pipeline that can handle CSV, Excel, XLSX, and XLS files for any type of data analysis.

## Architecture Overview

### Core Technologies Stack (2024-2025 Best Practices)

#### 1. **High-Performance Data Processing**
- **Primary Engine**: DuckDB (10x+ faster than pandas)
- **Secondary Engine**: Polars (30x faster than pandas for DataFrame operations)
- **Fallback**: Pandas 2.0 with PyArrow backend
- **Interoperability**: Apache Arrow for zero-copy data transfer between tools

#### 2. **Automated EDA Tools**
- **YData Profiling** (formerly Pandas Profiling) - Comprehensive analysis
- **SweetViz** - Quick comparisons and target analysis
- **AutoViz** - Rapid visualization generation
- **DataPrep** - For large datasets (10x faster than pandas-based tools)

#### 3. **File Format Handling**
- **Preferred Storage**: Parquet (6.5x smaller than CSV, much faster)
- **Input Support**: CSV, Excel (XLS/XLSX), JSON, Parquet
- **Smart Detection**: Auto-detect file format and structure
- **Streaming**: Support for large files via chunking

#### 4. **Architecture Pattern**
- **Medallion Architecture**: Bronze → Silver → Gold data layers
- **Pipeline Pattern**: Extract → Transform → Load (ETL)
- **Processing**: In-memory for speed, file-based for scale

## System Components

### 1. Data Ingestion Layer
```python
# app/eda/ingestion/file_handler.py
class UniversalFileHandler:
    """
    Handles all file formats with intelligent detection and parsing.
    Uses DuckDB for direct querying without loading into memory.
    """
    
    SUPPORTED_FORMATS = {
        'csv': ['csv', 'tsv', 'txt'],
        'excel': ['xlsx', 'xls', 'xlsm', 'xlsb'],
        'parquet': ['parquet', 'pq'],
        'json': ['json', 'jsonl'],
        'feather': ['feather', 'ftr'],
        'stata': ['dta'],
        'spss': ['sav', 'zsav'],
        'sas': ['sas7bdat', 'xpt']
    }
    
    def ingest(self, file_path):
        # Auto-detect format
        # Use DuckDB for direct querying
        # Fall back to Polars/Pandas if needed
        pass
```

### 2. Data Profiling Engine
```python
# app/eda/profiling/profiler.py
class SmartProfiler:
    """
    Intelligent profiling that chooses the best tool based on data size.
    """
    
    def profile(self, data, quick=False):
        if quick:
            return self._quick_profile_with_sweetviz(data)
        elif data.shape[0] > 1_000_000:
            return self._large_data_profile_with_dataprep(data)
        else:
            return self._comprehensive_profile_with_ydata(data)
```

### 3. Analysis Pipeline
```python
# app/eda/pipeline/analysis_pipeline.py
class EDAAnalysisPipeline:
    """
    Flexible pipeline that can handle simple to complex analysis.
    """
    
    ANALYSIS_LEVELS = {
        'basic': ['summary_stats', 'missing_values', 'data_types'],
        'intermediate': ['correlations', 'distributions', 'outliers'],
        'advanced': ['feature_engineering', 'dimensionality_reduction', 'clustering'],
        'ml_ready': ['feature_selection', 'train_test_split', 'baseline_models']
    }
    
    def run_analysis(self, data, level='intermediate', custom_steps=None):
        # Dynamic pipeline execution
        pass
```

### 4. Visualization Generator
```python
# app/eda/visualization/viz_engine.py
class VisualizationEngine:
    """
    Generates interactive and static visualizations.
    """
    
    VISUALIZATION_TYPES = {
        'univariate': ['histogram', 'boxplot', 'density', 'qq_plot'],
        'bivariate': ['scatter', 'heatmap', 'joint_plot', 'pair_plot'],
        'multivariate': ['parallel_coordinates', '3d_scatter', 'pca_plot'],
        'time_series': ['line_plot', 'seasonal_decompose', 'autocorrelation'],
        'categorical': ['bar_chart', 'count_plot', 'mosaic_plot'],
        'geographic': ['choropleth', 'bubble_map', 'heatmap']
    }
```

### 5. Statistical Analysis Module
```python
# app/eda/statistics/stats_engine.py
class StatisticalEngine:
    """
    Comprehensive statistical analysis capabilities.
    """
    
    TESTS = {
        'normality': ['shapiro', 'anderson', 'kstest'],
        'correlation': ['pearson', 'spearman', 'kendall'],
        'comparison': ['ttest', 'anova', 'kruskal', 'mann_whitney'],
        'regression': ['linear', 'logistic', 'ridge', 'lasso'],
        'time_series': ['adf', 'kpss', 'acf', 'pacf']
    }
```

## File Structure Changes

### Files to Remove (TPR-specific)
```
DELETE:
- app/tpr_module/                    # Entire TPR module
- app/web/routes/tpr_routes.py       # TPR-specific routes
- app/static/js/modules/tpr/         # TPR frontend modules
- app/templates/tpr_*.html           # TPR templates
```

### Files to Modify
```
MODIFY:
- app/web/routes/upload_routes.py    # Generalize for all data types
- app/core/request_interpreter.py    # Add EDA conversation handling
- app/static/js/modules/upload/      # Support multiple file formats
- app/services/container.py          # Add EDA service initialization
```

### New Files to Create
```
CREATE:
app/eda/
├── __init__.py
├── ingestion/
│   ├── file_handler.py         # Universal file ingestion
│   ├── format_detector.py      # Smart format detection
│   └── data_validator.py       # Data quality checks
├── profiling/
│   ├── profiler.py            # Intelligent profiling
│   ├── quick_insights.py      # Fast initial analysis
│   └── deep_analysis.py       # Comprehensive analysis
├── pipeline/
│   ├── analysis_pipeline.py   # Main pipeline orchestrator
│   ├── transformations.py     # Data transformations
│   └── feature_engineering.py # Feature creation
├── visualization/
│   ├── viz_engine.py          # Visualization generator
│   ├── interactive_plots.py   # Plotly/Bokeh plots
│   └── static_plots.py        # Matplotlib/Seaborn
├── statistics/
│   ├── stats_engine.py        # Statistical tests
│   ├── distributions.py       # Distribution analysis
│   └── hypothesis_testing.py  # Statistical tests
├── ml_exploration/
│   ├── auto_ml.py             # Automated ML exploration
│   ├── feature_selection.py   # Feature importance
│   └── model_comparison.py    # Quick model benchmarking
└── utils/
    ├── performance.py          # Performance monitoring
    ├── caching.py             # Result caching
    └── export.py              # Export utilities
```

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
1. Set up DuckDB and Polars integration
2. Create universal file handler
3. Remove TPR-specific code
4. Update upload routes for flexibility

### Phase 2: Core EDA (Week 3-4)
1. Integrate YData Profiling, SweetViz, AutoViz
2. Build analysis pipeline framework
3. Implement basic statistical tests
4. Create visualization engine

### Phase 3: Advanced Features (Week 5-6)
1. Add ML exploration capabilities
2. Implement feature engineering tools
3. Create custom analysis workflows
4. Add export/reporting features

### Phase 4: Optimization (Week 7-8)
1. Implement caching strategies
2. Add parallel processing
3. Optimize for large datasets
4. Performance testing

## API Design

### RESTful Endpoints
```python
# Data Upload
POST /api/eda/upload
  - Accepts: CSV, Excel, Parquet, JSON
  - Returns: session_id, data_summary

# Quick Profile
GET /api/eda/profile/{session_id}
  - Parameters: quick=true/false
  - Returns: profiling_report

# Run Analysis
POST /api/eda/analyze
  - Body: {session_id, analysis_type, parameters}
  - Returns: analysis_results

# Generate Visualization
POST /api/eda/visualize
  - Body: {session_id, viz_type, columns, options}
  - Returns: visualization_url

# Statistical Test
POST /api/eda/stats
  - Body: {session_id, test_type, columns, parameters}
  - Returns: test_results

# Export Results
GET /api/eda/export/{session_id}
  - Parameters: format=html/pdf/excel
  - Returns: download_url
```

## Frontend Updates

### New UI Components
```javascript
// app/static/js/modules/eda/

// Main EDA Manager
class EDAManager {
    constructor() {
        this.fileHandler = new FileHandler();
        this.profiler = new DataProfiler();
        this.visualizer = new Visualizer();
        this.analyzer = new Analyzer();
    }
    
    async uploadAndAnalyze(file) {
        // Upload file
        const session = await this.fileHandler.upload(file);
        
        // Quick profile
        const profile = await this.profiler.quickProfile(session.id);
        
        // Show initial insights
        this.showInsights(profile);
        
        // Enable analysis options
        this.enableAnalysisTools(session);
    }
}
```

## Performance Targets

### Based on 2024 Industry Standards
- **File Upload**: < 2 seconds for files up to 100MB
- **Quick Profile**: < 5 seconds for datasets up to 1M rows
- **Comprehensive Profile**: < 30 seconds for datasets up to 10M rows
- **Visualizations**: < 1 second per chart
- **Statistical Tests**: < 2 seconds per test
- **Memory Usage**: < 2x dataset size with DuckDB

## LLM Integration for Intelligent Analysis

### Conversational EDA
```python
# app/eda/llm/eda_assistant.py
class EDAAssistant:
    """
    LLM-powered assistant for intelligent data exploration.
    """
    
    CAPABILITIES = {
        'suggest_analysis': 'Recommend relevant analyses based on data',
        'interpret_results': 'Explain statistical results in plain language',
        'generate_insights': 'Discover patterns and anomalies',
        'recommend_viz': 'Suggest appropriate visualizations',
        'guide_cleaning': 'Provide data cleaning recommendations',
        'feature_ideas': 'Suggest feature engineering approaches'
    }
    
    def analyze_with_llm(self, data_profile, user_query):
        # Use LLM to provide intelligent recommendations
        pass
```

## Error Handling and Validation

### Robust Error Management
```python
class EDAErrorHandler:
    ERROR_TYPES = {
        'FILE_TOO_LARGE': 'File exceeds 1GB limit',
        'UNSUPPORTED_FORMAT': 'File format not supported',
        'CORRUPT_DATA': 'File appears to be corrupted',
        'INSUFFICIENT_DATA': 'Not enough data for analysis',
        'MEMORY_ERROR': 'Insufficient memory for operation'
    }
    
    def handle_gracefully(self, error):
        # Provide helpful error messages and recovery options
        pass
```

## Security Considerations

### Data Privacy and Security
- **File Scanning**: Virus/malware scanning on upload
- **Data Isolation**: Session-based data isolation
- **Sensitive Data**: PII detection and masking options
- **Access Control**: User-based access restrictions
- **Audit Logging**: Track all data operations

## Monitoring and Analytics

### System Metrics
```python
class EDAMonitor:
    METRICS = {
        'upload_count': 'Files uploaded per day',
        'analysis_types': 'Most used analysis features',
        'processing_time': 'Average analysis duration',
        'file_formats': 'Distribution of file types',
        'error_rate': 'Percentage of failed operations',
        'user_satisfaction': 'Feature usage and feedback'
    }
```

## Migration Strategy

### From TPR to EDA Pipeline
1. **Backup Current System**
   - Create full backup of TPR module
   - Document existing functionality

2. **Gradual Migration**
   - Keep TPR as legacy module initially
   - Run EDA pipeline in parallel
   - Migrate users gradually

3. **Feature Parity**
   - Ensure EDA can handle TPR use cases
   - Provide migration tools for existing data
   - Update documentation

4. **Deprecation**
   - Announce TPR deprecation timeline
   - Provide migration guides
   - Remove TPR code after transition

## Success Metrics

### KPIs for EDA Pipeline
- **Adoption Rate**: 80% of users within 3 months
- **Performance**: 10x faster than current system
- **User Satisfaction**: >4.5/5 rating
- **Feature Usage**: All analysis types used weekly
- **Error Rate**: <1% of operations fail
- **Data Volume**: Handle 100GB+ datasets

## Conclusion

This architecture transforms ChatMRPT into a state-of-the-art EDA platform leveraging the latest tools and best practices from 2024-2025. The system will be faster, more flexible, and capable of handling any data analysis task from simple summaries to complex machine learning explorations.

The use of DuckDB, Polars, and modern profiling tools ensures exceptional performance, while the modular architecture allows for easy extension and maintenance. The LLM integration provides intelligent guidance, making advanced analysis accessible to users of all skill levels.