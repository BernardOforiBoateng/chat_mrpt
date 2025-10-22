# NO Hardcoded Column Names - Pure Data Detection

## The Principle
We should NEVER look for specific column names like "orgunitlevel2" or "State". Instead, detect columns by their data characteristics.

## What NOT to Do
```python
# ❌ WRONG - Hardcoding column names
if 'orgunitlevel2' in df.columns:
    state_col = 'orgunitlevel2'
elif 'State' in df.columns:
    state_col = 'State'
```

## What TO Do
```python
# ✅ CORRECT - Detect by data characteristics
def detect_location_hierarchy(df):
    # Find all text columns
    text_columns = df.select_dtypes(include=['object']).columns
    
    # Calculate cardinality for each
    cardinalities = {}
    for col in text_columns:
        cardinalities[col] = df[col].nunique()
    
    # Sort by cardinality (ascending)
    sorted_cols = sorted(cardinalities.items(), key=lambda x: x[1])
    
    # Assign hierarchy based on cardinality alone
    # State has fewest unique values, Facility has most
    if len(sorted_cols) >= 4:
        return {
            'state': sorted_cols[0][0],      # Lowest cardinality
            'lga': sorted_cols[1][0],        # Second lowest
            'ward': sorted_cols[2][0],       # Second highest
            'facility': sorted_cols[3][0]    # Highest cardinality
        }
```

## Implementation Approach

1. **Detection Phase**: Find columns by data patterns
   - Test columns: Find by looking for numeric pairs where one <= another
   - Time column: Find by date pattern in values
   - Location columns: Order by cardinality

2. **Mapping Phase**: Create internal mapping
   ```python
   column_mapping = {
       detected_columns[0]: 'state',     # Whatever column has ~37 unique values
       detected_columns[1]: 'lga',       # Whatever column has ~774 unique values
       detected_columns[2]: 'ward',      # Whatever column has ~9,500 unique values
       detected_columns[3]: 'facility'   # Whatever column has ~30,000 unique values
   }
   ```

3. **Display Phase**: Show friendly names to users
   ```python
   # User sees: "Analyzing State: Adamawa"
   # Even if the actual column was named "X" or "Column1" or "orgunitlevel2"
   ```

## The Key Point
The column could be named ANYTHING:
- "State" → Detect as state by cardinality
- "orgunitlevel2" → Detect as state by cardinality
- "Column1" → Detect as state by cardinality
- "X" → Detect as state by cardinality
- "地域1" → Detect as state by cardinality

We don't care about the name, only the data!