# TPR Facility Level Detection Strategy

## The Challenge
- **Original TPR format**: Has explicit `level` column (Primary/Secondary/Tertiary)
- **New TPR format**: NO level column, facility names in `orgunitlevel5`

## Facility Level Patterns from Analysis

### Primary Health Facilities (91% of facilities)
**Keywords to detect:**
- "PRIMARY HEALTH" (54.9%)
- "HEALTH POST" (12.4%) 
- "BASIC HEALTH" (3.4%)
- "DISPENSARY" (1.8%)
- "PHC" 
- "HEALTH CENTRE" / "HEALTH CENTER"
- "CLINIC" (without "HOSPITAL")

### Secondary Health Facilities (8.4% of facilities)
**Keywords to detect:**
- "GENERAL HOSPITAL" (High confidence)
- "COTTAGE HOSPITAL" (High confidence)
- "HOSPITAL" (Medium confidence - 64.4% of secondary)
- "MEDICAL CENTRE" / "MEDICAL CENTER"
- "MATERNITY" (if not with PHC)

### Tertiary Health Facilities (0.6% of facilities)
**Keywords to detect:**
- "TEACHING HOSPITAL"
- "UNIVERSITY" + "HOSPITAL"
- "FEDERAL MEDICAL"
- "FEDERAL SPECIALIST"

## Intelligent Detection Algorithm

```python
def detect_facility_level(facility_name):
    """
    Detect facility level from name when level column is missing.
    Returns: 'Primary', 'Secondary', 'Tertiary', or None
    """
    if not facility_name:
        return None
        
    name_upper = str(facility_name).upper()
    
    # TERTIARY (Highest priority, most specific)
    tertiary_patterns = [
        'TEACHING HOSPITAL',
        'UNIVERSITY HOSPITAL',
        'FEDERAL MEDICAL CENTER',
        'FEDERAL MEDICAL CENTRE',
        'FEDERAL SPECIALIST'
    ]
    if any(pattern in name_upper for pattern in tertiary_patterns):
        return 'Tertiary'
    
    # SECONDARY (High confidence patterns first)
    if 'GENERAL HOSPITAL' in name_upper:
        return 'Secondary'
    if 'COTTAGE HOSPITAL' in name_upper:
        return 'Secondary'
    if 'SPECIALIST HOSPITAL' in name_upper and 'TEACHING' not in name_upper:
        return 'Secondary'
    
    # PRIMARY (Most common)
    primary_patterns = [
        'PRIMARY HEALTH',
        'PHC',
        'HEALTH POST',
        'BASIC HEALTH',
        'DISPENSARY',
        'HEALTH CLINIC',
        'HEALTH UNIT'
    ]
    if any(pattern in name_upper for pattern in primary_patterns):
        return 'Primary'
    
    # MEDIUM CONFIDENCE RULES
    if 'HOSPITAL' in name_upper:
        # Hospital without other qualifiers = Secondary
        return 'Secondary'
        
    if 'MEDICAL CENTRE' in name_upper or 'MEDICAL CENTER' in name_upper:
        return 'Secondary'
        
    if 'MATERNITY' in name_upper:
        # Standalone maternity = Primary
        if 'HOSPITAL' not in name_upper:
            return 'Primary'
        else:
            return 'Secondary'
    
    if 'CLINIC' in name_upper:
        return 'Primary'
    
    # DEFAULT: Most facilities are Primary
    return 'Primary'
```

## Implementation Strategy

### 1. **Update facility_filter.py**
```python
def get_facility_level(row):
    # First check if level column exists
    if 'level' in row:
        return row['level']
    elif 'facility_level' in row:
        return row['facility_level']
    
    # Fall back to name-based detection
    facility_col = None
    for col in ['facility', 'Health Faccility', 'orgunitlevel5']:
        if col in row:
            facility_col = col
            break
    
    if facility_col:
        return detect_facility_level(row[facility_col])
    
    return 'Unknown'
```

### 2. **Handle Missing Levels Gracefully**
```python
# In facility distribution analysis
if facility_levels_detected:
    # Show normal options
    show_facility_level_options()
else:
    # Inform user
    message = """
    Note: Facility level information is not available in this dataset.
    Analysis will include all facilities regardless of type.
    """
    # Only show "All facilities" option
```

### 3. **Confidence Scoring**
```python
def detect_with_confidence(facility_name):
    level = detect_facility_level(facility_name)
    confidence = 'high'
    
    name_upper = str(facility_name).upper()
    
    # High confidence patterns
    high_conf = ['TEACHING HOSPITAL', 'GENERAL HOSPITAL', 'PRIMARY HEALTH', 'PHC']
    if not any(p in name_upper for p in high_conf):
        if level == 'Secondary' and 'HOSPITAL' in name_upper:
            confidence = 'medium'  # Generic hospital
        elif level == 'Primary' and not any(p in name_upper for p in ['HEALTH', 'CLINIC']):
            confidence = 'low'  # Default assignment
    
    return level, confidence
```

## Expected Accuracy
- **High confidence**: ~66.5% of facilities
- **Medium confidence**: ~16.3% of facilities  
- **Low confidence**: ~17.1% of facilities
- **Overall accuracy**: ~83% based on pattern analysis

## User Experience
1. **With level column**: Normal facility filtering works
2. **Without level column**: 
   - System attempts pattern-based detection
   - Shows confidence indicator
   - Allows "All facilities" as safe option
   - Optionally shows detected breakdown for verification

## Benefits
- Works with both TPR formats
- No hardcoding required
- Graceful degradation
- User transparency
- Future-proof for new patterns