#!/usr/bin/env python3
"""
Test the encoding fix works properly.
"""

import sys
sys.path.insert(0, '.')

from app.data_analysis_v3.core.encoding_handler import EncodingHandler
import pandas as pd

# Test the fix
print("Testing EncodingHandler fix for corrupted ≥ character")
print("=" * 60)

# Read with EncodingHandler
df = EncodingHandler.read_csv_with_encoding('www/adamawa_tpr_cleaned.csv')

# Check column 9 (index 8)
col9 = df.columns[8]
print(f"Column 9: '{col9}'")
print(f"Contains corrupted 'â‰¥': {'â‰¥' in col9}")
print(f"Contains correct '≥': {'≥' in col9}")
print()

# Check column 12 (index 11) - should also have the symbol
col12 = df.columns[11]
print(f"Column 12: '{col12}'")
print(f"Contains corrupted 'â‰¥': {'â‰¥' in col12}")
print(f"Contains correct '≥': {'≥' in col12}")
print()

# Check if we can access these columns properly
try:
    # Try to access a column with the fixed name
    if '≥' in col9:
        test_sum = df[col9].sum()
        print(f"✅ Successfully accessed column and computed sum: {test_sum}")
    else:
        print("❌ Column still has corrupted character!")
except Exception as e:
    print(f"❌ Error accessing column: {e}")

print()
print("Summary:")
print("-" * 40)
if all('≥' in col for col in [col9, col12] if 'tested by RDT' in col or 'tested by Microscopy' in col):
    print("✅ All ≥ symbols are correctly fixed!")
else:
    print("❌ Some columns still have corrupted encoding")
    
# Show all columns with special characters
print("\nColumns with special characters:")
for i, col in enumerate(df.columns):
    if any(char in col for char in ['≥', '<', 'â', '‰', '¥']):
        print(f"  {i}: {col}")