# TPR Data Quality Issue Report

## Date: January 2025
## System: ChatMRPT - TPR Module

## Issue Summary
Test Positivity Rate (TPR) calculations are producing mathematically impossible values exceeding 100%, indicating significant data quality issues in the source files.

## Technical Details

### Expected Behavior
- TPR Formula: `(Positive Cases / Tested Cases) × 100`
- Valid Range: 0% to 100%
- Logical Constraint: Positive cases cannot exceed tested cases

### Observed Problem
Multiple wards showing TPR values > 100%:

| Ward Name | Total Tested | Total Positive | Calculated TPR | Issue |
|-----------|--------------|----------------|----------------|-------|
| ngwa 1 | 218 | 1,230 | 564.2% | Positive cases 5.6x higher than tested |
| ntighauzor | - | - | 113.0% | Positive exceeds tested |
| umuikuisi-asa | - | - | 109.2% | Positive exceeds tested |

### Data Source
- File: `ab_Abia_State_TPR_LLIN_2024.xlsx`
- State: Abia State
- Data Type: NMEP TPR and LLIN 2024 data
- Affected Age Group: Under 5 years
- Test Methods: Both RDT and Microscopy

## Root Cause Analysis

### Possible Causes:
1. **Data Entry Errors**: 
   - Positive cases may have been entered incorrectly
   - Tested cases may have been underreported
   - Column values may have been swapped during data collection

2. **Aggregation Issues**:
   - Multiple reporting from same facilities
   - Double counting of positive cases
   - Missing or incomplete testing data

3. **Reporting Period Mismatch**:
   - Positive cases from longer period than tested cases
   - Cumulative vs. period-specific reporting confusion

## Impact
- Cannot accurately calculate TPR for affected wards
- Risk analysis and ITN distribution planning affected
- Data reliability concerns for decision-making

## Recommendations

### Immediate Actions:
1. **Data Validation**: Review source data collection processes at facility level
2. **Cross-verification**: Compare with previous months' data for anomalies
3. **Contact Data Sources**: Reach out to facilities in affected wards for clarification

### System Improvements:
1. **Add Data Validation Rules**:
   - Flag when positive > tested
   - Require confirmation for TPR > 50%
   - Log all anomalies for review

2. **Alternative Calculation Method** (as used in previous production system):
   - When TPR > 50%, use: `(Positive Cases / OPD Attendance) × 100`
   - Provides more realistic estimates for high-transmission areas
   - Should be clearly labeled as "adjusted TPR"

3. **Data Quality Indicators**:
   - Add confidence scores to TPR calculations
   - Show data completeness metrics
   - Flag wards with data quality issues

## Technical Implementation Notes

### Current System Behavior:
- System correctly calculates TPR based on provided data
- Flexible column detection working properly
- Issue is with source data quality, not calculation logic

### Files Involved:
- `app/core/tpr_utils.py` - TPR calculation logic
- `app/data_analysis_v3/tools/tpr_analysis_tool.py` - TPR analysis tool
- Source data: `www/tpr_data_by_state/ab_Abia_State_TPR_LLIN_2024.xlsx`

## Next Steps
1. Review this report with NMEP data management team
2. Establish data quality thresholds and validation rules
3. Implement alternative calculation methods for edge cases
4. Create data quality dashboard for ongoing monitoring

---
*Report generated from ChatMRPT system analysis*
*For technical questions, contact the development team*