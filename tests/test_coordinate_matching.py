#!/usr/bin/env python3
"""Test coordinate-based matching between population and unified datasets."""

import sys
import os
import pandas as pd
import numpy as np
from math import radians, cos, sin, asin, sqrt

# Add the app directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.analysis.itn_pipeline import load_population_data

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on Earth (in km)."""
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of Earth in kilometers
    return c * r

def main():
    """Test coordinate-based matching."""
    print("Testing Coordinate-Based Ward Matching")
    print("=" * 60)
    
    # Load unified dataset
    session_id = "6e90b139-5d30-40fd-91ad-4af66fec5f00"
    unified_path = f"instance/uploads/{session_id}/unified_dataset.csv"
    unified_df = pd.read_csv(unified_path)
    print(f"\n1. Loaded unified dataset with {len(unified_df)} wards")
    
    # Check coordinate availability in unified dataset
    has_coords = unified_df[['centroid_lat', 'centroid_lon']].notna().all(axis=1).sum()
    print(f"   Wards with coordinates: {has_coords}/{len(unified_df)}")
    
    # Load population data
    pop_data_raw = load_population_data('Kano')
    print(f"\n2. Loaded raw population data with {len(pop_data_raw)} ward-LGA combinations")
    
    # Load raw population CSV to get distribution point coordinates
    pop_csv_path = 'app/data/population_data/pbi_distribution_Kano.csv'
    try:
        pop_dist = pd.read_csv(pop_csv_path, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            pop_dist = pd.read_csv(pop_csv_path, encoding='latin-1')
        except:
            pop_dist = pd.read_csv(pop_csv_path, encoding='cp1252')
    
    print(f"\n3. Loaded population distribution data with {len(pop_dist)} distribution points")
    
    # Check coordinate availability
    pop_has_coords = pop_dist[['AvgLatitude', 'AvgLongitude']].notna().all(axis=1).sum()
    print(f"   Distribution points with coordinates: {pop_has_coords}/{len(pop_dist)}")
    
    # Aggregate population data by ward with average coordinates
    print("\n4. Aggregating population data by ward with average coordinates...")
    pop_ward_coords = pop_dist.groupby(['AdminLevel3', 'AdminLevel2']).agg({
        'N_FamilyMembers': 'sum',
        'AvgLatitude': 'mean',
        'AvgLongitude': 'mean',
        'N_Distributions': 'sum'
    }).reset_index()
    pop_ward_coords.columns = ['WardName', 'LGA', 'Population', 'AvgLatitude', 'AvgLongitude', 'N_DistPoints']
    print(f"   Aggregated to {len(pop_ward_coords)} ward-LGA combinations")
    
    # Test coordinate matching for problem wards
    print("\n5. Testing coordinate matching for problem wards:")
    problem_wards = ['Dawaki', 'Falgore', 'Goron Dutse', 'Gurjiya', 'Gwarmai']
    
    for ward_prefix in problem_wards:
        print(f"\n   Ward: {ward_prefix}")
        
        # Find in unified dataset
        unified_wards = unified_df[unified_df['WardName'].str.startswith(ward_prefix)]
        if len(unified_wards) == 0:
            continue
            
        # Find in population data
        pop_wards = pop_ward_coords[pop_ward_coords['WardName'] == ward_prefix]
        if len(pop_wards) == 0:
            print(f"     Not found in population data")
            continue
        
        # Calculate distances between all combinations
        print(f"     Found {len(unified_wards)} in unified, {len(pop_wards)} in population")
        
        for _, u_row in unified_wards.iterrows():
            print(f"\n     Unified: {u_row['WardName']} (lat: {u_row['centroid_lat']:.4f}, lon: {u_row['centroid_lon']:.4f})")
            
            # Calculate distance to each population ward
            for _, p_row in pop_wards.iterrows():
                dist = haversine_distance(
                    u_row['centroid_lat'], u_row['centroid_lon'],
                    p_row['AvgLatitude'], p_row['AvgLongitude']
                )
                print(f"       Population: {p_row['WardName']} in {p_row['LGA']} (lat: {p_row['AvgLatitude']:.4f}, lon: {p_row['AvgLongitude']:.4f}) - Distance: {dist:.2f} km")
    
    # Test complete matching using nearest neighbor approach
    print("\n6. Testing complete coordinate-based matching:")
    
    # For each ward in unified dataset, find nearest in population data
    matches = []
    threshold_km = 5.0  # Maximum distance threshold in kilometers
    
    for idx, u_row in unified_df.iterrows():
        if pd.isna(u_row['centroid_lat']) or pd.isna(u_row['centroid_lon']):
            continue
        
        # Calculate distances to all population wards
        pop_ward_coords['distance'] = pop_ward_coords.apply(
            lambda p_row: haversine_distance(
                u_row['centroid_lat'], u_row['centroid_lon'],
                p_row['AvgLatitude'], p_row['AvgLongitude']
            ) if pd.notna(p_row['AvgLatitude']) and pd.notna(p_row['AvgLongitude']) else float('inf'),
            axis=1
        )
        
        # Find nearest match
        nearest = pop_ward_coords.nsmallest(1, 'distance').iloc[0]
        
        if nearest['distance'] <= threshold_km:
            matches.append({
                'unified_ward': u_row['WardName'],
                'unified_lga': u_row['LGACode'],
                'pop_ward': nearest['WardName'],
                'pop_lga': nearest['LGA'],
                'distance_km': nearest['distance'],
                'population': nearest['Population']
            })
    
    matches_df = pd.DataFrame(matches)
    print(f"   Matched {len(matches_df)} wards within {threshold_km} km threshold")
    
    # Check if this resolves the problem wards
    print("\n7. Checking if coordinate matching resolves problem wards:")
    for ward_prefix in problem_wards:
        ward_matches = matches_df[matches_df['unified_ward'].str.startswith(ward_prefix)]
        if len(ward_matches) > 0:
            print(f"\n   {ward_prefix}:")
            for _, m in ward_matches.iterrows():
                print(f"     {m['unified_ward']} -> {m['pop_ward']} in {m['pop_lga']} ({m['distance_km']:.2f} km)")
    
    print("\n" + "=" * 60)
    print(f"Summary: Coordinate matching found {len(matches_df)} matches out of {len(unified_df)} wards")

if __name__ == "__main__":
    main()