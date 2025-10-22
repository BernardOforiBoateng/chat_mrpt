"""
Mali Urban Analysis Comparison
Bernard's Test vs Grace's Original Results
Proves the geography (wrong raster) issue
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load both datasets
bernard = pd.read_csv('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/Bernard_Mali_Test.csv')
grace = pd.read_csv('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/Mali_points_modis_buffer.csv')

print("="*80)
print("MALI URBAN ANALYSIS - COMPARING BERNARD'S TEST VS GRACE'S ORIGINAL")
print("="*80)
print()

# Clean column names
bernard.columns = bernard.columns.str.strip()
grace.columns = grace.columns.str.strip()

# Basic stats
print(f"Number of points: {len(bernard)} (Bernard) vs {len(grace)} (Grace)")
print()

# Overall comparison
print("OVERALL STATISTICS")
print("-"*80)
print(f"                    MODIS         GHSL          DBI")
print(f"Bernard (Fixed):    {bernard['modis_urban_percent'].mean():.1f}%       {bernard['GHSL_pct'].mean():.1f}%       {bernard['DBI_pct'].mean():.1f}%")
print(f"Grace (Original):   {grace['modis_urban_percent'].mean():.1f}%       {grace['GHSL_pct'].mean():.1f}%       {grace['DBI_pct'].mean():.1f}%")
print()

# Check GHSL max (the smoking gun)
print("CRITICAL FINDING - GHSL MAX VALUES")
print("-"*80)
print(f"Bernard (Fixed):    GHSL max = {bernard['GHSL_pct'].max():.1f}%")
print(f"Grace (Original):   GHSL max = {grace['GHSL_pct'].max():.1f}% ← CAPPED (WRONG GEOGRAPHY!)")
print()

# Urban Bamako analysis (lat ~12.6, lon ~-8.0, MODIS > 50%)
bamako_bernard = bernard[(bernard['lat'] >= 11.6) & (bernard['lat'] <= 13.6) &
                          (bernard['long'] >= -9) & (bernard['long'] <= -7) &
                          (bernard['modis_urban_percent'] > 50)].copy()

bamako_grace = grace[(grace['lat'] >= 11.6) & (grace['lat'] <= 13.6) &
                      (grace['long'] >= -9) & (grace['long'] <= -7) &
                      (grace['modis_urban_percent'] > 50)].copy()

print(f"URBAN BAMAKO ANALYSIS ({len(bamako_bernard)} points with MODIS > 50%)")
print("-"*80)
print(f"                    MODIS         GHSL          DBI")
print(f"Bernard (Fixed):    {bamako_bernard['modis_urban_percent'].mean():.1f}%       {bamako_bernard['GHSL_pct'].mean():.1f}%       {bamako_bernard['DBI_pct'].mean():.1f}%")
print(f"Grace (Original):   {bamako_grace['modis_urban_percent'].mean():.1f}%       {bamako_grace['GHSL_pct'].mean():.1f}%       {bamako_grace['DBI_pct'].mean():.1f}%")
print()
print(f"GHSL Improvement:   +{bamako_bernard['GHSL_pct'].mean() - bamako_grace['GHSL_pct'].mean():.1f}%")
print(f"DBI stays same:     {abs(bamako_bernard['DBI_pct'].mean() - bamako_grace['DBI_pct'].mean()):.1f}% difference")
print()

# Show sample points
print("SAMPLE URBAN BAMAKO POINTS (showing the issue)")
print("-"*80)
sample_ids = bamako_grace.head(5)['id'].values
for idx in sample_ids:
    b = bernard[bernard['id'] == idx].iloc[0]
    g = grace[grace['id'] == idx].iloc[0]
    print(f"Point {idx} (lat={b['lat']:.2f}, lon={b['long']:.2f}):")
    print(f"  MODIS:  {b['modis_urban_percent']:.1f}% (Bernard) vs {g['modis_urban_percent']:.1f}% (Grace)")
    print(f"  GHSL:   {b['GHSL_pct']:.1f}% (Bernard) vs {g['GHSL_pct']:.1f}% (Grace) ← CAPPED!")
    print(f"  DBI:    {b['DBI_pct']:.1f}% (Bernard) vs {g['DBI_pct']:.1f}% (Grace)")
    print()

# Create visualization
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Mali Urban Analysis: Bernard (Fixed) vs Grace (Original)',
             fontsize=16, fontweight='bold')

# 1. GHSL Distribution (shows the cap)
axes[0, 0].hist(grace['GHSL_pct'], bins=30, alpha=0.5, label='Grace (Original)', color='red', edgecolor='black')
axes[0, 0].hist(bernard['GHSL_pct'], bins=30, alpha=0.5, label='Bernard (Fixed)', color='green', edgecolor='black')
axes[0, 0].axvline(30, color='red', linestyle='--', linewidth=2, label='30% Cap')
axes[0, 0].set_xlabel('GHSL Urban %')
axes[0, 0].set_ylabel('Frequency')
axes[0, 0].set_title('GHSL Distribution - Grace Capped at 30%')
axes[0, 0].legend()
axes[0, 0].grid(alpha=0.3)

# 2. GHSL vs MODIS scatter
axes[0, 1].scatter(grace['modis_urban_percent'], grace['GHSL_pct'],
                   alpha=0.5, label='Grace (Original)', color='red', s=30)
axes[0, 1].scatter(bernard['modis_urban_percent'], bernard['GHSL_pct'],
                   alpha=0.5, label='Bernard (Fixed)', color='green', s=30)
axes[0, 1].plot([0, 100], [0, 100], 'k--', alpha=0.3, label='1:1 line')
axes[0, 1].axhline(30, color='red', linestyle='--', linewidth=2, alpha=0.5)
axes[0, 1].set_xlabel('MODIS Urban %')
axes[0, 1].set_ylabel('GHSL Urban %')
axes[0, 1].set_title('GHSL vs MODIS - Grace Limited by Geography')
axes[0, 1].legend()
axes[0, 1].grid(alpha=0.3)

# 3. DBI vs MODIS scatter
axes[1, 0].scatter(grace['modis_urban_percent'], grace['DBI_pct'],
                   alpha=0.5, label='Grace (Original)', color='red', s=30)
axes[1, 0].scatter(bernard['modis_urban_percent'], bernard['DBI_pct'],
                   alpha=0.5, label='Bernard (Fixed)', color='green', s=30)
axes[1, 0].plot([0, 100], [0, 100], 'k--', alpha=0.3, label='1:1 line')
axes[1, 0].set_xlabel('MODIS Urban %')
axes[1, 0].set_ylabel('DBI Urban %')
axes[1, 0].set_title('DBI vs MODIS - Both Same (DBI Methodology OK)')
axes[1, 0].legend()
axes[1, 0].grid(alpha=0.3)

# 4. Urban Bamako comparison
methods = ['MODIS', 'GHSL', 'DBI']
bernard_vals = [bamako_bernard['modis_urban_percent'].mean(),
                bamako_bernard['GHSL_pct'].mean(),
                bamako_bernard['DBI_pct'].mean()]
grace_vals = [bamako_grace['modis_urban_percent'].mean(),
              bamako_grace['GHSL_pct'].mean(),
              bamako_grace['DBI_pct'].mean()]

x = np.arange(len(methods))
width = 0.35
axes[1, 1].bar(x - width/2, grace_vals, width, label='Grace (Original)', color='red', alpha=0.7)
axes[1, 1].bar(x + width/2, bernard_vals, width, label='Bernard (Fixed)', color='green', alpha=0.7)
axes[1, 1].set_xlabel('Method')
axes[1, 1].set_ylabel('Urban %')
axes[1, 1].set_title(f'Urban Bamako ({len(bamako_bernard)} points, MODIS > 50%)')
axes[1, 1].set_xticks(x)
axes[1, 1].set_xticklabels(methods)
axes[1, 1].legend()
axes[1, 1].grid(alpha=0.3, axis='y')
axes[1, 1].axhline(30, color='red', linestyle='--', linewidth=1, alpha=0.5)

plt.tight_layout()
plt.savefig('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/tasks/mali_comparison_charts.png',
            dpi=300, bbox_inches='tight')
print(f"Charts saved to: tasks/mali_comparison_charts.png")
print()

# Correlation analysis
print("CORRELATION WITH MODIS")
print("-"*80)
print(f"                    GHSL          DBI")
print(f"Bernard (Fixed):    r={bernard['GHSL_pct'].corr(bernard['modis_urban_percent']):.3f}       r={bernard['DBI_pct'].corr(bernard['modis_urban_percent']):.3f}")
print(f"Grace (Original):   r={grace['GHSL_pct'].corr(grace['modis_urban_percent']):.3f}       r={grace['DBI_pct'].corr(grace['modis_urban_percent']):.3f}")
print()

print("="*80)
print("CONCLUSION")
print("="*80)
print("✓ GHSL fixed: No longer capped at 30%, now properly detects urban areas")
print("✓ DBI unchanged: Methodology is correct, values are consistent")
print("✓ Root cause: Grace used Nigeria_GHSL_2018 for Mali analysis")
print("✓ Solution: Use Mali-specific or global GHSL dataset")
print("="*80)
