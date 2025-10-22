# TPR to EDA Migration Plan
## Transform ChatMRPT into General Purpose Data Analysis Platform

## Overview
This document provides a detailed migration plan to transform ChatMRPT from a TPR-specific system to a comprehensive Exploratory Data Analysis (EDA) platform supporting CSV, Excel, XLSX, XLS, and other data formats.

## Files to Remove

### 1. TPR Module Directory (Complete Removal)
```
app/tpr_module/                              # Entire directory
├── __init__.py
├── __pycache__/
├── conversation.py
├── prompts.py
├── sandbox.py
├── TPR_MODULE_PLAN.md
├── core/
│   ├── __init__.py
│   ├── __pycache__/
│   ├── tpr_calculator.py
│   ├── tpr_conversation_manager.py
│   ├── tpr_pipeline.py
│   └── tpr_state_manager.py
├── data/
│   ├── __init__.py
│   ├── __pycache__/
│   ├── column_mapper.py
│   ├── data_validator.py
│   ├── geopolitical_zones.py
│   └── nmep_parser.py
├── integration/
│   ├── __init__.py
│   ├── __pycache__/
│   ├── llm_tpr_handler.py
│   ├── tpr_handler.py
│   ├── tpr_workflow_router.py
│   └── upload_detector.py
├── output/
│   ├── __init__.py
│   ├── __pycache__/
│   ├── output_generator.py
│   └── tpr_report_generator.py
└── services/
    ├── __init__.py
    ├── __pycache__/
    ├── facility_filter.py
    ├── raster_extractor.py
    ├── state_selector.py
    ├── threshold_detector.py
    └── tpr_visualization_service.py
```

### 2. TPR-Specific Routes
```
DELETE:
- app/web/routes/tpr_routes.py
- app/web/routes/tpr_react_routes.py
- app/web/routes/__pycache__/tpr_routes.cpython-310.pyc
```

### 3. TPR Frontend Files
```
DELETE:
- app/static/js/modules/data/tpr-download-manager.js
- app/static/js/modules/tpr/ (if exists)
- app/templates/tpr_*.html (all TPR templates)
```

### 4. TPR Documentation and Tests
```
DELETE:
- TPR_FIXES_SUMMARY.md
- TPR_COMPLETE_FIX_SUMMARY.md
- TPR_PROPER_FIX_PLAN.md
- TPR_TEST_CHECKLIST.md
- TPR_PROPER_FIX_IMPLEMENTATION.md
- TPR_DEPLOYMENT_GUIDE.md
- COMPLETE_TPR_REDESIGN.md
- NEW_TPR_UPLOAD_SYSTEM.md
- tests/tpr_test_log_*.json
- tpr_test_log_*.json
- tpr_workflow_test_*.json
```

### 5. TPR Task Documentation
```
DELETE:
- tasks/tpr_workflow.md
- tasks/tpr_to_risk_gateway.md
- tasks/tpr_aws_issue_findings.md
- tasks/tpr_upload_investigation.md
- tasks/tpr_risk_analysis_investigation.md
- tasks/tpr_tool_calling_plan.md
- tasks/project_notes/tpr_*.md (all TPR-related notes)
```

### 6. TPR Sample Data
```
DELETE:
- www/TPR data.xlsx
- www/NMEP*.xlsx
- NMEP*.xlsx (in root)
- ITN_Distribution_Export_*/www/NMEP*.xlsx
```

## Files to Modify

### 1. Upload Routes
```python
# app/web/routes/upload_routes.py
# MODIFY: Remove TPR-specific logic, add general EDA upload handling

@upload_bp.route('/upload', methods=['POST'])
def upload_data():
    """
    Universal data upload endpoint for EDA.
    Supports: CSV, Excel, JSON, Parquet, etc.
    """
    # Remove TPR detection
    # Add universal file handling
    # Integrate with EDA pipeline
```

### 2. Request Interpreter
```python
# app/core/request_interpreter.py
# MODIFY: Remove TPR-specific prompts, add EDA conversation handling

class RequestInterpreter:
    def __init__(self):
        # Remove TPR handler
        # Add EDA assistant
        self.eda_assistant = EDAAssistant()
    
    def interpret(self, message):
        # Route to EDA analysis instead of TPR
        pass
```

### 3. Service Container
```python
# app/services/container.py
# MODIFY: Remove TPR services, add EDA services

class ServiceContainer:
    def __init__(self):
        # Remove TPR initialization
        # self.tpr_handler = None  # DELETE
        # self.tpr_viz_service = None  # DELETE
        
        # Add EDA services
        self.eda_pipeline = EDAAnalysisPipeline()
        self.data_profiler = SmartProfiler()
        self.viz_engine = VisualizationEngine()
        self.stats_engine = StatisticalEngine()
```

### 4. Routes Initialization
```python
# app/web/routes/__init__.py
# MODIFY: Remove TPR blueprint registration

def register_blueprints(app):
    # Remove these lines:
    # from .tpr_routes import tpr_bp
    # app.register_blueprint(tpr_bp, url_prefix='/api/tpr')
    
    # Add EDA routes
    from .eda_routes import eda_bp
    app.register_blueprint(eda_bp, url_prefix='/api/eda')
```

### 5. Frontend Upload Module
```javascript
// app/static/js/modules/upload/file-uploader.js
// MODIFY: Remove TPR verification, add universal upload

class FileUploader {
    async uploadFiles() {
        // Remove TPR-specific logic
        // Remove verifyTPRSessionState()
        // Add universal file handling
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('analysis_type', 'eda');  // Instead of 'tpr'
        
        // Upload to EDA endpoint
        const response = await fetch('/api/eda/upload', {
            method: 'POST',
            body: formData
        });
    }
}
```

### 6. Configuration Files
```python
# app/config/base.py
# MODIFY: Remove TPR-specific configuration

class Config:
    # Remove TPR settings
    # ENABLE_TPR_MODULE = False  # DELETE
    # TPR_DATA_PATH = None  # DELETE
    
    # Add EDA settings
    ENABLE_EDA_MODULE = True
    MAX_UPLOAD_SIZE_MB = 1000
    SUPPORTED_FORMATS = ['csv', 'xlsx', 'xls', 'json', 'parquet']
    USE_DUCKDB = True
    USE_POLARS = True
```

## New Files to Create

### 1. EDA Module Structure
```
app/eda/
├── __init__.py
├── config.py                    # EDA-specific configuration
├── ingestion/
│   ├── __init__.py
│   ├── file_handler.py         # Universal file handler
│   ├── format_detector.py      # Smart format detection
│   ├── data_validator.py       # Data quality checks
│   └── chunked_reader.py       # Large file handling
├── profiling/
│   ├── __init__.py
│   ├── smart_profiler.py       # Intelligent profiling
│   ├── quick_insights.py       # Fast initial analysis
│   ├── deep_analysis.py        # Comprehensive analysis
│   └── profiling_cache.py      # Cache profiling results
├── analysis/
│   ├── __init__.py
│   ├── pipeline.py             # Main analysis pipeline
│   ├── statistical.py          # Statistical tests
│   ├── correlations.py         # Correlation analysis
│   ├── distributions.py        # Distribution analysis
│   └── outliers.py            # Outlier detection
├── transformation/
│   ├── __init__.py
│   ├── cleaning.py            # Data cleaning utilities
│   ├── encoding.py            # Categorical encoding
│   ├── scaling.py             # Feature scaling
│   └── engineering.py         # Feature engineering
├── visualization/
│   ├── __init__.py
│   ├── engine.py              # Main viz engine
│   ├── plotly_viz.py          # Interactive plots
│   ├── matplotlib_viz.py      # Static plots
│   └── templates.py           # Viz templates
├── ml_exploration/
│   ├── __init__.py
│   ├── auto_ml.py             # Automated ML
│   ├── feature_selection.py   # Feature importance
│   └── model_comparison.py    # Model benchmarking
├── llm_integration/
│   ├── __init__.py
│   ├── eda_assistant.py       # LLM-powered assistant
│   ├── insight_generator.py   # Automatic insights
│   └── prompts.py            # EDA prompts
├── export/
│   ├── __init__.py
│   ├── report_generator.py    # Generate reports
│   ├── excel_export.py        # Excel export
│   └── pdf_export.py         # PDF export
└── utils/
    ├── __init__.py
    ├── performance.py          # Performance monitoring
    ├── caching.py             # Result caching
    └── database.py            # DuckDB integration
```

### 2. EDA Routes
```python
# app/web/routes/eda_routes.py
from flask import Blueprint, request, jsonify
from app.eda import EDAAnalysisPipeline

eda_bp = Blueprint('eda', __name__)

@eda_bp.route('/upload', methods=['POST'])
def upload_for_eda():
    """Universal data upload for EDA."""
    pass

@eda_bp.route('/profile/<session_id>', methods=['GET'])
def get_profile(session_id):
    """Get data profiling report."""
    pass

@eda_bp.route('/analyze', methods=['POST'])
def run_analysis():
    """Run specific analysis."""
    pass

@eda_bp.route('/visualize', methods=['POST'])
def create_visualization():
    """Generate visualization."""
    pass

@eda_bp.route('/export/<session_id>', methods=['GET'])
def export_results(session_id):
    """Export analysis results."""
    pass
```

### 3. Frontend EDA Modules
```javascript
// app/static/js/modules/eda/eda-manager.js
class EDAManager {
    constructor() {
        this.uploader = new DataUploader();
        this.profiler = new DataProfiler();
        this.analyzer = new DataAnalyzer();
        this.visualizer = new DataVisualizer();
    }
    
    async startEDASession(file) {
        // Upload and start analysis
    }
}

// app/static/js/modules/eda/data-profiler.js
class DataProfiler {
    async generateProfile(sessionId, quick = false) {
        // Generate profiling report
    }
}

// app/static/js/modules/eda/data-analyzer.js
class DataAnalyzer {
    async runAnalysis(sessionId, analysisType, params) {
        // Run specific analysis
    }
}

// app/static/js/modules/eda/data-visualizer.js
class DataVisualizer {
    async createVisualization(sessionId, vizType, columns) {
        // Create visualization
    }
}
```

### 4. Requirements Updates
```txt
# requirements.txt - ADD:
duckdb>=0.10.0
polars>=0.20.0
ydata-profiling>=4.6.0
sweetviz>=2.3.0
autoviz>=0.1.900
dataprep>=0.4.5
pyarrow>=15.0.0
fastparquet>=2024.2.0
```

## Migration Steps

### Phase 1: Preparation (Day 1-2)
1. **Backup Current System**
   ```bash
   # Create backup branch
   git checkout -b tpr-backup-before-eda
   git add .
   git commit -m "Backup TPR system before EDA migration"
   
   # Archive TPR module
   tar -czf tpr_module_backup.tar.gz app/tpr_module/
   ```

2. **Create EDA Branch**
   ```bash
   git checkout -b feature/eda-pipeline
   ```

### Phase 2: Remove TPR (Day 3-4)
1. **Delete TPR Files**
   ```bash
   # Remove TPR module
   rm -rf app/tpr_module/
   
   # Remove TPR routes
   rm app/web/routes/tpr_routes.py
   rm app/web/routes/tpr_react_routes.py
   
   # Remove TPR frontend
   rm app/static/js/modules/data/tpr-download-manager.js
   
   # Remove TPR docs
   rm TPR_*.md
   rm tasks/tpr_*.md
   rm tasks/project_notes/tpr_*.md
   ```

2. **Update Imports**
   - Remove all TPR imports from other files
   - Update service container
   - Update route registration

### Phase 3: Build EDA Foundation (Day 5-10)
1. **Create EDA Module Structure**
   ```bash
   mkdir -p app/eda/{ingestion,profiling,analysis,transformation,visualization,ml_exploration,llm_integration,export,utils}
   ```

2. **Implement Core Components**
   - File handler with DuckDB
   - Smart profiler
   - Analysis pipeline
   - Visualization engine

### Phase 4: Integration (Day 11-15)
1. **Update Existing Components**
   - Modify upload routes
   - Update request interpreter
   - Modify service container
   - Update frontend

2. **Add New Features**
   - LLM integration
   - Advanced analytics
   - Export capabilities

### Phase 5: Testing (Day 16-20)
1. **Unit Tests**
   ```python
   # tests/test_eda_pipeline.py
   def test_file_upload():
       pass
   
   def test_profiling():
       pass
   
   def test_analysis():
       pass
   ```

2. **Integration Tests**
   - Test with various file formats
   - Test with large datasets
   - Test all analysis types

### Phase 6: Documentation (Day 21-22)
1. **Update Documentation**
   - Update README.md
   - Create EDA user guide
   - Update API documentation

2. **Migration Guide**
   - For existing users
   - For developers

### Phase 7: Deployment (Day 23-25)
1. **Staging Deployment**
   ```bash
   # Deploy to staging
   ./deploy_to_staging.sh
   ```

2. **Production Deployment**
   ```bash
   # After testing, deploy to production
   ./deploy_to_production.sh
   ```

## Rollback Plan

If issues arise:

1. **Quick Rollback**
   ```bash
   # Revert to TPR backup branch
   git checkout tpr-backup-before-eda
   ```

2. **Restore TPR Module**
   ```bash
   # Restore from backup
   tar -xzf tpr_module_backup.tar.gz
   ```

3. **Re-enable TPR Routes**
   - Uncomment TPR blueprint registration
   - Restore TPR service initialization

## Success Criteria

### Technical Metrics
- [ ] All file formats supported (CSV, Excel, JSON, Parquet)
- [ ] 10x performance improvement with DuckDB
- [ ] Profiling completes in <5 seconds for 1M rows
- [ ] All statistical tests working
- [ ] Visualization generation <1 second

### User Experience
- [ ] Seamless file upload experience
- [ ] Intuitive analysis workflow
- [ ] Clear error messages
- [ ] Comprehensive documentation
- [ ] No breaking changes for existing features

### Business Metrics
- [ ] 80% user adoption within 1 month
- [ ] Support tickets reduced by 50%
- [ ] User satisfaction score >4.5/5
- [ ] Analysis time reduced by 70%

## Risk Mitigation

### Identified Risks
1. **Data Loss**: Backup all user data before migration
2. **Feature Gaps**: Ensure EDA covers all TPR use cases
3. **Performance Issues**: Test with large datasets
4. **User Resistance**: Provide training and documentation

### Mitigation Strategies
1. **Gradual Rollout**: Deploy to subset of users first
2. **Feature Flags**: Enable/disable EDA features dynamically
3. **Monitoring**: Track performance and errors closely
4. **Support**: Dedicated support during transition

## Communication Plan

### Internal Communication
- Engineering team briefing
- Daily standup updates
- Migration progress dashboard

### User Communication
- Email announcement 2 weeks before
- In-app notifications
- Migration guide and tutorials
- Support channels ready

## Post-Migration Tasks

1. **Monitor Performance**
   - Track response times
   - Monitor error rates
   - Analyze usage patterns

2. **Gather Feedback**
   - User surveys
   - Support ticket analysis
   - Usage analytics

3. **Iterate and Improve**
   - Fix identified issues
   - Add requested features
   - Optimize performance

## Conclusion

This migration plan transforms ChatMRPT from a specialized TPR tool to a comprehensive EDA platform. The new system will be more flexible, performant, and user-friendly, supporting any type of data analysis task while maintaining the core functionality users depend on.