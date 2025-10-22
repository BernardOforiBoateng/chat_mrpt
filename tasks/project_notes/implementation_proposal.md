# Column Sanitization Implementation Proposal

## Executive Summary
Column sanitization will solve the agent's code generation issues by converting complex column names to Python-friendly identifiers while preserving original names for display.

## Current Problems
- Agent fails on queries requiring multi-column aggregations
- Special characters (`<`, `≥`, `&`) break pandas operations  
- GPT-4 struggles with medical column names unlike its training data
- Hardcoded encoding fixes aren't scalable

## Proposed Solution

### Phase 1: Core Implementation (2 hours)

#### 1. Update EncodingHandler
```python
# app/data_analysis_v3/core/encoding_handler.py

class EncodingHandler:
    @staticmethod
    def sanitize_columns(df):
        """
        Sanitize column names for agent compatibility.
        Returns: (df_clean, mapping)
        """
        mapping = {}
        new_cols = []
        
        for i, col in enumerate(df.columns):
            # Create safe name
            safe = EncodingHandler._make_safe_name(col, i)
            new_cols.append(safe)
            mapping[safe] = col
        
        df_clean = df.copy()
        df_clean.columns = new_cols
        df_clean.attrs['column_mapping'] = mapping
        df_clean.attrs['original_columns'] = df.columns.tolist()
        
        return df_clean, mapping
```

#### 2. Update Agent to Use Sanitized Columns
```python
# app/data_analysis_v3/core/agent.py

def _check_and_add_tpr_tool(self):
    # ... existing code ...
    
    # Sanitize columns before storing
    df_clean, mapping = EncodingHandler.sanitize_columns(df)
    
    # Store sanitized version
    self.uploaded_data = df_clean
    self.column_mapping = mapping
    
    # Pass to tools with mapping context
```

#### 3. Update System Prompt
```python
# app/data_analysis_v3/prompts/system_prompt.py

COLUMN_CONTEXT = """
The DataFrame columns have been sanitized for easier use:
- Use simple names like: 'rdt_tested_under_5', 'facility_name'
- NOT complex names with special characters
- Column mapping available in df.attrs['column_mapping']

Example working code:
test_cols = [c for c in df.columns if 'tested' in c]
df.groupby('facility')[test_cols].sum()
"""
```

### Phase 2: Smart Features (1 hour)

#### 1. Semantic Detection
```python
def detect_tpr_semantics(df):
    """Auto-detect column purposes"""
    semantics = {
        'facility_col': None,
        'test_cols': [],
        'positive_cols': []
    }
    
    for col in df.columns:
        if 'facility' in col.lower():
            semantics['facility_col'] = col
        elif 'test' in col:
            semantics['test_cols'].append(col)
        elif 'positive' in col:
            semantics['positive_cols'].append(col)
    
    return semantics
```

#### 2. Display Original Names
```python
def format_results_with_original_names(results, mapping):
    """Convert back to original names for display"""
    if isinstance(results, pd.DataFrame):
        # Restore original column names
        reverse_map = {v: k for k, v in mapping.items()}
        results.columns = [reverse_map.get(c, c) for c in results.columns]
    return results
```

### Phase 3: Testing (30 mins)

1. Test with various encodings:
   - Arabic: "المرضى المختبرين <5"
   - Chinese: "检测人数 <5岁"
   - French: "Personnes testées <5ans"

2. Test complex queries:
   - "Top 10 facilities by total testing"
   - "Calculate TPR by ward"
   - "Create visualization of trends"

## Benefits

### Immediate
- ✅ Agent queries work reliably
- ✅ No more "difficulty accessing columns" errors
- ✅ Complex aggregations succeed

### Long-term
- ✅ Works with ANY language/encoding
- ✅ No hardcoded fixes needed
- ✅ Aligns with industry standards (Spark, BigQuery)
- ✅ Better performance (shorter column names)

## Risk Mitigation
- Original names preserved in metadata
- Can revert if needed
- Backwards compatible with existing code

## Industry Validation
This approach is used by:
- **Apache Spark**: Auto-sanitizes column names
- **Google BigQuery**: Replaces special chars with underscore
- **Databricks**: Column mapping feature
- **dbt**: Aliasing for complex names

## Implementation Timeline
- Hour 1: Core sanitization in EncodingHandler
- Hour 2: Agent integration and prompts
- Hour 3: Testing and deployment

## Success Metrics
- Agent successfully completes "top 10 facilities" query
- All test queries pass without errors
- Works with international datasets

## Alternative Approaches Considered

### 1. Fix in LLM Prompt Only
❌ Doesn't solve underlying pandas issues

### 2. Custom Pandas Wrapper
❌ Too complex, breaks standard pandas operations

### 3. Force Users to Clean Data
❌ Poor user experience

### 4. Column Sanitization (CHOSEN)
✅ Simple, proven, industry-standard

## Conclusion
Column sanitization is the industry-standard solution that will make the agent work reliably with any data. It's simple to implement and solves multiple problems at once.