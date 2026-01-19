#!/usr/bin/env python3
"""Check why specific wards didn't match."""

import sys
import os
import pandas as pd

# Add the app directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.analysis.itn_pipeline import load_population_data

def main():
    """Check unmatched wards."""
    print("Checking Unmatched Wards")
    print("=" * 60)
    
    # Load datasets
    session_id = "6e90b139-5d30-40fd-91ad-4af66fec5f00"
    unified_df = pd.read_csv(f"instance/uploads/{session_id}/unified_dataset.csv")
    pop_data = load_population_data('Kano')
    
    # Check specific unmatched wards
    unmatched_names = ['Jauben Kudu', 'Rigar Duka', 'Falgore (KN1104)']
    
    for ward_name in unmatched_names:
        print(f"\nChecking: {ward_name}")
        
        # In unified dataset
        unified_ward = unified_df[unified_df['WardName'] == ward_name]
        if len(unified_ward) > 0:
            row = unified_ward.iloc[0]
            print(f"  In unified dataset:")
            print(f"    LGACode: {row['LGACode']}")
            print(f"    Coordinates: ({row['centroid_lat']:.4f}, {row['centroid_lon']:.4f})")
        else:
            print(f"  NOT found in unified dataset")
        
        # In population data - check both exact and without code
        original_name = ward_name.replace(' (KN1104)', '') if '(KN' in ward_name else ward_name
        
        # Exact match
        pop_exact = pop_data[pop_data['WardName'] == original_name]
        if len(pop_exact) > 0:
            print(f"  In population data (exact match '{original_name}'):")
            for _, p_row in pop_exact.iterrows():
                print(f"    LGA: {p_row['AdminLevel2']}, Coordinates: ({p_row['AvgLatitude']:.4f}, {p_row['AvgLongitude']:.4f})")
        
        # Similar names
        pop_similar = pop_data[pop_data['WardName'].str.contains(original_name.split()[0], case=False)]
        if len(pop_similar) > 0 and len(pop_exact) == 0:
            print(f"  Similar names in population data:")
            for _, p_row in pop_similar.head(3).iterrows():
                print(f"    '{p_row['WardName']}' in {p_row['AdminLevel2']}")
        
        if len(pop_exact) == 0 and len(pop_similar) == 0:
            print(f"  NOT found in population data")
    
    # Check if these wards exist with different spelling
    print("\n" + "=" * 60)
    print("Checking for potential spelling variations:")
    
    # Get all ward names from both datasets
    unified_wards = set(unified_df['WardName'].str.replace(r'\s*\([A-Z]{2}\d+\)$', '', regex=True))
    pop_wards = set(pop_data['WardName'])
    
    # Find wards only in unified but not in population
    only_in_unified = unified_wards - pop_wards
    print(f"\nWards only in unified dataset ({len(only_in_unified)}):")
    for ward in sorted(list(only_in_unified))[:10]:
        print(f"  {ward}")
    
    # Find wards only in population but not in unified
    only_in_pop = pop_wards - unified_wards
    print(f"\nWards only in population dataset ({len(only_in_pop)}):")
    for ward in sorted(list(only_in_pop))[:10]:
        print(f"  {ward}")

if __name__ == "__main__":
    main()