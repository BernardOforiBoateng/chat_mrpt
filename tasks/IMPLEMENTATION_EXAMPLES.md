# LLM Data Analysis Pipeline - Implementation Examples

## 1. Core Data Handler Implementation

```python
# app/data_analysis/core/data_handler.py
import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
import hashlib

class UniversalDataHandler:
    """
    Universal data handler with automatic format detection and LLM-friendly context generation
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.data_path = Path(f"instance/uploads/{session_id}")
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.datasets = {}
        self.metadata = {}
    
    def load_data(self, file_path: Union[str, Path], name: Optional[str] = None) -> str:
        """
        Load data from file with automatic format detection
        Returns dataset_id for reference
        """
        file_path = Path(file_path)
        file_ext = file_path.suffix.lower()
        
        # Generate unique ID for dataset
        dataset_id = hashlib.md5(f"{file_path.name}_{self.session_id}".encode()).hexdigest()[:8]
        name = name or file_path.stem
        
        try:
            if file_ext == '.csv':
                df = pd.read_csv(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                # Try to load all sheets
                excel_file = pd.ExcelFile(file_path)
                if len(excel_file.sheet_names) == 1:
                    df = pd.read_excel(file_path)
                else:
                    # Load multiple sheets as dict
                    df = pd.read_excel(file_path, sheet_name=None)
                    # For now, concatenate or let user choose
                    df = pd.concat(df.values(), ignore_index=True)
            elif file_ext == '.json':
                df = pd.read_json(file_path)
            elif file_ext == '.parquet':
                df = pd.read_parquet(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
            
            # Store dataset
            self.datasets[dataset_id] = df
            
            # Generate metadata
            self.metadata[dataset_id] = {
                'name': name,
                'shape': df.shape,
                'columns': list(df.columns),
                'dtypes': df.dtypes.to_dict(),
                'memory_usage': df.memory_usage(deep=True).sum() / 1024**2,  # MB
                'null_counts': df.isnull().sum().to_dict(),
                'numeric_columns': list(df.select_dtypes(include=[np.number]).columns),
                'categorical_columns': list(df.select_dtypes(include=['object', 'category']).columns),
                'datetime_columns': list(df.select_dtypes(include=['datetime64']).columns),
            }
            
            # Add basic statistics for numeric columns
            if self.metadata[dataset_id]['numeric_columns']:
                self.metadata[dataset_id]['numeric_stats'] = df[
                    self.metadata[dataset_id]['numeric_columns']
                ].describe().to_dict()
            
            return dataset_id
            
        except Exception as e:
            raise Exception(f"Failed to load data: {str(e)}")
    
    def get_llm_context(self, dataset_id: str, privacy_mode: bool = False) -> Dict[str, Any]:
        """
        Prepare data context for LLM with privacy options
        """
        if dataset_id not in self.datasets:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        df = self.datasets[dataset_id]
        meta = self.metadata[dataset_id]
        
        context = {
            'dataset_id': dataset_id,
            'name': meta['name'],
            'shape': meta['shape'],
            'columns': meta['columns'],
            'dtypes': {k: str(v) for k, v in meta['dtypes'].items()},
            'null_counts': meta['null_counts'],
            'numeric_columns': meta['numeric_columns'],
            'categorical_columns': meta['categorical_columns'],
            'datetime_columns': meta['datetime_columns'],
        }
        
        if not privacy_mode:
            # Include sample data and statistics
            context['head'] = df.head(5).to_dict('records')
            context['numeric_stats'] = meta.get('numeric_stats', {})
            
            # Value counts for categorical columns (top 10)
            context['categorical_values'] = {}
            for col in meta['categorical_columns'][:5]:  # Limit to first 5
                value_counts = df[col].value_counts().head(10)
                context['categorical_values'][col] = value_counts.to_dict()
        
        return context
    
    def get_data_for_execution(self, dataset_id: str) -> pd.DataFrame:
        """Get actual dataframe for code execution"""
        return self.datasets.get(dataset_id)
```

## 2. Secure Code Executor

```python
# app/data_analysis/sandbox/executor.py
import subprocess
import tempfile
import pickle
import base64
import json
import sys
import io
import ast
import traceback
from typing import Dict, Any, Optional
from contextlib import redirect_stdout, redirect_stderr

class SecureCodeExecutor:
    """
    Secure sandbox for executing LLM-generated code
    Uses subprocess isolation with resource limits
    """
    
    def __init__(self):
        self.timeout = 30  # seconds
        self.max_memory = 512 * 1024 * 1024  # 512MB
        self.allowed_imports = {
            'pandas', 'numpy', 'matplotlib', 'seaborn', 'plotly',
            'scipy', 'sklearn', 'statsmodels', 'math', 'statistics',
            'datetime', 'json', 're', 'collections', 'itertools'
        }
    
    def validate_code(self, code: str) -> tuple[bool, str]:
        """
        Validate code for safety before execution
        """
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                # Check for dangerous operations
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module = alias.name.split('.')[0]
                        if module not in self.allowed_imports:
                            return False, f"Import of '{module}' is not allowed"
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module.split('.')[0] if node.module else ''
                    if module not in self.allowed_imports:
                        return False, f"Import from '{module}' is not allowed"
                
                # Block dangerous functions
                elif isinstance(node, ast.Name):
                    if node.id in ['eval', 'exec', '__import__', 'compile', 'open']:
                        return False, f"Use of '{node.id}' is not allowed"
                
                # Block attribute access to private methods
                elif isinstance(node, ast.Attribute):
                    if node.attr.startswith('_'):
                        return False, "Access to private attributes is not allowed"
            
            return True, "Code validation passed"
            
        except SyntaxError as e:
            return False, f"Syntax error: {str(e)}"
    
    def execute_code(self, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute code in isolated environment with data context
        """
        # Validate code first
        is_valid, message = self.validate_code(code)
        if not is_valid:
            return {
                'success': False,
                'error': message,
                'code': code
            }
        
        # Prepare execution environment
        exec_globals = {
            '__builtins__': __builtins__,
            'pd': None,
            'np': None,
            'plt': None,
            'sns': None,
            'px': None,
        }
        
        # Add data to context
        if 'dataframe' in context:
            exec_globals['df'] = context['dataframe']
        
        # Capture output
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        # Wrap code to capture results
        wrapped_code = f"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# User code
{code}

# Capture any created figures
import matplotlib.pyplot as plt
if plt.get_fignums():
    import io
    import base64
    _figures = []
    for fig_num in plt.get_fignums():
        fig = plt.figure(fig_num)
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        _figures.append(base64.b64encode(buf.read()).decode('utf-8'))
        plt.close(fig)
    result['figures'] = _figures
"""
        
        try:
            # Execute code with output capture
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec_locals = {}
                exec(wrapped_code, exec_globals, exec_locals)
            
            # Collect results
            result = {
                'success': True,
                'stdout': stdout_capture.getvalue(),
                'stderr': stderr_capture.getvalue(),
                'code': code,
                'variables': {}
            }
            
            # Capture important variables
            for key, value in exec_locals.items():
                if not key.startswith('_'):
                    if isinstance(value, pd.DataFrame):
                        result['variables'][key] = {
                            'type': 'dataframe',
                            'shape': value.shape,
                            'head': value.head().to_dict('records')
                        }
                    elif isinstance(value, (int, float, str, bool, list, dict)):
                        result['variables'][key] = value
                    elif isinstance(value, np.ndarray):
                        result['variables'][key] = {
                            'type': 'array',
                            'shape': value.shape,
                            'dtype': str(value.dtype)
                        }
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc(),
                'stdout': stdout_capture.getvalue(),
                'stderr': stderr_capture.getvalue(),
                'code': code
            }
```

## 3. LLM Data Analyst Agent

```python
# app/data_analysis/agents/analyst.py
from typing import Dict, Any, List, Optional
import json

class DataAnalystAgent:
    """
    LLM-powered data analyst with iterative code generation and execution
    """
    
    def __init__(self, llm_manager, data_handler, executor):
        self.llm = llm_manager
        self.data_handler = data_handler
        self.executor = executor
        self.max_iterations = 5
        self.conversation_history = []
    
    async def analyze(self, query: str, dataset_id: str) -> Dict[str, Any]:
        """
        Main analysis entry point - generates and executes code iteratively
        """
        # Get data context
        context = self.data_handler.get_llm_context(dataset_id)
        df = self.data_handler.get_data_for_execution(dataset_id)
        
        # Build prompt
        system_prompt = self._build_system_prompt(context)
        
        # Generate initial code
        response = await self._generate_code(query, system_prompt)
        
        # Extract code from response
        code = self._extract_code(response)
        
        # Execute with retry logic
        iteration = 0
        execution_context = {'dataframe': df}
        
        while iteration < self.max_iterations:
            result = self.executor.execute_code(code, execution_context)
            
            if result['success']:
                # Success! Format and return results
                return self._format_results(query, code, result)
            
            # Error occurred - try to fix
            iteration += 1
            if iteration < self.max_iterations:
                fix_prompt = self._build_error_fix_prompt(code, result['error'])
                response = await self._generate_code(fix_prompt, system_prompt)
                code = self._extract_code(response)
        
        # Max iterations reached
        return {
            'success': False,
            'message': 'Could not execute analysis after multiple attempts',
            'last_error': result.get('error'),
            'code': code
        }
    
    def _build_system_prompt(self, context: Dict[str, Any]) -> str:
        """Build system prompt with data context"""
        return f"""You are an expert data analyst with Python expertise.

## Available Data
Dataset shape: {context['shape']}
Columns: {context['columns']}
Data types: {json.dumps(context['dtypes'], indent=2)}
Numeric columns: {context['numeric_columns']}
Categorical columns: {context['categorical_columns']}

The dataframe is available as 'df'.

## Instructions
1. Generate Python code to answer the user's question
2. Use pandas, numpy, matplotlib, seaborn, plotly as needed
3. Always print key results and insights
4. Create visualizations when appropriate
5. Handle missing values and edge cases
6. Provide clear comments in the code

## Output Format
```python
# Your code here
```
"""
    
    async def _generate_code(self, query: str, system_prompt: str) -> str:
        """Generate code using LLM"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        response = await self.llm.generate_response(
            messages=messages,
            temperature=0.3,
            max_tokens=2000
        )
        
        return response
    
    def _extract_code(self, response: str) -> str:
        """Extract code from LLM response"""
        # Look for code blocks
        if "```python" in response:
            code = response.split("```python")[1].split("```")[0]
        elif "```" in response:
            code = response.split("```")[1].split("```")[0]
        else:
            # Assume entire response is code
            code = response
        
        return code.strip()
    
    def _build_error_fix_prompt(self, code: str, error: str) -> str:
        """Build prompt to fix code error"""
        return f"""The following code produced an error:

```python
{code}
```

Error: {error}

Please fix the code and provide a corrected version."""
    
    def _format_results(self, query: str, code: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format execution results for response"""
        response = {
            'success': True,
            'query': query,
            'code': code,
            'output': result.get('stdout', ''),
            'variables': result.get('variables', {}),
            'figures': result.get('figures', [])
        }
        
        # Add to conversation history
        self.conversation_history.append({
            'query': query,
            'code': code,
            'output': response['output']
        })
        
        return response
```

## 4. API Routes

```python
# app/web/routes/data_analysis_routes.py
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os

data_analysis_bp = Blueprint('data_analysis', __name__, url_prefix='/api/data-analysis')

@data_analysis_bp.route('/upload', methods=['POST'])
async def upload_data():
    """Handle data file upload"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Get session ID
    session_id = request.form.get('session_id', 'default')
    
    # Initialize data handler
    data_handler = current_app.services.data_handler
    
    # Save file
    filename = secure_filename(file.filename)
    file_path = os.path.join(f'instance/uploads/{session_id}', filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    file.save(file_path)
    
    try:
        # Load data
        dataset_id = data_handler.load_data(file_path)
        
        # Get context for response
        context = data_handler.get_llm_context(dataset_id, privacy_mode=False)
        
        return jsonify({
            'success': True,
            'dataset_id': dataset_id,
            'profile': {
                'shape': context['shape'],
                'columns': context['columns'],
                'dtypes': context['dtypes'],
                'null_counts': context['null_counts'],
                'head': context.get('head', [])
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_analysis_bp.route('/analyze', methods=['POST'])
async def analyze_data():
    """Perform data analysis using LLM"""
    data = request.json
    query = data.get('query')
    dataset_id = data.get('dataset_id')
    
    if not query or not dataset_id:
        return jsonify({'error': 'Query and dataset_id required'}), 400
    
    # Get services
    analyst = current_app.services.data_analyst
    
    try:
        # Perform analysis
        result = await analyst.analyze(query, dataset_id)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_analysis_bp.route('/datasets', methods=['GET'])
def list_datasets():
    """List available datasets for current session"""
    session_id = request.args.get('session_id', 'default')
    data_handler = current_app.services.data_handler
    
    datasets = []
    for dataset_id, metadata in data_handler.metadata.items():
        datasets.append({
            'id': dataset_id,
            'name': metadata['name'],
            'shape': metadata['shape'],
            'columns': len(metadata['columns'])
        })
    
    return jsonify({'datasets': datasets})
```

## 5. Frontend Implementation

```javascript
// app/static/js/modules/data_analysis/main.js
class DataAnalysisInterface {
    constructor() {
        this.currentDataset = null;
        this.analysisHistory = [];
        this.initializeUI();
    }
    
    initializeUI() {
        // File upload
        const uploadArea = document.getElementById('data-upload-area');
        uploadArea.addEventListener('drop', (e) => this.handleFileDrop(e));
        uploadArea.addEventListener('dragover', (e) => e.preventDefault());
        
        // Query input
        const queryInput = document.getElementById('analysis-query');
        const analyzeBtn = document.getElementById('analyze-btn');
        
        analyzeBtn.addEventListener('click', () => {
            const query = queryInput.value;
            if (query && this.currentDataset) {
                this.performAnalysis(query);
            }
        });
    }
    
    async handleFileDrop(event) {
        event.preventDefault();
        const file = event.dataTransfer.files[0];
        
        if (!file) return;
        
        // Check file type
        const validTypes = ['.csv', '.xlsx', '.xls', '.json'];
        const fileExt = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!validTypes.includes(fileExt)) {
            this.showError('Unsupported file type');
            return;
        }
        
        // Upload file
        const formData = new FormData();
        formData.append('file', file);
        formData.append('session_id', this.getSessionId());
        
        try {
            const response = await fetch('/api/data-analysis/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.currentDataset = result.dataset_id;
                this.displayDataProfile(result.profile);
                this.enableAnalysis();
            } else {
                this.showError(result.error);
            }
        } catch (error) {
            this.showError('Upload failed: ' + error.message);
        }
    }
    
    displayDataProfile(profile) {
        const profileDiv = document.getElementById('data-profile');
        
        profileDiv.innerHTML = `
            <div class="data-profile">
                <h3>Dataset Loaded</h3>
                <div class="profile-stats">
                    <div>Shape: ${profile.shape[0]} rows × ${profile.shape[1]} columns</div>
                    <div>Columns: ${profile.columns.slice(0, 5).join(', ')}${profile.columns.length > 5 ? '...' : ''}</div>
                </div>
                <div class="data-preview">
                    ${this.renderDataPreview(profile.head)}
                </div>
            </div>
        `;
    }
    
    renderDataPreview(data) {
        if (!data || data.length === 0) return '<p>No preview available</p>';
        
        const columns = Object.keys(data[0]);
        let html = '<table class="data-preview-table"><thead><tr>';
        
        columns.forEach(col => {
            html += `<th>${col}</th>`;
        });
        html += '</tr></thead><tbody>';
        
        data.forEach(row => {
            html += '<tr>';
            columns.forEach(col => {
                html += `<td>${row[col]}</td>`;
            });
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        return html;
    }
    
    async performAnalysis(query) {
        const resultsDiv = document.getElementById('analysis-results');
        
        // Show loading
        resultsDiv.innerHTML = '<div class="loading">Analyzing...</div>';
        
        try {
            const response = await fetch('/api/data-analysis/analyze', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    query: query,
                    dataset_id: this.currentDataset
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.displayResults(result);
                this.analysisHistory.push(result);
            } else {
                this.showError(result.error || 'Analysis failed');
            }
        } catch (error) {
            this.showError('Analysis error: ' + error.message);
        }
    }
    
    displayResults(result) {
        const resultsDiv = document.getElementById('analysis-results');
        
        let html = `
            <div class="analysis-result">
                <div class="query">${result.query}</div>
                <div class="code-block">
                    <pre><code class="language-python">${this.escapeHtml(result.code)}</code></pre>
                </div>
        `;
        
        if (result.output) {
            html += `
                <div class="output">
                    <h4>Output:</h4>
                    <pre>${this.escapeHtml(result.output)}</pre>
                </div>
            `;
        }
        
        if (result.figures && result.figures.length > 0) {
            html += '<div class="figures">';
            result.figures.forEach(fig => {
                html += `<img src="data:image/png;base64,${fig}" class="result-figure">`;
            });
            html += '</div>';
        }
        
        html += '</div>';
        resultsDiv.innerHTML = html;
        
        // Syntax highlighting if available
        if (typeof Prism !== 'undefined') {
            Prism.highlightAll();
        }
    }
    
    enableAnalysis() {
        document.getElementById('analysis-section').classList.remove('disabled');
        document.getElementById('analysis-query').focus();
    }
    
    getSessionId() {
        return sessionStorage.getItem('session_id') || 'default';
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        document.body.appendChild(errorDiv);
        
        setTimeout(() => errorDiv.remove(), 5000);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    new DataAnalysisInterface();
});
```

## 6. Service Container Integration

```python
# app/services/container.py (additions)

from app.data_analysis.core.data_handler import UniversalDataHandler
from app.data_analysis.sandbox.executor import SecureCodeExecutor
from app.data_analysis.agents.analyst import DataAnalystAgent

class ServiceContainer:
    def init_services(self, app):
        # ... existing services ...
        
        # Initialize data analysis services
        self.data_handler = UniversalDataHandler(session_id='default')
        self.code_executor = SecureCodeExecutor()
        self.data_analyst = DataAnalystAgent(
            llm_manager=self.llm_manager,
            data_handler=self.data_handler,
            executor=self.code_executor
        )
        
        app.logger.info("Data analysis services initialized")
```

This implementation provides a complete, working foundation for the LLM-powered data analysis pipeline with all the industry best practices incorporated.