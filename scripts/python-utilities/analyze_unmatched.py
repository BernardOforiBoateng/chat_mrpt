#!/usr/bin/env python3
"""Analyze unmatched wards in cleaned TPR data"""

import pandas as pd
from pathlib import Path

def analyze_unmatched():
    cleaned_dir = Path("www/all_states_cleaned")
    
    print("=" * 80)
    print("DETAILED UNMATCHED WARD ANALYSIS")
    print("=" * 80)
    
    total_unmatched_all = 0
    results = []
    
    for file_path in sorted(cleaned_dir.glob("*_tpr_cleaned.csv")):
        state_name = file_path.stem.replace("_tpr_cleaned", "").replace("_", " ").title()
        
        df = pd.read_csv(file_path)
        
        # Check for unmatched
        if 'Match_Status' in df.columns:
            unmatched_df = df[df['Match_Status'] == 'Unmatched']
            unmatched_count = len(unmatched_df)
        else:
            unmatched_count = 0
            
        total_rows = len(df)
        matched_count = total_rows - unmatched_count
        match_rate = (matched_count / total_rows * 100) if total_rows > 0 else 0
        
        total_unmatched_all += unmatched_count
        
        results.append({
            'state': state_name,
            'unmatched': unmatched_count,
            'total': total_rows,
            'rate': match_rate
        })
        
    # Sort by unmatched count (highest first)
    results = sorted(results, key=lambda x: x['unmatched'], reverse=True)
    
    print("\nStates with highest unmatched counts:")
    print("-" * 80)
    print(f"{'State':<30} | {'Unmatched':>10} | {'Total':>10} | {'Match Rate':>10}")
    print("-" * 80)
    
    for r in results[:15]:  # Top 15 worst
        flag = "⚠️ " if r['unmatched'] > 500 else "  "
        print(f"{flag}{r['state']:<28} | {r['unmatched']:>10,} | {r['total']:>10,} | {r['rate']:>9.2f}%")
    
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    
    # Calculate averages
    avg_unmatched = sum(r['unmatched'] for r in results) / len(results)
    states_over_100 = sum(1 for r in results if r['unmatched'] > 100)
    states_over_500 = sum(1 for r in results if r['unmatched'] > 500)
    states_over_1000 = sum(1 for r in results if r['unmatched'] > 1000)
    
    print(f"Total unmatched wards across all states: {total_unmatched_all:,}")
    print(f"Average unmatched per state: {avg_unmatched:.0f}")
    print(f"States with >100 unmatched: {states_over_100}")
    print(f"States with >500 unmatched: {states_over_500}")
    print(f"States with >1000 unmatched: {states_over_1000}")
    
    # Show best performing states
    print("\n" + "=" * 80)
    print("BEST PERFORMING STATES (Fewest unmatched):")
    print("-" * 80)
    
    best = sorted(results, key=lambda x: x['unmatched'])[:10]
    for r in best:
        print(f"✅ {r['state']:<28} | {r['unmatched']:>10,} unmatched | {r['rate']:>6.2f}% match rate")
    
    # Check if problem is at facility level (multiple facilities per ward)
    print("\n" + "=" * 80)
    print("CHECKING DATA STRUCTURE...")
    print("-" * 80)
    
    # Sample check on one state
    sample_file = list(cleaned_dir.glob("*kano*_tpr_cleaned.csv"))[0]
    df_sample = pd.read_csv(sample_file)
    
    print(f"\nSample from Kano State:")
    print(f"Total rows: {len(df_sample):,}")
    print(f"Unique wards: {df_sample['WardName'].nunique():,}")
    print(f"Unique facilities: {df_sample['HealthFacility'].nunique() if 'HealthFacility' in df_sample.columns else 'N/A'}")
    
    if len(df_sample) > df_sample['WardName'].nunique():
        print("\n⚠️  IMPORTANT: Data has multiple rows per ward (likely one per health facility)")
        print("This explains the high 'unmatched' counts - each facility in an unmatched ward counts separately!")
    
    return results

if __name__ == "__main__":
    results = analyze_unmatched()