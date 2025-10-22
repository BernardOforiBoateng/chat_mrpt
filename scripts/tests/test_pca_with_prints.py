#!/usr/bin/env python3
"""
Test script to demonstrate PCA statistical tests with detailed output.
This will show all the print statements during execution.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
from app.analysis.pca_statistical_tests import PCAStatisticalTests

def test_with_good_data():
    """Test with data that SHOULD pass PCA tests"""
    print("\n" + "#"*60)
    print("# TEST 1: GOOD DATA (Should PASS statistical tests)")
    print("#"*60)
    
    # Generate well-correlated data
    np.random.seed(42)
    n_samples = 100
    n_vars = 8
    
    # Create correlated variables (simulating malaria risk factors)
    base_poverty = np.random.beta(2, 5, n_samples)
    
    data = pd.DataFrame({
        'poverty_rate': base_poverty,
        'malaria_incidence': base_poverty * 0.8 + np.random.randn(n_samples) * 0.1,
        'healthcare_access': 1 - base_poverty * 0.7 + np.random.randn(n_samples) * 0.15,
        'education_level': 1 - base_poverty * 0.6 + np.random.randn(n_samples) * 0.2,
        'water_access': 1 - base_poverty * 0.5 + np.random.randn(n_samples) * 0.25,
        'sanitation': 1 - base_poverty * 0.65 + np.random.randn(n_samples) * 0.18,
        'population_density': np.random.lognormal(3, 0.5, n_samples),
        'rainfall_avg': base_poverty * 500 + np.random.normal(1200, 200, n_samples)
    })
    
    # Standardize the data
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    data_standardized = pd.DataFrame(
        scaler.fit_transform(data),
        columns=data.columns
    )
    
    print("\n📊 Dataset Information:")
    print(f"   - Number of samples: {n_samples}")
    print(f"   - Number of variables: {n_vars}")
    print(f"   - Variables: {', '.join(data.columns)}")
    
    # Run the statistical tests
    result = PCAStatisticalTests.check_pca_suitability(data_standardized)
    
    print("\n" + "#"*60)
    print("# EXPECTED OUTCOME: Should PASS and proceed with PCA")
    print("#"*60)
    
    return result

def test_with_bad_data():
    """Test with data that should FAIL PCA tests"""
    print("\n" + "#"*60)
    print("# TEST 2: BAD DATA (Should FAIL statistical tests)")
    print("#"*60)
    
    # Generate mostly uncorrelated data
    np.random.seed(123)
    n_samples = 50
    n_vars = 6
    
    # Create mostly independent variables
    data = pd.DataFrame({
        'random_var1': np.random.randn(n_samples),
        'random_var2': np.random.randn(n_samples),
        'random_var3': np.random.randn(n_samples),
        'random_var4': np.random.uniform(0, 100, n_samples),
        'random_var5': np.random.poisson(5, n_samples),
        'random_var6': np.random.exponential(2, n_samples)
    })
    
    # Standardize the data
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    data_standardized = pd.DataFrame(
        scaler.fit_transform(data),
        columns=data.columns
    )
    
    print("\n📊 Dataset Information:")
    print(f"   - Number of samples: {n_samples}")
    print(f"   - Number of variables: {n_vars}")
    print(f"   - Variables: {', '.join(data.columns)}")
    print("   - Note: These are random, uncorrelated variables")
    
    # Run the statistical tests
    result = PCAStatisticalTests.check_pca_suitability(data_standardized)
    
    print("\n" + "#"*60)
    print("# EXPECTED OUTCOME: Should FAIL and skip PCA")
    print("#"*60)
    
    return result

def test_with_insufficient_data():
    """Test with too few samples"""
    print("\n" + "#"*60)
    print("# TEST 3: INSUFFICIENT DATA (Too few samples)")
    print("#"*60)
    
    # Generate data with more variables than samples
    np.random.seed(456)
    n_samples = 10  # Only 10 samples
    n_vars = 15     # But 15 variables!
    
    data = pd.DataFrame(
        np.random.randn(n_samples, n_vars),
        columns=[f'var_{i+1}' for i in range(n_vars)]
    )
    
    print("\n📊 Dataset Information:")
    print(f"   - Number of samples: {n_samples}")
    print(f"   - Number of variables: {n_vars}")
    print(f"   - Problem: More variables than samples!")
    
    # This should fail even before statistical tests
    result = PCAStatisticalTests.check_pca_suitability(data)
    
    print("\n" + "#"*60)
    print("# EXPECTED OUTCOME: Should FAIL due to insufficient samples")
    print("#"*60)
    
    return result

def main():
    """Run all test scenarios"""
    print("\n" + "="*60)
    print("PCA STATISTICAL TESTS - DEMONSTRATION WITH DETAILED OUTPUT")
    print("="*60)
    print("\nThis test will show all the print statements that appear")
    print("when the PCA statistical tests are run during analysis.")
    print("="*60)
    
    # Test 1: Good data
    print("\n🔬 Running Test 1: Good correlated data")
    result1 = test_with_good_data()
    
    print("\n" + "-"*60)
    print("Continuing to Test 2...")
    print("-"*60)
    
    # Test 2: Bad data
    print("\n🔬 Running Test 2: Uncorrelated data")
    result2 = test_with_bad_data()
    
    print("\n" + "-"*60)
    print("Continuing to Test 3...")
    print("-"*60)
    
    # Test 3: Insufficient data
    print("\n🔬 Running Test 3: Insufficient samples")
    result3 = test_with_insufficient_data()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY OF ALL TESTS")
    print("="*60)
    print(f"\nTest 1 (Good data):        {'✅ SUITABLE' if result1['suitable'] else '❌ NOT SUITABLE'}")
    print(f"  - KMO: {result1['kmo_value']:.3f}")
    print(f"  - Bartlett's p: {result1['bartlett_p_value']:.4e}")
    
    print(f"\nTest 2 (Bad data):         {'✅ SUITABLE' if result2['suitable'] else '❌ NOT SUITABLE'}")
    print(f"  - KMO: {result2['kmo_value']:.3f}")
    print(f"  - Bartlett's p: {result2['bartlett_p_value']:.4e}")
    
    print(f"\nTest 3 (Insufficient):     {'✅ SUITABLE' if result3['suitable'] else '❌ NOT SUITABLE'}")
    print(f"  - KMO: {result3['kmo_value']:.3f}")
    print(f"  - Bartlett's p: {result3['bartlett_p_value']:.4e}")
    
    print("\n" + "="*60)
    print("TEST COMPLETE - All print statements demonstrated")
    print("="*60)

if __name__ == "__main__":
    main()