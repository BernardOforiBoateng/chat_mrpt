#!/usr/bin/env python3
"""Test script for ITN population data integration"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.data.population_data.itn_population_loader import get_population_loader
from app.analysis.itn_pipeline import load_population_data

def test_population_loader():
    """Test the new population loader"""
    print("=== Testing ITN Population Data Loader ===\n")
    
    loader = get_population_loader()
    
    # Test 1: List available states
    print("1. Available states with ITN data:")
    states = loader.get_available_states()
    for state in states:
        print(f"   - {state}")
    print()
    
    # Test 2: Load Kaduna data
    print("2. Loading Kaduna population data:")
    kaduna_data = loader.load_state_population('Kaduna')
    if kaduna_data is not None:
        print(f"   - Loaded {len(kaduna_data)} wards")
        print(f"   - Total population: {kaduna_data['Population'].sum():,.0f}")
        print(f"   - Sample data:")
        print(kaduna_data.head())
    else:
        print("   - Failed to load Kaduna data")
    print()
    
    # Test 3: Get ward populations
    print("3. Getting specific ward populations for Kaduna:")
    ward_pops = loader.get_ward_populations('Kaduna', ['Abadawa', 'Aboro', 'Afaka'])
    for ward, pop in ward_pops.items():
        print(f"   - {ward}: {pop:,}")
    print()
    
    # Test 4: Test pipeline integration
    print("4. Testing pipeline integration:")
    pop_data = load_population_data('Kaduna')
    if pop_data is not None:
        print(f"   - Pipeline loaded {len(pop_data)} wards")
        print(f"   - Columns: {pop_data.columns.tolist()}")
        print(f"   - Total population: {pop_data['Population'].sum():,.0f}")
    else:
        print("   - Pipeline failed to load data")
    print()
    
    # Test 5: Compare with old format (if available)
    print("5. Comparing formats for Osun (has both old and new):")
    osun_new = loader.load_state_population('Osun', use_new_format=True)
    osun_old = loader.load_state_population('Osun', use_new_format=False)
    
    if osun_new is not None:
        print(f"   - New format: {len(osun_new)} wards, pop: {osun_new['Population'].sum():,.0f}")
    else:
        print("   - New format not available")
        
    if osun_old is not None:
        print(f"   - Old format: {len(osun_old)} records")
    else:
        print("   - Old format not available")
    print()
    
    print("=== Test Complete ===")

if __name__ == "__main__":
    test_population_loader()