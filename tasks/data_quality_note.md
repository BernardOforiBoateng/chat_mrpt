# Data Quality Check - Correlation Issue

## Problem
When users run "check data quality", the system attempts to calculate correlations using `df.corr()` which fails with error:
```
could not convert string to float: 'Achika'
```

This happens because the correlation is being run on ALL columns including ward names and other string identifiers.

## Identifiers to Exclude
The following columns should be excluded from correlation analysis:
- X.1
- X
- WardName
- StateCode
- WardCode
- LGACode
- Urban
- Source
- Timestamp
- GlobalID
- AMAPCODE

## Solution Options

### Option 1: Remove Correlation from Data Quality Check
Simply don't include correlation matrix in the data quality check output.

### Option 2: Filter Numeric Columns Only
Use `df.select_dtypes(include=[np.number]).corr()` instead of `df.corr()`

### Option 3: Exclude Known Identifiers
Create a list of identifier columns and exclude them before correlation:
```python
identifier_cols = ['X.1', 'X', 'WardName', 'StateCode', 'WardCode', 'LGACode', 'Urban', 'Source', 'Timestamp', 'GlobalID', 'AMAPCODE']
numeric_cols = [col for col in df.columns if col not in identifier_cols and df[col].dtype in ['float64', 'int64']]
correlation_matrix = df[numeric_cols].corr()
```

## Recommendation
For now, **remove correlation from the data quality check** entirely. Users can still run correlation analysis separately if needed, but it shouldn't be part of the default data quality check to avoid errors.