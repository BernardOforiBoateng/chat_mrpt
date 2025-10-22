#!/usr/bin/env python3
"""Analyze UNIQUE ward matching (not facility-level)"""

import pandas as pd
from pathlib import Path

def analyze_unique_wards():
    cleaned_dir = Path("www/all_states_cleaned")
    
    print("=" * 80)
    print("UNIQUE WARD-LEVEL MATCHING ANALYSIS")
    print("(Not counting duplicate rows for multiple facilities)")
    print("=" * 80)
    
    results = []
    
    for file_path in sorted(cleaned_dir.glob("*_tpr_cleaned.csv")):
        state_name = file_path.stem.replace("_tpr_cleaned", "").replace("_", " ").title()
        
        df = pd.read_csv(file_path)
        
        # Get UNIQUE wards only
        unique_wards = df[['WardName_Original', 'Match_Status']].drop_duplicates()
        
        total_unique_wards = len(unique_wards)
        unmatched_unique_wards = len(unique_wards[unique_wards['Match_Status'] == 'Unmatched'])
        matched_unique_wards = total_unique_wards - unmatched_unique_wards
        match_rate = (matched_unique_wards / total_unique_wards * 100) if total_unique_wards > 0 else 0
        
        # Also count facilities to show the multiplication effect
        total_facilities = len(df)
        unmatched_facilities = len(df[df['Match_Status'] == 'Unmatched'])
        
        results.append({
            'state': state_name,
            'unique_wards': total_unique_wards,
            'unmatched_wards': unmatched_unique_wards,
            'matched_wards': matched_unique_wards,
            'match_rate': match_rate,
            'total_facilities': total_facilities,
            'unmatched_facilities': unmatched_facilities,
            'facilities_per_ward': total_facilities / total_unique_wards if total_unique_wards > 0 else 0
        })
    
    # Sort by match rate
    results = sorted(results, key=lambda x: x['match_rate'])
    
    print("\n" + "=" * 80)
    print("STATES BY UNIQUE WARD MATCH RATE (Worst to Best):")
    print("-" * 80)
    print(f"{'State':<25} | {'Unique Wards':>12} | {'Unmatched':>10} | {'Match Rate':>10} | {'Facilities/Ward':>15}")
    print("-" * 80)
    
    for r in results:
        flag = "⚠️ " if r['match_rate'] < 90 else "✅ " if r['match_rate'] >= 95 else "  "
        print(f"{flag}{r['state']:<23} | {r['unique_wards']:>12} | {r['unmatched_wards']:>10} | {r['match_rate']:>9.2f}% | {r['facilities_per_ward']:>15.1f}")
    
    print("\n" + "=" * 80)
    print("OVERALL STATISTICS (UNIQUE WARDS ONLY):")
    print("=" * 80)
    
    total_unique_wards = sum(r['unique_wards'] for r in results)
    total_unmatched_wards = sum(r['unmatched_wards'] for r in results)
    total_matched_wards = sum(r['matched_wards'] for r in results)
    overall_match_rate = (total_matched_wards / total_unique_wards * 100) if total_unique_wards > 0 else 0
    
    print(f"Total unique wards across all states: {total_unique_wards:,}")
    print(f"Total matched unique wards: {total_matched_wards:,}")
    print(f"Total unmatched unique wards: {total_unmatched_wards:,}")
    print(f"Overall unique ward match rate: {overall_match_rate:.2f}%")
    
    # Show the multiplication effect
    print("\n" + "=" * 80)
    print("MULTIPLICATION EFFECT (Why numbers looked bad):")
    print("=" * 80)
    
    total_facilities = sum(r['total_facilities'] for r in results)
    total_unmatched_facilities = sum(r['unmatched_facilities'] for r in results)
    
    print(f"Total facility rows: {total_facilities:,}")
    print(f"Total unmatched facility rows: {total_unmatched_facilities:,}")
    print(f"Average facilities per ward: {total_facilities/total_unique_wards:.1f}")
    print(f"\n⚠️  Each unmatched ward gets counted {total_facilities/total_unique_wards:.0f}+ times in the raw data!")
    
    # Identify states needing attention (based on unique wards)
    print("\n" + "=" * 80)
    print("STATES NEEDING ATTENTION (Unique ward match rate < 90%):")
    print("-" * 80)
    
    needs_attention = [r for r in results if r['match_rate'] < 90]
    if needs_attention:
        for r in needs_attention:
            print(f"  {r['state']}: {r['unmatched_wards']} unmatched wards ({r['match_rate']:.2f}% match rate)")
    else:
        print("  None! All states have ≥90% unique ward match rate")
    
    return results

if __name__ == "__main__":
    results = analyze_unique_wards()