#!/usr/bin/env python
"""
Test script to verify TPR calculation fix works with actual adamawa_tpr_cleaned.csv data
"""

import sys
import os
sys.path.insert(0, '.')

import pandas as pd
from app.core.tpr_utils import calculate_ward_tpr

def test_with_actual_data():
    """Test with actual adamawa_tpr_cleaned.csv data."""
    
    print("="*60)
    print("TESTING TPR CALCULATION WITH ACTUAL DATA")
    print("="*60)
    
    # Load actual data
    data_file = 'www/adamawa_tpr_cleaned.csv'
    if not os.path.exists(data_file):
        print(f"❌ Data file not found: {data_file}")
        return
    
    print(f"\n📁 Loading data from: {data_file}")
    df = pd.read_csv(data_file)
    print(f"✅ Loaded {len(df)} rows, {len(df.columns)} columns")
    
    # Show sample columns
    test_cols = [col for col in df.columns if any(
        keyword in col.lower() for keyword in ['test', 'rdt', 'microscop', 'fever', 'positive']
    )]
    print(f"\n📊 Sample test-related columns ({len(test_cols)} total):")
    for col in test_cols[:5]:
        print(f"  - {col}")
    
    # Test different configurations
    test_cases = [
        ('u5', 'rdt', 'primary', 'Under 5 with RDT at Primary'),
        ('u5', 'both', 'primary', 'Under 5 with Both methods at Primary'),
        ('all_ages', 'both', 'all', 'All Ages with Both methods at All facilities'),
        ('o5', 'rdt', 'primary', 'Over 5 with RDT at Primary')
    ]
    
    for age_group, test_method, facility_level, description in test_cases:
        print(f"\n🔬 Testing: {description}")
        print(f"   Parameters: age_group='{age_group}', test_method='{test_method}', facility_level='{facility_level}'")
        
        result = calculate_ward_tpr(df, age_group=age_group, test_method=test_method, facility_level=facility_level)
        
        if not result.empty:
            print(f"   ✅ SUCCESS: {len(result)} wards analyzed")
            print(f"      Total tested: {result['Total_Tested'].sum():,}")
            print(f"      Total positive: {result['Total_Positive'].sum():,}")
            print(f"      Mean TPR: {result['TPR'].mean():.2f}%")
            print(f"      Max TPR: {result['TPR'].max():.2f}%")
            
            # Show top 3 wards by TPR
            if len(result) > 0:
                top_wards = result.nlargest(3, 'TPR')[['WardName', 'LGA', 'TPR', 'Total_Tested']]
                print(f"      Top 3 wards by TPR:")
                for idx, row in top_wards.iterrows():
                    print(f"        - {row['WardName']} ({row['LGA']}): {row['TPR']:.2f}% ({row['Total_Tested']} tested)")
        else:
            print(f"   ❌ FAILED: No results returned")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

if __name__ == '__main__':
    test_with_actual_data()