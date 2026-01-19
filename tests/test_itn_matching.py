#!/usr/bin/env python3
"""Test ward name matching for ITN distribution."""

import sys
import os
import pandas as pd
import re

# Add the app directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.analysis.itn_pipeline import load_population_data
from app.analysis.lga_mapping import get_lga_name

def test_ward_matching():
    """Test the ward name matching logic."""
    print("Testing Ward Name Matching for ITN Distribution")
    print("=" * 60)
    
    # Load unified dataset
    session_id = "6e90b139-5d30-40fd-91ad-4af66fec5f00"
    unified_path = f"instance/uploads/{session_id}/unified_dataset.csv"
    unified_df = pd.read_csv(unified_path)
    print(f"\n1. Loaded unified dataset with {len(unified_df)} wards")
    
    # Load population data
    pop_data = load_population_data('Kano')
    print(f"\n2. Loaded population data with {len(pop_data)} ward-LGA combinations")
    
    # Extract ward names with codes
    wards_with_codes = unified_df[unified_df['WardName'].str.contains(r'\([A-Z]{2}\d+\)', regex=True)]
    print(f"\n3. Found {len(wards_with_codes)} wards with appended codes:")
    for idx, row in wards_with_codes.head(5).iterrows():
        original = re.sub(r'\s*\([A-Z]{2}\d+\)$', '', row['WardName'])
        lga_name = get_lga_name(row['LGACode'])
        print(f"   {row['WardName']} -> {original} (LGA: {lga_name})")
    
    # Test matching logic
    print("\n4. Testing matching logic...")
    
    # Create test dataframe similar to rankings
    test_df = unified_df[['WardName', 'LGACode']].copy()
    test_df['WardName_original'] = test_df['WardName'].str.replace(r'\s*\([A-Z]{2}\d+\)$', '', regex=True)
    test_df['WardName_original_lower'] = test_df['WardName_original'].str.lower()
    test_df['LGA_name'] = test_df['LGACode'].apply(lambda x: get_lga_name(x) or 'Unknown')
    
    # Create composite keys
    test_df['match_key'] = test_df['WardName_original_lower'] + '|' + test_df['LGA_name'].str.lower()
    pop_data['match_key'] = pop_data['WardName_lower'] + '|' + pop_data['AdminLevel2'].str.lower()
    
    # Test exact matching
    matched_exact = test_df.merge(
        pop_data[['match_key', 'Population']],
        on='match_key',
        how='inner'
    )
    
    print(f"\n   Exact matches (ward+LGA): {len(matched_exact)}")
    
    # Find unmatched
    unmatched_mask = ~test_df['match_key'].isin(matched_exact['match_key'])
    unmatched = test_df[unmatched_mask]
    print(f"   Unmatched: {len(unmatched)}")
    
    # Test fallback matching for unique wards
    ward_only_pop = pop_data.groupby('WardName_lower')['Population'].agg(['sum', 'count']).reset_index()
    unique_ward_pop = ward_only_pop[ward_only_pop['count'] == 1]
    print(f"\n   Unique ward names in population data: {len(unique_ward_pop)}")
    
    # Try fallback matching
    fallback_matched = unmatched.merge(
        unique_ward_pop[['WardName_lower', 'sum']],
        left_on='WardName_original_lower',
        right_on='WardName_lower',
        how='inner'
    )
    print(f"   Fallback matches (unique wards only): {len(fallback_matched)}")
    
    # Total matches
    total_matched = len(matched_exact) + len(fallback_matched)
    print(f"\n5. Total matches: {total_matched}/{len(test_df)} ({(total_matched/len(test_df))*100:.1f}%)")
    
    # Show some unmatched examples
    still_unmatched = unmatched[~unmatched['WardName_original_lower'].isin(fallback_matched['WardName_original_lower'])]
    if len(still_unmatched) > 0:
        print(f"\n6. Examples of unmatched wards:")
        for idx, row in still_unmatched.head(5).iterrows():
            print(f"   {row['WardName']} (LGA: {row['LGA_name']})")
            # Check if ward exists in population data
            ward_in_pop = pop_data[pop_data['WardName_lower'] == row['WardName_original_lower']]
            if len(ward_in_pop) > 0:
                print(f"     Found in population data with LGAs: {ward_in_pop['AdminLevel2'].tolist()}")
            else:
                print(f"     NOT found in population data")

if __name__ == "__main__":
    test_ward_matching()