#!/usr/bin/env python3
"""
Test TPR Detection with Adamawa State File
"""

import pandas as pd
import sys
import os

# Add app to path
sys.path.insert(0, '.')

# Import TPR utilities
from app.core.tpr_utils import (
    is_tpr_data, 
    calculate_ward_tpr,
    normalize_ward_name,
    extract_state_from_data,
    validate_tpr_data
)

def test_tpr_detection():
    """Test TPR detection with Adamawa state file"""
    
    print("=" * 60)
    print("TESTING TPR DETECTION")
    print("=" * 60)
    
    # Load Adamawa TPR file
    file_path = 'www/tpr_data_by_state/ad_Adamawa_State_TPR_LLIN_2024.xlsx'
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    print(f"✅ Loading file: {file_path}")
    
    try:
        df = pd.read_excel(file_path)
        print(f"✅ Loaded data with shape: {df.shape}")
        
        # Test TPR detection
        is_tpr, info = is_tpr_data(df)
        
        print(f"\n📊 TPR Detection Results:")
        print(f"  - Is TPR Data: {is_tpr}")
        print(f"  - Confidence: {info['confidence']:.2%}")
        print(f"  - Matched columns: {info['matched_columns']}")
        print(f"  - Has RDT: {info['has_rdt']}")
        print(f"  - Has Microscopy: {info['has_microscopy']}")
        print(f"  - Has Tested: {info['has_tested']}")
        print(f"  - Has Positive: {info['has_positive']}")
        
        # Test state extraction
        state = extract_state_from_data(df)
        print(f"\n🌍 Extracted State: {state}")
        
        # Test validation
        is_valid, errors = validate_tpr_data(df)
        print(f"\n✔️ Validation Result: {'Passed' if is_valid else 'Failed'}")
        if errors:
            print("  Errors:")
            for error in errors:
                print(f"    - {error}")
        
        # Show sample columns
        print(f"\n📋 Sample Columns (first 20):")
        for i, col in enumerate(df.columns[:20]):
            dtype = df[col].dtype
            nulls = df[col].isna().sum()
            print(f"  {i+1:2}. {col[:50]:<50} [{dtype}] ({nulls} nulls)")
        
        return is_tpr
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tpr_calculation():
    """Test TPR calculation with different options"""
    
    print("\n" + "=" * 60)
    print("TESTING TPR CALCULATION")
    print("=" * 60)
    
    file_path = 'www/tpr_data_by_state/ad_Adamawa_State_TPR_LLIN_2024.xlsx'
    
    try:
        df = pd.read_excel(file_path)
        
        # Test 1: All ages, both methods, all facilities (default)
        print("\n1️⃣ Test: All ages, both methods, all facilities")
        result1 = calculate_ward_tpr(df)
        if not result1.empty:
            print(f"✅ Calculated TPR for {len(result1)} wards")
            print(f"   Mean TPR: {result1['TPR'].mean():.2f}%")
            print(f"   Max TPR: {result1['TPR'].max():.2f}%")
            print(f"   Top 3 wards:")
            for _, row in result1.head(3).iterrows():
                print(f"     - {row['WardName']}: {row['TPR']:.1f}%")
        else:
            print("❌ No results returned")
        
        # Test 2: Under 5, RDT only
        print("\n2️⃣ Test: Under 5, RDT only")
        result2 = calculate_ward_tpr(df, age_group='u5', test_method='rdt')
        if not result2.empty:
            print(f"✅ Calculated TPR for {len(result2)} wards")
            print(f"   Mean TPR: {result2['TPR'].mean():.2f}%")
        else:
            print("⚠️ No results for U5/RDT (might not have data)")
        
        # Test 3: Pregnant women, microscopy
        print("\n3️⃣ Test: Pregnant women, microscopy only")
        result3 = calculate_ward_tpr(df, age_group='pw', test_method='microscopy')
        if not result3.empty:
            print(f"✅ Calculated TPR for {len(result3)} wards")
            print(f"   Mean TPR: {result3['TPR'].mean():.2f}%")
        else:
            print("⚠️ No results for PW/Microscopy (might not have data)")
        
        # Test 4: Facility level filtering
        print("\n4️⃣ Test: Primary facilities only")
        result4 = calculate_ward_tpr(df, facility_level='primary')
        if not result4.empty:
            print(f"✅ Calculated TPR for {len(result4)} wards")
        else:
            print("⚠️ No results for primary facilities (might not have facility column)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in calculation: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ward_name_normalization():
    """Test ward name normalization"""
    
    print("\n" + "=" * 60)
    print("TESTING WARD NAME NORMALIZATION")
    print("=" * 60)
    
    test_cases = [
        ("ad Girei Ward", "girei"),
        ("Girei", "girei"),
        ("kw Ilorin East Ward", "ilorin east"),
        ("os Ife North", "ife north"),
        ("  Shelleng Ward  ", "shelleng"),
        ("YOLA NORTH", "yola north")
    ]
    
    all_passed = True
    for input_name, expected in test_cases:
        result = normalize_ward_name(input_name)
        passed = result == expected
        all_passed = all_passed and passed
        
        status = "✅" if passed else "❌"
        print(f"{status} '{input_name}' → '{result}' (expected: '{expected}')")
    
    return all_passed


if __name__ == "__main__":
    print("🚀 Starting TPR Tests\n")
    
    # Run tests
    detection_passed = test_tpr_detection()
    calculation_passed = test_tpr_calculation()
    normalization_passed = test_ward_name_normalization()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"TPR Detection: {'✅ PASSED' if detection_passed else '❌ FAILED'}")
    print(f"TPR Calculation: {'✅ PASSED' if calculation_passed else '❌ FAILED'}")
    print(f"Ward Normalization: {'✅ PASSED' if normalization_passed else '❌ FAILED'}")
    
    all_passed = detection_passed and calculation_passed and normalization_passed
    
    print("\n" + ("✅ ALL TESTS PASSED!" if all_passed else "❌ SOME TESTS FAILED"))
    
    sys.exit(0 if all_passed else 1)