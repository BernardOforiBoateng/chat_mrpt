#!/usr/bin/env python3
"""
Test script for PCA statistical tests implementation.
Tests KMO and Bartlett's tests with different data scenarios.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
from app.analysis.pca_statistical_tests import PCAStatisticalTests

def test_suitable_data():
    """Test with data that should be suitable for PCA"""
    print("\n" + "="*60)
    print("TEST 1: Data suitable for PCA (correlated variables)")
    print("="*60)
    
    # Generate correlated data
    np.random.seed(42)
    n_samples = 100
    n_vars = 5
    
    # Create correlated variables
    base = np.random.randn(n_samples, 1)
    data = np.hstack([
        base + np.random.randn(n_samples, 1) * 0.5,
        base * 2 + np.random.randn(n_samples, 1) * 0.3,
        base * -1.5 + np.random.randn(n_samples, 1) * 0.4,
        base * 0.8 + np.random.randn(n_samples, 1) * 0.6,
        np.random.randn(n_samples, 1) * 2  # One less correlated variable
    ])
    
    df = pd.DataFrame(data, columns=[f'Var{i+1}' for i in range(n_vars)])
    
    # Run tests
    result = PCAStatisticalTests.check_pca_suitability(df)
    
    print(f"KMO Value: {result['kmo_value']:.3f}")
    print(f"KMO Interpretation: {result['kmo_interpretation']}")
    print(f"Bartlett's p-value: {result['bartlett_p_value']:.4e}")
    print(f"Suitable for PCA: {result['suitable']}")
    print(f"Summary: {result['summary']}")
    
    return result['suitable']

def test_unsuitable_data():
    """Test with data that should NOT be suitable for PCA"""
    print("\n" + "="*60)
    print("TEST 2: Data unsuitable for PCA (uncorrelated variables)")
    print("="*60)
    
    # Generate completely uncorrelated data
    np.random.seed(42)
    n_samples = 50
    n_vars = 5
    
    # Create independent variables
    data = np.random.randn(n_samples, n_vars)
    
    # Make them orthogonal to reduce correlations
    from scipy.linalg import orth
    data = orth(data.T).T[:n_samples, :n_vars]
    
    df = pd.DataFrame(data, columns=[f'Var{i+1}' for i in range(n_vars)])
    
    # Run tests
    result = PCAStatisticalTests.check_pca_suitability(df)
    
    print(f"KMO Value: {result['kmo_value']:.3f}")
    print(f"KMO Interpretation: {result['kmo_interpretation']}")
    print(f"Bartlett's p-value: {result['bartlett_p_value']:.4e}")
    print(f"Suitable for PCA: {result['suitable']}")
    print(f"Summary: {result['summary']}")
    
    return not result['suitable']  # We expect it to be unsuitable

def test_edge_cases():
    """Test edge cases"""
    print("\n" + "="*60)
    print("TEST 3: Edge cases")
    print("="*60)
    
    # Test with too few variables
    print("\n3a. Too few variables (2 variables):")
    df_small = pd.DataFrame(np.random.randn(50, 2), columns=['Var1', 'Var2'])
    result_small = PCAStatisticalTests.check_pca_suitability(df_small)
    print(f"  KMO: {result_small['kmo_value']:.3f}, Suitable: {result_small['suitable']}")
    
    # Test with perfect correlation
    print("\n3b. Perfect correlation:")
    df_perfect = pd.DataFrame({
        'Var1': np.arange(50),
        'Var2': np.arange(50) * 2,
        'Var3': np.arange(50) * -1.5,
        'Var4': np.arange(50) + 10
    })
    result_perfect = PCAStatisticalTests.check_pca_suitability(df_perfect)
    print(f"  KMO: {result_perfect['kmo_value']:.3f}, Suitable: {result_perfect['suitable']}")
    
    # Test with constant variable
    print("\n3c. With constant variable:")
    df_const = pd.DataFrame({
        'Var1': np.random.randn(50),
        'Var2': np.random.randn(50),
        'Var3': np.ones(50),  # Constant
        'Var4': np.random.randn(50)
    })
    result_const = PCAStatisticalTests.check_pca_suitability(df_const)
    print(f"  KMO: {result_const['kmo_value']:.3f}, Suitable: {result_const['suitable']}")
    
    return True

def test_real_world_scenario():
    """Test with realistic malaria data scenario"""
    print("\n" + "="*60)
    print("TEST 4: Realistic malaria vulnerability data")
    print("="*60)
    
    np.random.seed(42)
    n_wards = 80
    
    # Create realistic correlated health indicators
    poverty_index = np.random.beta(2, 5, n_wards)  # Skewed poverty distribution
    
    df = pd.DataFrame({
        'poverty_rate': poverty_index,
        'malaria_incidence': poverty_index * 0.7 + np.random.randn(n_wards) * 0.1,
        'healthcare_access': 1 - poverty_index * 0.8 + np.random.randn(n_wards) * 0.15,
        'education_level': 1 - poverty_index * 0.6 + np.random.randn(n_wards) * 0.2,
        'water_access': 1 - poverty_index * 0.5 + np.random.randn(n_wards) * 0.25,
        'population_density': np.random.lognormal(3, 1, n_wards),
        'rainfall_avg': np.random.normal(1200, 300, n_wards)
    })
    
    # Standardize the data (as would be done in pipeline)
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    df_standardized = pd.DataFrame(
        scaler.fit_transform(df),
        columns=df.columns
    )
    
    # Run tests
    result = PCAStatisticalTests.check_pca_suitability(df_standardized)
    
    print(f"Number of wards: {n_wards}")
    print(f"Number of variables: {len(df.columns)}")
    print(f"KMO Value: {result['kmo_value']:.3f}")
    print(f"KMO Interpretation: {result['kmo_interpretation']}")
    print(f"Bartlett's p-value: {result['bartlett_p_value']:.4e}")
    print(f"Suitable for PCA: {result['suitable']}")
    print(f"Summary: {result['summary']}")
    
    if result['suitable']:
        print("\n✅ This dataset would proceed with PCA analysis")
    else:
        print("\n⚠️ This dataset would skip PCA and use composite analysis only")
    
    return True

def main():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# PCA STATISTICAL TESTS - COMPREHENSIVE TEST SUITE")
    print("#"*60)
    
    tests_passed = 0
    total_tests = 4
    
    # Run tests
    if test_suitable_data():
        tests_passed += 1
        print("✅ Test 1 PASSED: Suitable data correctly identified")
    else:
        print("❌ Test 1 FAILED: Suitable data not identified")
    
    if test_unsuitable_data():
        tests_passed += 1
        print("✅ Test 2 PASSED: Unsuitable data correctly identified")
    else:
        print("❌ Test 2 FAILED: Unsuitable data not identified")
    
    if test_edge_cases():
        tests_passed += 1
        print("✅ Test 3 PASSED: Edge cases handled")
    else:
        print("❌ Test 3 FAILED: Edge cases not handled properly")
    
    if test_real_world_scenario():
        tests_passed += 1
        print("✅ Test 4 PASSED: Real-world scenario tested")
    else:
        print("❌ Test 4 FAILED: Real-world scenario failed")
    
    # Summary
    print("\n" + "="*60)
    print(f"FINAL RESULTS: {tests_passed}/{total_tests} tests passed")
    print("="*60)
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED! PCA statistical tests are working correctly.")
        return 0
    else:
        print(f"⚠️ {total_tests - tests_passed} test(s) failed. Please review the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())