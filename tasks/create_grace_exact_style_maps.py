"""
Create maps matching Grace's exact style from b.png and bb.png
- b.png: Aridity classification (blue=non-arid, tan=arid)
- bb.png: DBI Urban % (plasma colormap)
"""

import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

# Load Bernard's Mali data
bernard = pd.read_csv('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/Bernard_Mali_Test.csv')

print("Creating Grace-style maps...")

# Load Mali boundary
try:
    world = gpd.read_file('https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip')
    mali_boundary = world[world.NAME == 'Mali']
    has_boundary = True
    print("✓ Mali boundary loaded")
except:
    has_boundary = False
    print("⚠ Could not load boundary")

# Create figure with 2 subplots matching Grace's layout
fig, axes = plt.subplots(1, 2, figsize=(16, 7))
fig.patch.set_facecolor('white')

# ========================================================
# MAP 1: ARIDITY CLASSIFICATION (matching b.png)
# ========================================================
ax = axes[0]

# Set background color to match Grace's style
ax.set_facecolor('#e6f3ff')  # Light blue background

# Plot Mali boundary
if has_boundary:
    mali_boundary.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1.5)

# Separate points by aridity
non_arid = bernard[bernard['arid_flag'] == 0]
arid = bernard[bernard['arid_flag'] == 1]

# Plot with Grace's exact colors
# Non-arid = Blue (#4575b4)
# Arid = Tan/brown (#d8b365)
ax.scatter(non_arid['long'], non_arid['lat'],
           c='#4575b4', s=50, alpha=0.8, edgecolors='white', linewidth=0.5,
           label='Non-arid (0)', zorder=3)

ax.scatter(arid['long'], arid['lat'],
           c='#d8b365', s=50, alpha=0.8, edgecolors='white', linewidth=0.5,
           label='Arid (1)', zorder=3)

# Styling to match Grace's map
ax.set_xlabel('', fontsize=11)
ax.set_ylabel('', fontsize=11)
ax.set_title('Mali Cluster Points by Aridity Class',
             fontsize=14, fontweight='bold', pad=15)

# Add legend matching Grace's style
legend = ax.legend(loc='lower right', fontsize=11, title='Aridity',
                   title_fontsize=12, frameon=True, fancybox=True,
                   edgecolor='black', framealpha=0.9)

# Grid styling
ax.grid(True, alpha=0.2, color='gray', linestyle='-', linewidth=0.5)
ax.set_axisbelow(True)

# Set aspect and limits
ax.set_aspect('equal', adjustable='box')

# ========================================================
# MAP 2: DBI URBAN % (matching bb.png)
# ========================================================
ax = axes[1]

# Set background color
ax.set_facecolor('#e6f3ff')

# Plot Mali boundary
if has_boundary:
    mali_boundary.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1.5)

# Create scatter plot with plasma colormap (matching bb.png)
scatter = ax.scatter(bernard['long'], bernard['lat'],
                     c=bernard['DBI_pct'], s=50, alpha=0.85,
                     cmap='plasma', vmin=0, vmax=100,
                     edgecolors='white', linewidth=0.5, zorder=3)

# Add colorbar matching Grace's style
cbar = plt.colorbar(scatter, ax=ax, shrink=0.8, pad=0.02,
                    label='DBI Urban %')
cbar.ax.tick_params(labelsize=10)
cbar.set_label('DBI Urban %', fontsize=11, fontweight='bold')

# Styling
ax.set_xlabel('', fontsize=11)
ax.set_ylabel('', fontsize=11)
ax.set_title('Mali Cluster Points by DBI Urban Percentage',
             fontsize=14, fontweight='bold', pad=15)

# Grid styling
ax.grid(True, alpha=0.2, color='gray', linestyle='-', linewidth=0.5)
ax.set_axisbelow(True)

# Set aspect
ax.set_aspect('equal', adjustable='box')

plt.tight_layout()

# Save
output_path = '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/tasks/bernard_mali_grace_style.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
print(f"✓ Saved: {output_path}")

# ========================================================
# CREATE INDIVIDUAL MAPS (matching Grace's exactly)
# ========================================================

# ARIDITY MAP ONLY
fig, ax = plt.subplots(1, 1, figsize=(10, 8))
fig.patch.set_facecolor('white')
ax.set_facecolor('#e6f3ff')

if has_boundary:
    mali_boundary.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1.5)

ax.scatter(non_arid['long'], non_arid['lat'],
           c='#4575b4', s=55, alpha=0.8, edgecolors='white', linewidth=0.5,
           label='Non-arid (0)', zorder=3)
ax.scatter(arid['long'], arid['lat'],
           c='#d8b365', s=55, alpha=0.8, edgecolors='white', linewidth=0.5,
           label='Arid (1)', zorder=3)

ax.set_title('Mali Cluster Points by Aridity Class',
             fontsize=16, fontweight='bold', pad=20)
legend = ax.legend(loc='lower right', fontsize=12, title='Aridity',
                   title_fontsize=13, frameon=True, fancybox=True,
                   edgecolor='black', framealpha=0.9)
ax.grid(True, alpha=0.2, color='gray', linestyle='-', linewidth=0.5)
ax.set_aspect('equal', adjustable='box')

plt.tight_layout()
output_arid = '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/tasks/bernard_aridity_map.png'
plt.savefig(output_arid, dpi=300, bbox_inches='tight', facecolor='white')
print(f"✓ Saved: {output_arid}")

# DBI MAP ONLY
fig, ax = plt.subplots(1, 1, figsize=(10, 8))
fig.patch.set_facecolor('white')
ax.set_facecolor('#e6f3ff')

if has_boundary:
    mali_boundary.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1.5)

scatter = ax.scatter(bernard['long'], bernard['lat'],
                     c=bernard['DBI_pct'], s=55, alpha=0.85,
                     cmap='plasma', vmin=0, vmax=100,
                     edgecolors='white', linewidth=0.5, zorder=3)

cbar = plt.colorbar(scatter, ax=ax, shrink=0.8, pad=0.03)
cbar.ax.tick_params(labelsize=11)
cbar.set_label('DBI Urban %', fontsize=12, fontweight='bold')

ax.set_title('Mali Cluster Points by DBI Urban Percentage',
             fontsize=16, fontweight='bold', pad=20)
ax.grid(True, alpha=0.2, color='gray', linestyle='-', linewidth=0.5)
ax.set_aspect('equal', adjustable='box')

plt.tight_layout()
output_dbi = '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/tasks/bernard_dbi_map.png'
plt.savefig(output_dbi, dpi=300, bbox_inches='tight', facecolor='white')
print(f"✓ Saved: {output_dbi}")

# ========================================================
# STATISTICS
# ========================================================
print()
print("="*80)
print("BERNARD'S MALI RESULTS (Grace-style maps)")
print("="*80)
print(f"Total points: {len(bernard)}")
print(f"Non-arid points: {len(non_arid)} ({100*len(non_arid)/len(bernard):.1f}%)")
print(f"Arid points: {len(arid)} ({100*len(arid)/len(bernard):.1f}%)")
print()
print(f"DBI statistics:")
print(f"  Mean: {bernard['DBI_pct'].mean():.1f}%")
print(f"  Min: {bernard['DBI_pct'].min():.1f}%")
print(f"  Max: {bernard['DBI_pct'].max():.1f}%")
print()
print(f"Non-arid southwest (Bamako region):")
bamako = bernard[(bernard['lat'] >= 11.6) & (bernard['lat'] <= 13.6) &
                 (bernard['long'] >= -9) & (bernard['long'] <= -7) &
                 (bernard['arid_flag'] == 0)]
print(f"  Points: {len(bamako)}")
print(f"  DBI mean: {bamako['DBI_pct'].mean():.1f}%")
print(f"  MODIS mean: {bamako['modis_urban_percent'].mean():.1f}%")
print(f"  Gap: {bamako['modis_urban_percent'].mean() - bamako['DBI_pct'].mean():.1f}%")
print()
print("="*80)
print("FILES CREATED:")
print("  1. bernard_mali_grace_style.png - Side-by-side (aridity + DBI)")
print("  2. bernard_aridity_map.png - Aridity only (matches b.png)")
print("  3. bernard_dbi_map.png - DBI only (matches bb.png)")
print("="*80)
print()
print("These maps use YOUR corrected data but match Grace's visual style.")
print("Share these alongside your Slack message to show validation.")
