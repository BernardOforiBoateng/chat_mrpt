#!/usr/bin/env python3
"""Simple test for ITN distribution with Kano data."""

import sys
import os
import pandas as pd
import geopandas as gpd

# Add the app directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.analysis.itn_pipeline import calculate_itn_distribution, detect_state, load_population_data

class SimpleDataHandler:
    """Simple data handler for testing."""
    def __init__(self, session_id):
        self.session_id = session_id
        self.unified_dataset = None
        self.shapefile_data = None
        self.vulnerability_rankings = None
        self.vulnerability_rankings_pca = None

def main():
    """Run simple ITN distribution test."""
    print("Simple ITN Distribution Test for Kano Data")
    print("=" * 60)
    
    # Create simple data handler
    session_id = "6e90b139-5d30-40fd-91ad-4af66fec5f00"
    data_handler = SimpleDataHandler(session_id)
    
    # Load unified dataset (CSV)
    print("\n1. Loading unified dataset...")
    unified_path = f"instance/uploads/{session_id}/unified_dataset.csv"
    data_handler.unified_dataset = pd.read_csv(unified_path)
    print(f"✓ Loaded {len(data_handler.unified_dataset)} wards")
    
    # Check for duplicate ward names
    dup_mask = data_handler.unified_dataset['WardName'].str.contains(r'\([A-Z]{2}\d+\)', regex=True)
    print(f"✓ Found {dup_mask.sum()} wards with appended codes")
    
    # Load shapefile
    print("\n2. Loading shapefile...")
    shapefile_path = f"instance/uploads/{session_id}/shapefile/raw.shp"
    data_handler.shapefile_data = gpd.read_file(shapefile_path)
    print(f"✓ Loaded {len(data_handler.shapefile_data)} features")
    
    # Test state detection
    print("\n3. Testing state detection...")
    state = detect_state(data_handler)
    print(f"✓ Detected state: {state}")
    
    # Test population data loading
    print("\n4. Loading population data...")
    pop_data = load_population_data(state)
    if pop_data is not None:
        print(f"✓ Loaded population data for {len(pop_data)} ward-LGA combinations")
        print(f"  Total population: {pop_data['Population'].sum():,.0f}")
        
        # Check for duplicate ward names in population data
        dup_wards = pop_data[pop_data.duplicated(subset=['WardName'], keep=False)]
        if len(dup_wards) > 0:
            print(f"  Found {len(dup_wards)} duplicate ward entries across LGAs")
    else:
        print("✗ Failed to load population data")
        return
    
    # Test ITN distribution
    print("\n5. Testing ITN distribution with 50,000 nets...")
    result = calculate_itn_distribution(
        data_handler,
        total_nets=50000,
        avg_household_size=5.0,
        urban_threshold=30.0,
        method='composite'
    )
    
    if result['status'] == 'success':
        stats = result['stats']
        print(f"\n✓ ITN Distribution Results:")
        print(f"  Total nets: {stats['total_nets']:,}")
        print(f"  Allocated: {stats['allocated']:,}")
        print(f"  Remaining: {stats['remaining']:,}")
        print(f"  Coverage: {stats['coverage_percent']}%")
        print(f"  Prioritized wards (rural): {stats['prioritized_wards']}")
        print(f"  Reprioritized wards (urban): {stats['reprioritized_wards']}")
        print(f"  Total population: {stats['total_population']:,}")
        print(f"  Covered population: {stats['covered_population']:,}")
        
        # Show top 5 allocations
        prioritized = result['prioritized']
        if len(prioritized) > 0:
            print(f"\n  Top 5 prioritized wards by allocation:")
            top_5 = prioritized.nlargest(5, 'nets_allocated')[['WardName', 'Population', 'nets_allocated']]
            for idx, row in top_5.iterrows():
                print(f"    {row['WardName']}: {int(row['Population']):,} people, {int(row['nets_allocated']):,} nets")
    else:
        print(f"\n✗ Error: {result['message']}")
    
    print("\n" + "=" * 60)
    print("Test completed!")

if __name__ == "__main__":
    main()