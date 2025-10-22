#!/usr/bin/env python
"""
Debug why all_ages isn't working
"""

import pandas as pd
import sys
sys.path.insert(0, '.')

# Load the actual TPR file
file_path = "www/NMEP TPR and LLIN 2024_16072025.xlsx"
df = pd.read_excel(file_path, sheet_name=0)

print("="*60)
print("Debug all_ages column detection")
print("="*60)

# Simulate what the function does for all_ages
rdt_tested_cols = []
rdt_positive_cols = []
micro_tested_cols = []
micro_positive_cols = []

for col in df.columns:
    col_lower = col.lower()
    # RDT tested - include all age groups
    if 'rdt' in col_lower and ('presenting' in col_lower or 'tested' in col_lower):
        if 'positive' not in col_lower:  # Exclude positive columns
            rdt_tested_cols.append(col)
            print(f"RDT tested: {col}")
    # RDT positive - include all age groups
    elif 'rdt' in col_lower and 'positive' in col_lower:
        rdt_positive_cols.append(col)
        print(f"RDT positive: {col}")
    # Microscopy tested - include all age groups
    elif 'microscop' in col_lower and ('presenting' in col_lower or 'tested' in col_lower):
        if 'positive' not in col_lower:
            micro_tested_cols.append(col)
            print(f"Microscopy tested: {col}")
    # Microscopy positive - include all age groups
    elif 'microscop' in col_lower and 'positive' in col_lower:
        micro_positive_cols.append(col)
        print(f"Microscopy positive: {col}")

print(f"\n Summary:")
print(f"RDT tested columns: {len(rdt_tested_cols)}")
print(f"RDT positive columns: {len(rdt_positive_cols)}")
print(f"Microscopy tested columns: {len(micro_tested_cols)}")
print(f"Microscopy positive columns: {len(micro_positive_cols)}")

has_rdt_data = len(rdt_tested_cols) > 0 and len(rdt_positive_cols) > 0
has_micro_data = len(micro_tested_cols) > 0 and len(micro_positive_cols) > 0

print(f"\nhas_rdt_data: {has_rdt_data}")
print(f"has_micro_data: {has_micro_data}")

if has_rdt_data or has_micro_data:
    print("\n✅ Should work for all_ages!")
    
    # Test actual calculation
    print("\nTesting with ward/LGA grouping...")
    
    # Check if we have the right columns
    if 'orgunitlevel4' in df.columns and 'orgunitlevel3' in df.columns:
        # Group by ward and LGA
        grouped = df.groupby(['orgunitlevel4', 'orgunitlevel3'], dropna=False)
        
        total_groups = len(grouped)
        print(f"Total ward/LGA groups: {total_groups}")
        
        # Calculate for first few groups
        results = []
        for i, ((ward, lga), group) in enumerate(grouped):
            if i >= 5:  # Just check first 5
                break
                
            rdt_tested = sum(group[col].fillna(0).sum() for col in rdt_tested_cols if col in group.columns)
            rdt_positive = sum(group[col].fillna(0).sum() for col in rdt_positive_cols if col in group.columns)
            
            if rdt_tested > 0:
                tpr = (rdt_positive / rdt_tested) * 100
                print(f"  {ward[:30]}: {rdt_tested:,.0f} tested, {rdt_positive:,.0f} positive, TPR={tpr:.1f}%")
                results.append(tpr)
        
        if results:
            print(f"\nAverage TPR for sample: {sum(results)/len(results):.1f}%")
else:
    print("\n❌ Would fail for all_ages - no complete test data")
