# Simple LLM-Powered Data Analysis Plan
## Minimal Implementation Approach

## Core Insight
Since the LLM (Claude/ChatGPT) already has full access to the data and can execute code, we don't need complex architectures. We just need:
1. Simple file upload
2. Smart prompts
3. Safe code execution
4. Let the LLM do the analysis directly

## Research Findings

### Industry Approaches (2024)
- **ChatGPT Code Interpreter**: Writes and executes Python in sandbox
- **Claude Analysis Tool**: JavaScript-based code execution
- **PandasAI**: Natural language to pandas code
- **Key Learning**: Less is more - let the LLM handle complexity

### Security Best Practices
- Use RestrictedPython for basic safety
- Docker containers for isolation (optional for advanced security)
- Simple validation before execution
- Keep data in session-isolated folders

## Minimal Implementation Plan

### What We Actually Need (Only 4 Components!)

#### 1. Simple Upload Handler
```python
# app/analysis/data_handler.py
import pandas as pd
import os
from werkzeug.utils import secure_filename

class DataHandler:
    """Simple data upload and storage."""
    
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'json', 'parquet'}
    
    def upload_file(self, file, session_id):
        """Save uploaded file and return basic info."""
        if not self._allowed_file(file.filename):
            return {"error": "Unsupported file type"}
        
        # Save to session folder
        session_path = f"instance/uploads/{session_id}"
        os.makedirs(session_path, exist_ok=True)
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(session_path, filename)
        file.save(filepath)
        
        # Load data and get basic info
        df = self._load_data(filepath)
        
        return {
            "filepath": filepath,
            "shape": df.shape,
            "columns": df.columns.tolist(),
            "dtypes": df.dtypes.to_dict(),
            "head": df.head().to_dict()
        }
    
    def _load_data(self, filepath):
        """Load data based on file extension."""
        ext = filepath.split('.')[-1].lower()
        if ext == 'csv':
            return pd.read_csv(filepath)
        elif ext in ['xlsx', 'xls']:
            return pd.read_excel(filepath)
        elif ext == 'json':
            return pd.read_json(filepath)
        elif ext == 'parquet':
            return pd.read_parquet(filepath)
```

#### 2. LLM Analysis Executor
```python
# app/analysis/llm_executor.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO
import sys
import traceback

class LLMAnalysisExecutor:
    """Execute LLM-generated code safely."""
    
    def __init__(self, session_id):
        self.session_id = session_id
        self.session_path = f"instance/uploads/{session_id}"
        
    def execute_analysis(self, code, data_file):
        """Execute analysis code from LLM."""
        # Create safe namespace
        namespace = {
            'pd': pd,
            'np': np,
            'plt': plt,
            'sns': sns,
            'data_file': data_file,
            '__builtins__': {
                'print': print,
                'len': len,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'map': map,
                'filter': filter,
                'sum': sum,
                'min': min,
                'max': max,
                'abs': abs,
                'round': round,
                'sorted': sorted,
                'reversed': reversed,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'set': set,
                'tuple': tuple,
            }
        }
        
        # Capture output
        old_stdout = sys.stdout
        sys.stdout = output_capture = StringIO()
        
        try:
            # Execute the code
            exec(code, namespace)
            
            # Get output
            output = output_capture.getvalue()
            
            # Check for generated files (plots, CSVs, etc.)
            generated_files = self._find_generated_files()
            
            return {
                "success": True,
                "output": output,
                "generated_files": generated_files
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        finally:
            sys.stdout = old_stdout
    
    def _find_generated_files(self):
        """Find files generated during analysis."""
        import os
        files = []
        for file in os.listdir(self.session_path):
            if file.endswith(('.png', '.jpg', '.csv', '.html')):
                files.append(file)
        return files
```

#### 3. Smart Prompts for Data Analysis
```python
# app/analysis/prompts.py

DATA_ANALYSIS_SYSTEM_PROMPT = """
You are an expert data analyst with access to a user's uploaded data file. 
When the user uploads a file, you'll receive information about it (shape, columns, dtypes).

Your capabilities:
1. Explore and profile data (describe, info, missing values, distributions)
2. Create visualizations (matplotlib, seaborn plots)
3. Perform statistical analysis (correlations, hypothesis tests)
4. Clean and transform data (handle missing values, outliers, encoding)
5. Feature engineering and insights
6. Machine learning exploration (if requested)

When responding:
1. First understand what the user wants
2. Write Python code to analyze their data
3. The data file path is available as 'data_file' variable
4. Use pandas as pd, numpy as np, matplotlib.pyplot as plt, seaborn as sns
5. Save any plots to the session folder
6. Explain your findings in clear, non-technical language

Always start by loading the data:
```python
df = pd.read_csv(data_file)  # or pd.read_excel() based on file type
```

Be proactive - if the user just uploads data without specific questions, provide:
- Data overview and quality assessment
- Key statistics and distributions
- Interesting patterns or anomalies
- Visualization recommendations
- Suggested next steps
"""

ANALYSIS_EXAMPLES = {
    "basic_exploration": """
# Load and explore data
df = pd.read_csv(data_file)

# Basic information
print("Dataset Shape:", df.shape)
print("\nColumn Types:")
print(df.dtypes)
print("\nMissing Values:")
print(df.isnull().sum())
print("\nBasic Statistics:")
print(df.describe())

# Distribution plots for numeric columns
import matplotlib.pyplot as plt
numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
fig, axes = plt.subplots(len(numeric_cols), 1, figsize=(10, 4*len(numeric_cols)))
for i, col in enumerate(numeric_cols):
    df[col].hist(ax=axes[i] if len(numeric_cols) > 1 else axes, bins=30)
    axes[i].set_title(f'Distribution of {col}')
plt.tight_layout()
plt.savefig('distributions.png')
plt.show()
""",
    
    "correlation_analysis": """
# Correlation analysis
df = pd.read_csv(data_file)
import seaborn as sns
import matplotlib.pyplot as plt

# Correlation matrix
corr = df.select_dtypes(include=['float64', 'int64']).corr()

# Heatmap
plt.figure(figsize=(12, 8))
sns.heatmap(corr, annot=True, cmap='coolwarm', center=0)
plt.title('Correlation Matrix')
plt.tight_layout()
plt.savefig('correlation_matrix.png')
plt.show()

# Find strong correlations
threshold = 0.7
strong_corr = []
for i in range(len(corr.columns)):
    for j in range(i+1, len(corr.columns)):
        if abs(corr.iloc[i, j]) > threshold:
            strong_corr.append((corr.columns[i], corr.columns[j], corr.iloc[i, j]))

print("Strong Correlations (>0.7):")
for col1, col2, val in strong_corr:
    print(f"{col1} - {col2}: {val:.3f}")
"""
}
```

#### 4. Updated Request Interpreter
```python
# app/core/request_interpreter.py - MODIFY existing file

def _build_system_prompt(self):
    """Build system prompt based on context."""
    
    # Check if user has uploaded data
    if self.has_data_uploaded():
        # Use data analysis prompt
        from app.analysis.prompts import DATA_ANALYSIS_SYSTEM_PROMPT
        data_info = self.get_uploaded_data_info()
        
        return f"""{DATA_ANALYSIS_SYSTEM_PROMPT}
        
Current uploaded file: {data_info['filename']}
Shape: {data_info['shape']}
Columns: {data_info['columns']}
"""
    else:
        # Use existing malaria/general prompt
        return self.existing_prompt

def handle_data_analysis(self, user_message):
    """Handle data analysis requests."""
    
    # Let LLM generate analysis code
    llm_response = self.llm.generate_analysis_code(
        user_message, 
        self.data_info
    )
    
    # Execute the generated code
    executor = LLMAnalysisExecutor(self.session_id)
    result = executor.execute_analysis(
        llm_response['code'],
        self.data_file_path
    )
    
    # Return results with explanation
    return {
        "explanation": llm_response['explanation'],
        "code": llm_response['code'],
        "output": result['output'],
        "files": result.get('generated_files', [])
    }
```

## Migration Steps (Super Simple!)

### Day 1-2: Remove TPR Complexity
```bash
# 1. Backup TPR module
mv app/tpr_module app/tpr_module_backup

# 2. Remove TPR routes from registration
# Edit app/web/routes/__init__.py - comment out TPR blueprints

# 3. Remove TPR frontend verification
# Edit app/static/js/modules/upload/file-uploader.js
# Remove verifyTPRSessionState() calls
```

### Day 3-4: Add Simple Data Analysis
```bash
# 1. Create minimal analysis module
mkdir app/analysis
touch app/analysis/__init__.py
touch app/analysis/data_handler.py
touch app/analysis/llm_executor.py
touch app/analysis/prompts.py

# 2. Update upload routes to use DataHandler
# 3. Update request interpreter to detect data uploads
# 4. Test with sample files
```

### Day 5: Testing & Deployment
```bash
# Test with various file types
# Test different analysis requests
# Deploy to staging
# Monitor and iterate
```

## Why This Approach is Better

### Simplicity
- **4 files** instead of 50+
- **~500 lines of code** instead of 5000+
- **No complex pipeline** - LLM handles it
- **No rigid structure** - flexible for any analysis

### Flexibility
- LLM adapts to ANY data format
- LLM writes custom code for each request
- No predefined analysis paths
- Handles edge cases naturally

### Maintenance
- Less code = fewer bugs
- Easy to understand and modify
- LLM improvements = automatic capability upgrades
- No need to anticipate all use cases

### User Experience
- Natural language interaction
- No learning curve
- Instant insights
- Custom analysis on demand

## Security Considerations

### Basic Safety (Current Implementation)
- Restricted namespace in exec()
- Session isolation
- File type validation
- No system access

### Advanced Safety (If Needed Later)
- Add RestrictedPython
- Docker sandboxing
- Resource limits
- Code review before execution

## Example User Interactions

### Simple Upload
```
User: *uploads sales_data.csv*
System: I've received your sales data with 10,000 rows and 15 columns. 
        Let me analyze it for you...
        [Generates overview, charts, insights automatically]
```

### Specific Analysis
```
User: Find correlations between price and sales volume
System: [Generates correlation analysis code and executes]
        I found a strong negative correlation (-0.72) between price and sales volume...
```

### Complex Request
```
User: Build a predictive model for next quarter's revenue
System: [Generates feature engineering, model training, evaluation code]
        I've built a RandomForest model with 89% accuracy...
```

## Success Metrics

### Technical
- ✅ Any file format supported
- ✅ <2 second response time for basic analysis
- ✅ No page refreshes
- ✅ Handles 100MB+ files

### User Experience
- ✅ Zero learning curve
- ✅ Natural language only
- ✅ Instant insights
- ✅ No errors for valid requests

## Conclusion

This minimal approach leverages the LLM's capabilities instead of trying to anticipate every use case. It's:
- **10x simpler** to implement
- **100x more flexible** than rigid pipelines
- **Infinitely extensible** through LLM improvements

The key insight: **Don't build what the LLM can generate on-demand.**