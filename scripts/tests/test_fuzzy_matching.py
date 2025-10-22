#!/usr/bin/env python3
"""Test script for fuzzy matching in ITN distribution planning."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.analysis.itn_pipeline import normalize_ward_name, fuzzy_match_ward_names

def test_normalize_ward_name():
    """Test ward name normalization."""
    print("Testing ward name normalization...")
    
    test_cases = [
        ("Girei I", "girei 1"),
        ("Girei II", "girei 2"),
        ("Ajingi (F)", "ajingi"),
        ("Adamawa North", "adamawa north"),
        ("Adamawa-North", "adamawa north"),
        ("ADAMAWA_NORTH", "adamawa north"),
        ("Ward III", "ward 3"),
        ("Ward_Name_Test", "ward name test"),
        ("Test (Urban)", "test"),
        ("Test (Rural)", "test"),
    ]
    
    for input_name, expected in test_cases:
        result = normalize_ward_name(input_name)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{input_name}' -> '{result}' (expected: '{expected}')")
    
    print()

def test_fuzzy_matching():
    """Test fuzzy matching between ward lists."""
    print("Testing fuzzy matching...")
    
    # Sample ward names from analysis (with variations)
    analysis_wards = [
        "Girei I",
        "Girei II", 
        "Ajingi (F)",
        "Adamawa North",
        "Kiru Ward",
        "Gaya-North",
        "Test Ward III",
        "Unknown Ward XYZ"
    ]
    
    # Sample ward names from population data
    population_wards = [
        "Girei 1",
        "Girei 2",
        "Ajingi",
        "Adamawa-North",
        "Kiru",
        "Gaya North",
        "Test Ward 3",
        "Completely Different Ward"
    ]
    
    # Test with different thresholds
    for threshold in [75, 80, 85]:
        print(f"\n  Testing with threshold: {threshold}%")
        matches = fuzzy_match_ward_names(analysis_wards, population_wards, threshold=threshold)
        
        print(f"  Matched {len(matches)} out of {len(analysis_wards)} wards")
        
        for analysis_ward, (matched_ward, score) in matches.items():
            print(f"    '{analysis_ward}' -> '{matched_ward}' (score: {score})")
        
        unmatched = [w for w in analysis_wards if w not in matches]
        if unmatched:
            print(f"  Unmatched: {unmatched}")

def test_real_data():
    """Test with real Adamawa data if available."""
    print("\nTesting with real Adamawa data...")
    
    try:
        # Load real data
        from app.data.population_data.itn_population_loader import get_population_loader
        loader = get_population_loader()
        
        # Check if Adamawa data exists
        pop_df = loader.load_state_population("Adamawa")
        if pop_df is None:
            print("  Adamawa population data not found")
            return
            
        # Get population ward names
        pop_wards = pop_df['WardName'].unique().tolist()
        print(f"  Found {len(pop_wards)} wards in population data")
        print(f"  Sample population wards: {pop_wards[:5]}")
        
        # Simulate some analysis ward names with variations
        analysis_wards = [
            "girei i",  # lowercase with roman
            "GIREI 1",  # uppercase with arabic
            "Ajingi (F)",  # with suffix
            "Adamawa North",  # with hyphen variation
            "Test Ward"  # may not exist
        ]
        
        # Test matching
        matches = fuzzy_match_ward_names(analysis_wards, pop_wards, threshold=75)
        
        print(f"\n  Matching results:")
        for analysis_ward in analysis_wards:
            if analysis_ward in matches:
                matched, score = matches[analysis_ward]
                print(f"    '{analysis_ward}' -> '{matched}' (score: {score})")
            else:
                print(f"    '{analysis_ward}' -> NO MATCH")
                
    except Exception as e:
        print(f"  Error testing real data: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("ITN Fuzzy Matching Test Suite")
    print("=" * 60)
    
    test_normalize_ward_name()
    test_fuzzy_matching()
    test_real_data()
    
    print("\nTest complete!")