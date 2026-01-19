#!/usr/bin/env python3
"""Compare LGA names between datasets."""

import sys
import os
import pandas as pd

# Add the app directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.analysis.itn_pipeline import load_population_data
from app.analysis.lga_mapping import get_lga_name, KANO_LGA_MAPPING

def main():
    """Compare LGA names between unified dataset and population data."""
    print("Comparing LGA Names Between Datasets")
    print("=" * 60)
    
    # Load unified dataset
    session_id = "6e90b139-5d30-40fd-91ad-4af66fec5f00"
    unified_path = f"instance/uploads/{session_id}/unified_dataset.csv"
    unified_df = pd.read_csv(unified_path)
    
    # Load population data
    pop_data = load_population_data('Kano')
    
    # Get unique LGA names from mapping
    print("\n1. LGA names from mapping (LGACode -> Name):")
    mapping_lgas = sorted(set(KANO_LGA_MAPPING.values()))
    print(f"   Total: {len(mapping_lgas)}")
    for i in range(0, len(mapping_lgas), 5):
        print(f"   {', '.join(mapping_lgas[i:i+5])}")
    
    # Get unique LGA names from population data
    print("\n2. LGA names from population data:")
    pop_lgas = sorted(pop_data['AdminLevel2'].unique())
    print(f"   Total: {len(pop_lgas)}")
    for i in range(0, len(pop_lgas), 5):
        print(f"   {', '.join(pop_lgas[i:i+5])}")
    
    # Compare the two sets
    mapping_set = set(mapping_lgas)
    pop_set = set(pop_lgas)
    
    print("\n3. Comparison:")
    print(f"   In mapping but not in population: {mapping_set - pop_set}")
    print(f"   In population but not in mapping: {pop_set - mapping_set}")
    print(f"   Common LGAs: {len(mapping_set & pop_set)}")
    
    # Check specific problem cases
    print("\n4. Checking specific problem wards:")
    problem_wards = ['Dawaki', 'Falgore', 'Goron Dutse']
    
    for ward in problem_wards:
        print(f"\n   Ward: {ward}")
        # From unified dataset
        unified_ward_data = unified_df[unified_df['WardName'].str.startswith(ward)]
        if len(unified_ward_data) > 0:
            for idx, row in unified_ward_data.iterrows():
                lga_name = get_lga_name(row['LGACode'])
                print(f"     In unified: {row['WardName']} -> LGA: {lga_name} (code: {row['LGACode']})")
        
        # From population data
        pop_ward_data = pop_data[pop_data['WardName'] == ward]
        if len(pop_ward_data) > 0:
            for idx, row in pop_ward_data.iterrows():
                print(f"     In population: {row['WardName']} -> LGA: {row['AdminLevel2']}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()