#!/usr/bin/env python3
"""
Test to understand the encoding issue with column names.
"""

import pandas as pd
import sys
sys.path.insert(0, '.')

# Test 1: Read the file directly with pandas
print("Test 1: Direct pandas read")
print("=" * 60)
df1 = pd.read_csv('www/adamawa_tpr_cleaned.csv')
print(f"Column 9: '{df1.columns[8]}'")
print(f"Column 9 bytes: {df1.columns[8].encode('utf-8')}")
print(f"Contains â‰¥: {' â‰¥' in df1.columns[8]}")
print(f"Contains ≥: {'≥' in df1.columns[8]}")
print()

# Test 2: Read with EncodingHandler (skipped - chardet not installed)
print("Test 2: EncodingHandler read (SKIPPED - chardet not installed)")
print("=" * 60)
# from app.data_analysis_v3.core.encoding_handler import EncodingHandler
# df2 = EncodingHandler.read_csv_with_encoding('www/adamawa_tpr_cleaned.csv')
# print(f"Column 9: '{df2.columns[8]}'")
# print(f"Column 9 bytes: {df2.columns[8].encode('utf-8')}")
# print(f"Contains â‰¥: {' â‰¥' in df2.columns[8]}")
# print(f"Contains ≥: {'≥' in df2.columns[8]}")
print()

# Test 3: Check what the actual character is
print("Test 3: Character analysis")
print("=" * 60)
col = df1.columns[8]
# Find the special character position
for i, char in enumerate(col):
    if ord(char) > 127:  # Non-ASCII character
        print(f"Position {i}: '{char}' (Unicode: U+{ord(char):04X}, UTF-8: {char.encode('utf-8')})")

print()

# Test 4: Try the fix manually
print("Test 4: Manual fix")
print("=" * 60)
test_col = df1.columns[8]
fixed_col = test_col.replace('â‰¥', '≥')
print(f"Original: '{test_col}'")
print(f"After fix: '{fixed_col}'")
print(f"Changed? {test_col != fixed_col}")

# The actual bytes sequence we're getting
import codecs
corrupted_seq = b'\xe2\x80\x89\xe2\x89\xa5'  # This is what â‰¥ looks like in UTF-8
try:
    decoded = corrupted_seq.decode('utf-8')
    print(f"\nCorrupted sequence decodes to: '{decoded}'")
    print(f"This matches our column? {decoded in test_col}")
except:
    pass

# Check what we actually have
actual_bytes = test_col.encode('utf-8')
print(f"\nActual bytes in column: {actual_bytes[40:50]}")  # Around where the symbol should be