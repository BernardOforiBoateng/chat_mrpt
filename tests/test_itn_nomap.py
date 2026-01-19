#!/usr/bin/env python3
"""Test ITN distribution without map generation."""

import sys
import os
import pandas as pd
import geopandas as gpd

# Add the app directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Set up logging to see the matching statistics
import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Temporarily disable map generation
import app.analysis.itn_pipeline as itn
original_generate_map = itn.generate_itn_map
itn.generate_itn_map = lambda *args, **kwargs: "test_map.html"

from app.analysis.itn_pipeline import calculate_itn_distribution, detect_state, load_population_data

class SimpleDataHandler:
    """Simple data handler for testing."""
    def __init__(self, session_id):
        self.session_id = session_id
        self.unified_dataset = None
        self.shapefile_data = None

def main():
    """Run ITN distribution test without map."""
    print("ITN Distribution Test (No Map)")
    print("=" * 60)
    
    # Create simple data handler
    session_id = "6e90b139-5d30-40fd-91ad-4af66fec5f00"
    data_handler = SimpleDataHandler(session_id)
    
    # Load unified dataset
    data_handler.unified_dataset = pd.read_csv(f"instance/uploads/{session_id}/unified_dataset.csv")
    print(f"Loaded {len(data_handler.unified_dataset)} wards")
    
    # Load shapefile
    data_handler.shapefile_data = gpd.read_file(f"instance/uploads/{session_id}/shapefile/raw.shp")
    
    # Run ITN distribution
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
        print(f"  Coverage: {stats['coverage_percent']}%")
        print(f"  Total population: {stats['total_population']:,}")
        print(f"  Covered population: {stats['covered_population']:,}")
        
        # Check how many wards got allocations
        prioritized = result['prioritized']
        wards_with_nets = len(prioritized[prioritized['nets_allocated'] > 0])
        print(f"  Wards receiving nets: {wards_with_nets}/{len(prioritized)}")
        
        # Show matching statistics from logs
        print(f"\nCheck terminal output above for matching statistics!")
    else:
        print(f"\n✗ Error: {result['message']}")

if __name__ == "__main__":
    main()