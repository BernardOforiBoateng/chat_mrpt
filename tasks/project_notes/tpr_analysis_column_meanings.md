# TPR Dataset Column Meanings

## Dataset: NMEP TPR and LLIN 2024_16072025.xlsx

### Column Structure and Meanings

#### 1. Geographic/Organizational Columns (DHIS2 Format)
- **orgunitlevel2**: State name (37 states in Nigeria)
- **orgunitlevel3**: Local Government Area (LGA) name (773 LGAs)
- **orgunitlevel4**: Ward name (8,433 wards)
- **orgunitlevel5**: Health Facility name (27,929 facilities)

#### 2. Temporal Columns
- **periodname**: Reporting period in date format (e.g., "2025-01-24")
- **periodcode**: Period identifier code

#### 3. Testing Data Columns (12 columns)

##### RDT Testing Columns (6 columns)
- **Persons presenting with fever & tested by RDT <5yrs**: Number of children under 5 years who presented with fever and were tested using Rapid Diagnostic Test
- **Persons presenting with fever & tested by RDT ≥5yrs (excl PW)**: Number of people 5 years and older (excluding pregnant women) tested by RDT
- **Persons presenting with fever & tested by RDT Preg Women (PW)**: Number of pregnant women tested by RDT
- **Persons tested positive for malaria by RDT <5yrs**: Number of under-5 children who tested positive
- **Persons tested positive for malaria by RDT ≥5yrs (excl PW)**: Number of 5+ year olds who tested positive
- **Persons tested positive for malaria by RDT Preg Women (PW)**: Number of pregnant women who tested positive

##### Microscopy Testing Columns (6 columns)
- **Persons presenting with fever and tested by Microscopy <5yrs**: Number of children under 5 tested by microscopy
- **Persons presenting with fever and tested by Microscopy ≥5yrs (excl PW)**: Number of 5+ year olds tested by microscopy
- **Persons presenting with fever and tested by Microscopy Preg Women (PW)**: Number of pregnant women tested by microscopy
- **Persons tested positive for malaria by Microscopy <5yrs**: Number of under-5 children who tested positive by microscopy
- **Persons tested positive for malaria by Microscopy ≥5yrs (excl PW)**: Number of 5+ year olds who tested positive by microscopy
- **Persons tested positive for malaria by Microscopy Preg Women (PW)**: Number of pregnant women who tested positive by microscopy

#### 4. Intervention Columns (2 columns)
- **PW who received LLIN**: Number of pregnant women who received Long-Lasting Insecticidal Nets
- **Children <5 yrs who received LLIN**: Number of children under 5 who received LLINs

### Data Characteristics

1. **Reporting Level**: Data is reported at facility level with aggregation possible up to ward, LGA, and state levels
2. **Time Granularity**: Monthly reporting periods
3. **Age Stratification**: Three distinct age groups for both testing methods
4. **Test Methods**: Two testing methods tracked separately (RDT and Microscopy)
5. **TPR Calculation**: Test Positivity Rate = (Positive tests / Total tests) × 100

### Key Observations

1. **Encoding Issue**: Some column names have encoding problems with special characters (≥ appears as â‰¥)
2. **Data Completeness**: RDT data generally more complete than microscopy data
3. **Total Row**: Last row appears to be totals/sums and needs to be excluded from analysis
4. **Period Coverage**: Data shows 2025 dates which may be a data entry issue or future projections

### Usage Notes for Analysis

1. Always check for and remove total/sum rows before analysis
2. Handle encoding issues in column names for consistent processing
3. Calculate TPR separately for each age group and test method
4. Consider data completeness when interpreting results
5. Facility-level data allows for various aggregation strategies