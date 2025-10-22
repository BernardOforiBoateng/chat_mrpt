# Thursday Urban Validation Checklist

## ✅ Completed Tasks
- [x] Literature review of 2-3 alternative urbanicity definitions
- [x] Identified control method (MODIS urban class from current system)
- [x] Implemented alternative methods:
  - NDBI (Normalized Difference Built-up Index) using Sentinel-2
  - GHSL (Global Human Settlement Layer) - UN standard
  - Night Lights (VIIRS) as urban proxy
- [x] Created GEE script comparing all methods
- [x] Script exports results identifying consistently rural wards

## 📋 Ready to Run
1. **GEE Script**: `gee_urban_validation_final_verified.js`
   - Compares 4 urban detection methods
   - Identifies wards consistently rural across ALL methods
   - These are wards that should NOT be urban-targeted

2. **Analysis Script**: `analyze_urban_validation.py`
   - Generates comprehensive report
   - Identifies suspicious rural/urban mismatches
   - Provides state-by-state breakdown

## 🎯 Key Deliverables for Thursday
1. **Validation Results CSV** showing:
   - Urban percentage from each method for all 9,410 Nigerian wards
   - Wards consistently classified as rural (<30% urban) by ALL methods
   - Mean urban percentage and classification

2. **Validation Report** containing:
   - Method comparison and agreement rates
   - List of consistently rural wards that shouldn't be urban-targeted
   - Delta State specific analysis (addressing the concern about swapped designations)
   - Recommendations for urban classification

3. **Key Finding**: 
   - Wards marked "consistently_rural = YES" are definitively rural
   - If any state selected these for urban interventions, indicates potential data issue

## 🚀 Next Steps (User Action Required)
1. [ ] Run `gee_urban_validation_final_verified.js` in Google Earth Engine
2. [ ] Export results to Google Drive
3. [ ] Download CSV when export completes
4. [ ] Run: `python analyze_urban_validation.py <downloaded_csv_path>`
5. [ ] Review generated report for Thursday presentation

## 📊 What This Validates
- **Research Question**: Are there wards incorrectly classified as urban/rural?
- **Method**: Compare multiple satellite-based urban detection methods
- **Output**: List of wards with consistent classification across all methods
- **Impact**: Prevents misallocation of urban-targeted malaria interventions