# TPR Dynamic System - Summary & Next Steps

## 🎯 THE PROBLEM
ChatMRPT currently only accepts one rigid TPR format (NMEP with raw/pivot/tpr sheets). Users have different formats that are being rejected.

## 🔍 KEY FINDINGS

### What's Different:
1. **Sheet Structure:**
   - Old: 3 sheets (raw, pivot, tpr)
   - New: 1 sheet (Sheet1)

2. **Location Columns:**
   - Old: State, LGA, Ward, Health Faccility
   - New: orgunitlevel2, orgunitlevel3, orgunitlevel4, orgunitlevel5

3. **State Name Format:**
   - Old: "Adamawa State"
   - New: "ad Adamawa State" (has 2-letter prefix)

### What's the Same:
✅ **All testing columns are identical!**
- RDT tested/positive columns
- Microscopy tested/positive columns
- Age groups (<5, ≥5, Pregnant Women)

## 💡 SOLUTION APPROACH

### Core Strategy: "Smart Detection, Flexible Parsing"

1. **Auto-detect format type** by checking:
   - Number of sheets
   - Column name patterns
   - Data structure

2. **Map columns dynamically:**
   - State ← State OR orgunitlevel2
   - LGA ← LGA OR orgunitlevel3
   - Ward ← Ward OR orgunitlevel4
   - Facility ← Health Faccility OR orgunitlevel5

3. **Clean data intelligently:**
   - Remove state prefixes ("ad " → "")
   - Fix encoding issues (â‰¥ → ≥)
   - Standardize names

## 📝 IMPLEMENTATION CHECKLIST

### Phase 1: Core Components (Priority HIGH)
- [ ] Create `format_detector.py` - Detect which TPR format
- [ ] Create `universal_parser.py` - Parse any format
- [ ] Update `column_mapper.py` - Add orgunitlevel mappings
- [ ] Test with both sample files

### Phase 2: Integration (Priority HIGH)
- [ ] Update `upload_detector.py` - Use universal parser
- [ ] Update `tpr_conversation_manager.py` - Handle both formats
- [ ] Update `tpr_pipeline.py` - Work with dynamic columns
- [ ] Maintain backward compatibility

### Phase 3: Robustness (Priority MEDIUM)
- [ ] Add encoding normalization
- [ ] Handle missing columns gracefully
- [ ] Add detailed logging
- [ ] Create user-friendly error messages

### Phase 4: Testing (Priority HIGH)
- [ ] Test with original format (TPR data.xlsx)
- [ ] Test with new format (NMEP TPR and LLIN 2024_16072025.xlsx)
- [ ] Test with large files (300K+ rows)
- [ ] Test error handling

## 🚀 QUICK WINS

These changes will have immediate impact:

1. **Add orgunitlevel mappings to column_mapper.py:**
```python
'state': [..., 'orgunitlevel2', 'org_unit_level_2'],
'lga': [..., 'orgunitlevel3', 'org_unit_level_3'],
'ward': [..., 'orgunitlevel4', 'org_unit_level_4'],
```

2. **Make sheet detection flexible in nmep_parser.py:**
```python
# Instead of requiring 'raw' sheet
sheets = excel_file.sheet_names
data_sheet = 'raw' if 'raw' in sheets else sheets[0]
```

3. **Clean state names in pipeline:**
```python
# Remove prefixes like "ad "
df['state'] = df['state'].str.replace(r'^[a-z]{2}\s+', '', regex=True)
```

## ⚠️ CRITICAL CONSIDERATIONS

1. **Don't break existing functionality** - Keep old parser as fallback
2. **Performance matters** - 338K rows must process quickly
3. **Clear user feedback** - Tell users which format was detected
4. **Logging is essential** - Track format detection decisions

## 📊 SUCCESS METRICS

1. ✅ Both TPR formats accepted without errors
2. ✅ Processing time <5 seconds for 300K rows
3. ✅ No manual file pre-processing required
4. ✅ Clear error messages for unsupported formats
5. ✅ All existing features still work

## 🎬 NEXT IMMEDIATE STEPS

1. **Create format_detector.py** with basic detection logic
2. **Test detection with both sample files**
3. **Update column_mapper.py** with new mappings
4. **Create universal_parser.py** combining both approaches
5. **Test end-to-end with real workflow

## 📅 TIMELINE ESTIMATE

- **Week 1:** Core detection and parsing (format_detector, universal_parser)
- **Week 2:** Integration and testing
- **Week 3:** Edge cases and optimization
- **Week 4:** Documentation and deployment

## 💬 KEY MESSAGE

This change will make ChatMRPT **truly user-friendly** by accepting TPR data "as-is" from different states without requiring users to reformat their files. This is a **major improvement** in usability!