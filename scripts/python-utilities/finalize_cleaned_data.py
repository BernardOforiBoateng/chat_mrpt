#!/usr/bin/env python3
"""
Finalize cleaned TPR data
Consolidate all improvements and create final versions
"""

import pandas as pd
from pathlib import Path
import shutil

def finalize_cleaned_data():
    """Create final consolidated versions of cleaned data"""
    
    print("FINALIZING CLEANED TPR DATA")
    print("="*60)
    
    # Create final output directory
    final_dir = Path('www/final_cleaned_tpr_data')
    final_dir.mkdir(exist_ok=True)
    
    # States to process (19-37)
    states = [
        'kaduna', 'kano', 'katsina', 'kebbi', 'kogi', 'kwara', 
        'lagos', 'nasarawa', 'niger', 'ogun', 'ondo', 'osun', 
        'oyo', 'plateau', 'rivers', 'sokoto', 'taraba', 'yobe', 'zamfara'
    ]
    
    overall_stats = {
        'total_rows': 0,
        'total_matched': 0,
        'total_unmatched': 0
    }
    
    for state in states:
        # Check for smart matched version first
        smart_path = Path(f'www/cleaned_tpr_data/{state}_tpr_smart_matched.csv')
        original_path = Path(f'www/cleaned_tpr_data/{state}_tpr_cleaned.csv')
        
        # Use smart matched if available, otherwise original
        source_path = smart_path if smart_path.exists() else original_path
        
        if source_path.exists():
            # Load the data
            df = pd.read_csv(source_path)
            
            # Calculate statistics
            if 'Match_Status' in df.columns:
                matched = len(df[df['Match_Status'] == 'Matched'])
                unmatched = len(df[df['Match_Status'] == 'Unmatched'])
                match_rate = (matched / len(df)) * 100
                
                overall_stats['total_rows'] += len(df)
                overall_stats['total_matched'] += matched
                overall_stats['total_unmatched'] += unmatched
                
                print(f"\n{state.title()}:")
                print(f"  Source: {source_path.name}")
                print(f"  Rows: {len(df):,}")
                print(f"  Match rate: {match_rate:.1f}%")
                print(f"  Unmatched: {unmatched:,}")
                
                # Clean up columns for final version
                columns_to_keep = [col for col in df.columns if col != 'WardName_Mapped']
                df_final = df[columns_to_keep]
                
                # Save to final directory
                output_path = final_dir / f'{state}_tpr_final.csv'
                df_final.to_csv(output_path, index=False)
                print(f"  ✓ Saved: {output_path}")
            else:
                # If no Match_Status column, just copy the file
                shutil.copy2(source_path, final_dir / f'{state}_tpr_final.csv')
                print(f"\n{state.title()}: Copied from {source_path.name}")
    
    # Create summary report
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    print(f"Total states processed: {len(states)}")
    print(f"Total rows: {overall_stats['total_rows']:,}")
    print(f"Total matched: {overall_stats['total_matched']:,}")
    print(f"Total unmatched: {overall_stats['total_unmatched']:,}")
    
    if overall_stats['total_rows'] > 0:
        final_match_rate = (overall_stats['total_matched'] / overall_stats['total_rows']) * 100
        print(f"\nFINAL OVERALL MATCH RATE: {final_match_rate:.1f}%")
        
        if final_match_rate >= 95:
            print("✓ EXCELLENT: Achieved >95% match rate!")
        elif final_match_rate >= 90:
            print("✓ VERY GOOD: Achieved >90% match rate!")
        elif final_match_rate >= 85:
            print("✓ GOOD: Achieved >85% match rate!")
    
    # Create a summary CSV
    summary_data = []
    for state in states:
        final_path = final_dir / f'{state}_tpr_final.csv'
        if final_path.exists():
            df = pd.read_csv(final_path)
            if 'Match_Status' in df.columns:
                matched = len(df[df['Match_Status'] == 'Matched'])
                unmatched = len(df[df['Match_Status'] == 'Unmatched'])
                match_rate = (matched / len(df)) * 100
                
                summary_data.append({
                    'State': state.title(),
                    'Total_Rows': len(df),
                    'Matched_Rows': matched,
                    'Unmatched_Rows': unmatched,
                    'Match_Rate_%': round(match_rate, 1),
                    'Unique_Wards': df['WardName'].nunique()
                })
    
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(final_dir / 'cleaning_summary.csv', index=False)
        print(f"\n✓ Saved summary report: {final_dir}/cleaning_summary.csv")
    
    print(f"\n✅ FINALIZATION COMPLETE!")
    print(f"All final files saved to: {final_dir}/")
    print(f"Files are named: {{state}}_tpr_final.csv")
    
    return overall_stats


if __name__ == "__main__":
    finalize_cleaned_data()