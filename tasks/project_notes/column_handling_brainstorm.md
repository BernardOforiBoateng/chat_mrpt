# Column Handling & Encoding - Scalable Solutions Brainstorm

## Date: 2025-01-20

## Current Problems

### 1. Encoding Issues
- **Hardcoded fixes**: Only handles specific patterns (â‰¥ → ≥)
- **Not scalable**: What about Arabic? Chinese? Cyrillic? Other corruptions?
- **Fragile**: Each new encoding issue requires code changes

### 2. Column Name Complexity
- Spaces in names: `"Persons presenting with fever & tested by RDT <5yrs"`
- Special characters: `<`, `≥`, `&`, `(`, `)`
- Long descriptive names (60+ characters)
- Agent struggles to reference these in Python code

### 3. Current Approach Limitations
```python
ENCODING_FIXES = {
    'â‰¥': '≥',  # What about other corruptions?
    'â‰¤': '≤',  # Not scalable!
}
```

## Industry Best Practices

### 1. **Column Sanitization (Most Common)**
```python
def sanitize_column_name(col):
    """Convert to Python-friendly names"""
    # Remove special chars, replace spaces with underscore
    clean = re.sub(r'[^\w\s]', '', col)
    clean = re.sub(r'\s+', '_', clean)
    return clean.lower()

# Example: "Persons tested by RDT <5yrs" → "persons_tested_by_rdt_5yrs"
```

### 2. **Dual-Name System (Pandas Standard)**
```python
class ColumnMapper:
    def __init__(self, df):
        self.original_to_clean = {}
        self.clean_to_original = {}
        
        for col in df.columns:
            clean = self.sanitize(col)
            self.original_to_clean[col] = clean
            self.clean_to_original[clean] = col
        
        # Rename DataFrame columns
        df.columns = [self.original_to_clean[c] for c in df.columns]
    
    def get_original(self, clean_name):
        return self.clean_to_original.get(clean_name)
```

### 3. **Schema Inference (Apache Arrow/Parquet)**
- Automatically detect and normalize column types
- Store metadata separately from data
- Used by: Databricks, Snowflake, BigQuery

### 4. **Universal Character Detection (Industry)**
```python
import ftfy  # "fixes text for you" - Mozilla library

def fix_text_encoding(text):
    """Fixes mojibake and other encoding issues"""
    return ftfy.fix_text(text)

# Handles ALL encoding issues, not just specific patterns
```

## Proposed Solutions

### Solution 1: Column Sanitization + Mapping (RECOMMENDED)
**Pros:**
- Agent works with clean names: `rdt_test_under_5`, `rdt_test_5_plus`
- Original names preserved for display
- No special character issues
- Works with ANY encoding/language

**Implementation:**
```python
class SmartColumnHandler:
    def __init__(self):
        self.mapping = {}
        
    def process_dataframe(self, df):
        # Store original columns
        original_cols = df.columns.tolist()
        
        # Create clean versions
        clean_cols = []
        for i, col in enumerate(original_cols):
            # Create semantic name
            clean = self._create_semantic_name(col, i)
            clean_cols.append(clean)
            self.mapping[clean] = col
        
        # Apply clean names
        df.columns = clean_cols
        
        # Store metadata
        df.attrs['original_columns'] = original_cols
        df.attrs['column_mapping'] = self.mapping
        
        return df
    
    def _create_semantic_name(self, col, index):
        """Create meaningful short names"""
        col_lower = col.lower()
        
        # Detect column type and create semantic name
        if 'rdt' in col_lower and '<5' in col_lower:
            return 'rdt_tested_under_5'
        elif 'rdt' in col_lower and '≥5' in col_lower:
            return 'rdt_tested_5_plus'
        elif 'rdt' in col_lower and 'positive' in col_lower and '<5' in col_lower:
            return 'rdt_positive_under_5'
        # ... etc
        else:
            # Fallback to generic sanitization
            return f"col_{index}_{self._sanitize(col[:20])}"
```

### Solution 2: Use Industry Libraries

**Option A: ftfy (Recommended for encoding)**
```python
pip install ftfy

import ftfy

def fix_all_column_names(df):
    df.columns = [ftfy.fix_text(col) for col in df.columns]
    return df
```

**Option B: python-slugify (For URL-safe names)**
```python
from slugify import slugify

df.columns = [slugify(col, separator='_') for col in df.columns]
```

**Option C: pandas-profiling approach**
```python
# They use this pattern
def clean_column_name(name):
    name = re.sub('[^a-zA-Z0-9_]', '_', name)
    name = re.sub('_+', '_', name)
    return name.strip('_').lower()
```

### Solution 3: Semantic Column Detection
```python
class TPRColumnDetector:
    """Understand what each column means regardless of name"""
    
    PATTERNS = {
        'rdt_test_children': [
            r'rdt.*<\s*5|under.*5.*rdt|children.*rdt',
            lambda col, df: 'rdt' in col.lower() and df[col].dtype == 'int64'
        ],
        'rdt_test_adults': [
            r'rdt.*(?:≥|>=)\s*5|adult.*rdt|5\+.*rdt',
            lambda col, df: 'rdt' in col.lower() and '5' in col
        ],
        # ... more patterns
    }
    
    def detect_columns(self, df):
        """Auto-detect column purposes"""
        detected = {}
        for semantic_name, patterns in self.PATTERNS.items():
            for col in df.columns:
                if self._matches(col, df, patterns):
                    detected[semantic_name] = col
                    break
        return detected
```

### Solution 4: LLM-Friendly Column Descriptions
```python
def generate_column_context(df):
    """Generate context for the LLM about columns"""
    context = []
    
    for col in df.columns:
        safe_name = sanitize_column_name(col)
        sample_values = df[col].dropna().head(3).tolist()
        
        context.append({
            'original': col,
            'safe_name': safe_name,
            'dtype': str(df[col].dtype),
            'samples': sample_values,
            'non_null': df[col].notna().sum(),
            'usage_hint': generate_usage_hint(col)  # "Use for malaria testing counts"
        })
    
    return context
```

## Comparison with Industry Tools

### 1. **Apache Spark**
- Auto-sanitizes column names
- Backticks for special chars: `` `Person tested <5` ``
- We could do: ```df['`' + original_col + '`']```

### 2. **Google BigQuery**
- Replaces special chars with underscore
- Preserves original in metadata
- Exactly what we're proposing!

### 3. **Databricks Delta Lake**
- Column mapping feature
- Physical name vs logical name
- Similar to our dual-name approach

### 4. **dbt (Data Build Tool)**
- Uses aliasing: `select "Ugly Column!" as nice_column`
- We could generate similar aliasing

## Recommended Approach

### Phase 1: Immediate Fix
```python
class UniversalColumnHandler:
    @staticmethod
    def prepare_dataframe(df):
        # 1. Fix encoding issues universally
        import ftfy
        df.columns = [ftfy.fix_text(str(col)) for col in df.columns]
        
        # 2. Create safe column names
        original_columns = df.columns.tolist()
        safe_columns = []
        
        for col in original_columns:
            # Remove special characters but keep meaning
            safe = re.sub(r'[<>≥≤]', '', col)
            safe = re.sub(r'\s+', '_', safe)
            safe = re.sub(r'[^\w]', '', safe)
            safe = safe.lower()[:50]  # Limit length
            
            # Handle duplicates
            if safe in safe_columns:
                safe = f"{safe}_{safe_columns.count(safe)}"
            
            safe_columns.append(safe)
        
        # 3. Store mapping
        column_mapping = dict(zip(safe_columns, original_columns))
        
        # 4. Apply safe names
        df.columns = safe_columns
        
        # 5. Attach metadata
        df.attrs['column_mapping'] = column_mapping
        df.attrs['original_columns'] = original_columns
        
        return df, column_mapping
```

### Phase 2: Agent Instructions
```python
COLUMN_INSTRUCTION = """
The DataFrame columns have been sanitized for easier use:
- Original: "Persons tested by RDT <5yrs"  
- Safe name: "persons_tested_by_rdt_5yrs"

Always use the safe column names in your code.
Column mapping is available in df.attrs['column_mapping'].
"""
```

### Phase 3: Smart Detection
```python
def detect_tpr_columns(df):
    """Auto-detect TPR-related columns"""
    detections = {
        'total_tested': [],
        'positive_cases': [],
        'facility_id': None,
        'location': None
    }
    
    for col in df.columns:
        col_lower = col.lower()
        
        # Testing columns
        if 'test' in col_lower and 'fever' in col_lower:
            detections['total_tested'].append(col)
        
        # Positive columns  
        if 'positive' in col_lower:
            detections['positive_cases'].append(col)
        
        # Facility column
        if 'facility' in col_lower or 'health' in col_lower:
            detections['facility_id'] = col
    
    return detections
```

## Benefits of Column Sanitization

1. **Agent Success**: Clean names = successful code generation
2. **Universal**: Works with Arabic, Chinese, emoji, anything!
3. **Debugging**: Easier to debug `rdt_under_5` than `"Persons presenting with fever & tested by RDT <5yrs"`
4. **Performance**: Shorter column names = faster processing
5. **Compatibility**: Works with all Python libraries

## Action Items

1. **Immediate**: Implement column sanitization in EncodingHandler
2. **Short-term**: Add ftfy for universal encoding fixes
3. **Long-term**: Build semantic column detection for TPR data
4. **Best**: Combine all approaches for maximum robustness

## Code to Test
```python
# Test with various encodings
test_columns = [
    "Personnes testées <5ans",  # French
    "检测人数 <5岁",              # Chinese  
    "المرضى المختبرين <5",       # Arabic
    "Больные тестированные <5",  # Russian
    "🏥 Patients tested <5 📊",   # Emoji
]

handler = UniversalColumnHandler()
for col in test_columns:
    safe = handler.sanitize(col)
    print(f"{col} → {safe}")
```

This approach would make the agent work with ANY data from ANY country in ANY language!