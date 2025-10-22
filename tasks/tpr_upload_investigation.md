# TPR Upload and Data Reading Investigation Report

## Executive Summary

The TPR module has significant hardcoding issues that prevent it from handling variations in NMEP data formats. The second file "NMEP TPR and LLIN 2024_16072025.xlsx" fails to upload because:
1. Sheet name is 'Sheet1' instead of hardcoded 'raw'
2. Column names use 'orgunitlevel' format instead of expected names
3. Missing critical columns (level, ownership)
4. Column mapper doesn't support the new naming convention

## Detailed Findings

### 1. Hardcoded Sheet Name Requirement

**Location**: `app/tpr_module/data/nmep_parser.py`, lines 78-79

```python
# Check for 'raw' sheet
if 'raw' not in excel_file.sheet_names:
    return False
```

**Issue**: The parser REQUIRES a sheet named 'raw' to identify a TPR file
- File 1 has: ['pivot', 'raw', 'tpr'] ✓
- File 2 has: ['Sheet1'] ✗

**Impact**: File 2 is immediately rejected despite containing valid TPR data

### 2. Column Name Incompatibility

**File 1 (Working)** uses standard NMEP column names:
- State
- LGA  
- Ward
- Health Faccility
- level
- ownership

**File 2 (Failing)** uses hierarchical organization unit names:
- orgunitlevel2 (State)
- orgunitlevel3 (LGA)
- orgunitlevel4 (Ward)
- orgunitlevel5 (Facility)
- Missing: level, ownership

### 3. Column Mapper Limitations

**Location**: `app/tpr_module/data/column_mapper.py`

The column mapper doesn't include mappings for:
- orgunitlevel2 → state
- orgunitlevel3 → lga
- orgunitlevel4 → ward
- orgunitlevel5 → facility

Current state mappings only include:
```python
'state': ['State', 'state', 'STATE', 'State Name']
```

### 4. Data Format Differences

**File 2 Data Sample**:
- orgunitlevel2: 'ab Abia State' (has 'ab' prefix like Adamawa's 'ad')
- orgunitlevel3: 'ab Ukwa West Local Government Area'
- orgunitlevel4: 'ab Oza-Ukwu Ward II'
- orgunitlevel5: 'ab ablight of God Maternity(Nnenne Maternity)'

The cleaning functions would work IF the columns were mapped correctly.

### 5. Missing Required Data

File 2 is missing:
- **Facility Level** (Primary/Secondary/Tertiary) - CRITICAL for filtering
- **Ownership** (Public/Private) - Used for analysis

These missing columns would cause issues even if the file was accepted.

## Hardcoding Locations

### 1. Sheet Name Detection
- **File**: `nmep_parser.py`
- **Line**: 78
- **Hardcoded Value**: 'raw'

### 2. Column Detection for TPR Identification  
- **File**: `nmep_parser.py`
- **Lines**: 83-88
- **Hardcoded Values**: Exact column names for RDT testing

### 3. Parse Process
- **File**: `nmep_parser.py`
- **Line**: 108
- **Hardcoded Value**: sheet_name='raw'

### 4. Facility Level Values
- **File**: `nmep_parser.py`
- **Lines**: 495-499
- **Hardcoded Values**: 'Primary', 'Secondary', 'Tertiary'

## Why File 2 Fails: Step-by-Step

1. **Detection Phase**:
   - `is_tpr_file()` checks for 'raw' sheet
   - File 2 has 'Sheet1' → Returns False
   - File rejected before any data is examined

2. **If Detection Was Fixed**:
   - Column mapper would fail to map orgunitlevel columns
   - Geographic columns would remain unmapped
   - Parser would fail to find required columns

3. **If Columns Were Mapped**:
   - Missing 'level' column would break facility filtering
   - TPR calculation would work for 'all facilities' only
   - Users couldn't filter by Primary/Secondary/Tertiary

## Impact Assessment

### Current System Limitations:
1. **Rigid Sheet Naming**: Only accepts 'raw' sheet
2. **Limited Column Flexibility**: Can't handle alternative naming schemes
3. **Incomplete Mappings**: Column mapper missing common variations
4. **No Fallback Logic**: Fails completely rather than degrading gracefully

### User Experience Impact:
- Valid TPR files are rejected
- No clear error messages about why files fail
- Users must rename sheets and columns manually
- Different NMEP export formats aren't supported

## Recommendations (Not Implemented)

1. **Sheet Detection**: Check all sheets for TPR columns, not just 'raw'
2. **Column Mapping**: Add orgunitlevel mappings to column mapper
3. **Graceful Degradation**: Allow analysis without level/ownership columns
4. **Error Messages**: Provide specific feedback about what's missing
5. **Format Detection**: Auto-detect different NMEP export formats

## File Format Comparison

### Working File Structure:
```
Sheet: 'raw'
Columns: State, LGA, Ward, Health Faccility, level, ownership
TPR Columns: Standard NMEP naming
Data: Includes all required fields
```

### Failing File Structure:  
```
Sheet: 'Sheet1'
Columns: orgunitlevel2-5 (no facility metadata)
TPR Columns: Standard NMEP naming (these work!)
Data: Missing level and ownership fields
```

## Conclusion

The TPR module is too rigid in its expectations. While it handles the original NMEP format well, it cannot adapt to variations in:
- Sheet naming
- Column naming conventions
- Missing non-critical columns

The second file contains valid TPR data but is rejected due to hardcoded assumptions about file structure. This significantly limits the module's usefulness with real-world data variations.