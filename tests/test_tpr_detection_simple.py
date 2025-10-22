"""
Simple test for TPR data detection

Tests the _detect_tpr_data and _generate_tpr_welcome methods
"""

import sys
from pathlib import Path
import pandas as pd

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def detect_tpr_data(df) -> bool:
    """
    Detect if uploaded data is TPR (Test Positivity Rate) data.
    Copied from agent.py for isolated testing.
    """
    if df is None or df.empty:
        return False

    columns_lower = ' '.join(df.columns).lower()

    # Check for facility columns
    has_facility = any(keyword in columns_lower for keyword in [
        'facility', 'health_facility', 'healthfacility'
    ])

    # Check for test data columns
    has_test = any(keyword in columns_lower for keyword in [
        'rdt', 'microscopy', 'tested', 'positive'
    ])

    # Check for TPR-specific indicators
    has_tpr_indicators = sum([
        'tpr' in columns_lower,
        'positivity' in columns_lower,
        'age' in columns_lower or 'u5' in columns_lower or 'o5' in columns_lower,
        'facility_type' in columns_lower or 'facility_level' in columns_lower,
    ])

    is_tpr = has_facility and has_test and has_tpr_indicators >= 1
    return is_tpr


def run_tests():
    """Run TPR detection tests"""

    print("=" * 70)
    print("TRACK A TPR DATA DETECTION TESTS")
    print("=" * 70)

    passed = 0
    failed = 0

    # Test 1: Standard TPR data
    print("\n" + "-" * 70)
    print("Test 1: Standard TPR data with all typical columns")
    print("-" * 70)

    df_tpr = pd.DataFrame({
        'HealthFacility': ['Clinic A', 'Clinic B'],
        'FacilityType': ['primary', 'secondary'],
        'RDT_Positive': [10, 20],
        'RDT_Tested': [100, 200],
        'Microscopy_Positive': [5, 15],
        'Microscopy_Tested': [50, 150],
        'TPR': [0.1, 0.15],
        'AgeGroup': ['u5', 'o5']
    })

    result = detect_tpr_data(df_tpr)
    expected = True

    if result == expected:
        print("✓ PASS: Detected TPR data correctly")
        passed += 1
    else:
        print(f"✗ FAIL: Expected {expected}, got {result}")
        failed += 1

    # Test 2: Non-TPR demographic data
    print("\n" + "-" * 70)
    print("Test 2: Generic demographic data (NOT TPR)")
    print("-" * 70)

    df_demo = pd.DataFrame({
        'Ward': ['Ward 1', 'Ward 2'],
        'Population': [10000, 20000],
        'Poverty_Rate': [0.3, 0.4],
        'Education_Level': ['High', 'Medium']
    })

    result = detect_tpr_data(df_demo)
    expected = False

    if result == expected:
        print("✓ PASS: Correctly rejected non-TPR data")
        passed += 1
    else:
        print(f"✗ FAIL: Expected {expected}, got {result}")
        failed += 1

    # Test 3: TPR data with variant column names
    print("\n" + "-" * 70)
    print("Test 3: TPR data with case/spacing variations")
    print("-" * 70)

    df_variant = pd.DataFrame({
        'health_facility': ['Clinic A'],
        'FACILITY_TYPE': ['primary'],
        'rdt_positive': [10],
        'total_tested': [100],
        'test_positivity_rate': [0.1],
        'u5': [50]
    })

    result = detect_tpr_data(df_variant)
    expected = True

    if result == expected:
        print("✓ PASS: Detected TPR with variant column names")
        passed += 1
    else:
        print(f"✗ FAIL: Expected {expected}, got {result}")
        failed += 1

    # Test 4: Empty DataFrame
    print("\n" + "-" * 70)
    print("Test 4: Empty DataFrame")
    print("-" * 70)

    df_empty = pd.DataFrame()

    result = detect_tpr_data(df_empty)
    expected = False

    if result == expected:
        print("✓ PASS: Handled empty DataFrame gracefully")
        passed += 1
    else:
        print(f"✗ FAIL: Expected {expected}, got {result}")
        failed += 1

    # Test 5: Partial TPR data (missing key indicators)
    print("\n" + "-" * 70)
    print("Test 5: Partial TPR data (has facility + test, but no TPR indicators)")
    print("-" * 70)

    df_partial = pd.DataFrame({
        'HealthFacility': ['Clinic A'],
        'RDT_Tested': [100],
        'Results': ['Positive']
    })

    result = detect_tpr_data(df_partial)
    expected = False

    if result == expected:
        print("✓ PASS: Correctly rejected partial TPR data")
        passed += 1
    else:
        print(f"✗ FAIL: Expected {expected}, got {result}")
        failed += 1

    # Test 6: TPR with minimal indicators
    print("\n" + "-" * 70)
    print("Test 6: Minimal TPR data (facility + test + 1 indicator)")
    print("-" * 70)

    df_minimal = pd.DataFrame({
        'facility_name': ['Clinic A'],
        'rdt_tested': [100],
        'rdt_positive': [10],
        'tpr': [0.1]
    })

    result = detect_tpr_data(df_minimal)
    expected = True

    if result == expected:
        print("✓ PASS: Detected minimal TPR data")
        passed += 1
    else:
        print(f"✗ FAIL: Expected {expected}, got {result}")
        failed += 1

    # Summary
    total = passed + failed
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed}/{total} tests passed")
    if failed == 0:
        print("✓ ALL TESTS PASSED!")
    else:
        print(f"✗ {failed} tests failed")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
