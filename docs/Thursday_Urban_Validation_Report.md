# Urban Validation Report for Thursday Meeting
**Date Generated**: September 3, 2025  
**Total Wards Analyzed**: 9,410 Nigerian wards

---

## Executive Summary

The urban validation analysis compared 4 satellite-based urban detection methods across all Nigerian wards to identify areas that are consistently classified as rural. This validation addresses concerns about potential misclassification of rural areas as urban in intervention targeting.

### Key Finding
Only **102 wards (1.1%)** were consistently classified as rural (<30% urban) by ALL four satellite methods. These wards should definitively NOT be selected for urban-targeted interventions.

---

## Methodology

### Methods Compared:
1. **Control (HLS NDBI)**: Current ChatMRPT method using NASA HLS
2. **NDBI Sentinel-2**: Normalized Difference Built-up Index (Zha et al. 2003)
3. **GHSL**: Global Human Settlement Layer (UN standard)
4. **EBBI**: Enhanced Built-Up and Bareness Index (As-syakur et al. 2012)

### Classification Thresholds:
- **Urban**: >50% mean urban percentage
- **Peri-urban**: 30-50% mean urban percentage
- **Rural**: <30% mean urban percentage
- **Consistently Rural**: <30% across ALL 4 methods

---

## National Results

### Classification Distribution
| Category | Wards | Percentage |
|----------|-------|------------|
| Urban | 1,081 | 11.5% |
| Peri-urban | 5,219 | 55.5% |
| Rural | 3,110 | 33.0% |
| **Consistently Rural** | **102** | **1.1%** |

### Method Comparison
| Method | Mean Urban % |
|--------|--------------|
| Control (HLS NDBI) | 10.3% |
| NDBI Sentinel-2 | 51.4% |
| GHSL | 29.6% |
| EBBI | 49.5% |

**Note**: The control method (HLS NDBI) shows significantly lower urban percentages than alternative methods, suggesting it may be too conservative.

---

## Delta State Analysis (State of Concern)

### Delta State Overview
- **Total wards**: 267
- **Urban wards**: 15 (5.6%)
- **Peri-urban wards**: 69 (25.8%)
- **Rural wards**: 183 (68.5%)
- **Consistently rural**: 1 ward (0.4%)

### Key Findings for Delta:
1. **Only 1 ward** (Egodor in Burutu LGA) is consistently rural across all methods
2. **No suspicious mismatches**: All wards marked "Urban=Yes" have >30% satellite urban
3. **Average urban percentages**:
   - Wards marked "Urban=Yes": 49.6% satellite urban
   - Wards marked "Urban=No": 29.1% satellite urban

### Validation Result
✅ **Delta State's urban/rural classifications appear reasonable** based on satellite analysis. No evidence of systematic misclassification was found.

---

## States with Highest Rural Consistency

| State | Consistently Rural Wards | Total Wards | Percentage |
|-------|-------------------------|-------------|------------|
| Ebonyi | 23 | 235 | 9.8% |
| Imo | 28 | 376 | 7.4% |
| Enugu | 20 | 280 | 7.1% |
| Abia | 17 | 267 | 6.4% |
| Plateau | 4 | 325 | 1.2% |

---

## Critical Recommendations

### For Thursday Meeting:

1. **Validation Approach Works**: The multi-method comparison successfully identifies truly rural wards

2. **Delta State Concern**: 
   - No evidence of swapped rural/urban designations found
   - Delta's classifications align with satellite measurements
   - Only 1 ward is definitively rural by all methods

3. **Method Reliability**:
   - GHSL (UN standard) appears most balanced
   - Current HLS NDBI method may be too conservative
   - Consider adopting GHSL as primary method

4. **Action Items**:
   - Review the 102 consistently rural wards nationwide
   - If any were selected for urban interventions, flag for review
   - Consider updating urban percentage thresholds

---

## Technical Notes

### Data Quality
- All 9,410 wards successfully processed
- No missing data issues
- Methods showed varying agreement levels

### Method Agreement
- Control method (HLS NDBI) consistently shows lower urban values
- NDBI Sentinel-2 and EBBI show similar patterns
- GHSL provides middle-ground estimates

### Limitations
- Seasonal variations not captured (single year used)
- Cloud cover may affect some optical methods
- Resolution differences between methods (100m standardized)

---

## Conclusion

The validation successfully demonstrates that:
1. Multi-method satellite validation can identify truly rural wards
2. Delta State's classifications are reasonable (no systematic issues found)
3. Only 102 wards nationwide are definitively rural by all measures
4. These 102 wards should NOT receive urban-targeted interventions

**The concern about swapped rural/urban designations in Delta State is not supported by the satellite evidence.**