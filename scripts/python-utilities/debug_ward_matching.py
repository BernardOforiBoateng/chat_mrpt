#!/usr/bin/env python3
"""Debug ward matching issues."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from app.data.population_data.itn_population_loader import get_population_loader

def debug_ward_matching():
    session_id = "59b18890-638c-4c1e-862b-82a900cea3e9"
    
    print("Debugging Ward Matching Issues")
    print("=" * 60)
    
    # Load analysis data
    print("\n1. Loading analysis ward names...")
    rankings_path = f"instance/uploads/{session_id}/analysis_vulnerability_rankings.csv"
    rankings_df = pd.read_csv(rankings_path)
    analysis_wards = rankings_df['WardName'].unique()
    print(f"   Found {len(analysis_wards)} unique wards in analysis")
    print(f"   First 10: {list(analysis_wards[:10])}")
    
    # Load population data
    print("\n2. Loading population ward names...")
    loader = get_population_loader()
    pop_df = loader.load_state_population("Adamawa")
    
    if pop_df is None:
        print("   ERROR: Could not load population data")
        return
        
    pop_wards = pop_df['WardName'].unique()
    print(f"   Found {len(pop_wards)} unique wards in population data")
    print(f"   First 10: {list(pop_wards[:10])}")
    
    # Check for exact matches
    print("\n3. Checking exact matches...")
    exact_matches = set(analysis_wards) & set(pop_wards)
    print(f"   Found {len(exact_matches)} exact matches")
    
    # Check for case-insensitive matches
    print("\n4. Checking case-insensitive matches...")
    analysis_lower = {w.lower(): w for w in analysis_wards}
    pop_lower = {w.lower(): w for w in pop_wards}
    case_matches = set(analysis_lower.keys()) & set(pop_lower.keys())
    print(f"   Found {len(case_matches)} case-insensitive matches")
    
    # Find mismatches
    print("\n5. Sample mismatches (analysis wards not in population):")
    mismatches = [w for w in analysis_wards if w not in pop_wards][:10]
    for ward in mismatches:
        # Try to find similar ward in population
        ward_lower = ward.lower()
        similar = [p for p in pop_wards if ward_lower in p.lower() or p.lower() in ward_lower]
        if similar:
            print(f"   '{ward}' -> possible matches: {similar[:3]}")
        else:
            print(f"   '{ward}' -> no similar wards found")
    
    # Check the actual data in the pipeline
    print("\n6. Checking what happens in the pipeline...")
    # Look at the unified dataset to see what columns it has
    unified_path = f"instance/uploads/{session_id}/unified_dataset.csv"
    if os.path.exists(unified_path):
        unified_df = pd.read_csv(unified_path)
        print(f"   Unified dataset columns: {list(unified_df.columns)}")
        if 'WardName' in unified_df.columns:
            unified_wards = unified_df['WardName'].unique()
            print(f"   Unified dataset has {len(unified_wards)} unique wards")
            print(f"   First 5: {list(unified_wards[:5])}")

if __name__ == "__main__":
    debug_ward_matching()