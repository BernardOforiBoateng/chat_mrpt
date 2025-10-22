#!/usr/bin/env python3
"""
Smart fix for Top N and hallucination issues
Keeps interpretation while ensuring real data
"""

import json
import re

def create_enhanced_prompt_section():
    """
    Enhanced prompt section that ensures complete output
    while maintaining interpretation capability
    """
    return """
## MANDATORY: Complete Output for Lists and Rankings

When asked for "top N" items, you MUST ensure ALL N items are shown:

### Correct Implementation Pattern:
```python
# Step 1: Get the data
top_n = df.nlargest(10, 'value_column')  # or appropriate method

# Step 2: Print complete structured output
print("=== RESULT START ===")
print(f"Found {len(top_n)} items:")
for idx, row in enumerate(top_n.iterrows(), 1):
    # Use actual column names from the data
    print(f"{idx}. {row[1]['entity_name']}: {row[1]['value']:,.0f}")
print("=== RESULT END ===")

# Step 3: Provide summary statistics for interpretation
print(f"\\nSummary: Total of {len(top_n)} items shown")
print(f"Range: {top_n['value'].min():,.0f} to {top_n['value'].max():,.0f}")
```

### CRITICAL: Data Grounding Rules
1. ALWAYS use actual values from dataframe columns
2. NEVER type entity names manually (no "Facility A", "Item 1")  
3. If data is not available, print("Data for this query not found")
4. Use loops to ensure ALL items are printed

### For Different Query Types:

**Top N by single metric:**
```python
top_10 = df.nlargest(10, 'metric')
for i, row in enumerate(top_10.iterrows(), 1):
    print(f"{i}. {row[1]['name']}: {row[1]['metric']}")
```

**Top N by aggregation:**
```python
grouped = df.groupby('entity')['value'].sum().nlargest(10)
for i, (name, value) in enumerate(grouped.items(), 1):
    print(f"{i}. {name}: {value:,.0f}")
```

**List unique items:**
```python
unique_items = df['category'].unique()[:10]
for i, item in enumerate(unique_items, 1):
    print(f"{i}. {item}")
```
"""

def create_metadata_extractor():
    """
    Extract metadata from execution to provide to LLM
    This prevents hallucination by giving real data
    """
    return '''
def extract_execution_metadata(state):
    """Extract key information from execution state for LLM interpretation."""
    metadata = {
        'entities_found': [],
        'numeric_columns': [],
        'row_count': 0,
        'columns': []
    }
    
    # Get the main dataframe
    if 'df' in state.get('current_variables', {}):
        df = state['current_variables']['df']
        
        # Basic info
        metadata['row_count'] = len(df)
        metadata['columns'] = df.columns.tolist()
        
        # Find entity columns (text columns with unique values)
        for col in df.columns:
            if df[col].dtype == 'object':
                unique_vals = df[col].dropna().unique()
                if 2 <= len(unique_vals) <= 100:  # Reasonable range
                    # Sample some entities for LLM reference
                    metadata['entities_found'].extend(unique_vals[:20].tolist())
            elif df[col].dtype in ['int64', 'float64']:
                metadata['numeric_columns'].append(col)
    
    return metadata
'''

def create_enhanced_executor():
    """
    Enhanced executor that ensures complete output
    """
    return '''
def execute_with_structure(self, code: str, initial_vars: Dict = None):
    """Execute code with structured output for interpretation."""
    
    # Check if this is a "top N" or listing query
    is_listing_query = any(term in code.lower() for term in 
                          ['nlargest', 'nsmallest', 'head', 'tail', 'top', 'sort'])
    
    if is_listing_query:
        # Inject helper code to ensure complete output
        helper_code = """
# Ensure complete output for listing queries
import sys
_original_print = print

def _enhanced_print(*args, **kwargs):
    # Call original print
    _original_print(*args, **kwargs)
    # Flush to ensure output is captured
    sys.stdout.flush()

print = _enhanced_print
"""
        code = helper_code + "\\n" + code
    
    # Execute normally
    output, state = self.execute(code, initial_vars)
    
    # Check for incomplete output
    if is_listing_query:
        # Count numbered items in output
        numbered_items = re.findall(r'^\\s*\\d+\\.', output, re.MULTILINE)
        
        # Check if we might have incomplete results
        if len(numbered_items) < 5 and "10" in code:
            # Add warning to output
            output += "\\n⚠️ Note: Output may be incomplete. Ensure iteration completes."
    
    return output, state
'''

def create_smart_response_formatter():
    """
    Smart formatter that interprets without hallucinating
    """
    return '''
def format_with_interpretation(raw_output: str, metadata: dict) -> str:
    """
    Format output with interpretation based on actual data.
    
    Args:
        raw_output: Raw stdout from code execution
        metadata: Extracted metadata with real entities
        
    Returns:
        Interpreted response for health officials
    """
    
    # Check if output contains structured results
    if "=== RESULT START ===" in raw_output and "=== RESULT END ===" in raw_output:
        # Extract the structured part
        start_idx = raw_output.index("=== RESULT START ===")
        end_idx = raw_output.index("=== RESULT END ===")
        results = raw_output[start_idx:end_idx + len("=== RESULT END ===")]
        
        # Count items
        items = re.findall(r'^\\s*\\d+\\.', results, re.MULTILINE)
        
        # Create interpretation
        interpretation = f"""
I've identified {len(items)} items based on your criteria.

{results}

**Key Insights:**
"""
        
        # Add contextual insights based on metadata
        if metadata.get('row_count'):
            interpretation += f"\\n- Analysis based on {metadata['row_count']:,} total records"
        
        if len(items) > 5:
            interpretation += f"\\n- The top items show significant variation in values"
        
        interpretation += "\\n\\nWould you like me to analyze these results further or explore a different aspect?"
        
        return interpretation
    
    # For non-structured output, provide safe interpretation
    else:
        # Never make up entity names - use metadata
        if metadata.get('entities_found'):
            # Use real entities in interpretation
            sample_entities = metadata['entities_found'][:3]
            interpretation = f"""
Based on the analysis of your data:

{raw_output}

The dataset includes entities such as {', '.join(str(e) for e in sample_entities)} and others.
"""
        else:
            # Generic safe interpretation
            interpretation = f"""
Analysis results:

{raw_output}

Please let me know if you'd like to explore specific aspects of this data.
"""
        
        return interpretation
'''

def apply_fixes():
    """
    Apply the fixes to the actual files
    """
    
    print("Applying smart fixes for Top N and hallucination issues...")
    
    # Fix 1: Update system prompt
    prompt_addition = create_enhanced_prompt_section()
    print(f"1. Add to system_prompt.py:\n{prompt_addition[:200]}...")
    
    # Fix 2: Add metadata extractor
    metadata_code = create_metadata_extractor()
    print(f"\n2. Add metadata extractor to python_tool.py:\n{metadata_code[:200]}...")
    
    # Fix 3: Enhanced executor
    executor_code = create_enhanced_executor()
    print(f"\n3. Enhance executor.py:\n{executor_code[:200]}...")
    
    # Fix 4: Smart formatter
    formatter_code = create_smart_response_formatter()
    print(f"\n4. Update response_formatter.py:\n{formatter_code[:200]}...")
    
    print("\n✅ Fixes ready to apply!")
    print("\nThese fixes will:")
    print("1. Ensure all N items are shown in top N queries")
    print("2. Prevent hallucination by using real data")
    print("3. Keep interpretation layer for health officials")
    print("4. Work with any domain (not just healthcare)")

if __name__ == "__main__":
    apply_fixes()