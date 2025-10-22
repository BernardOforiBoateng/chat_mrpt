# TPR Dynamic Implementation Plan

## Executive Summary
The current TPR system is rigid and only accepts NMEP format with specific sheets and columns. Users have different TPR formats that need to be supported. We need to make the system intelligent and dynamic.

## Key Differences Between Formats

| Aspect | Current Format | New User Format |
|--------|---------------|-----------------|
| **File Structure** | 3 sheets (pivot, raw, tpr) | 1 sheet (Sheet1) |
| **Rows** | ~89K | ~338K |
| **State Column** | `State` | `orgunitlevel2` |
| **LGA Column** | `LGA` | `orgunitlevel3` |
| **Ward Column** | `Ward` | `orgunitlevel4` |
| **Facility Column** | `Health Faccility` | `orgunitlevel5` |
| **State Format** | "Adamawa State" | "ad Adamawa State" |
| **Additional Data** | None | LLIN distribution |

## Implementation Components

### 1. Format Detection System (`format_detector.py`)
```python
class TPRFormatDetector:
    """Intelligent detection of TPR file formats"""
    
    KNOWN_FORMATS = {
        'nmep_standard': {
            'sheets': ['raw', 'pivot', 'tpr'],
            'key_columns': ['State', 'LGA', 'Ward'],
            'identifier': 'multi_sheet_nmep'
        },
        'nmep_unified': {
            'sheets': ['Sheet1'],
            'key_columns': ['orgunitlevel2', 'orgunitlevel3', 'orgunitlevel4'],
            'identifier': 'single_sheet_orgunits'
        }
    }
    
    def detect_format(self, file_path: str) -> Dict:
        # 1. Check sheet structure
        # 2. Analyze column patterns
        # 3. Return format type and mappings
        
    def detect_hierarchy_columns(self, df: pd.DataFrame) -> Dict:
        # Use cardinality to identify hierarchy
        # States: ~37 unique values
        # LGAs: ~774 unique values  
        # Wards: ~8,500 unique values
        # Facilities: ~30,000 unique values
```

### 2. Enhanced Column Mapper (`column_mapper.py` - UPDATE)
```python
# Add to COLUMN_MAPPINGS:
'state': [
    'State', 'state', 'STATE',
    'orgunitlevel2', 'org_unit_level_2', 'OrgUnitLevel2',
    'State Name', 'StateName'
],
'lga': [
    'LGA', 'lga', 'Local Government Area',
    'orgunitlevel3', 'org_unit_level_3', 'OrgUnitLevel3',
    'LGA Name', 'LGAName'
],
'ward': [
    'Ward', 'ward', 'WARD',
    'orgunitlevel4', 'org_unit_level_4', 'OrgUnitLevel4',
    'Ward Name', 'WardName'
],
'facility': [
    'Health Faccility', 'Health Facility',
    'orgunitlevel5', 'org_unit_level_5', 'OrgUnitLevel5',
    'Facility Name', 'FacilityName'
]
```

### 3. Universal Parser (`universal_parser.py` - NEW)
```python
class UniversalTPRParser:
    """Parse any TPR format intelligently"""
    
    def __init__(self):
        self.format_detector = TPRFormatDetector()
        self.column_mapper = ColumnMapper()
        self.nmep_parser = NMEPParser()  # Keep for backward compatibility
        
    def parse(self, file_path: str) -> Dict:
        # 1. Detect format
        format_info = self.format_detector.detect_format(file_path)
        
        # 2. Load appropriate sheet
        df = self.load_data(file_path, format_info)
        
        # 3. Normalize columns
        df = self.normalize_columns(df, format_info)
        
        # 4. Clean location names
        df = self.clean_location_names(df)
        
        # 5. Validate and return
        return self.package_results(df, format_info)
        
    def clean_location_names(self, df: pd.DataFrame) -> pd.DataFrame:
        # Handle "ad Adamawa State" -> "Adamawa State"
        if 'state' in df.columns:
            df['state'] = df['state'].str.replace(r'^[a-z]{2}\s+', '', regex=True)
        return df
```

### 4. Update Integration Points

#### A. `upload_detector.py` - UPDATE
```python
def detect_file_type(self, file_path: str) -> str:
    # Try universal parser first
    universal_parser = UniversalTPRParser()
    if universal_parser.can_parse(file_path):
        return 'tpr'
    
    # Fallback to original detection
    ...
```

#### B. `tpr_conversation_manager.py` - UPDATE
```python
def process_tpr_file(self, file_path: str) -> Dict:
    # Use universal parser
    parser = UniversalTPRParser()
    result = parser.parse(file_path)
    
    # Handle both old and new format results
    ...
```

#### C. `nmep_parser.py` - KEEP BUT MODIFY
```python
# Add method to NMEPParser:
def can_parse(self, file_path: str) -> bool:
    """Check if this parser can handle the file"""
    try:
        excel_file = pd.ExcelFile(file_path)
        return 'raw' in excel_file.sheet_names
    except:
        return False
```

## File Changes Required

### New Files to Create:
1. `/app/tpr_module/data/format_detector.py` - Format detection logic
2. `/app/tpr_module/data/universal_parser.py` - Universal parser

### Files to Modify:
1. `/app/tpr_module/data/column_mapper.py` - Add orgunitlevel mappings
2. `/app/tpr_module/data/nmep_parser.py` - Add can_parse method
3. `/app/tpr_module/integration/upload_detector.py` - Use universal parser
4. `/app/tpr_module/core/tpr_conversation_manager.py` - Use universal parser
5. `/app/tpr_module/core/tpr_pipeline.py` - Handle dynamic columns

## Testing Strategy

### Test Cases:
1. **Original Format:** TPR data.xlsx with raw/pivot/tpr sheets
2. **New Format:** NMEP TPR and LLIN 2024_16072025.xlsx with Sheet1
3. **Mixed Encoding:** Files with â‰¥ vs ≥ characters
4. **Missing Columns:** Files with partial data
5. **Large Files:** 300K+ row files

### Validation Points:
- Correct state/LGA/ward detection
- Proper column mapping
- Data integrity after parsing
- Performance with large files

## Rollout Plan

### Phase 1: Detection & Mapping (Week 1)
- Create format_detector.py
- Update column_mapper.py
- Test with both formats

### Phase 2: Universal Parser (Week 2)
- Create universal_parser.py
- Integrate with existing code
- Maintain backward compatibility

### Phase 3: Testing & Refinement (Week 3)
- Test with real user data
- Handle edge cases
- Performance optimization

### Phase 4: Documentation & Deployment (Week 4)
- Update user documentation
- Deploy to staging
- Monitor and fix issues

## Success Metrics

1. **Compatibility:** System accepts both formats without errors
2. **Accuracy:** Correct parsing of all location hierarchies
3. **Performance:** <5 seconds for 300K row files
4. **User Experience:** No manual pre-processing required
5. **Maintainability:** Clear code structure for future formats

## Risk Mitigation

1. **Keep Original Parser:** Don't delete NMEPParser, use as fallback
2. **Extensive Logging:** Log format detection decisions
3. **Validation:** Verify parsed data before processing
4. **User Feedback:** Clear messages about detected format
5. **Gradual Rollout:** Test in staging before production