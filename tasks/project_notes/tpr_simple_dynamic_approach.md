# TPR Dynamic Detection - Simple Approach

## The Insight
After analyzing both TPR formats, we realized:
1. The 12 test columns ALWAYS have the same names
2. Only the location column names vary
3. Everything else stays consistent

## Simple Solution

### Step 1: Find Test Columns (Easy!)
```python
# These column names are ALWAYS the same across all TPR files
STANDARD_TEST_COLUMNS = [
    'RDT tested <5', 'RDT positive <5',
    'RDT tested ≥5', 'RDT positive ≥5',
    'RDT tested Pregnant Women', 'RDT positive Pregnant Women',
    'Microscopy tested <5', 'Microscopy positive <5',
    'Microscopy tested ≥5', 'Microscopy positive ≥5',
    'Microscopy tested Pregnant Women', 'Microscopy positive Pregnant Women'
]

# Just match by name!
test_columns = [col for col in df.columns if col in STANDARD_TEST_COLUMNS]
```

### Step 2: Find Time Column
```python
# Look for YYYY-MM pattern
def has_date_pattern(series):
    # Check if values match date pattern
    sample = series.dropna().head(10)
    return all(re.match(r'\d{4}-\d{2}', str(val)) for val in sample)

time_columns = [col for col in df.columns if has_date_pattern(df[col])]
```

### Step 3: Location Columns = What's Left
```python
# Get all text columns
text_columns = df.select_dtypes(include=['object']).columns

# Remove test and time columns
location_columns = [
    col for col in text_columns 
    if col not in test_columns + time_columns
]
```

### Step 4: Order Location Hierarchy
```python
# Sort by unique count (State has least, Facility has most)
location_hierarchy = sorted(location_columns, key=lambda x: df[x].nunique())

# Map to our internal names
column_mapping = {
    'state': location_hierarchy[0],     # Fewest unique values
    'lga': location_hierarchy[1],       # Second fewest
    'ward': location_hierarchy[2],      # Second most
    'facility': location_hierarchy[3]   # Most unique values
}
```

## Handle Edge Cases

### Single State Upload
```python
# If state column has only 1 value, it's still the state!
if df[location_hierarchy[0]].nunique() == 1:
    # This is fine - user uploaded single state data
    state_name = df[location_hierarchy[0]].iloc[0]
    logger.info(f"Processing single state: {state_name}")
```

### Encoding Issues
```python
# Fix encoding in column names
df.columns = [col.replace('â‰¥', '≥') for col in df.columns]
```

### State Prefixes
```python
# Clean prefixes like "ad Adamawa State"
if 'state' in column_mapping:
    state_col = column_mapping['state']
    df[state_col] = df[state_col].str.replace(r'^[a-z]{2}\s+', '', regex=True)
```

## Complete Implementation

```python
class SimpleTPRDetector:
    def detect_columns(self, df):
        # 1. Fix encoding
        df = self.fix_encoding(df)
        
        # 2. Find test columns (by name)
        test_columns = self.find_test_columns(df)
        
        # 3. Find time column (by pattern)
        time_column = self.find_time_column(df)
        
        # 4. Find location columns (what's left)
        location_columns = self.find_location_columns(df, test_columns, time_column)
        
        # 5. Order location hierarchy
        location_hierarchy = self.order_locations(df, location_columns)
        
        return {
            'test_columns': test_columns,
            'time_column': time_column,
            'location_mapping': {
                'state': location_hierarchy[0],
                'lga': location_hierarchy[1],
                'ward': location_hierarchy[2],
                'facility': location_hierarchy[3]
            }
        }
```

## Why This Works

1. **Test columns never change names** - We can rely on exact matching
2. **Only 4 text columns remain** after removing test/time - These must be locations
3. **Cardinality ordering is reliable** - State always has fewer unique values than LGA, etc.
4. **No complex ML needed** - Simple, deterministic logic

## Files to Modify

1. **nmep_parser.py**: Remove hardcoded 'raw' sheet requirement
2. **tpr_pipeline.py**: Use detected column names instead of hardcoded
3. **column_mapper.py**: Not needed anymore - we detect dynamically!

This approach is simple, fast, and will work with ANY TPR format!