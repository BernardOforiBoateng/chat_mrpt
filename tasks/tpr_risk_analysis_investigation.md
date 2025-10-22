# TPR to Risk Analysis Workflow Investigation

## Executive Summary

Two critical issues were identified in the TPR to risk analysis workflow:

1. **TPR Map Color Issue**: All wards showing same purple color despite different TPR values
2. **Ward Name Mismatches**: 42-46 wards have mismatched names between TPR data and shapefile

## Issue 1: TPR Map Uniform Purple Color

### Root Cause
The TPR visualization code caps the color scale at 50% (`zmax=50` in line 115 of `tpr_visualization_service.py`), but 218 out of 226 wards (96.5%) have TPR values above 50%.

### Evidence
- TPR values range from 29.7% to 97.6%
- 218 wards have TPR > 50%
- Color scale: Green (0%) → Yellow (20%) → Orange (40%) → Red (60%) → Purple (100%)
- With `zmax=50`, all values above 50% are rendered as maximum purple

### Impact
- Map appears uniform purple, failing to show TPR variations
- Users cannot visually distinguish between 50% and 97.6% TPR
- Defeats the purpose of a choropleth map

## Issue 2: Ward Name Mismatches

### Summary
46 ward names in TPR data don't match the shapefile, causing:
- Missing data on maps (white spaces)
- Failed merges during visualization
- Incorrect risk analysis results

### Types of Mismatches Found

#### 1. Space vs Hyphen (7 wards)
- Shapefile: "Mayo Lope" → TPR: "Mayo-Lope"
- Shapefile: "Uki Tuki" → TPR: "Uki-Tuki"
- Shapefile: "Wuro Bokki" → TPR: "Wuro-Bokki"

#### 2. Slash vs Space/No Space (10+ wards)
- Shapefile: "Bazza Margi" → TPR: "Bazza/Margi"
- Shapefile: "Gang Fada" → TPR: "Gangfada"
- Shapefile: "Gudu Mboi" → TPR: "Gudu/Mboi"

#### 3. Roman Numerals (2 wards)
- Shapefile: "Girei 1" → TPR: "Girei I"
- Shapefile: "Girei 2" → TPR: "Girei II"

#### 4. Spelling Variations (15+ wards)
- Shapefile: "Betso" → TPR: "Besto"
- Shapefile: "Gabon" → TPR: "Gabun"
- Shapefile: "Dubange" → TPR: "Dubwange"
- Shapefile: "Hoserezum" → TPR: "Hosheri-Zum"

#### 5. Apostrophes/Special Characters
- Shapefile: "Gaanda" → TPR: "Ga'anda"

#### 6. Duplicate Ward Names with LGA Disambiguation
- TPR has: "Lamurde (Lamurde)" and "Lamurde (Mubi South)"
- Shapefile has: only "Lamurde"

### Data Quality Impact
- **TPR Map**: Missing 46 wards (20.4% of data)
- **Risk Analysis**: May be using incomplete data
- **ITN Planning**: Only 1 out of 224 wards matched population data

## Additional Findings

### Ward Count Consistency
- Shapefile: 226 total wards, 222 unique names
- TPR Data: 226 total wards, 226 unique names
- The 4 duplicate names in shapefile are likely disambiguated by LGA

### Merge Strategy Issues
From AWS logs:
- System detects duplicate ward names
- Attempts to use WardCode for matching
- But ward name mismatches prevent successful merges

## Recommendations for Demo

### Quick Fixes (for demo):
1. **TPR Map**: Change `zmax=50` to `zmax=100` to show full color range
2. **Ward Names**: Create a mapping table for common mismatches

### Long-term Solutions:
1. **Standardize Ward Names**: Use official gazette names
2. **Fuzzy Matching**: Implement similarity matching for ward names
3. **Dynamic Color Scaling**: Auto-adjust color scale based on data range
4. **Data Validation**: Add pre-upload validation for ward name consistency

## Impact on Demo
- TPR map will appear uniform purple, not showing variations
- Some wards will appear blank on maps
- ITN distribution will only work for 1 ward instead of all high-risk wards
- Risk analysis may be missing data for ~20% of wards