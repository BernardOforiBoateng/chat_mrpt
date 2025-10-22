#!/usr/bin/env python3
"""
Check ITN distribution coverage and identify missing wards
"""

import json
import pandas as pd
import sys

def analyze_itn_coverage(session_folder):
    """Analyze ITN distribution coverage issues"""
    
    # Load ITN distribution results
    with open(f'{session_folder}/itn_distribution_results.json', 'r') as f:
        results = json.load(f)
    
    print("=== ITN Distribution Summary ===")
    print(f"Total nets: {results.get('total_nets', 0):,}")
    print(f"Total allocated: {results.get('total_allocated', 0):,}")
    print(f"Coverage percentage: {results.get('coverage_percentage', 0):.2f}%")
    print(f"Urban threshold: {results.get('urban_threshold', 0)}%")
    print(f"Method: {results.get('method', 'unknown')}")
    
    # Check distribution details
    distribution = results.get('distribution', [])
    print(f"\nWards in ITN distribution: {len(distribution)}")
    
    # Count allocation status
    allocated = sum(1 for w in distribution if w.get('nets_allocated', 0) > 0)
    not_allocated = sum(1 for w in distribution if w.get('nets_allocated', 0) == 0)
    print(f"Wards with nets allocated: {allocated}")
    print(f"Wards without nets: {not_allocated}")
    
    # Check for missing population data
    no_pop = sum(1 for w in distribution if not w.get('population') or w.get('population') == 0)
    print(f"Wards with no population data: {no_pop}")
    
    # Load analysis data to compare
    try:
        analysis_df = pd.read_csv(f'{session_folder}/analysis_normalized_data.csv')
        print(f"\n=== Analysis Data ===")
        print(f"Total wards in analysis: {len(analysis_df)}")
        print(f"Wards with valid WardName: {analysis_df['WardName'].notna().sum()}")
        
        # Check for duplicates
        duplicates = analysis_df['WardName'].duplicated().sum()
        if duplicates > 0:
            print(f"WARNING: {duplicates} duplicate ward names in analysis data")
        
        # Compare ward coverage
        itn_wards = set(w.get('ward_name', '') for w in distribution if w.get('ward_name'))
        analysis_wards = set(analysis_df['WardName'].dropna())
        
        print(f"\n=== Ward Coverage Comparison ===")
        print(f"Unique wards in ITN distribution: {len(itn_wards)}")
        print(f"Unique wards in analysis data: {len(analysis_wards)}")
        
        missing_from_itn = analysis_wards - itn_wards
        extra_in_itn = itn_wards - analysis_wards
        
        print(f"Wards missing from ITN map: {len(missing_from_itn)}")
        print(f"Extra wards in ITN (not in analysis): {len(extra_in_itn)}")
        
        if missing_from_itn:
            print(f"\nSample of missing wards (first 10):")
            for ward in list(missing_from_itn)[:10]:
                print(f"  - {ward}")
        
        # Check population data availability
        if 'Population' in analysis_df.columns:
            pop_missing = analysis_df['Population'].isna().sum()
            print(f"\n=== Population Data ===")
            print(f"Wards with missing population in analysis: {pop_missing}")
            if pop_missing > 0:
                print("This could cause wards to be excluded from ITN distribution")
    
    except FileNotFoundError:
        print("\nERROR: analysis_normalized_data.csv not found")
    
    # Check shapefile data
    try:
        # Check if unified dataset exists
        unified_df = pd.read_csv(f'{session_folder}/unified_dataset.csv')
        print(f"\n=== Unified Dataset ===")
        print(f"Total rows: {len(unified_df)}")
        
        # Check for urban percentage
        urban_cols = [col for col in unified_df.columns if 'urban' in col.lower()]
        print(f"Urban-related columns: {urban_cols}")
        
        if 'urban_percentage' in unified_df.columns:
            urban_missing = unified_df['urban_percentage'].isna().sum()
            print(f"Wards with missing urban_percentage: {urban_missing}")
        
    except FileNotFoundError:
        print("\nNote: unified_dataset.csv not found")
    
    # Analyze allocation patterns
    print(f"\n=== Allocation Analysis ===")
    if distribution:
        # Check Phase 1 vs Phase 2
        phase1 = sum(1 for w in distribution if w.get('allocation_phase') == 1)
        phase2 = sum(1 for w in distribution if w.get('allocation_phase') == 2)
        unphased = len(distribution) - phase1 - phase2
        
        print(f"Phase 1 allocations: {phase1}")
        print(f"Phase 2 allocations: {phase2}")
        print(f"Unphased/missing: {unphased}")
        
        # Check urban classification
        urban_wards = sum(1 for w in distribution if w.get('urban_percentage', 0) >= results.get('urban_threshold', 30))
        rural_wards = sum(1 for w in distribution if w.get('urban_percentage', 0) < results.get('urban_threshold', 30))
        urban_unknown = sum(1 for w in distribution if 'urban_percentage' not in w)
        
        print(f"\nUrban classification (threshold {results.get('urban_threshold', 30)}%):")
        print(f"Urban wards: {urban_wards}")
        print(f"Rural wards: {rural_wards}")
        print(f"Unknown urban status: {urban_unknown}")

if __name__ == "__main__":
    session_folder = sys.argv[1] if len(sys.argv) > 1 else '/home/ec2-user/ChatMRPT/instance/uploads/0b7e3bbc-284a-421c-ab89-b53ea56b1dc3'
    analyze_itn_coverage(session_folder)