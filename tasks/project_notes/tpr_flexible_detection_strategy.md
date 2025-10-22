# TPR Flexible Detection Strategy

## Key Improvements for True Flexibility

### 1. Test Column Detection - Pattern Based, Not Exact

**Problem**: What if columns are named differently?
- "RDT test <5" instead of "RDT tested <5"
- "Positive cases <5" instead of "RDT positive <5"
- Missing some columns (only 10 instead of 12)

**Solution**: Use pattern matching
```python
def find_test_columns(df):
    # Look for patterns that indicate test data
    test_indicators = {
        'tested': [r'test', r'exam', r'screen'],
        'positive': [r'positive', r'confirm', r'case'],
        'age_groups': [r'<\s*5', r'≥\s*5', r'[Pp]regnant'],
        'test_types': [r'RDT', r'[Mm]icroscopy', r'rapid']
    }
    
    # Also detect by relationships (positive <= tested)
    numeric_pairs = find_test_positive_pairs(df)
    
    return combine_pattern_and_relationship_detection(pattern_matches, numeric_pairs)
```

### 2. Time Column - Multiple Format Support

**Problem**: Date formats vary widely
- "2024-04" (YYYY-MM)
- "04/2024" (MM/YYYY)
- "April 2024" (MonthName Year)
- "2024/04" (YYYY/MM)

**Solution**: Try multiple patterns
```python
def detect_time_column(df):
    date_patterns = [
        (r'^\d{4}-\d{2}$', 'YYYY-MM'),
        (r'^\d{2}/\d{4}$', 'MM/YYYY'),
        (r'^[A-Za-z]+ \d{4}$', 'Month Year'),
        (r'^\d{4}/\d{2}$', 'YYYY/MM'),
        (r'^\d{6}$', 'YYYYMM'),  # No separator
    ]
    
    for col in df.columns:
        if df[col].dtype == 'object':
            for pattern, format_name in date_patterns:
                if matches_pattern(df[col], pattern):
                    return col, format_name
```

### 3. Graceful Missing Column Handling

**Problem**: What if some expected columns are missing?

**Solution**: Work with what we have
```python
def handle_missing_columns(detected):
    # Required vs optional columns
    required = {
        'location': len(detected['location_columns']) >= 2,  # At least LGA and Ward
        'test_data': len(detected['test_columns']) >= 4,     # At least some test data
        'time': detected['time_column'] is not None
    }
    
    if not all(required.values()):
        # Provide clear feedback about what's missing
        missing = [k for k, v in required.items() if not v]
        return {
            'success': False,
            'missing': missing,
            'suggestion': generate_helpful_message(missing)
        }
```

### 4. Frontend Display Mapping

**Problem**: Users shouldn't see technical column names

**Solution**: Always map to user-friendly names
```python
class FrontendMapper:
    def __init__(self, detected_columns):
        self.mapping = self.build_mapping(detected_columns)
    
    def build_mapping(self, detected):
        # Map detected columns to display names
        location_hierarchy = detected['location_hierarchy']
        
        return {
            location_hierarchy[0]: 'State',
            location_hierarchy[1]: 'LGA', 
            location_hierarchy[2]: 'Ward',
            location_hierarchy[3]: 'Health Facility',
            # Test columns
            'any_rdt_tested_col': 'RDT Tests',
            'any_micro_positive_col': 'Microscopy Positive',
            # etc.
        }
    
    def get_display_name(self, column):
        return self.mapping.get(column, column)
```

### 5. Robust Location Detection

**Problem**: Can't rely on exact cardinality numbers

**Solution**: Use relative relationships
```python
def detect_location_hierarchy(df, text_columns):
    # Don't assume specific counts, use relationships
    cardinalities = {col: df[col].nunique() for col in text_columns}
    
    # Sort by cardinality
    sorted_cols = sorted(cardinalities.items(), key=lambda x: x[1])
    
    # Assign levels based on relative position
    if len(sorted_cols) >= 4:
        return {
            'state': sorted_cols[0][0],
            'lga': sorted_cols[1][0],
            'ward': sorted_cols[2][0],
            'facility': sorted_cols[3][0]
        }
    elif len(sorted_cols) == 3:
        # Missing state? Single state upload?
        if sorted_cols[0][1] == 1:  # First column has 1 value
            return {
                'state': sorted_cols[0][0],  # Single state
                'lga': sorted_cols[1][0],
                'ward': sorted_cols[2][0],
                'facility': None  # Missing
            }
```

## Complete Flexible Detector

```python
class FlexibleTPRDetector:
    def detect(self, df):
        # Clean up first
        df = self.normalize_columns(df)
        
        # Detect all column types
        detected = {
            'test_columns': self.find_test_columns_flexibly(df),
            'time_column': self.find_time_column_flexibly(df),
            'location_columns': self.find_location_columns(df),
            'metadata_columns': self.find_metadata_columns(df)
        }
        
        # Validate what we found
        validation = self.validate_detection(detected)
        
        # Build frontend mapping
        display_mapping = self.build_display_mapping(detected)
        
        return {
            'detected_columns': detected,
            'validation': validation,
            'display_mapping': display_mapping,
            'warnings': self.generate_warnings(detected, validation)
        }
    
    def generate_warnings(self, detected, validation):
        warnings = []
        
        # Check for missing expected columns
        if len(detected['test_columns']) < 8:
            warnings.append(f"Only found {len(detected['test_columns'])} test columns (expected at least 8)")
        
        # Check location hierarchy
        if len(detected['location_columns']) < 3:
            warnings.append("Incomplete location hierarchy detected")
        
        # Check time column
        if not detected['time_column']:
            warnings.append("No time period column found")
        
        return warnings
```

## Key Principles

1. **Pattern Matching > Exact Matching**: Use regex and patterns, not hardcoded names
2. **Relationship Detection**: Find test/positive pairs by mathematical relationships
3. **Graceful Degradation**: Work with what's available, warn about missing data
4. **User-Friendly Display**: Never show technical column names to users
5. **Multiple Format Support**: Try various patterns for dates, encodings, etc.
6. **Clear Feedback**: Tell users exactly what was detected and what might be missing

This approach ensures ChatMRPT can handle:
- Files with 10 or 14 test columns instead of exactly 12
- Different date formats
- Missing columns
- Various naming conventions
- Single state/LGA uploads
- Future format variations we haven't seen yet