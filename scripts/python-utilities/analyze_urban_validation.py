#!/usr/bin/env python3
"""
Urban Validation Analysis Script
Analyzes GEE export results to generate Thursday meeting report
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path
import json

def analyze_validation(csv_path):
    """Analyze urban validation results from GEE export"""
    
    print("=" * 60)
    print("URBAN VALIDATION ANALYSIS REPORT")
    print("=" * 60)
    
    # Load data
    df = pd.read_csv(csv_path)
    print(f"\nTotal wards analyzed: {len(df)}")
    
    # Check for missing data
    print("\n--- DATA COMPLETENESS ---")
    for col in ['control_urban', 'ndbi_urban', 'ghsl_urban', 'nightlights_urban']:
        if col in df.columns:
            missing = df[col].isna().sum()
            print(f"{col}: {len(df) - missing}/{len(df)} valid ({(1-missing/len(df))*100:.1f}% complete)")
    
    # Overall classification
    print("\n--- CLASSIFICATION DISTRIBUTION ---")
    if 'classification' in df.columns:
        class_dist = df['classification'].value_counts()
        for cls, count in class_dist.items():
            print(f"{cls}: {count} wards ({count/len(df)*100:.1f}%)")
    
    # Consistently rural analysis
    print("\n--- CONSISTENTLY RURAL WARDS ---")
    if 'consistently_rural' in df.columns:
        rural_yes = df[df['consistently_rural'] == 'YES']
        print(f"Wards consistently rural across ALL methods: {len(rural_yes)}")
        print(f"Percentage of total: {len(rural_yes)/len(df)*100:.1f}%")
        
        # By state analysis
        if 'StateName' in df.columns:
            print("\n--- CONSISTENTLY RURAL BY STATE ---")
            state_rural = rural_yes.groupby('StateName').size().sort_values(ascending=False)
            for state, count in state_rural.head(10).items():
                state_total = len(df[df['StateName'] == state])
                print(f"{state}: {count}/{state_total} wards ({count/state_total*100:.1f}%)")
    
    # Method comparison
    print("\n--- METHOD COMPARISON ---")
    methods = ['control_urban', 'ndbi_urban', 'ghsl_urban', 'nightlights_urban']
    existing_methods = [m for m in methods if m in df.columns]
    
    if existing_methods:
        stats = df[existing_methods].describe()
        print("\nMean urban percentage by method:")
        for method in existing_methods:
            print(f"{method}: {df[method].mean():.1f}%")
        
        print("\nMedian urban percentage by method:")
        for method in existing_methods:
            print(f"{method}: {df[method].median():.1f}%")
        
        # Agreement analysis
        print("\n--- METHOD AGREEMENT ---")
        threshold = 30  # Urban threshold
        
        for i, m1 in enumerate(existing_methods):
            for m2 in existing_methods[i+1:]:
                m1_urban = df[m1] >= threshold
                m2_urban = df[m2] >= threshold
                agreement = (m1_urban == m2_urban).mean() * 100
                print(f"{m1} vs {m2}: {agreement:.1f}% agreement")
    
    # Delta State specific analysis
    print("\n--- DELTA STATE ANALYSIS ---")
    if 'StateName' in df.columns and 'Delta' in df['StateName'].values:
        delta_df = df[df['StateName'] == 'Delta']
        print(f"Total Delta State wards: {len(delta_df)}")
        
        if 'consistently_rural' in delta_df.columns:
            delta_rural = delta_df[delta_df['consistently_rural'] == 'YES']
            print(f"Consistently rural in Delta: {len(delta_rural)} ({len(delta_rural)/len(delta_df)*100:.1f}%)")
            
            # Check if any were marked as Urban in original data
            if 'Urban' in delta_df.columns:
                mismatched = delta_rural[delta_rural['Urban'] == 'Yes']
                if len(mismatched) > 0:
                    print(f"\n⚠️ POTENTIAL ISSUE: {len(mismatched)} wards in Delta State")
                    print(f"   are consistently rural by satellite but marked as Urban")
                    print("\n   Sample mismatched wards:")
                    for _, ward in mismatched.head(5).iterrows():
                        print(f"   - {ward['WardName']}: {ward['mean_urban']:.1f}% urban (satellite avg)")
    
    # Suspicious patterns
    print("\n--- VALIDATION FLAGS ---")
    
    # Find extreme disagreements
    if 'mean_urban' in df.columns:
        # High disagreement wards
        df['method_std'] = df[existing_methods].std(axis=1)
        high_disagreement = df[df['method_std'] > 30].sort_values('method_std', ascending=False)
        
        if len(high_disagreement) > 0:
            print(f"\nWards with high method disagreement (std > 30): {len(high_disagreement)}")
            print("Top 5 disagreement cases:")
            for _, ward in high_disagreement.head(5).iterrows():
                print(f"  {ward.get('WardName', 'Unknown')} ({ward.get('StateName', 'Unknown')}): std={ward['method_std']:.1f}")
    
    # Export summary
    print("\n--- RECOMMENDATIONS ---")
    print("1. Wards marked 'consistently_rural=YES' should NOT be urban-targeted")
    print("2. Review wards with high method disagreement for manual verification")
    print("3. Consider using GHSL as primary method (UN standard)")
    print("4. Night lights may underestimate peri-urban areas")
    
    # Save detailed report
    report_path = Path(csv_path).parent / "validation_report.txt"
    with open(report_path, 'w') as f:
        # Redirect print to file
        original_stdout = sys.stdout
        sys.stdout = f
        
        # Re-run all analysis to file
        analyze_validation(csv_path)
        
        sys.stdout = original_stdout
    
    print(f"\n✓ Detailed report saved to: {report_path}")
    
    # Create filtered dataset of suspicious wards
    if 'consistently_rural' in df.columns:
        suspicious = df[df['consistently_rural'] == 'YES']
        if 'Urban' in suspicious.columns:
            suspicious = suspicious[suspicious['Urban'] == 'Yes']
            if len(suspicious) > 0:
                suspicious_path = Path(csv_path).parent / "suspicious_urban_rural_mismatch.csv"
                suspicious.to_csv(suspicious_path, index=False)
                print(f"✓ Suspicious wards exported to: {suspicious_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_urban_validation.py <path_to_csv>")
        print("\nExample:")
        print("  python analyze_urban_validation.py ~/Downloads/urban_validation_final_2024-01-03.csv")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    if not Path(csv_path).exists():
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)
    
    analyze_validation(csv_path)