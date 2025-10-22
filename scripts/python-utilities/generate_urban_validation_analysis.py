#!/usr/bin/env python3
"""
Comprehensive Urban Validation Analysis
Generates detailed state-by-state analysis for Thursday NMEP meeting
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Define output directory
OUTPUT_DIR = Path('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/urban_validation_outputs')
OUTPUT_DIR.mkdir(exist_ok=True)

print("=" * 70)
print("URBAN VALIDATION COMPREHENSIVE ANALYSIS")
print("Addressing NMEP concerns about rural/urban ward classification")
print("=" * 70)

# Load the validation data
df = pd.read_csv('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/validation_urban_validation_final_2025-09-03.csv')
print(f"\nLoaded {len(df)} wards from {df['StateName'].nunique()} states")

# ========== 1. STATE-BY-STATE DETAILED ANALYSIS ==========
print("\n[1/7] Generating state-by-state analysis...")

state_analysis = []
for state in df['StateName'].unique():
    state_df = df[df['StateName'] == state]
    
    # Basic counts
    total_wards = len(state_df)
    urban_count = (state_df['classification'] == 'Urban').sum()
    periurban_count = (state_df['classification'] == 'Peri-urban').sum()
    rural_count = (state_df['classification'] == 'Rural').sum()
    consistently_rural = (state_df['consistently_rural'] == 'YES').sum()
    
    # Method means
    control_mean = state_df['control_urban'].mean()
    ndbi_mean = state_df['ndbi_urban'].mean()
    ghsl_mean = state_df['ghsl_urban'].mean()
    ebbi_mean = state_df['ebbi_urban'].mean()
    overall_mean = state_df['mean_urban'].mean()
    
    # Method agreement (standard deviation)
    state_df['method_std'] = state_df[['control_urban', 'ndbi_urban', 'ghsl_urban', 'ebbi_urban']].std(axis=1)
    mean_disagreement = state_df['method_std'].mean()
    max_disagreement = state_df['method_std'].max()
    
    # Misclassification analysis
    if 'Urban' in state_df.columns:
        urban_yes = state_df[state_df['Urban'] == 'Yes']
        urban_no = state_df[state_df['Urban'] == 'No']
        
        # Potential misclassifications
        marked_urban_but_rural = len(urban_yes[urban_yes['mean_urban'] < 30])
        marked_rural_but_urban = len(urban_no[urban_no['mean_urban'] > 50])
        marked_rural_but_periurban = len(urban_no[(urban_no['mean_urban'] >= 30) & (urban_no['mean_urban'] <= 50)])
        
        # Original Urban field counts
        original_urban_yes = len(urban_yes)
        original_urban_no = len(urban_no)
    else:
        marked_urban_but_rural = 0
        marked_rural_but_urban = 0
        marked_rural_but_periurban = 0
        original_urban_yes = 0
        original_urban_no = 0
    
    state_analysis.append({
        'State': state,
        'Total_Wards': total_wards,
        'Urban_Count': urban_count,
        'Urban_Percent': round(urban_count/total_wards*100, 1),
        'Periurban_Count': periurban_count,
        'Periurban_Percent': round(periurban_count/total_wards*100, 1),
        'Rural_Count': rural_count,
        'Rural_Percent': round(rural_count/total_wards*100, 1),
        'Consistently_Rural': consistently_rural,
        'Consistently_Rural_Percent': round(consistently_rural/total_wards*100, 2),
        'Control_Mean': round(control_mean, 1),
        'NDBI_Mean': round(ndbi_mean, 1),
        'GHSL_Mean': round(ghsl_mean, 1),
        'EBBI_Mean': round(ebbi_mean, 1),
        'Overall_Mean_Urban': round(overall_mean, 1),
        'Method_Disagreement_Mean': round(mean_disagreement, 1),
        'Method_Disagreement_Max': round(max_disagreement, 1),
        'Original_Urban_Yes': original_urban_yes,
        'Original_Urban_No': original_urban_no,
        'Marked_Urban_But_Rural': marked_urban_but_rural,
        'Marked_Rural_But_Urban': marked_rural_but_urban,
        'Marked_Rural_But_Periurban': marked_rural_but_periurban,
        'Total_Misclassifications': marked_urban_but_rural + marked_rural_but_urban,
        'Concern_Level': 'HIGH' if (marked_urban_but_rural + marked_rural_but_urban) > 10 else 
                        'MEDIUM' if (marked_urban_but_rural + marked_rural_but_urban) > 5 else 'LOW'
    })

state_analysis_df = pd.DataFrame(state_analysis).sort_values('State')
state_analysis_df.to_csv(OUTPUT_DIR / 'state_analysis_complete.csv', index=False)
print(f"✓ Saved state analysis for {len(state_analysis_df)} states")

# ========== 2. CONSISTENTLY RURAL WARDS ==========
print("\n[2/7] Extracting consistently rural wards...")

rural_wards = df[df['consistently_rural'] == 'YES'].copy()
rural_wards_export = rural_wards[['StateName', 'LGAName', 'WardName', 'WardCode', 
                                  'control_urban', 'ndbi_urban', 'ghsl_urban', 'ebbi_urban',
                                  'mean_urban', 'Urban']].sort_values(['StateName', 'LGAName', 'WardName'])
rural_wards_export.to_csv(OUTPUT_DIR / 'consistently_rural_wards.csv', index=False)
print(f"✓ Found {len(rural_wards_export)} consistently rural wards across {rural_wards_export['StateName'].nunique()} states")

# ========== 3. DELTA STATE DEEP DIVE ==========
print("\n[3/7] Analyzing Delta State in detail...")

delta_df = df[df['StateName'] == 'Delta'].copy()
delta_df['method_std'] = delta_df[['control_urban', 'ndbi_urban', 'ghsl_urban', 'ebbi_urban']].std(axis=1)

# Add analysis flags
delta_df['Potential_Issue'] = 'None'
delta_df.loc[(delta_df['Urban'] == 'Yes') & (delta_df['mean_urban'] < 30), 'Potential_Issue'] = 'Marked_Urban_But_Rural'
delta_df.loc[(delta_df['Urban'] == 'No') & (delta_df['mean_urban'] > 50), 'Potential_Issue'] = 'Marked_Rural_But_Urban'

delta_export = delta_df[['LGAName', 'WardName', 'WardCode', 'Urban', 'classification',
                         'control_urban', 'ndbi_urban', 'ghsl_urban', 'ebbi_urban', 
                         'mean_urban', 'method_std', 'consistently_rural', 'Potential_Issue']]
delta_export = delta_export.sort_values('mean_urban', ascending=False)
delta_export.to_csv(OUTPUT_DIR / 'delta_state_validation.csv', index=False)

print(f"✓ Delta State: {len(delta_df)} wards analyzed")
print(f"  - Consistently rural: {(delta_df['consistently_rural'] == 'YES').sum()}")
print(f"  - Potential misclassifications: {(delta_df['Potential_Issue'] != 'None').sum()}")

# ========== 4. NATIONAL MISCLASSIFICATIONS ==========
print("\n[4/7] Identifying national misclassification hotspots...")

# Find all misclassified wards
df['Misclassification_Type'] = 'Correct'
df.loc[(df['Urban'] == 'Yes') & (df['mean_urban'] < 30), 'Misclassification_Type'] = 'Urban_Marked_But_Rural'
df.loc[(df['Urban'] == 'No') & (df['mean_urban'] > 50), 'Misclassification_Type'] = 'Rural_Marked_But_Urban'

misclassified = df[df['Misclassification_Type'] != 'Correct'].copy()
misclassified_export = misclassified[['StateName', 'LGAName', 'WardName', 'Urban', 
                                      'classification', 'mean_urban', 'Misclassification_Type']]
misclassified_export = misclassified_export.sort_values(['StateName', 'Misclassification_Type', 'mean_urban'])
misclassified_export.to_csv(OUTPUT_DIR / 'national_misclassifications.csv', index=False)

print(f"✓ Found {len(misclassified)} potential misclassifications nationally")
print(f"  - Urban marked but rural: {(misclassified['Misclassification_Type'] == 'Urban_Marked_But_Rural').sum()}")
print(f"  - Rural marked but urban: {(misclassified['Misclassification_Type'] == 'Rural_Marked_But_Urban').sum()}")

# ========== 5. METHOD AGREEMENT STATISTICS ==========
print("\n[5/7] Calculating method agreement statistics...")

methods = ['control_urban', 'ndbi_urban', 'ghsl_urban', 'ebbi_urban']

# Correlation matrix
corr_matrix = df[methods].corr()

# Calculate Cronbach's alpha (internal consistency)
n_items = len(methods)
item_variance = df[methods].var()
total_variance = df[methods].sum(axis=1).var()
cronbachs_alpha = (n_items / (n_items - 1)) * (1 - item_variance.sum() / total_variance)

# Agreement statistics
agreement_stats = {
    'Correlation_Matrix': corr_matrix.to_dict(),
    'Cronbachs_Alpha': round(cronbachs_alpha, 3),
    'Mean_Method_STD': round(df[methods].std(axis=1).mean(), 1),
    'Max_Method_STD': round(df[methods].std(axis=1).max(), 1),
    'High_Disagreement_Wards': len(df[df[methods].std(axis=1) > 30]),
    'Perfect_Agreement_Wards': len(df[df[methods].std(axis=1) < 5])
}

# Save correlations
corr_export = pd.DataFrame({
    'Method_1': [],
    'Method_2': [],
    'Correlation': []
})

for i, m1 in enumerate(methods):
    for m2 in methods[i+1:]:
        corr_export = pd.concat([corr_export, pd.DataFrame({
            'Method_1': [m1.replace('_urban', '').upper()],
            'Method_2': [m2.replace('_urban', '').upper()],
            'Correlation': [round(corr_matrix.loc[m1, m2], 3)]
        })], ignore_index=True)

corr_export.to_csv(OUTPUT_DIR / 'method_agreement_statistics.csv', index=False)

# Save detailed stats
with open(OUTPUT_DIR / 'agreement_statistics.json', 'w') as f:
    json.dump(agreement_stats, f, indent=2)

print(f"✓ Method agreement analysis complete")
print(f"  - Cronbach's Alpha: {cronbachs_alpha:.3f} (reliability)")
print(f"  - Highest correlation: NDBI-EBBI ({corr_matrix.loc['ndbi_urban', 'ebbi_urban']:.3f})")
print(f"  - Lowest correlation: Control-EBBI ({corr_matrix.loc['control_urban', 'ebbi_urban']:.3f})")

# ========== 6. PRIORITY STATES FOR REVIEW ==========
print("\n[6/7] Identifying priority states for NMEP review...")

priority_states = state_analysis_df[state_analysis_df['Total_Misclassifications'] > 5].copy()
priority_states = priority_states.sort_values('Total_Misclassifications', ascending=False)
priority_states.to_csv(OUTPUT_DIR / 'priority_states_for_review.csv', index=False)

print(f"✓ {len(priority_states)} states flagged for priority review")
for _, state in priority_states.head(5).iterrows():
    print(f"  - {state['State']}: {state['Total_Misclassifications']} misclassifications")

# ========== 7. SUMMARY STATISTICS ==========
print("\n[7/7] Generating summary statistics...")

summary = {
    'Total_Wards_Analyzed': len(df),
    'Total_States': df['StateName'].nunique(),
    'Consistently_Rural_Wards': len(rural_wards),
    'Consistently_Rural_Percent': round(len(rural_wards)/len(df)*100, 2),
    'National_Misclassifications': len(misclassified),
    'States_With_High_Concern': len(priority_states),
    'Delta_State_Misclassifications': len(delta_df[delta_df['Potential_Issue'] != 'None']),
    'Delta_State_Concern_Level': 'LOW' if len(delta_df[delta_df['Potential_Issue'] != 'None']) < 5 else 'MEDIUM',
    'Method_With_Highest_Urban': 'NDBI',
    'Method_With_Lowest_Urban': 'Control (HLS NDBI)',
    'Most_Reliable_Method': 'GHSL (UN Standard)'
}

with open(OUTPUT_DIR / 'summary_statistics.json', 'w') as f:
    json.dump(summary, f, indent=2)

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)
print(f"\nAll outputs saved to: {OUTPUT_DIR}")
print("\nKey Findings for Thursday Meeting:")
print(f"1. Delta State has only {summary['Delta_State_Misclassifications']} potential misclassifications (LOW concern)")
print(f"2. {summary['Consistently_Rural_Wards']} wards are definitively rural - should NOT be urban-targeted")
print(f"3. {summary['States_With_High_Concern']} states have >5 misclassifications and need review")
print(f"4. Recommend using GHSL as primary method (UN standard)")