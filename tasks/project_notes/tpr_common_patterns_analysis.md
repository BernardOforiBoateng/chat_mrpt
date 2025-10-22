# Common Patterns Analysis from TPR Formats

## 🔍 What's ALWAYS Present (100% Reliable Patterns)

### 1. **Four-Level Geographic Hierarchy**
Both formats have EXACTLY 4 levels of location data:
- **Level 1**: ~37 unique values (Nigerian states)
- **Level 2**: ~774 unique values (LGAs)
- **Level 3**: ~9,500 unique values (Wards)
- **Level 4**: ~30,000+ unique values (Health facilities)

**Detection Rule**: Look for 4 text columns with cardinality ratios of approximately 1:20:250:800

### 2. **Six Core Testing Columns**
Both formats have IDENTICAL testing structure:
- 3 demographic groups: Under 5, Over 5, Pregnant Women
- 2 test types: RDT, Microscopy
- Each has tested + positive counts

**Pattern**: 12 numeric columns that form 6 pairs where:
- Column A (tested) >= Column B (positive) ALWAYS
- Strong correlation between A and B
- Integer values (counts, not percentages)

### 3. **Temporal Column**
Both have a time period identifier:
- Format A: "Months" (e.g., "2024-04")
- Format B: "period" (e.g., "2024-04")

**Detection Rule**: Text column with date-like patterns (YYYY-MM or similar)

## 📊 Key Detection Signals

### Signal 1: Cardinality Cascade
```
Column Cardinality Pattern:
- Column A: 37 unique → State level
- Column B: 774 unique → LGA level  
- Column C: 9,500 unique → Ward level
- Column D: 30,000+ unique → Facility level

Validation: Each level should map many-to-one with previous level
```

### Signal 2: Numeric Column Pairing
```
Testing Pattern Recognition:
- Find all numeric columns
- Group by correlation and <= relationship
- 6 pairs should emerge naturally
- Each pair represents tested/positive for one demographic+test combo
```

### Signal 3: Data Type Distribution
```
Expected Distribution:
- 4 text columns (hierarchy)
- 1 text column (time period)
- 12+ numeric columns (test data)
- Optional: facility metadata columns
```

## 🎯 Specific Patterns to Detect

### 1. **State Name Patterns**
```python
def detect_state_column(df):
    # Nigerian states often appear with these patterns:
    patterns = [
        "State",           # Common suffix
        "STATE",          # Case variations
        r"^[a-z]{2}\s+",  # Two-letter prefix (e.g., "ad Adamawa")
        "Nigeria"         # Country reference
    ]
    
    # Also check cardinality
    for col in df.columns:
        if 30 <= df[col].nunique() <= 40:  # Nigeria has 36 states + FCT
            # This is likely the state column
```

### 2. **Test Column Patterns**
```python
def detect_test_columns(df):
    # Look for these keywords in ANY language/format:
    test_indicators = {
        'tested': ['test', 'exam', 'screen', 'check'],
        'positive': ['positive', 'confirm', 'case', 'malaria'],
        'rdt': ['rdt', 'rapid'],
        'microscopy': ['micro', 'microscop'],
        'age_groups': ['<5', '≥5', 'u5', 'o5', 'under', 'over', 'pregnant', 'pw']
    }
    
    # But more importantly, look for VALUE relationships:
    # If column A always >= column B, they're likely a tested/positive pair
```

### 3. **Hierarchy Validation**
```python
def validate_hierarchy(df, detected_levels):
    # Check that each level properly nests
    for i in range(len(detected_levels)-1):
        parent = detected_levels[i]
        child = detected_levels[i+1]
        
        # Each parent value should map to multiple children
        mapping = df.groupby(parent)[child].nunique()
        avg_children = mapping.mean()
        
        # Expected ratios:
        # State->LGA: ~20 children
        # LGA->Ward: ~12 children  
        # Ward->Facility: ~3-4 children
```

## 🔧 Implementation Strategy

### 1. **Template-Based Detection**
```python
class TPRTemplate:
    """Known patterns from analyzed TPR formats"""
    
    HIERARCHY_LEVELS = 4
    EXPECTED_CARDINALITIES = [37, 774, 9500, 30000]
    CARDINALITY_TOLERANCE = 0.2  # 20% tolerance
    
    TEST_COLUMN_COUNT = 12
    TEST_PAIRS = 6
    
    def matches_template(self, df):
        """Check if dataframe matches known TPR patterns"""
        
        # Check for hierarchy
        hierarchy_match = self.check_hierarchy_pattern(df)
        
        # Check for test columns
        test_match = self.check_test_pattern(df)
        
        # Check for temporal column
        time_match = self.check_time_pattern(df)
        
        return {
            'is_tpr': hierarchy_match and test_match,
            'confidence': self.calculate_confidence(hierarchy_match, test_match, time_match),
            'details': {
                'hierarchy': hierarchy_match,
                'testing': test_match,
                'temporal': time_match
            }
        }
```

### 2. **Pattern Scoring System**
```python
def score_column_as_hierarchy_level(col_data, expected_cardinality):
    """Score how well a column matches expected hierarchy level"""
    
    actual_cardinality = col_data.nunique()
    expected = expected_cardinality
    
    # Calculate similarity score
    ratio = actual_cardinality / expected
    if 0.8 <= ratio <= 1.2:  # Within 20%
        score = 1.0
    else:
        # Decrease score based on distance
        score = max(0, 1 - abs(1 - ratio))
    
    return score
```

### 3. **Relationship-Based Validation**
```python
def find_test_positive_pairs(df):
    """Find column pairs that represent tested/positive counts"""
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    pairs = []
    
    for col1 in numeric_cols:
        for col2 in numeric_cols:
            if col1 != col2:
                # Check if col2 <= col1 for all rows
                if (df[col2] <= df[col1]).all():
                    # Check correlation
                    corr = df[col1].corr(df[col2])
                    if corr > 0.7:
                        pairs.append({
                            'tested': col1,
                            'positive': col2,
                            'correlation': corr,
                            'confidence': min(corr + 0.2, 1.0)
                        })
    
    # Group pairs by similar value ranges (likely same test type)
    grouped_pairs = group_by_value_distribution(pairs, df)
    
    return grouped_pairs
```

## 📈 Confidence Boosters

### 1. **Multi-Signal Validation**
If multiple signals point to the same conclusion, increase confidence:
- Cardinality matches expected range
- Column has relationship with others as expected
- Data type is correct
- Value patterns match

### 2. **Cross-Validation**
- If detected state column has ~37 values AND each maps to ~20 LGAs → High confidence
- If detected test columns come in pairs of 6 AND values correlate → High confidence

### 3. **Negative Signals**
Decrease confidence if:
- Expected patterns are missing
- Cardinalities are way off
- No clear hierarchy detected
- Test columns don't pair up

## 🎪 The Magic Formula

```python
def detect_tpr_structure(df):
    """
    Use everything we learned from the two formats
    """
    
    detection = {
        'hierarchy': detect_4_level_hierarchy(df),
        'test_pairs': detect_6_test_pairs(df),
        'time_column': detect_temporal_column(df),
        'confidence': 0.0
    }
    
    # Calculate confidence based on how well it matches known patterns
    confidence_factors = [
        (detection['hierarchy'] is not None, 0.4),  # 40% weight
        (len(detection['test_pairs']) == 6, 0.4),   # 40% weight
        (detection['time_column'] is not None, 0.2) # 20% weight
    ]
    
    detection['confidence'] = sum(weight for matches, weight in confidence_factors if matches)
    
    # Explain what we found
    detection['explanation'] = generate_explanation(detection, df)
    
    return detection
```

## Summary: What We Can Rely On

1. **ALWAYS 4-level hierarchy** with predictable cardinalities
2. **ALWAYS 6 test/positive pairs** (3 age groups × 2 test types)
3. **ALWAYS integer count data** (not percentages)
4. **ALWAYS a time period column**
5. **Tested >= Positive** relationship is ironclad
6. **Cardinality ratios** between hierarchy levels are consistent

These patterns give us a strong template to match against ANY TPR format!