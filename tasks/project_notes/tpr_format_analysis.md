# TPR Format Analysis and Dynamic Implementation Plan

## 1. CRITICAL DISCOVERY: Two Different TPR Formats

### Format 1: Current NMEP Format (What system expects)
**File:** `/www/TPR data.xlsx`
- **Structure:** Multiple sheets (pivot, raw, tpr)
- **Key Sheet:** `raw` sheet with 89,046 rows
- **Location Columns:**
  - `State` → State name
  - `LGA` → Local Government Area
  - `Ward` → Ward name
  - `Health Faccility` → Facility name (note spelling)
  - `level` → Primary/Secondary/Tertiary
  - `ownership` → Public/Private

- **Testing Columns:**
  - `Persons presenting with fever & tested by RDT <5yrs`
  - `Persons tested positive for malaria by RDT <5yrs`
  - Similar columns for ≥5yrs and Pregnant Women
  - Microscopy columns follow same pattern

### Format 2: New User Format (What users will bring)
**File:** `/www/NMEP TPR and LLIN 2024_16072025.xlsx`
- **Structure:** Single sheet (`Sheet1`)
- **Rows:** 337,774 (much larger!)
- **Location Columns:**
  - `orgunitlevel2` → State (e.g., "ab Abia State")
  - `orgunitlevel3` → LGA
  - `orgunitlevel4` → Ward  
  - `orgunitlevel5` → Facility
  
- **Testing Columns:** SAME as Format 1 but with encoding variations:
  - `â‰¥5yrs` instead of `≥5yrs` (character encoding issue)
  
- **Additional Data:**
  - LLIN distribution columns
  - `PW who received LLIN`
  - `Children <5 yrs who received LLIN`

## 2. CURRENT CODE LIMITATIONS

### A. NMEPParser (`/app/tpr_module/data/nmep_parser.py`)
**Problems:**
1. **Hardcoded sheet detection:** Expects 'raw' sheet (line 78)
2. **Rigid column detection:** Looks for exact column names (lines 82-87)
3. **No fallback logic:** Fails if 'raw' sheet missing

### B. ColumnMapper (`/app/tpr_module/data/column_mapper.py`)
**Good:**
- Has mapping system for column variations
- Handles encoding variants (≥ vs â‰¥)

**Bad:**
- Doesn't map orgunitlevel columns
- No dynamic detection of hierarchy

### C. TPR Pipeline (`/app/tpr_module/core/tpr_pipeline.py`)
**Issues:**
- Expects specific column names after mapping
- No flexibility in hierarchy detection

## 3. PROPOSED SOLUTION: Dynamic TPR System

### Phase 1: Intelligent Format Detection
Create a new `DynamicTPRDetector` class that:
1. **Detects format type** (NMEP multi-sheet vs single-sheet)
2. **Identifies location hierarchy** automatically:
   - Look for patterns: State/LGA/Ward or orgunitlevel2/3/4/5
   - Use heuristics: unique value counts (States < LGAs < Wards < Facilities)
3. **Maps columns dynamically** using fuzzy matching

### Phase 2: Enhanced Column Mapping
Extend `ColumnMapper` to:
1. **Add orgunitlevel mappings:**
```python
'state': ['State', 'orgunitlevel2', 'org_unit_level_2', ...],
'lga': ['LGA', 'orgunitlevel3', 'org_unit_level_3', ...],
'ward': ['Ward', 'orgunitlevel4', 'org_unit_level_4', ...],
'facility': ['Health Faccility', 'orgunitlevel5', 'org_unit_level_5', ...]
```

2. **Smart hierarchy detection:**
   - Count unique values per column
   - Identify hierarchy by cardinality (fewer states than LGAs than wards)

3. **Encoding normalization:**
   - Handle UTF-8 encoding issues (â‰¥ → ≥)
   - Normalize special characters

### Phase 3: Flexible Parser
Create `UniversalTPRParser` that:
1. **Auto-detects sheet structure:**
   - Try 'raw' sheet first
   - Fall back to 'Sheet1' or first sheet
   - Use sheet with most rows

2. **Validates data quality:**
   - Check for required testing columns
   - Verify location hierarchy completeness
   - Handle missing values gracefully

3. **Preserves extra data:**
   - Keep LLIN columns if present
   - Store metadata about source format

### Phase 4: Pipeline Adaptation
Modify `TPRPipeline` to:
1. Use detected column names dynamically
2. Handle both formats transparently
3. Log format detection for debugging

## 4. IMPLEMENTATION STEPS

### Step 1: Create Format Detection System
**New File:** `/app/tpr_module/data/format_detector.py`
```python
class TPRFormatDetector:
    def detect_format(self, file_path: str) -> Dict:
        """Returns format type and column mappings"""
        
    def identify_hierarchy(self, df: pd.DataFrame) -> Dict:
        """Auto-detect location hierarchy columns"""
        
    def normalize_encoding(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fix encoding issues in column names"""
```

### Step 2: Enhance Column Mapper
**Update:** `/app/tpr_module/data/column_mapper.py`
- Add orgunitlevel mappings
- Add fuzzy matching for unknown columns
- Add hierarchy detection logic

### Step 3: Create Universal Parser
**New File:** `/app/tpr_module/data/universal_parser.py`
```python
class UniversalTPRParser:
    def __init__(self):
        self.format_detector = TPRFormatDetector()
        self.column_mapper = EnhancedColumnMapper()
        
    def parse(self, file_path: str) -> Dict:
        """Parse any TPR format intelligently"""
```

### Step 4: Update Integration Points
- Modify `tpr_conversation_manager.py` to use UniversalTPRParser
- Update `upload_detector.py` to handle both formats
- Ensure backward compatibility

## 5. TESTING REQUIREMENTS

1. **Test with both formats:**
   - Original NMEP format (multi-sheet)
   - New user format (single-sheet with orgunitlevel)

2. **Edge cases:**
   - Files with encoding issues
   - Missing columns
   - Mixed formats

3. **Performance:**
   - Large files (300K+ rows)
   - Format detection speed

## 6. BENEFITS OF THIS APPROACH

1. **Flexibility:** Handles current and future formats
2. **User-Friendly:** No need to pre-process files
3. **Maintainable:** Clear separation of concerns
4. **Extensible:** Easy to add new format support
5. **Robust:** Graceful handling of variations

## 7. RISK MITIGATION

1. **Backward Compatibility:** Keep original parser as fallback
2. **Validation:** Extensive checking before processing
3. **Logging:** Detailed logs for debugging
4. **User Feedback:** Clear error messages for unsupported formats