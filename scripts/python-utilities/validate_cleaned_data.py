#!/usr/bin/env python3
"""
Validation script for cleaned TPR data
Verifies the quality of ward name matching and provides statistics
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

def validate_cleaned_data():
    """Validate all cleaned TPR files"""
    
    # Load shapefile for validation
    print("Loading shapefile for validation...")
    gdf = gpd.read_file('www/complete_names_wards/wards.shp')
    
    # Get list of cleaned files
    cleaned_files = list(Path('www').glob('*_tpr_cleaned.csv'))
    cleaned_files.sort()
    
    print(f"\nFound {len(cleaned_files)} cleaned files to validate")
    print("="*60)
    
    # Overall statistics
    total_stats = {
        'total_rows': 0,
        'total_matched': 0,
        'total_unmatched': 0,
        'states_processed': 0
    }
    
    # Validate each file
    for file_path in cleaned_files:
        state_name = file_path.stem.replace('_tpr_cleaned', '').title()
        print(f"\nValidating {state_name}...")
        
        # Read cleaned file
        df = pd.read_csv(file_path)
        
        # Get standard wards for this state
        state_wards = set(gdf[gdf['StateName'] == state_name]['WardName'].dropna().unique())
        
        if not state_wards:
            # Try with different capitalization
            for s in gdf['StateName'].unique():
                if s and s.lower() == state_name.lower():
                    state_wards = set(gdf[gdf['StateName'] == s]['WardName'].dropna().unique())
                    state_name = s
                    break
        
        # Check matching status
        if 'Match_Status' in df.columns:
            matched = df[df['Match_Status'] == 'Matched']
            unmatched = df[df['Match_Status'] == 'Unmatched']
            
            print(f"  Total rows: {len(df):,}")
            print(f"  Matched rows: {len(matched):,} ({len(matched)/len(df)*100:.1f}%)")
            print(f"  Unmatched rows: {len(unmatched):,} ({len(unmatched)/len(df)*100:.1f}%)")
            
            # Check unique wards
            unique_wards = df['WardName'].nunique()
            matched_wards = df[df['Match_Status'] == 'Matched']['WardName'].nunique()
            
            print(f"  Unique wards: {unique_wards}")
            print(f"  Matched unique wards: {matched_wards} ({matched_wards/unique_wards*100:.1f}%)")
            
            # Update total stats
            total_stats['total_rows'] += len(df)
            total_stats['total_matched'] += len(matched)
            total_stats['total_unmatched'] += len(unmatched)
            total_stats['states_processed'] += 1
            
            # Show sample of unmatched wards
            if len(unmatched) > 0:
                unmatched_sample = unmatched['WardName_Original'].dropna().unique()[:5]
                if len(unmatched_sample) > 0:
                    print(f"  Sample unmatched wards:")
                    for ward in unmatched_sample:
                        print(f"    - {ward}")
        else:
            print(f"  Warning: No Match_Status column found in {file_path}")
            print(f"  Total rows: {len(df):,}")
            print(f"  Unique wards: {df['WardName'].nunique()}")
    
    # Print overall summary
    print("\n" + "="*60)
    print("OVERALL VALIDATION SUMMARY")
    print("="*60)
    print(f"States processed: {total_stats['states_processed']}")
    print(f"Total rows: {total_stats['total_rows']:,}")
    print(f"Total matched: {total_stats['total_matched']:,} ({total_stats['total_matched']/total_stats['total_rows']*100:.1f}%)")
    print(f"Total unmatched: {total_stats['total_unmatched']:,} ({total_stats['total_unmatched']/total_stats['total_rows']*100:.1f}%)")
    
    # Quality assessment
    match_rate = total_stats['total_matched'] / total_stats['total_rows'] * 100
    print(f"\nOverall Match Rate: {match_rate:.1f}%")
    
    if match_rate >= 95:
        print("✓ EXCELLENT: Data cleaning achieved >95% match rate")
    elif match_rate >= 90:
        print("✓ GOOD: Data cleaning achieved >90% match rate")
    elif match_rate >= 80:
        print("⚠ ACCEPTABLE: Data cleaning achieved >80% match rate")
    else:
        print("✗ NEEDS IMPROVEMENT: Match rate below 80%")
    
    return total_stats


def check_specific_state(state_name):
    """Check a specific state's cleaned data in detail"""
    
    file_path = Path(f'www/{state_name.lower()}_tpr_cleaned.csv')
    
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return
    
    print(f"\nDetailed validation for {state_name}")
    print("="*60)
    
    # Load data
    df = pd.read_csv(file_path)
    gdf = gpd.read_file('www/complete_names_wards/wards.shp')
    
    # Get standard wards
    state_wards = set(gdf[gdf['StateName'] == state_name]['WardName'].dropna().unique())
    
    # Check each unique ward
    unique_wards = df['WardName'].dropna().unique()
    
    matched_to_standard = []
    not_in_standard = []
    
    for ward in unique_wards:
        if ward in state_wards:
            matched_to_standard.append(ward)
        else:
            not_in_standard.append(ward)
    
    print(f"Unique wards in cleaned data: {len(unique_wards)}")
    print(f"Wards matching shapefile standard: {len(matched_to_standard)} ({len(matched_to_standard)/len(unique_wards)*100:.1f}%)")
    print(f"Wards not in shapefile: {len(not_in_standard)} ({len(not_in_standard)/len(unique_wards)*100:.1f}%)")
    
    if not_in_standard:
        print(f"\nWards not found in shapefile (first 10):")
        for ward in not_in_standard[:10]:
            print(f"  - {ward}")
            # Find original name
            if 'WardName_Original' in df.columns:
                original = df[df['WardName'] == ward]['WardName_Original'].iloc[0] if len(df[df['WardName'] == ward]) > 0 else 'N/A'
                print(f"    (original: {original})")


if __name__ == "__main__":
    # Run overall validation
    stats = validate_cleaned_data()
    
    # Example: Check specific state in detail
    # check_specific_state('Kaduna')