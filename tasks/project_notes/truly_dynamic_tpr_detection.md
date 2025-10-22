# Truly Dynamic TPR Detection - No Hardcoded Names

## The Paradigm Shift

**Old Approach**: Look for specific column names (State, LGA, orgunitlevel2, etc.)
**New Approach**: Understand what the data IS, not what it's CALLED

## Core Principle: Data Speaks Louder Than Names

### Example Scenario
Imagine a TPR file with these columns:
- Column1, Column2, Column3, Column4 (hierarchical locations)
- X, Y, Z (test counts)
- A, B, C (positive counts)

Our system should understand:
- Column1 is State (because it has ~37 unique values)
- Column2 is LGA (because it has ~774 unique values and maps many-to-one with Column1)
- X and A are paired (A <= X always, suggesting tested/positive relationship)

## The Intelligence Engine

### 1. Data Profiling (No Names Needed)

```python
class DataProfiler:
    def profile_column(self, data: pd.Series) -> Dict:
        return {
            'cardinality': data.nunique(),
            'data_type': self.detect_type(data),
            'null_rate': data.isna().sum() / len(data),
            'value_distribution': self.analyze_distribution(data),
            'patterns': self.detect_patterns(data),
            'statistics': self.calculate_stats(data)
        }
    
    def detect_type(self, data: pd.Series) -> str:
        # Don't look at column name, look at the data!
        if pd.api.types.is_numeric_dtype(data):
            if all(data.dropna() == data.dropna().astype(int)):
                return 'integer_counts'
            elif data.min() >= 0 and data.max() <= 100:
                return 'percentage'
            else:
                return 'numeric'
        else:
            # Analyze string patterns
            return self.analyze_string_type(data)
```

### 2. Hierarchy Detection by Cardinality

```python
def detect_hierarchy(df: pd.DataFrame) -> Dict:
    # Step 1: Find all text columns
    text_columns = [col for col in df.columns if df[col].dtype == 'object']
    
    # Step 2: Calculate cardinalities
    cardinalities = {
        col: df[col].nunique() 
        for col in text_columns
    }
    
    # Step 3: Sort by cardinality
    sorted_cols = sorted(cardinalities.items(), key=lambda x: x[1])
    
    # Step 4: Assign hierarchy levels by cardinality ranges
    hierarchy = {}
    for col, card in sorted_cols:
        if card <= 50 and 'state' not in hierarchy:
            hierarchy['state'] = col
        elif 50 < card <= 1000 and 'lga' not in hierarchy:
            hierarchy['lga'] = col
        elif 1000 < card <= 20000 and 'ward' not in hierarchy:
            hierarchy['ward'] = col
        elif card > 20000 and 'facility' not in hierarchy:
            hierarchy['facility'] = col
    
    # Step 5: Validate relationships
    hierarchy = validate_hierarchy(df, hierarchy)
    
    return hierarchy
```

### 3. Relationship Discovery

```python
def discover_relationships(df: pd.DataFrame) -> Dict:
    relationships = {}
    
    # Find parent-child relationships
    for col1 in df.columns:
        for col2 in df.columns:
            if col1 != col2:
                # Check if col1 -> col2 is one-to-many
                mapping = df.groupby(col1)[col2].nunique()
                if mapping.mean() > 5:  # Each col1 maps to multiple col2
                    relationships[f"{col1}_parent_of_{col2}"] = {
                        'parent': col1,
                        'child': col2,
                        'avg_children': mapping.mean()
                    }
    
    return relationships
```

### 4. Test Data Detection Without Names

```python
def detect_test_columns(df: pd.DataFrame) -> Dict:
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    test_pairs = {}
    
    # Find columns where one is always <= another
    for col1 in numeric_cols:
        for col2 in numeric_cols:
            if col1 != col2:
                # Check if col2 <= col1 for all rows
                if all(df[col2] <= df[col1]):
                    # Likely col1=tested, col2=positive
                    pair_key = f"test_pair_{len(test_pairs)+1}"
                    test_pairs[pair_key] = {
                        'tested': col1,
                        'positive': col2,
                        'confidence': calculate_confidence(df, col1, col2)
                    }
    
    # Group by similar ranges to identify age groups
    groups = cluster_columns_by_distribution(df, numeric_cols)
    
    return {
        'test_pairs': test_pairs,
        'column_groups': groups
    }
```

## Real-World Example

### Input: Mystery TPR File
```
| A | B | C | D | E | F | G | H | I | J |
|---|---|---|---|---|---|---|---|---|---|
| X1| Y1| Z1| W1| 50| 10| 45| 8 | 20| 5 |
| X1| Y1| Z1| W2| 60| 12| 55| 10| 25| 6 |
| X1| Y2| Z2| W3| 40| 8 | 38| 7 | 18| 4 |
```

### Our System Detects:
1. **Hierarchy**: A→B→C→D (by cardinality: 5→20→400→8000)
2. **Test Pairs**: 
   - E & F are paired (F always ≤ E)
   - G & H are paired (H always ≤ G)
   - I & J are paired (J always ≤ I)
3. **Groups**: E,G,I have similar distributions (likely same test type, different demographics)

### Output:
```json
{
  "hierarchy": {
    "state": "A",
    "lga": "B", 
    "ward": "C",
    "facility": "D"
  },
  "testing_data": {
    "group1_tested": "E",
    "group1_positive": "F",
    "group2_tested": "G",
    "group2_positive": "H",
    "group3_tested": "I",
    "group3_positive": "J"
  },
  "confidence": 0.95
}
```

## Implementation Strategy

### Phase 1: Pure Data Understanding
```python
class UniversalDataUnderstander:
    def understand(self, df: pd.DataFrame) -> Dict:
        # No column name assumptions!
        understanding = {
            'profiles': self.profile_all_columns(df),
            'relationships': self.discover_all_relationships(df),
            'hierarchies': self.detect_hierarchies(df),
            'numeric_patterns': self.analyze_numeric_patterns(df),
            'data_quality': self.assess_quality(df)
        }
        
        # Build semantic understanding
        return self.build_semantic_model(understanding)
```

### Phase 2: Intelligent Mapping
Once we understand what each column represents by its data characteristics, we can map it to our internal model:

```python
def map_to_internal_model(understanding: Dict) -> Dict:
    # Map detected hierarchies to our concepts
    mapping = {
        'location_hierarchy': understanding['hierarchies'],
        'test_data': understanding['numeric_patterns']['test_pairs'],
        'demographics': understanding['numeric_patterns']['groups']
    }
    
    return mapping
```

## Benefits of This Approach

1. **Truly Universal**: Works with ANY column naming convention
2. **Self-Validating**: Uses data relationships to verify detections
3. **Adaptable**: Learns from new patterns without code changes
4. **Robust**: Handles missing columns, extra columns, any order
5. **Explainable**: Can show WHY it made each detection

## Example Detection Logic

### Detecting State Column (No Name Needed!)
```python
def find_state_column(df: pd.DataFrame) -> str:
    candidates = []
    
    for col in df.columns:
        if df[col].dtype == 'object':
            profile = {
                'unique_count': df[col].nunique(),
                'has_children': False,
                'sample_values': df[col].unique()[:5]
            }
            
            # Check if this column has child relationships
            for other_col in df.columns:
                if col != other_col:
                    if is_parent_of(df, col, other_col):
                        profile['has_children'] = True
                        profile['child_count'] = df.groupby(col)[other_col].nunique().mean()
            
            # State-like characteristics:
            # - 10-50 unique values
            # - Has child columns with 10-30 children each
            # - Is at the top of hierarchy
            if 10 <= profile['unique_count'] <= 50 and profile['has_children']:
                if 10 <= profile.get('child_count', 0) <= 30:
                    candidates.append((col, profile))
    
    # Return best candidate
    return select_best_candidate(candidates)
```

## The Magic: It Just Works!

Whether your columns are named:
- State, LGA, Ward, Facility
- orgunitlevel2, orgunitlevel3, orgunitlevel4, orgunitlevel5  
- Column1, Column2, Column3, Column4
- A, B, C, D
- Location1, Location2, Location3, Location4
- 地域1, 地域2, 地域3, 地域4 (even in other languages!)

**Our system will understand what they represent by analyzing the data itself!**