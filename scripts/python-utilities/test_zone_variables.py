#!/usr/bin/env python3
"""Quick test for updated zone variables"""

import pandas as pd
import sys
sys.path.insert(0, '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT')

from app.analysis.region_aware_selection import (
    ZONE_VARIABLES,
    CORE_VARIABLES,
    detect_geopolitical_zone,
    select_variables_by_zone
)

def test_zone_variables():
    print("=" * 60)
    print("Testing Updated Zone Variables")
    print("=" * 60)

    # Display new zone variables
    print("\n📊 Updated Zone Variables from CSV:")
    for zone, variables in ZONE_VARIABLES.items():
        print(f"\n{zone} ({len(variables)} variables):")
        for var in variables:
            print(f"  • {var}")

    print(f"\n🎯 Core Variables: {CORE_VARIABLES}")

    # Test with sample data
    print("\n" + "=" * 60)
    print("Testing Variable Selection")
    print("=" * 60)

    # Create sample data for North Central zone
    sample_data = pd.DataFrame({
        'WardName': ['Ward1', 'Ward2', 'Ward3'],
        'State': ['Benue', 'Benue', 'Benue'],
        'u5_tpr_rdt': [0.25, 0.30, 0.28],
        'nighttime_lights': [0.5, 0.6, 0.4],
        'housing_quality': [3, 4, 3],
        'soil_wetness': [0.7, 0.8, 0.75],
        'distance_to_waterbodies': [500, 600, 450],
        'ndmi': [0.3, 0.35, 0.32],
        'rainfall': [120, 115, 125],
        'elevation': [200, 210, 195]
    })

    # Detect zone
    zone, method = detect_geopolitical_zone(sample_data)
    print(f"\n✅ Detected Zone: {zone} (via {method})")

    # Get available variables
    available_vars = [col for col in sample_data.columns
                     if col not in ['WardName', 'State']]
    print(f"\n📋 Available Variables: {available_vars}")

    # Select variables for zone
    selected = select_variables_by_zone(zone, available_vars)
    print(f"\n🎯 Selected Variables for {zone}:")
    for var in selected:
        print(f"  ✓ {var}")

    # Compare with expected
    expected = ZONE_VARIABLES.get(zone, [])
    matched = [v for v in selected if v in expected]
    print(f"\n📊 Match Rate: {len(matched)}/{len(expected)} expected variables found")

    # Test other zones
    print("\n" + "=" * 60)
    print("Testing All Zones")
    print("=" * 60)

    test_states = {
        'North_Central': 'Plateau',
        'North_East': 'Adamawa',
        'North_West': 'Kano',
        'South_East': 'Enugu',
        'South_South': 'Rivers',
        'South_West': 'Lagos'
    }

    for zone, state in test_states.items():
        test_df = pd.DataFrame({'State': [state], 'WardName': ['Test']})
        detected_zone, _ = detect_geopolitical_zone(test_df)
        status = "✅" if detected_zone == zone else "❌"
        print(f"{status} {zone}: {state} → {detected_zone}")

    print("\n✅ Zone variables test complete!")

if __name__ == "__main__":
    test_zone_variables()