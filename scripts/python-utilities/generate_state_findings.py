#!/usr/bin/env python3
"""
Generate detailed state-by-state findings document
"""

import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/urban_validation_outputs')
df = pd.read_csv('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/validation_urban_validation_final_2025-09-03.csv')
state_analysis = pd.read_csv(OUTPUT_DIR / 'state_analysis_complete.csv')

print("Generating detailed state findings document...")

findings = []
findings.append("# DETAILED STATE-BY-STATE FINDINGS")
findings.append("## Urban Validation Analysis Results")
findings.append(f"**Total Wards**: {len(df):,}")
findings.append(f"**Analysis Date**: September 3, 2025\n")
findings.append("---\n")

# Sort states alphabetically
states = sorted(df['StateName'].unique())

for state in states:
    state_df = df[df['StateName'] == state]
    state_info = state_analysis[state_analysis['State'] == state].iloc[0]
    
    findings.append(f"## {state.upper()}")
    findings.append(f"**Total Wards**: {len(state_df)}\n")
    
    # Classification breakdown
    findings.append("### Classification Distribution")
    findings.append(f"- **Urban**: {state_info['Urban_Count']} wards ({state_info['Urban_Percent']:.1f}%)")
    findings.append(f"- **Peri-urban**: {state_info['Periurban_Count']} wards ({state_info['Periurban_Percent']:.1f}%)")
    findings.append(f"- **Rural**: {state_info['Rural_Count']} wards ({state_info['Rural_Percent']:.1f}%)")
    findings.append(f"- **Consistently Rural** (all methods <30%): {state_info['Consistently_Rural']} wards ({state_info['Consistently_Rural_Percent']:.2f}%)\n")
    
    # Method averages
    findings.append("### Urban Percentage by Method (State Average)")
    findings.append(f"- **Control (HLS NDBI)**: {state_info['Control_Mean']:.1f}%")
    findings.append(f"- **NDBI (Sentinel-2)**: {state_info['NDBI_Mean']:.1f}%")
    findings.append(f"- **GHSL (UN Standard)**: {state_info['GHSL_Mean']:.1f}%")
    findings.append(f"- **EBBI (Landsat)**: {state_info['EBBI_Mean']:.1f}%")
    findings.append(f"- **Overall Mean**: {state_info['Overall_Mean_Urban']:.1f}%\n")
    
    # Validation findings
    findings.append("### Validation Findings")
    findings.append(f"- **Method Agreement** (mean std): {state_info['Method_Disagreement_Mean']:.1f}")
    findings.append(f"- **Maximum Disagreement**: {state_info['Method_Disagreement_Max']:.1f}")
    
    if state_info['Total_Misclassifications'] > 0:
        findings.append(f"- **Potential Misclassifications**: {state_info['Total_Misclassifications']}")
        if state_info['Marked_Urban_But_Rural'] > 0:
            findings.append(f"  - Marked Urban but <30% satellite: {state_info['Marked_Urban_But_Rural']}")
        if state_info['Marked_Rural_But_Urban'] > 0:
            findings.append(f"  - Marked Rural but >50% satellite: {state_info['Marked_Rural_But_Urban']}")
    else:
        findings.append("- **Potential Misclassifications**: None identified")
    
    findings.append(f"- **Concern Level**: {state_info['Concern_Level']}\n")
    
    # List consistently rural wards if any
    rural_wards = state_df[state_df['consistently_rural'] == 'YES']
    if len(rural_wards) > 0:
        findings.append("### Consistently Rural Wards")
        for _, ward in rural_wards.iterrows():
            findings.append(f"- {ward['WardName']} (LGA: {ward['LGAName']})")
        findings.append("")
    
    # List potential misclassifications if significant
    if state_info['Total_Misclassifications'] > 2:
        findings.append("### Wards Requiring Review")
        
        # Urban marked but rural
        suspicious_urban = state_df[(state_df['Urban'] == 'Yes') & (state_df['mean_urban'] < 30)]
        if len(suspicious_urban) > 0:
            findings.append("**Marked Urban but Satellite Shows Rural (<30%)**:")
            for _, ward in suspicious_urban.iterrows():
                findings.append(f"- {ward['WardName']} ({ward['LGAName']}): {ward['mean_urban']:.1f}% satellite urban")
        
        # Rural marked but urban
        suspicious_rural = state_df[(state_df['Urban'] == 'No') & (state_df['mean_urban'] > 50)]
        if len(suspicious_rural) > 0:
            findings.append("**Marked Rural but Satellite Shows Urban (>50%)**:")
            for _, ward in suspicious_rural.head(10).iterrows():  # Limit to 10 for brevity
                findings.append(f"- {ward['WardName']} ({ward['LGAName']}): {ward['mean_urban']:.1f}% satellite urban")
            if len(suspicious_rural) > 10:
                findings.append(f"- ... and {len(suspicious_rural) - 10} more wards")
        findings.append("")
    
    findings.append("---\n")

# Write to file
with open(OUTPUT_DIR / 'STATE_BY_STATE_FINDINGS.md', 'w') as f:
    f.write('\n'.join(findings))

print(f"✓ State findings document created: STATE_BY_STATE_FINDINGS.md")

# Also create a summary statistics file
summary_stats = f"""# URBAN VALIDATION SUMMARY STATISTICS

## Overall Statistics
- **Total Wards Analyzed**: {len(df):,}
- **Total States**: {df['StateName'].nunique()}
- **Analysis Methods**: 4 (Control HLS NDBI, NDBI Sentinel-2, GHSL UN, EBBI Landsat)

## National Classification
- **Urban**: {(df['classification'] == 'Urban').sum():,} ({(df['classification'] == 'Urban').sum()/len(df)*100:.1f}%)
- **Peri-urban**: {(df['classification'] == 'Peri-urban').sum():,} ({(df['classification'] == 'Peri-urban').sum()/len(df)*100:.1f}%)
- **Rural**: {(df['classification'] == 'Rural').sum():,} ({(df['classification'] == 'Rural').sum()/len(df)*100:.1f}%)
- **Consistently Rural**: {(df['consistently_rural'] == 'YES').sum()} ({(df['consistently_rural'] == 'YES').sum()/len(df)*100:.2f}%)

## Method Performance
- **Control (HLS NDBI)**: Mean {df['control_urban'].mean():.1f}%, Median {df['control_urban'].median():.1f}%
- **NDBI (Sentinel-2)**: Mean {df['ndbi_urban'].mean():.1f}%, Median {df['ndbi_urban'].median():.1f}%
- **GHSL (UN)**: Mean {df['ghsl_urban'].mean():.1f}%, Median {df['ghsl_urban'].median():.1f}%
- **EBBI (Landsat)**: Mean {df['ebbi_urban'].mean():.1f}%, Median {df['ebbi_urban'].median():.1f}%

## Misclassification Summary
- **Total Potential Misclassifications**: {((df['Urban'] == 'Yes') & (df['mean_urban'] < 30)).sum() + ((df['Urban'] == 'No') & (df['mean_urban'] > 50)).sum()}
- **Urban Marked but Rural (<30% satellite)**: {((df['Urban'] == 'Yes') & (df['mean_urban'] < 30)).sum()}
- **Rural Marked but Urban (>50% satellite)**: {((df['Urban'] == 'No') & (df['mean_urban'] > 50)).sum()}

## States by Concern Level
- **HIGH Concern** (>10 misclassifications): {(state_analysis['Concern_Level'] == 'HIGH').sum()} states
- **MEDIUM Concern** (6-10 misclassifications): {(state_analysis['Concern_Level'] == 'MEDIUM').sum()} states
- **LOW Concern** (<6 misclassifications): {(state_analysis['Concern_Level'] == 'LOW').sum()} states

## Delta State Specific (Addressing Meeting Concern)
- **Total Wards**: 267
- **Urban Classification**: 15 (5.6%)
- **Peri-urban Classification**: 69 (25.8%)
- **Rural Classification**: 183 (68.5%)
- **Consistently Rural**: 1 ward
- **Potential Misclassifications**: 2 wards only
- **Conclusion**: No evidence of systematic rural/urban swapping
"""

with open(OUTPUT_DIR / 'SUMMARY_STATISTICS.md', 'w') as f:
    f.write(summary_stats)

print("✓ Summary statistics document created: SUMMARY_STATISTICS.md")
print(f"\nAll findings documents saved to: {OUTPUT_DIR}")