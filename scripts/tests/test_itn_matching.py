#!/usr/bin/env python3
"""
Test ITN ward name matching between rankings and population data
"""

import sys
import os
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

def test_ward_matching(session_id):
    """Test ward name matching for ITN distribution"""
    
    # Add app to path
    sys.path.insert(0, '/home/ec2-user/ChatMRPT')
    
    from app.data.population_data.itn_population_loader import get_population_loader
    from app.analysis.itn_pipeline import fuzzy_match_ward_names, detect_state
    from app.data import DataHandler
    
    session_folder = f'/home/ec2-user/ChatMRPT/instance/uploads/{session_id}'
    print(f"Testing session: {session_id}")
    print(f"Session folder: {session_folder}")
    
    # Initialize data handler
    data_handler = DataHandler(session_folder)
    data_handler._attempt_data_reload()
    
    # Detect state
    state = detect_state(data_handler)
    print(f"\n✅ Detected state: {state}")
    
    # Load population data
    loader = get_population_loader()
    pop_data = loader.load_state_population(state)
    
    if pop_data is not None:
        print(f"\n✅ Population data loaded for {state}")
        print(f"   Total wards: {len(pop_data)}")
        print(f"   Total population: {pop_data['Population'].sum():,.0f}")
    else:
        print(f"❌ Failed to load population data for {state}")
        return False
    
    # Load rankings data
    rankings_path = os.path.join(session_folder, 'analysis_vulnerability_rankings.csv')
    if not os.path.exists(rankings_path):
        print(f"❌ Rankings file not found: {rankings_path}")
        return False
    
    rankings = pd.read_csv(rankings_path)
    print(f"\n✅ Rankings loaded")
    print(f"   Total wards: {len(rankings)}")
    
    # Check unified dataset
    unified_path = os.path.join(session_folder, 'unified_dataset.csv')
    if os.path.exists(unified_path):
        unified = pd.read_csv(unified_path)
        print(f"\n✅ Unified dataset loaded")
        print(f"   Total rows: {len(unified)}")
        if 'urbanPercentage' in unified.columns:
            print(f"   ✅ Has urbanPercentage column")
            non_null_urban = unified['urbanPercentage'].notna().sum()
            print(f"   Non-null urban values: {non_null_urban}/{len(unified)}")
    
    # Compare ward names
    print(f"\n=== Ward Name Comparison ===")
    
    # Get unique ward names
    pop_wards = pop_data['WardName'].unique()
    ranking_wards = rankings['WardName'].unique()
    
    print(f"Population data wards: {len(pop_wards)}")
    print(f"Ranking data wards: {len(ranking_wards)}")
    
    # Check for exact matches (case-insensitive)
    pop_wards_lower = set(w.lower() for w in pop_wards)
    ranking_wards_lower = set(w.lower() for w in ranking_wards)
    
    common = pop_wards_lower.intersection(ranking_wards_lower)
    print(f"\n📊 Exact matches (case-insensitive): {len(common)}")
    
    if len(common) == 0:
        print("\n⚠️ No exact matches found!")
        
        # Show samples
        print(f"\nPopulation ward samples (first 10):")
        for w in list(pop_wards)[:10]:
            print(f"  - {w}")
        
        print(f"\nRanking ward samples (first 10):")
        for w in list(ranking_wards)[:10]:
            print(f"  - {w}")
    else:
        print(f"\nSome matching wards:")
        for w in list(common)[:10]:
            print(f"  - {w}")
    
    # Test fuzzy matching
    print(f"\n=== Fuzzy Matching Test ===")
    
    ranking_list = list(ranking_wards)
    pop_list = list(pop_wards)
    
    # Test with different thresholds
    for threshold in [90, 80, 75, 70, 60]:
        matches = fuzzy_match_ward_names(ranking_list, pop_list, threshold=threshold)
        print(f"\nThreshold {threshold}: {len(matches)} matches")
        
        if len(matches) > 0:
            # Show some examples
            examples = list(matches.items())[:5]
            for rw, (pw, score) in examples:
                print(f"  '{rw}' -> '{pw}' (score: {score})")
            break
    
    # Check if the issue is with ward name format
    print(f"\n=== Ward Name Format Analysis ===")
    
    # Check for common patterns
    def analyze_format(wards, name):
        has_roman = sum(1 for w in wards if any(x in w.upper() for x in ['I', 'II', 'III', 'IV', 'V']))
        has_numbers = sum(1 for w in wards if any(c.isdigit() for c in w))
        has_parentheses = sum(1 for w in wards if '(' in w)
        has_slash = sum(1 for w in wards if '/' in w)
        
        print(f"\n{name}:")
        print(f"  With Roman numerals: {has_roman}/{len(wards)}")
        print(f"  With numbers: {has_numbers}/{len(wards)}")
        print(f"  With parentheses: {has_parentheses}/{len(wards)}")
        print(f"  With slash: {has_slash}/{len(wards)}")
    
    analyze_format(pop_wards, "Population data")
    analyze_format(ranking_wards, "Ranking data")
    
    return len(common) > 0 or len(matches) > 0

if __name__ == "__main__":
    session_id = sys.argv[1] if len(sys.argv) > 1 else '4e21ce78-66e6-4ef4-b13e-23e994846de8'
    success = test_ward_matching(session_id)
    
    print("\n" + "="*50)
    if success:
        print("✅ Ward matching successful - ITN should work")
    else:
        print("❌ Ward matching failed - ITN will not work")