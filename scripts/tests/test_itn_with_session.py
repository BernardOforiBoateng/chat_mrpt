#!/usr/bin/env python3
"""Test ITN distribution planning with actual session data."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from app.analysis.itn_pipeline import calculate_itn_distribution, detect_state, load_population_data, fuzzy_match_ward_names
from app.models.data_handler import DataHandler
from app.data.population_data.itn_population_loader import get_population_loader

def test_with_session_data():
    """Test ITN distribution with actual Adamawa session data."""
    
    session_id = "59b18890-638c-4c1e-862b-82a900cea3e9"
    
    print("Testing ITN Distribution Planning with Session Data")
    print("=" * 60)
    
    # Load the analysis results
    print("\n1. Loading analysis results...")
    composite_path = f"instance/uploads/{session_id}/analysis_vulnerability_rankings.csv"
    
    if not os.path.exists(composite_path):
        print(f"   ERROR: Analysis file not found at {composite_path}")
        return
        
    rankings_df = pd.read_csv(composite_path)
    print(f"   ✓ Loaded {len(rankings_df)} wards from analysis")
    print(f"   Sample wards: {list(rankings_df['WardName'].head())}")
    
    # Load population data
    print("\n2. Loading population data for Adamawa...")
    loader = get_population_loader()
    pop_df = loader.load_state_population("Adamawa")
    
    if pop_df is None:
        print("   ERROR: Could not load Adamawa population data")
        return
        
    print(f"   ✓ Loaded {len(pop_df)} wards from population data")
    print(f"   Sample wards: {list(pop_df['WardName'].head())}")
    
    # Test fuzzy matching
    print("\n3. Testing fuzzy matching between datasets...")
    ranking_wards = rankings_df['WardName'].unique().tolist()
    pop_wards = pop_df['WardName'].unique().tolist()
    
    matches = fuzzy_match_ward_names(ranking_wards, pop_wards, threshold=75)
    
    print(f"   Matched {len(matches)} out of {len(ranking_wards)} wards ({len(matches)/len(ranking_wards)*100:.1f}%)")
    
    # Show some matched examples
    print("\n   Sample matches:")
    for i, (analysis_ward, (pop_ward, score)) in enumerate(matches.items()):
        if i >= 5:
            break
        print(f"   - '{analysis_ward}' -> '{pop_ward}' (score: {score})")
    
    # Show unmatched wards
    unmatched = [w for w in ranking_wards if w not in matches]
    if unmatched:
        print(f"\n   Unmatched wards ({len(unmatched)}):")
        for ward in unmatched[:10]:
            print(f"   - '{ward}'")
        if len(unmatched) > 10:
            print(f"   ... and {len(unmatched) - 10} more")
    
    # Create a mock DataHandler to test the full pipeline
    print("\n4. Testing full ITN distribution calculation...")
    
    # Create mock data handler with the actual data
    class MockDataHandler:
        def __init__(self):
            self.session_id = session_id
            self.unified_dataset = pd.read_csv(f"instance/uploads/{session_id}/unified_dataset.csv")
            self.vulnerability_rankings = rankings_df
            self.shapefile_data = None  # Not needed for basic test
            
    data_handler = MockDataHandler()
    
    # Test ITN calculation
    try:
        result = calculate_itn_distribution(
            data_handler=data_handler,
            session_id=session_id,
            total_nets=10000,
            avg_household_size=5.0,
            urban_threshold=30.0,
            method='composite'
        )
        
        if result['status'] == 'success':
            print("   ✓ ITN distribution calculation successful!")
            stats = result['stats']
            print(f"   - Total nets: {stats['total_nets']:,}")
            print(f"   - Allocated: {stats['allocated']:,}")
            print(f"   - Population covered: {stats['covered_population']:,}")
            print(f"   - Coverage: {stats['coverage_percent']}%")
            print(f"   - Prioritized wards: {stats['prioritized_wards']}")
        else:
            print(f"   ✗ ITN calculation failed: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ✗ Error during ITN calculation: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_with_session_data()