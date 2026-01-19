# SQL + Python Hybrid Approach for ChatMRPT

## Core Insight
- **SQL for simple queries** (80% of requests) - reliable, simple syntax
- **Python for complex analysis** (20% of requests) - when SQL isn't enough
- **LLM is good at both**, but SQL is simpler and more constrained

## Architecture Options

### Option 1: Single Unified Tool with Mode Selection
```python
def execute_data_query(
    session_id: str,
    query_type: str = "auto",  # "sql", "python", "auto"
    query: str = None,         # SQL query or description
    code: str = None          # Python code if needed
):
    """
    Smart query execution - uses SQL when possible, Python when needed
    """
    if query_type == "auto":
        # LLM decides: "I'll use SQL for this simple query"
        # or "This needs Python for statistical analysis"
        pass
```

### Option 2: Separate Tools (Cleaner)
```python
def execute_sql_query(session_id: str, query: str) -> pd.DataFrame:
    """
    Execute SQL on the unified dataset
    Uses pandas.query() or DuckDB for speed
    """
    df = get_session_unified_dataset(session_id)
    # Convert SQL to pandas operations or use DuckDB
    return execute_sql_on_dataframe(df, query)

def execute_python_analysis(session_id: str, code: str) -> Any:
    """
    Execute Python for complex analysis
    More controlled than current approach
    """
    # Similar to current but with better templates
```

## SQL Capabilities in ChatMRPT

### What SQL Can Handle Well:
```sql
-- Top N queries (40% of requests)
SELECT * FROM data ORDER BY composite_score DESC LIMIT 10

-- Filtering (20% of requests)
SELECT * FROM data WHERE water_access < 0.3 AND population > 50000

-- Aggregations (15% of requests)
SELECT region, AVG(risk_score) as avg_risk, COUNT(*) as ward_count 
FROM data GROUP BY region

-- Specific ward lookup
SELECT * FROM data WHERE ward_name IN ('Dala', 'Fagge')

-- Simple stats
SELECT 
    AVG(population) as avg_pop,
    MIN(water_access) as min_water,
    MAX(composite_score) as max_risk
FROM data
```

### What Still Needs Python:
```python
# Correlation analysis
df[['rainfall', 'malaria_risk']].corr()

# PCA analysis
from sklearn.decomposition import PCA
pca = PCA(n_components=2)
transformed = pca.fit_transform(df[numeric_columns])

# Custom visualizations
plt.scatter(df['rainfall'], df['risk'], c=df['urban'])
plt.xlabel('Rainfall (mm)')

# Complex conditions
df['risk_category'] = pd.cut(df['risk'], bins=[0, 0.3, 0.7, 1.0], 
                             labels=['Low', 'Medium', 'High'])
```

## Implementation Approach

### Phase 1: Add SQL Support
```python
class SQLQueryExecutor:
    def __init__(self, session_id: str):
        self.df = get_session_unified_dataset(session_id)
        
    def execute(self, sql: str) -> Dict[str, Any]:
        try:
            # Option A: Use pandasql
            from pandasql import sqldf
            result = sqldf(sql, {'data': self.df})
            
            # Option B: Use DuckDB (faster)
            import duckdb
            result = duckdb.sql(sql).df()
            
            # Option C: Convert SQL to pandas
            result = self._sql_to_pandas(sql)
            
            return {
                'success': True,
                'data': result.to_dict('records'),
                'shape': result.shape,
                'query': sql
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
```

### Phase 2: Teach LLM When to Use What

**System Prompt Addition:**
```
For data queries, you have two tools:

1. execute_sql_query - Use for:
   - Selecting specific wards (SELECT * FROM data WHERE...)
   - Top/bottom N queries (ORDER BY ... LIMIT)
   - Simple filtering (WHERE conditions)
   - Basic aggregations (GROUP BY, AVG, COUNT)
   - Joins if multiple tables

2. execute_python_analysis - Use for:
   - Statistical analysis (correlations, regression)
   - Machine learning (PCA, clustering)
   - Custom visualizations beyond basic plots
   - Complex transformations
   - Anything requiring numpy, scipy, sklearn

Choose SQL when possible - it's simpler and more reliable.
```

### Phase 3: Templates for Common Patterns

```python
SQL_TEMPLATES = {
    'top_wards': "SELECT * FROM data ORDER BY {score_column} DESC LIMIT {n}",
    'filter_wards': "SELECT * FROM data WHERE {condition}",
    'compare_wards': "SELECT * FROM data WHERE ward_name IN ({ward_list})",
    'stats_by_group': "SELECT {group_col}, {aggregations} FROM data GROUP BY {group_col}"
}

PYTHON_TEMPLATES = {
    'correlation': """
corr_matrix = df[{columns}].corr()
print(corr_matrix)
""",
    'distribution_plot': """
plt.figure(figsize=(10, 6))
plt.hist(df['{column}'], bins=30)
plt.title('{column} Distribution')
plt.show()
"""
}
```

## Benefits of Hybrid Approach

1. **Best of Both Worlds**
   - SQL reliability for simple queries
   - Python flexibility for complex analysis

2. **Gradual Migration**
   - Start by adding SQL support
   - Keep Python fallback
   - Migrate common patterns to SQL

3. **Clear Mental Model**
   - "Can I express this in SQL?" → Use SQL
   - "Do I need statistics/ML/custom viz?" → Use Python

4. **Performance**
   - SQL/DuckDB is often faster for filtering/aggregation
   - Python still available for numpy/pandas operations

## Example User Flows

```
User: "Show me the top 10 wards"
LLM: execute_sql_query("SELECT * FROM data ORDER BY composite_score DESC LIMIT 10")

User: "Which wards have water access below 30%?"
LLM: execute_sql_query("SELECT * FROM data WHERE water_access < 0.3")

User: "What's the correlation between rainfall and malaria risk?"
LLM: execute_python_analysis("
    corr = df[['rainfall', 'composite_score']].corr()
    print(f'Correlation: {corr.iloc[0,1]:.3f}')
")

User: "Create a scatter plot of population vs risk, colored by urban/rural"
LLM: execute_python_analysis("
    plt.scatter(df['population'], df['composite_score'], c=df['urban'])
    plt.xlabel('Population')
    plt.ylabel('Risk Score')
    plt.show()
")
```

## Questions to Consider

1. **Should we use DuckDB or pandas.query()?**
   - DuckDB: Faster, full SQL support
   - pandas.query(): Simpler, no extra dependency

2. **How to handle SQL injection?**
   - Parameterized queries
   - Whitelist of allowed operations
   - Read-only access

3. **Should SQL see the original data or unified dataset?**
   - Unified: Has analysis results
   - Original: Simpler, clearer

4. **Error handling strategy?**
   - Fallback to Python if SQL fails?
   - Clear error messages for LLM to correct?