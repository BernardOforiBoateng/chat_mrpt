# TPR Calculation Logic - Production Implementation

## Overview
The production TPR calculator implements sophisticated logic that handles different scenarios based on data availability and aggregation level. This document captures the exact logic used in production for accurate reimplementation.

## Core Calculation Methods

### 1. Standard TPR Calculation

The standard TPR calculation uses different approaches based on the aggregation level:

#### A. All Ages Aggregation
When calculating TPR across all age groups combined:

```
1. Sum all RDT data across facilities:
   - rdt_tested_total = SUM(all facilities' RDT tested for u5, o5, pw)
   - rdt_positive_total = SUM(all facilities' RDT positive for u5, o5, pw)

2. Sum all Microscopy data across facilities:
   - micro_tested_total = SUM(all facilities' Microscopy tested for u5, o5, pw)
   - micro_positive_total = SUM(all facilities' Microscopy positive for u5, o5, pw)

3. Calculate TPR for each method:
   - rdt_tpr = (rdt_positive_total / rdt_tested_total) × 100
   - micro_tpr = (micro_positive_total / micro_tested_total) × 100

4. Use the maximum TPR:
   - final_tpr = max(rdt_tpr, micro_tpr)
```

**Rationale**: This approach gives the most accurate picture when combining age groups, as it preserves the integrity of each testing method's results before comparison.

#### B. Specific Age Group Calculation
When calculating TPR for a specific age group (u5, o5, or pw):

```
1. For each facility:
   - tested = max(facility.rdt_tested, facility.micro_tested)
   - positive = max(facility.rdt_positive, facility.micro_positive)
   - Add to totals: total_tested += tested, total_positive += positive

2. Calculate ward-level TPR:
   - ward_tpr = (total_positive / total_tested) × 100
```

**Rationale**: This facility-level max approach handles cases where facilities might only use one testing method, ensuring we capture all testing activity.

### 2. Alternative TPR Calculation (Urban High-Burden Areas)

For urban areas with TPR > 50%, an alternative calculation is used:

```
TPR_alternative = (Total Positive Cases / Total OPD Attendance) × 100
```

**Trigger Conditions**:
- Ward is classified as urban (>60% urban facilities)
- Standard TPR exceeds 50%
- OPD attendance data is available

**Rationale**: In high-transmission urban settings, using OPD attendance as denominator provides a more stable metric per WHO guidelines.

## Data Structure Requirements

### Required Columns for TPR Calculation

#### Testing Data Columns
- **RDT Testing**: 
  - `Persons presenting with fever & tested by RDT <5yrs`
  - `Persons presenting with fever & tested by RDT ≥5yrs (excl PW)`
  - `Persons presenting with fever & tested by RDT Preg Women (PW)`

- **RDT Positive**:
  - `Persons tested positive for malaria by RDT <5yrs`
  - `Persons tested positive for malaria by RDT ≥5yrs (excl PW)`
  - `Persons tested positive for malaria by RDT Preg Women (PW)`

- **Microscopy Testing**:
  - `Persons presenting with fever and tested by Microscopy <5yrs`
  - `Persons presenting with fever and tested by Microscopy ≥5yrs (excl PW)`
  - `Persons presenting with fever and tested by Microscopy Preg Women (PW)`

- **Microscopy Positive**:
  - `Persons tested positive for malaria by Microscopy <5yrs`
  - `Persons tested positive for malaria by Microscopy ≥5yrs (excl PW)`
  - `Persons tested positive for malaria by Microscopy Preg Women (PW)`

#### Supporting Data Columns
- **LLIN Distribution**:
  - `PW who received LLIN`
  - `Children <5 yrs who received LLIN`

- **Facility Information**:
  - `State`
  - `LGA`
  - `WardName`
  - `HealthFacility`
  - `FacilityLevel` (Primary/Secondary/Tertiary)

- **For Alternative Calculation**:
  - `Out-patient Attendance` or `General Attendance`

## Implementation Logic Flow

### Step 1: Data Validation
```python
def validate_tpr_data(df):
    required_patterns = ['RDT', 'Microscopy', 'tested', 'positive']
    missing = []
    
    for pattern in required_patterns:
        if not any(pattern in col for col in df.columns):
            missing.append(pattern)
    
    if missing:
        raise ValueError(f"Missing required data: {missing}")
    
    return True
```

### Step 2: Ward Grouping
```python
def group_by_ward(df):
    # Group by geographic hierarchy
    ward_groups = df.groupby(['State', 'LGA', 'WardName'])
    return ward_groups
```

### Step 3: Apply Calculation Logic
```python
def calculate_ward_tpr(ward_data, age_group='all'):
    if age_group == 'all':
        return calculate_all_ages_tpr(ward_data)
    else:
        return calculate_age_specific_tpr(ward_data, age_group)
```

### Step 4: Handle Edge Cases

#### Missing Data
- If RDT data missing: Use only Microscopy
- If Microscopy missing: Use only RDT
- If both missing for a facility: Exclude that facility
- If no data for entire ward: Return NaN with warning

#### Data Quality Checks
- **Logical Consistency**: Positive cases cannot exceed tested cases
- **Outlier Detection**: Flag TPR > 80% for review
- **Completeness Score**: Track % of facilities with data

## Aggregation Hierarchy

### Ward Level (Primary)
- Base unit for TPR calculation
- Aggregates all facilities within ward
- Produces single TPR value per ward

### LGA Level (Secondary)
- Weighted average of ward TPRs
- Weight by number of tests performed
- Not simple average to avoid bias

### State Level (Tertiary)
- Weighted average of LGA TPRs
- Include confidence intervals
- Report data completeness

## Special Considerations

### 1. Facility Level Stratification
When requested, TPR can be stratified by facility level:
- **Primary**: Community-level facilities
- **Secondary**: General hospitals
- **Tertiary**: Specialist/teaching hospitals

Different patterns expected:
- Primary: Lower TPR (early cases)
- Secondary/Tertiary: Higher TPR (referred severe cases)

### 2. Temporal Analysis
When time series data available:
- Group by month using `periodname` column
- Calculate monthly TPR trends
- Identify seasonal patterns

### 3. Data Completeness Thresholds
- **Acceptable**: >70% facilities reporting
- **Marginal**: 50-70% facilities reporting
- **Poor**: <50% facilities reporting

Flag wards with poor completeness for alternative data collection.

## Error Handling

### Common Issues and Solutions

1. **Column Name Variations**
   - Issue: Column names may have encoding issues (e.g., ≥ appears as â‰¥)
   - Solution: Flexible column matching using partial string matching

2. **Mixed Data Types**
   - Issue: Numeric columns may contain text values
   - Solution: Coerce to numeric, treating errors as NaN

3. **Zero Denominators**
   - Issue: No tests performed but positive cases reported
   - Solution: Flag as data quality issue, exclude from calculation

4. **Duplicate Facilities**
   - Issue: Same facility appears multiple times
   - Solution: Aggregate duplicates before ward-level calculation

## Confidence Intervals

For robust reporting, calculate 95% confidence intervals:

```python
def calculate_ci(positive, tested, confidence=0.95):
    from scipy import stats
    
    if tested == 0:
        return (0, 0)
    
    # Wilson score interval for proportions
    p = positive / tested
    z = stats.norm.ppf((1 + confidence) / 2)
    
    denominator = 1 + z**2 / tested
    center = (p + z**2 / (2 * tested)) / denominator
    spread = z * np.sqrt(p * (1 - p) / tested + z**2 / (4 * tested**2)) / denominator
    
    lower = max(0, (center - spread) * 100)
    upper = min(100, (center + spread) * 100)
    
    return (lower, upper)
```

## Output Format

### Standard TPR Result Structure
```json
{
  "ward_name": "Girei",
  "lga": "Girei",
  "state": "Adamawa",
  "tpr_value": 42.3,
  "confidence_interval": [38.1, 46.5],
  "calculation_method": "standard",
  "total_tested": 1250,
  "total_positive": 529,
  "rdt_tested": 950,
  "rdt_positive": 380,
  "microscopy_tested": 300,
  "microscopy_positive": 149,
  "facility_count": 12,
  "data_completeness": 85.0,
  "facility_level_breakdown": {
    "primary": {"tpr": 38.2, "facilities": 8},
    "secondary": {"tpr": 51.5, "facilities": 3},
    "tertiary": {"tpr": 62.0, "facilities": 1}
  }
}
```

## Best Practices

1. **Always validate data before calculation**
2. **Log all calculation steps for debugging**
3. **Preserve raw values alongside calculated metrics**
4. **Include metadata about calculation method used**
5. **Flag unusual patterns for manual review**
6. **Document any assumptions or adjustments made**
7. **Maintain audit trail of data transformations**

## Testing Checklist

- [ ] Test with complete data (all columns present)
- [ ] Test with RDT-only data
- [ ] Test with Microscopy-only data
- [ ] Test with missing age groups
- [ ] Test with zero denominators
- [ ] Test with single facility wards
- [ ] Test with urban high-TPR scenarios
- [ ] Test aggregation to LGA and State levels
- [ ] Verify confidence interval calculations
- [ ] Validate against known TPR values from production

---

*This document captures the production TPR calculation logic as implemented in app/tpr_module/core/tpr_calculator.py*
*Last verified: January 2025*