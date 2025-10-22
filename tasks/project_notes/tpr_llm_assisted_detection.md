# LLM-Assisted Intelligent TPR Detection

## Key Insights from the Two Formats

### Pattern 1: Hierarchical Location Data Always Exists
- Format A: State → LGA → Ward → Health Facility
- Format B: orgunitlevel2 → orgunitlevel3 → orgunitlevel4 → orgunitlevel5
- **Inference**: There's ALWAYS a 4-level hierarchy representing geographic divisions

### Pattern 2: Test Data Structure is Consistent
Both formats have identical testing columns:
- RDT/Microscopy tested and positive counts
- Split by demographics: <5 years, ≥5 years, Pregnant Women
- **Inference**: The medical data structure is standardized, only location naming varies

### Pattern 3: Cardinality Patterns are Predictable
- Level 1 (State): ~37 unique values (Nigeria's states)
- Level 2 (LGA): ~774 unique values
- Level 3 (Ward): ~9,500 unique values  
- Level 4 (Facility): ~30,000+ unique values
- **Inference**: We can use these ratios to detect hierarchy levels

## LLM-Assisted Detection Strategy

### 1. Data Analysis First
```python
def analyze_columns_with_llm(df: pd.DataFrame) -> Dict:
    # Step 1: Generate column profiles
    profiles = {}
    for col in df.columns:
        profiles[col] = {
            'name': col,
            'cardinality': df[col].nunique(),
            'data_type': str(df[col].dtype),
            'sample_values': df[col].dropna().head(10).tolist(),
            'null_percentage': df[col].isna().sum() / len(df) * 100,
            'numeric_stats': get_numeric_stats(df[col]) if pd.api.types.is_numeric_dtype(df[col]) else None
        }
    
    # Step 2: Find relationships
    relationships = discover_column_relationships(df)
    
    # Step 3: Ask LLM to interpret
    return ask_llm_to_interpret(profiles, relationships)
```

### 2. LLM Prompt for Column Understanding
```python
def ask_llm_to_interpret(profiles: Dict, relationships: Dict) -> Dict:
    prompt = f"""
    I have a health data file with the following columns. Please help me understand what each column represents.
    
    Column Profiles:
    {json.dumps(profiles, indent=2)}
    
    Detected Relationships:
    {json.dumps(relationships, indent=2)}
    
    Based on the data characteristics:
    1. Which columns form a geographic hierarchy (State/Region → District → Subdistrict → Facility)?
    2. Which numeric columns represent test counts vs positive results?
    3. Are there demographic groupings in the data?
    
    Consider:
    - Cardinality (unique values) often indicates hierarchy level
    - Columns where values in one are always <= another suggest tested/positive pairs
    - Similar value distributions might indicate the same metric for different groups
    
    Respond with your analysis and confidence level for each detection.
    """
    
    return llm.analyze(prompt)
```

### 3. Hybrid Detection System
```python
class HybridTPRDetector:
    def __init__(self, llm_client):
        self.llm = llm_client
        self.data_analyzer = DataAnalyzer()
    
    def detect_all(self, df: pd.DataFrame) -> Dict:
        # Phase 1: Statistical Analysis
        stats_detection = {
            'hierarchy': self.detect_hierarchy_by_cardinality(df),
            'test_pairs': self.detect_test_pairs_by_relationships(df),
            'patterns': self.detect_patterns_statistically(df)
        }
        
        # Phase 2: LLM Enhancement
        llm_insights = self.get_llm_insights(df, stats_detection)
        
        # Phase 3: Combine and Validate
        final_detection = self.combine_detections(stats_detection, llm_insights)
        
        # Phase 4: Explain reasoning
        explanation = self.generate_explanation(final_detection)
        
        return {
            'detection': final_detection,
            'confidence': self.calculate_confidence(final_detection),
            'explanation': explanation
        }
    
    def get_llm_insights(self, df: pd.DataFrame, initial_detection: Dict) -> Dict:
        # Prepare context for LLM
        context = {
            'sample_data': df.head(20).to_dict(),
            'column_profiles': self.profile_all_columns(df),
            'initial_detection': initial_detection,
            'ambiguous_columns': self.find_ambiguous_columns(initial_detection)
        }
        
        # Ask LLM for help with ambiguous cases
        prompt = self.build_llm_prompt(context)
        response = self.llm.analyze(prompt)
        
        return self.parse_llm_response(response)
```

## Specific Inferences We Can Make

### 1. From Column Names (even without hardcoding)
```python
def infer_from_column_patterns(col_name: str) -> Dict:
    """Use LLM to understand column naming patterns"""
    
    prompt = f"""
    This column is named: "{col_name}"
    
    Common patterns in health data:
    - Geographic hierarchies often use: level, unit, division, region, area
    - Test data often includes: test, exam, screen, check, rdt, micro
    - Positive results often include: positive, confirmed, case, malaria
    - Age groups might include: age, years, u5, o5, <5, ≥5
    
    What type of data might this column contain? Consider:
    1. Is it likely geographic/location data?
    2. Is it likely test/medical data?
    3. Is it likely demographic data?
    
    Respond with your best guess and reasoning.
    """
    
    return llm.analyze(prompt)
```

### 2. From Data Relationships
```python
def infer_from_relationships(df: pd.DataFrame) -> Dict:
    """Use both statistics and LLM to understand relationships"""
    
    # Statistical inference
    inferences = {}
    
    # Find hierarchies by cardinality ratios
    for col1, col2 in itertools.combinations(df.columns, 2):
        ratio = df[col2].nunique() / df[col1].nunique()
        if 10 <= ratio <= 30:
            inferences[f'{col1}_parent_of_{col2}'] = {
                'confidence': 0.8,
                'reasoning': f'Cardinality ratio of {ratio:.1f} suggests parent-child'
            }
    
    # Find test pairs by value relationships
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col1, col2 in itertools.combinations(numeric_cols, 2):
        if all(df[col2] <= df[col1]):
            correlation = df[col1].corr(df[col2])
            if correlation > 0.7:
                inferences[f'{col1}_tested_{col2}_positive'] = {
                    'confidence': 0.9,
                    'reasoning': 'Values always <=, high correlation'
                }
    
    # Ask LLM to validate
    llm_validation = validate_with_llm(inferences, df)
    
    return combine_inferences(inferences, llm_validation)
```

### 3. From Data Patterns
```python
def infer_from_patterns(df: pd.DataFrame) -> Dict:
    """Detect patterns that reveal data meaning"""
    
    patterns = {}
    
    # Pattern 1: State names with prefixes
    for col in df.select_dtypes(include=['object']).columns:
        sample = df[col].dropna().head(100)
        # Check for prefix patterns like "ad Adamawa State"
        if sample.str.match(r'^[a-z]{2}\s+').any():
            patterns[col] = {
                'pattern': 'prefix_before_name',
                'likely_type': 'state_with_code',
                'confidence': 0.85
            }
    
    # Pattern 2: Facility naming conventions
    for col in df.select_dtypes(include=['object']).columns:
        sample = df[col].dropna().head(100)
        facility_keywords = ['Hospital', 'Clinic', 'Health', 'Medical', 'PHC', 'Center']
        if any(keyword in ' '.join(sample.astype(str)) for keyword in facility_keywords):
            patterns[col] = {
                'pattern': 'facility_names',
                'likely_type': 'health_facility',
                'confidence': 0.9
            }
    
    return patterns
```

## Complete LLM-Integrated Detection Flow

```python
class IntelligentTPRDetector:
    def __init__(self, llm_client):
        self.llm = llm_client
        self.stats_engine = StatisticalEngine()
        self.pattern_engine = PatternEngine()
    
    def detect_complete(self, file_path: str) -> Dict:
        # Load data intelligently
        df = self.load_any_format(file_path)
        
        # Phase 1: Statistical Detection
        stats_result = self.stats_engine.analyze(df)
        
        # Phase 2: Pattern Detection  
        patterns = self.pattern_engine.detect_all_patterns(df)
        
        # Phase 3: LLM-Assisted Understanding
        llm_context = {
            'file_name': file_path,
            'shape': df.shape,
            'columns': df.columns.tolist(),
            'stats': stats_result,
            'patterns': patterns,
            'sample_data': df.head(10).to_dict()
        }
        
        llm_analysis = self.llm.deep_analyze(llm_context)
        
        # Phase 4: Synthesis
        final_result = self.synthesize_all_findings(
            stats_result, patterns, llm_analysis
        )
        
        # Phase 5: Confidence and Explanation
        final_result['confidence'] = self.calculate_overall_confidence(final_result)
        final_result['explanation'] = self.generate_human_explanation(final_result)
        
        return final_result
    
    def generate_human_explanation(self, result: Dict) -> str:
        """Generate clear explanation of what was detected and why"""
        
        prompt = f"""
        Based on our analysis, please generate a clear explanation:
        
        Detected Structure:
        {json.dumps(result['structure'], indent=2)}
        
        Confidence Levels:
        {json.dumps(result['confidence_breakdown'], indent=2)}
        
        Please explain:
        1. What type of data file this appears to be
        2. How we identified each column's purpose
        3. Any assumptions we made
        4. Suggestions for the user to verify
        
        Keep it concise and user-friendly.
        """
        
        return self.llm.generate(prompt)
```

## The Power of LLM + Data Analysis

By combining:
1. **Statistical Analysis**: Cardinality, relationships, distributions
2. **Pattern Recognition**: Naming patterns, data patterns, structural patterns
3. **LLM Intelligence**: Context understanding, ambiguity resolution, explanation

We get a system that can:
- Handle ANY column naming convention
- Explain its reasoning clearly
- Learn from experience
- Adapt to new formats without code changes

This is truly dynamic and intelligent!