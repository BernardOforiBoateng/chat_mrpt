# TPR Flexible Column Matching Plan

## Problem Statement
Users upload TPR data with varying column formats:
- Different naming conventions (e.g., "RDT", "rdt", "Rapid Diagnostic Test")
- Special characters (≥5, <5, etc.)
- Different structures (some have "Persons presenting with fever", others just "Tested")
- Age group representations vary (u5, under5, <5, Under 5 years, etc.)

## Analysis of Deleted Production Implementation

### Key Findings
1. **Recommended Pathway**:
   - Primary facilities (recommended)
   - Under 5 age group (recommended)
   - Both RDT and Microscopy (takes max TPR)

2. **Flexible Conversation Flow**:
   ```python
   # Not rigid steps, but flexible stages
   ConversationStage.INITIAL_ANALYSIS
   ConversationStage.STATE_SELECTION
   ConversationStage.FACILITY_SELECTION  # Recommends Primary
   ConversationStage.AGE_GROUP_SELECTION  # Recommends Under 5
   ```

3. **Column Handling**:
   - Used multiple fallback patterns
   - Checked for variations in naming
   - Normalized column names for matching

## Proposed Solution

### 1. Intelligent Column Detector
```python
class FlexibleColumnDetector:
    """
    Detects TPR columns regardless of naming variations.
    """
    
    # Pattern matching for different column types
    TEST_PATTERNS = {
        'rdt_tested': [
            r'.*rdt.*test.*',
            r'.*rapid.*diagnostic.*',
            r'.*presenting.*fever.*rdt.*',
            r'.*tested.*rdt.*'
        ],
        'rdt_positive': [
            r'.*rdt.*positive.*',
            r'.*positive.*rdt.*',
            r'.*confirmed.*rdt.*'
        ],
        'microscopy_tested': [
            r'.*microscop.*test.*',
            r'.*micro.*test.*',
            r'.*presenting.*fever.*microscop.*',
            r'.*tested.*microscop.*'
        ],
        'microscopy_positive': [
            r'.*microscop.*positive.*',
            r'.*positive.*microscop.*',
            r'.*confirmed.*microscop.*'
        ]
    }
    
    AGE_PATTERNS = {
        'under5': [
            r'.*<\s*5.*',
            r'.*under.*5.*',
            r'.*u5.*',
            r'.*≤\s*5.*',
            r'.*5\s*yr.*',
            r'.*child.*'
        ],
        'over5': [
            r'.*≥\s*5.*',
            r'.*>\s*5.*',
            r'.*over.*5.*',
            r'.*o5.*',
            r'.*5\+.*',
            r'.*adult.*'
        ],
        'pregnant': [
            r'.*preg.*',
            r'.*pw.*',
            r'.*anc.*',
            r'.*women.*'
        ]
    }
```

### 2. Column Normalization Strategy
1. **First Pass**: Direct column name matching
2. **Second Pass**: Pattern matching with regex
3. **Third Pass**: Fuzzy string matching (>85% similarity)
4. **Fourth Pass**: Semantic similarity using keywords

### 3. User Guidance with Recommendations

```python
def generate_tpr_guidance(data_analysis):
    """
    Generate user guidance with recommendations.
    """
    return {
        'message': """
        I've analyzed your TPR data. Here are my recommendations:
        
        **Facility Level Selection:**
        ✓ Primary Health Centers (recommended) - Best data completeness
        • Secondary Facilities - Good coverage
        • Tertiary Facilities - Limited data
        • All Facilities - Complete picture
        
        **Age Group Selection:**
        ✓ Under 5 years (recommended) - Highest priority group
        • Over 5 years - Adult population
        • Pregnant Women - Special risk group
        • All Ages - Comprehensive view
        
        **Test Method:**
        ✓ Both RDT & Microscopy (recommended) - Most accurate
        • RDT Only - Rapid testing data
        • Microscopy Only - Lab-confirmed cases
        
        Would you like to proceed with the recommendations or customize?
        """,
        'defaults': {
            'facility_level': 'primary',
            'age_group': 'u5',
            'test_method': 'both'
        }
    }
```

### 4. Implementation Steps

1. **Create FlexibleColumnDetector class**
   - Pattern-based detection
   - Fuzzy matching fallback
   - Returns confidence scores

2. **Update calculate_ward_tpr function**
   - Use FlexibleColumnDetector
   - Handle missing columns gracefully
   - Provide informative feedback

3. **Add recommendation system**
   - Analyze data completeness
   - Suggest best options
   - Allow user override

4. **Enhance error messages**
   - Show what was detected
   - Suggest alternatives
   - Provide column mapping summary

## Example Usage Flow

```
User uploads TPR file
↓
System detects columns flexibly
↓
System analyzes data completeness
↓
System presents recommendations:
  "I recommend using Primary facilities with Under 5 data 
   (95% complete). Would you like to proceed?"
↓
User can:
  - Accept recommendations (just say "yes")
  - Choose different options
  - Ask for alternatives
```

## Testing Strategy

1. Test with multiple TPR file formats:
   - NMEP standard format
   - State-specific formats
   - Custom hospital formats

2. Verify column detection accuracy:
   - All patterns match correctly
   - Fuzzy matching works
   - Confidence scores are meaningful

3. Validate recommendations:
   - Based on actual data completeness
   - Appropriate for the context
   - User can override easily

## Benefits

1. **Flexibility**: Handles any TPR format
2. **User-Friendly**: Clear recommendations
3. **Robust**: Multiple fallback strategies
4. **Informative**: Shows what was detected
5. **Configurable**: Easy to add new patterns