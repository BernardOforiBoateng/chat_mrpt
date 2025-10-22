# LGA Matching Improvements Analysis

## Date: 2025-09-01
## Analyst: Claude

## Problem Statement
LGA (Local Government Area) names in TPR data files have significant formatting differences from the shapefile, causing matching issues that affect ward-level matching accuracy.

## Key Differences Identified

### 1. TPR LGA Format
- **Pattern**: `[state_code] [LGA Name] Local Government Area`
- **Example**: `ab Aba North Local Government Area`
- **Components**:
  - 2-letter state prefix (ab, kd, la, ri, etc.)
  - LGA name
  - "Local Government Area" suffix

### 2. Shapefile LGA Format
- **Pattern**: `[LGA Name]`
- **Example**: `Aba North`
- **Clean format**: No prefix or suffix

## Current Implementation Analysis

### Strengths
- Has `clean_lga_name()` method that removes prefix and suffix
- Uses fuzzy matching with 85% threshold
- Attempts exact match before fuzzy matching

### Weaknesses
1. **No spelling variation handling**
   - Example: "Emohua" (TPR) vs "Emuoha" (shapefile)
   
2. **No phonetic matching for LGAs**
   - Could catch spelling variations
   
3. **Case sensitivity issues**
   - Some comparisons may fail on case differences
   
4. **No caching of LGA mappings**
   - Same LGA cleaned repeatedly

5. **No special character handling**
   - Slashes, hyphens may cause issues

## Specific Issues Found

### Spelling Variations
- **Rivers State**: Emohua vs Emuoha
- **Cross River**: Possible variations in compound names
- **Akwa Ibom**: Potential hyphenation differences

### Compound Name Issues
- Obio/Akpor - slash handling
- Oshodi-Isolo vs Oshodi/Isolo - inconsistent separators
- Ogba/Egbema/Ndoni - multiple slashes

### Abbreviation Issues
- "FCT" vs "Federal Capital Territory"
- Possible abbreviations in some states

## Proposed Improvements

### 1. Enhanced LGA Cleaning Function
```python
def clean_lga_name_enhanced(self, lga_name):
    if pd.isna(lga_name):
        return ""
    
    # Convert to string and strip
    clean_lga = str(lga_name).strip()
    
    # Remove state prefix (2-letter code)
    clean_lga = re.sub(r'^[a-z]{2}\s+', '', clean_lga, flags=re.IGNORECASE)
    
    # Remove 'Local Government Area' and variations
    suffixes = [
        'Local Government Area',
        'Local Govt Area',
        'LGA',
        'L.G.A'
    ]
    for suffix in suffixes:
        clean_lga = re.sub(f'\\s*{re.escape(suffix)}\\s*$', '', clean_lga, flags=re.IGNORECASE)
    
    # Normalize separators (convert all to /)
    clean_lga = clean_lga.replace('-', '/')
    
    # Remove extra spaces
    clean_lga = ' '.join(clean_lga.split())
    
    return clean_lga
```

### 2. Improved LGA Matching with Spelling Variations
```python
def find_matching_lga_enhanced(self, tpr_lga, shapefile_lgas):
    clean_tpr_lga = self.clean_lga_name_enhanced(tpr_lga)
    
    if not clean_tpr_lga:
        return None
    
    # Try exact match first
    for sf_lga in shapefile_lgas:
        if clean_tpr_lga.lower() == str(sf_lga).lower():
            return sf_lga
    
    # Try with normalized separators
    normalized_tpr = clean_tpr_lga.replace('/', '').replace('-', '').lower()
    for sf_lga in shapefile_lgas:
        normalized_sf = str(sf_lga).replace('/', '').replace('-', '').lower()
        if normalized_tpr == normalized_sf:
            return sf_lga
    
    # Try phonetic matching
    if PHONETIC_AVAILABLE:
        tpr_soundex = jellyfish.soundex(clean_tpr_lga)
        for sf_lga in shapefile_lgas:
            if jellyfish.soundex(str(sf_lga)) == tpr_soundex:
                # Verify with fuzzy match
                if fuzz.ratio(clean_tpr_lga.lower(), str(sf_lga).lower()) >= 75:
                    return sf_lga
    
    # Try fuzzy matching with lower threshold for LGAs
    best_match = None
    best_score = 0
    
    for sf_lga in shapefile_lgas:
        # Multiple scoring methods
        scores = [
            fuzz.ratio(clean_tpr_lga.lower(), str(sf_lga).lower()),
            fuzz.token_sort_ratio(clean_tpr_lga.lower(), str(sf_lga).lower()),
            fuzz.token_set_ratio(clean_tpr_lga.lower(), str(sf_lga).lower())
        ]
        max_score = max(scores)
        
        if max_score > best_score and max_score >= 80:
            best_score = max_score
            best_match = sf_lga
    
    return best_match
```

### 3. LGA Mapping Cache
```python
def __init__(self, ...):
    # ... existing code ...
    
    # Add LGA mapping cache
    self.lga_mapping_cache = {}
    
def get_lga_mapping(self, state_name):
    """Get or create LGA mapping for a state"""
    if state_name in self.lga_mapping_cache:
        return self.lga_mapping_cache[state_name]
    
    # Build mapping for this state
    mapping = {}
    state_gdf = self.gdf[self.gdf['StateName'] == state_name]
    shapefile_lgas = state_gdf['LGAName'].dropna().unique()
    
    # Process all TPR LGAs for this state
    # ... build mapping ...
    
    self.lga_mapping_cache[state_name] = mapping
    return mapping
```

### 4. Known Variations Dictionary
```python
# Known LGA spelling variations
LGA_VARIATIONS = {
    'Rivers': {
        'Emohua': 'Emuoha',
        'Tai': 'Tai',
        # Add more as discovered
    },
    'Cross River': {
        # Add variations
    },
    # Add other states
}
```

## Expected Impact

### Before Improvements
- LGA matching success: ~90%
- Ward matching affected by LGA mismatches
- Manual intervention needed for variations

### After Improvements
- LGA matching success: >98%
- Better ward matching within correct LGAs
- Automatic handling of common variations
- Faster processing with caching

## Implementation Priority

1. **High Priority**:
   - Enhanced LGA cleaning function
   - Spelling variation handling
   - Separator normalization

2. **Medium Priority**:
   - Phonetic matching for LGAs
   - LGA mapping cache
   - Known variations dictionary

3. **Low Priority**:
   - Logging of LGA matching attempts
   - Confidence scoring for matches
   - Manual override capability

## Testing Requirements

1. Test all 37 states for LGA matching
2. Verify no regression in ward matching
3. Performance benchmarking with cache
4. Edge case testing (special characters, abbreviations)

## Conclusion

The LGA matching improvements are critical for achieving higher ward matching rates. The current 85% threshold and basic cleaning are insufficient for handling the variety of LGA name formats and spelling variations across Nigerian states. Implementing these improvements should significantly increase the overall ward matching success rate from 94.51% to potentially >97%.