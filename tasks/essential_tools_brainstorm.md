# Essential Tools Brainstorm - ChatMRPT

## Most Common User Requests (from real usage)

### 1. Ward Queries (MOST COMMON)
- "Show me the top 10 highest risk wards"
- "Which wards need urgent intervention?"
- "Tell me about Dala ward"
- "Compare Fagge and Nassarawa wards"
- "Which wards have poor water access?"
- "Show wards with population > 50000"

### 2. Variable Exploration
- "Map housing quality across all wards"
- "Show rainfall distribution"
- "What's the average population?"
- "Which variables correlate with risk?"
- "Show me areas with low clinic access"

### 3. Analysis Results
- "Which method is better - PCA or Composite?"
- "Why is Dala high risk?"
- "What factors drive risk in urban areas?"
- "Show me the risk rankings"

### 4. Data Understanding
- "What data do you have?"
- "Are there missing values?"
- "How many wards in total?"
- "What variables are available?"

## Proposed Essential Tools

### Tool 1: `query_wards`
```python
def query_wards(
    session_id: str,
    # Flexible filtering
    top_n: Optional[int] = None,
    bottom_n: Optional[int] = None,
    ward_names: Optional[List[str]] = None,
    
    # Ranking criteria
    rank_by: str = "composite_score",  # or "pca_score", "population", any variable
    
    # Filtering criteria
    filters: Optional[Dict[str, Any]] = None,  # {"population": {">": 50000}, "water_access": {"<": 0.5}}
    
    # What to return
    include_details: bool = False,
    include_risk_factors: bool = False
) -> Dict[str, Any]:
    """
    Universal ward query tool - handles 80% of ward-related questions
    """
```

**Examples:**
- `query_wards(top_n=10)` → "Show top 10 wards"
- `query_wards(ward_names=["Dala", "Fagge"], include_details=True)` → "Compare these wards"
- `query_wards(filters={"water_access": {"<": 0.3}})` → "Wards with poor water"

### Tool 2: `analyze_variable`
```python
def analyze_variable(
    session_id: str,
    variable_name: str,
    
    # Analysis type
    analysis_type: str = "summary",  # "summary", "distribution", "map", "correlation"
    
    # Optional parameters
    create_map: bool = False,
    compare_with: Optional[str] = None,  # Another variable for correlation
    group_by: Optional[str] = None,  # Group by urban/rural, etc.
    
    # Spatial focus
    ward_filter: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Universal variable analysis tool
    """
```

**Examples:**
- `analyze_variable("housing_quality", create_map=True)` → "Map housing quality"
- `analyze_variable("population", analysis_type="distribution")` → "Show population distribution"
- `analyze_variable("rainfall", compare_with="malaria_risk")` → "Correlate rainfall with risk"

### Tool 3: `compare_analysis_methods`
```python
def compare_analysis_methods(
    session_id: str,
    
    # Comparison type
    comparison_type: str = "overall",  # "overall", "by_ward", "correlation", "top_differences"
    
    # Focus area
    top_n: Optional[int] = 10,
    ward_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Compare PCA vs Composite scoring methods
    """
```

### Tool 4: `get_data_overview`
```python
def get_data_overview(
    session_id: str,
    
    # What to include
    include_schema: bool = True,
    include_quality: bool = True,
    include_summary_stats: bool = False,
    check_variable: Optional[str] = None  # Deep dive on specific variable
) -> Dict[str, Any]:
    """
    Understand the data structure and quality
    """
```

### Tool 5: `explain_risk_factors`
```python
def explain_risk_factors(
    session_id: str,
    
    # What to explain
    ward_name: Optional[str] = None,  # Specific ward
    ward_group: Optional[str] = None,  # "top10", "bottom10", "urban", "rural"
    
    # Analysis depth
    num_factors: int = 5,  # Top N contributing factors
    include_recommendations: bool = False
) -> Dict[str, Any]:
    """
    Explain what drives malaria risk
    """
```

### Tool 6: `flexible_data_query` (Escape hatch)
```python
def flexible_data_query(
    session_id: str,
    query_type: str,  # "sql", "pandas", "custom"
    query: str,       # SQL query or pandas operations description
    
    # Safety
    allowed_operations: List[str] = ["select", "filter", "aggregate", "join"],
    max_rows: int = 1000
) -> Dict[str, Any]:
    """
    For complex queries that don't fit other tools
    BUT with structured parameters for safety
    """
```

## Why This Works

1. **Covers 90% of requests** with just 6 tools
2. **Flexible parameters** handle variations without new tools
3. **Clear intent** - each tool has obvious purpose
4. **Structured but powerful** - no string code generation for common tasks
5. **Escape hatch** - flexible_data_query for edge cases

## Implementation Priority

1. **First**: `query_wards` - Most common request
2. **Second**: `analyze_variable` - Variable exploration
3. **Third**: `get_data_overview` - Data understanding
4. **Fourth**: `compare_analysis_methods` - Post-analysis
5. **Fifth**: `explain_risk_factors` - Insights
6. **Last**: `flexible_data_query` - Edge cases

## Next Steps

1. Implement `query_wards` first
2. Test with real user queries
3. Refine parameters based on usage
4. Add other tools incrementally
5. Keep `execute_data_query` as fallback during transition