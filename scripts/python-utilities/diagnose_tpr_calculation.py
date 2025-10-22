#!/usr/bin/env python
"""
Diagnose why TPR calculation is returning 0.0%
"""

import pandas as pd
import sys
sys.path.insert(0, '.')

from app.core.tpr_utils import calculate_ward_tpr, fix_column_encoding

# Load the actual TPR file
file_path = "www/NMEP TPR and LLIN 2024_16072025.xlsx"

print("="*60)
print("TPR Calculation Diagnosis")
print("="*60)

# Load data
df = pd.read_excel(file_path, sheet_name=0)
print(f"\nData shape: {df.shape}")

# Fix encoding
df = fix_column_encoding(df)

# Show all columns
print("\nAll columns in the data:")
for i, col in enumerate(df.columns, 1):
    print(f"{i}. {col}")

# Check for test-related columns
print("\n" + "="*60)
print("Looking for test-related columns...")

# Find RDT columns
rdt_cols = [col for col in df.columns if 'rdt' in col.lower()]
print(f"\nRDT columns found ({len(rdt_cols)}):")
for col in rdt_cols[:5]:
    print(f"  - {col}")

# Find Microscopy columns
micro_cols = [col for col in df.columns if 'microscop' in col.lower()]
print(f"\nMicroscopy columns found ({len(micro_cols)}):")
for col in micro_cols[:5]:
    print(f"  - {col}")

# Find tested columns
tested_cols = [col for col in df.columns if 'tested' in col.lower() or 'presenting' in col.lower()]
print(f"\nTested columns found ({len(tested_cols)}):")
for col in tested_cols[:5]:
    print(f"  - {col}")

# Find positive columns
positive_cols = [col for col in df.columns if 'positive' in col.lower()]
print(f"\nPositive columns found ({len(positive_cols)}):")
for col in positive_cols[:5]:
    print(f"  - {col}")

# Find age-specific columns for U5
u5_cols = [col for col in df.columns if any(pattern in col.lower() for pattern in ['<5yrs', '<5 yrs', '<5', 'under5', 'u5', 'under 5'])]
print(f"\nUnder 5 columns found ({len(u5_cols)}):")
for col in u5_cols[:5]:
    print(f"  - {col}")

print("\n" + "="*60)
print("Testing TPR calculation for different scenarios...")

# Test 1: All ages, all facilities
print("\n1. All ages, all facilities:")
try:
    result = calculate_ward_tpr(df, age_group='all_ages', test_method='both', facility_level='all')
    print(f"  Result shape: {result.shape}")
    if not result.empty:
        print(f"  Average TPR: {result['TPR'].mean():.2f}%")
        print(f"  Non-zero TPR wards: {(result['TPR'] > 0).sum()}")
        print(f"  Total tested: {result['Total_Tested'].sum():,}")
        print(f"  Total positive: {result['Total_Positive'].sum():,}")
        # Show a sample
        if len(result) > 0:
            print("\n  Sample results:")
            print(result.head(3))
except Exception as e:
    print(f"  Error: {e}")

# Test 2: Under 5, primary facilities
print("\n2. Under 5, primary facilities:")
try:
    result = calculate_ward_tpr(df, age_group='u5', test_method='both', facility_level='primary')
    print(f"  Result shape: {result.shape}")
    if not result.empty:
        print(f"  Average TPR: {result['TPR'].mean():.2f}%")
        print(f"  Non-zero TPR wards: {(result['TPR'] > 0).sum()}")
        print(f"  Total tested: {result['Total_Tested'].sum():,}")
        print(f"  Total positive: {result['Total_Positive'].sum():,}")
except Exception as e:
    print(f"  Error: {e}")

# Check specific column patterns that might work
print("\n" + "="*60)
print("Checking specific column patterns...")

# Check if columns have specific patterns
for col in df.columns[:20]:  # Check first 20 columns
    col_lower = col.lower()
    if 'rdt' in col_lower and '<5yrs' in col_lower:
        print(f"\nFound U5 RDT column: {col}")
        non_zero = (df[col] > 0).sum()
        print(f"  Non-zero values: {non_zero}/{len(df)}")
        print(f"  Sum: {df[col].sum():,.0f}")