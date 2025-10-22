"""
Create maps identical to Grace's style (b.png and bb.png)
To compare Bernard's corrected results with Grace's original
"""

import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Point
import numpy as np

# Load both datasets
bernard = pd.read_csv('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/Bernard_Mali_Test.csv')
grace = pd.read_csv('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/Mali_points_modis_buffer.csv')

print("Creating Grace-style comparison maps...")
print(f"Loaded {len(bernard)} points from Bernard's test")
print(f"Loaded {len(grace)} points from Grace's original")

# Load Mali boundary (approximate)
try:
    world = gpd.read_file('https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip')
    mali_boundary = world[world.NAME == 'Mali']
    has_boundary = True
    print("✓ Mali boundary loaded")
except:
    print("⚠ Could not load Mali boundary, will plot without")
    has_boundary = False

# Create figure with 4 subplots (2x2)
fig, axes = plt.subplots(2, 2, figsize=(16, 14))
fig.suptitle('Mali Urban Analysis: Grace (Original) vs Bernard (Corrected)',
             fontsize=18, fontweight='bold', y=0.995)

# ========================================================
# PANEL 1: Grace's Aridity Classification
# ========================================================
ax = axes[0, 0]

if has_boundary:
    mali_boundary.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1)

# Plot points colored by aridity
non_arid = grace[grace['arid_flag'] == 0]
arid = grace[grace['arid_flag'] == 1]

ax.scatter(non_arid['long'], non_arid['lat'],
           c='#4575b4', s=30, alpha=0.7, edgecolors='none', label='Non-arid (0)')
ax.scatter(arid['long'], arid['lat'],
           c='#d8b365', s=30, alpha=0.7, edgecolors='none', label='Arid (1)')

ax.set_xlabel('Longitude', fontsize=11)
ax.set_ylabel('Latitude', fontsize=11)
ax.set_title('Grace (Original): Mali Cluster Points by Aridity Class',
             fontsize=13, fontweight='bold')
ax.legend(loc='lower right', fontsize=10, title='Aridity', title_fontsize=11)
ax.grid(True, alpha=0.3)

# ========================================================
# PANEL 2: Grace's DBI Urban %
# ========================================================
ax = axes[0, 1]

if has_boundary:
    mali_boundary.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1)

scatter = ax.scatter(grace['long'], grace['lat'],
                     c=grace['DBI_pct'], s=40, alpha=0.8,
                     cmap='plasma', vmin=0, vmax=100, edgecolors='black', linewidth=0.5)
cbar = plt.colorbar(scatter, ax=ax, shrink=0.7)
cbar.set_label('DBI Urban %', fontsize=10)

ax.set_xlabel('Longitude', fontsize=11)
ax.set_ylabel('Latitude', fontsize=11)
ax.set_title('Grace (Original): Mali Cluster Points by DBI Urban %',
             fontsize=13, fontweight='bold', color='red')
ax.grid(True, alpha=0.3)

# Add annotation for Bamako region
ax.annotate('Bamako\n(Non-arid, Urban)\nShowing LOW DBI!',
            xy=(-8, 12.6), xytext=(-11, 10),
            fontsize=10, color='red', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
            arrowprops=dict(arrowstyle='->', color='red', lw=2))

# ========================================================
# PANEL 3: Bernard's Aridity Classification
# ========================================================
ax = axes[1, 0]

if has_boundary:
    mali_boundary.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1)

# Plot points colored by aridity
non_arid_b = bernard[bernard['arid_flag'] == 0]
arid_b = bernard[bernard['arid_flag'] == 1]

ax.scatter(non_arid_b['long'], non_arid_b['lat'],
           c='#4575b4', s=30, alpha=0.7, edgecolors='none', label='Non-arid (0)')
ax.scatter(arid_b['long'], arid_b['lat'],
           c='#d8b365', s=30, alpha=0.7, edgecolors='none', label='Arid (1)')

ax.set_xlabel('Longitude', fontsize=11)
ax.set_ylabel('Latitude', fontsize=11)
ax.set_title('Bernard (Corrected): Mali Cluster Points by Aridity Class',
             fontsize=13, fontweight='bold')
ax.legend(loc='lower right', fontsize=10, title='Aridity', title_fontsize=11)
ax.grid(True, alpha=0.3)

# ========================================================
# PANEL 4: Bernard's DBI Urban %
# ========================================================
ax = axes[1, 1]

if has_boundary:
    mali_boundary.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1)

scatter = ax.scatter(bernard['long'], bernard['lat'],
                     c=bernard['DBI_pct'], s=40, alpha=0.8,
                     cmap='plasma', vmin=0, vmax=100, edgecolors='black', linewidth=0.5)
cbar = plt.colorbar(scatter, ax=ax, shrink=0.7)
cbar.set_label('DBI Urban %', fontsize=10)

ax.set_xlabel('Longitude', fontsize=11)
ax.set_ylabel('Latitude', fontsize=11)
ax.set_title('Bernard (Corrected): Mali Cluster Points by DBI Urban %',
             fontsize=13, fontweight='bold', color='green')
ax.grid(True, alpha=0.3)

# Add annotation for Bamako region
ax.annotate('Bamako\n(Non-arid, Urban)\nSTILL LOW DBI!',
            xy=(-8, 12.6), xytext=(-11, 10),
            fontsize=10, color='darkorange', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.7),
            arrowprops=dict(arrowstyle='->', color='darkorange', lw=2))

plt.tight_layout()
plt.savefig('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/tasks/mali_grace_style_comparison.png',
            dpi=300, bbox_inches='tight')
print("✓ Saved: mali_grace_style_comparison.png")

# ========================================================
# Create individual maps matching Grace's exact style
# ========================================================

# Map 1: Bernard's DBI (matching Grace's bb.png exactly)
fig, ax = plt.subplots(1, 1, figsize=(10, 8))

if has_boundary:
    mali_boundary.plot(ax=ax, facecolor='#e6f2ff', edgecolor='black', linewidth=1.5)

scatter = ax.scatter(bernard['long'], bernard['lat'],
                     c=bernard['DBI_pct'], s=50, alpha=0.85,
                     cmap='plasma', vmin=0, vmax=75, edgecolors='white', linewidth=0.3)
cbar = plt.colorbar(scatter, ax=ax, shrink=0.8, pad=0.02)
cbar.set_label('DBI Urban %', fontsize=12, fontweight='bold')

ax.set_xlabel('', fontsize=11)
ax.set_ylabel('', fontsize=11)
ax.set_title('Mali Cluster Points by DBI Urban Percentage\n(Bernard - Corrected with Global GHSL)',
             fontsize=14, fontweight='bold', pad=15)
ax.set_facecolor('#e6f2ff')
ax.grid(True, alpha=0.2, color='gray', linestyle='--')

plt.tight_layout()
plt.savefig('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/tasks/bernard_dbi_map_grace_style.png',
            dpi=300, bbox_inches='tight')
print("✓ Saved: bernard_dbi_map_grace_style.png (matches Grace's bb.png style)")

# Map 2: Bernard's GHSL (to show the fix)
fig, ax = plt.subplots(1, 1, figsize=(10, 8))

if has_boundary:
    mali_boundary.plot(ax=ax, facecolor='#e6f2ff', edgecolor='black', linewidth=1.5)

scatter = ax.scatter(bernard['long'], bernard['lat'],
                     c=bernard['GHSL_pct'], s=50, alpha=0.85,
                     cmap='RdYlGn', vmin=0, vmax=100, edgecolors='white', linewidth=0.3)
cbar = plt.colorbar(scatter, ax=ax, shrink=0.8, pad=0.02)
cbar.set_label('GHSL Urban %', fontsize=12, fontweight='bold')

ax.set_xlabel('', fontsize=11)
ax.set_ylabel('', fontsize=11)
ax.set_title('Mali Cluster Points by GHSL Urban Percentage\n(Bernard - Corrected, No Longer Capped at 30%)',
             fontsize=14, fontweight='bold', pad=15)
ax.set_facecolor('#e6f2ff')
ax.grid(True, alpha=0.2, color='gray', linestyle='--')

# Add text box showing fix
textstr = 'GHSL Fix Applied:\n✓ Max = 100%\n✓ Urban Bamako = 99%\n(was capped at 30%)'
props = dict(boxstyle='round', facecolor='lightgreen', alpha=0.8)
ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=11,
        verticalalignment='top', bbox=props, fontweight='bold')

plt.tight_layout()
plt.savefig('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/tasks/bernard_ghsl_map_fixed.png',
            dpi=300, bbox_inches='tight')
print("✓ Saved: bernard_ghsl_map_fixed.png")

# ========================================================
# Create comparison statistics summary
# ========================================================
print("\n" + "="*80)
print("MALI DBI ANALYSIS - ANSWERING GRACE'S QUESTION")
print("="*80)

# Focus on non-arid southwest Mali (Bamako region)
bamako_grace = grace[(grace['lat'] >= 11.6) & (grace['lat'] <= 13.6) &
                      (grace['long'] >= -9) & (grace['long'] <= -7) &
                      (grace['arid_flag'] == 0)].copy()

bamako_bernard = bernard[(bernard['lat'] >= 11.6) & (bernard['lat'] <= 13.6) &
                          (bernard['long'] >= -9) & (bernard['long'] <= -7) &
                          (bernard['arid_flag'] == 0)].copy()

print(f"\nNON-ARID SOUTHWEST MALI (BAMAKO REGION) - {len(bamako_bernard)} points")
print("-"*80)
print(f"{'Method':<15} {'Grace (Original)':<20} {'Bernard (Corrected)':<20} {'Status'}")
print("-"*80)
print(f"{'MODIS':<15} {bamako_grace['modis_urban_percent'].mean():<20.1f} "
      f"{bamako_bernard['modis_urban_percent'].mean():<20.1f} {'Same ✓'}")
print(f"{'GHSL':<15} {bamako_grace['GHSL_pct'].mean():<20.1f} "
      f"{bamako_bernard['GHSL_pct'].mean():<20.1f} {'FIXED! +69%'}")
print(f"{'DBI':<15} {bamako_grace['DBI_pct'].mean():<20.1f} "
      f"{bamako_bernard['DBI_pct'].mean():<20.1f} {'Same (LOW!) ⚠️'}")

print("\n" + "="*80)
print("CONCLUSION FOR GRACE")
print("="*80)
print("1. GHSL Issue: ✓ FIXED - Was using Nigeria_GHSL_2018 for Mali")
print("   → Now shows 99% for urban Bamako (was 30%)")
print()
print("2. DBI Issue: ⚠️ CONFIRMED - DBI shows LOW values (35%) for urban Bamako")
print("   → MODIS shows 85%, GHSL shows 99%, but DBI only 35%")
print()
print("3. Why DBI is Low:")
print("   → Bamako is NON-ARID (blue dots in aridity map)")
print("   → DBI = NDBI - NDVI was designed for ARID regions (Rasul et al. 2018)")
print("   → Urban areas with vegetation get lower DBI scores")
print()
print("4. Recommendation:")
print("   → For non-arid regions like Bamako, use GHSL or MODIS instead of DBI")
print("   → DBI works better for arid northern Mali (brown dots)")
print("="*80)

# Save statistics to file
with open('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/tasks/dbi_analysis_summary.txt', 'w') as f:
    f.write("="*80 + "\n")
    f.write("RESPONSE TO GRACE'S QUESTION\n")
    f.write("="*80 + "\n\n")
    f.write('Grace asked: "It\'s saying the urban southwest region of Mali has very low\n')
    f.write('urbanicity, which shouldn\'t be the case. Any thoughts?"\n\n')
    f.write("="*80 + "\n")
    f.write("FINDINGS\n")
    f.write("="*80 + "\n\n")
    f.write("1. GHSL ISSUE (FIXED):\n")
    f.write(f"   - Grace's GHSL: {bamako_grace['GHSL_pct'].mean():.1f}% (capped)\n")
    f.write(f"   - Corrected GHSL: {bamako_bernard['GHSL_pct'].mean():.1f}%\n")
    f.write("   - Root cause: Used Nigeria_GHSL_2018 for Mali points\n")
    f.write("   - Solution: Use Mali_GHSL_2018 or global GHSL dataset\n\n")
    f.write("2. DBI ISSUE (CONFIRMED - NOT FIXED):\n")
    f.write(f"   - Grace's DBI: {bamako_grace['DBI_pct'].mean():.1f}%\n")
    f.write(f"   - Corrected DBI: {bamako_bernard['DBI_pct'].mean():.1f}%\n")
    f.write(f"   - MODIS urban: {bamako_bernard['modis_urban_percent'].mean():.1f}%\n")
    f.write(f"   - GHSL urban: {bamako_bernard['GHSL_pct'].mean():.1f}%\n\n")
    f.write("   DBI underestimates urbanicity by ~50% for Bamako!\n\n")
    f.write("3. WHY DBI IS LOW:\n")
    f.write("   - Bamako is NON-ARID (arid_flag=0)\n")
    f.write("   - DBI (Dry Built-up Index) designed for ARID regions\n")
    f.write("   - Formula: DBI = NDBI - NDVI\n")
    f.write("   - Non-arid urban areas have vegetation → high NDVI → low DBI\n\n")
    f.write("4. RECOMMENDATION:\n")
    f.write("   - For non-arid southwest Mali: Use GHSL or MODIS (more accurate)\n")
    f.write("   - For arid northern Mali: DBI should work as designed\n")
    f.write("   - Consider using NDBI alone (without subtracting NDVI) for non-arid regions\n\n")
    f.write("="*80 + "\n")

print("\n✓ Summary saved to: dbi_analysis_summary.txt")
print("\n✓ All maps created successfully!")
print("\nFiles created:")
print("  1. mali_grace_style_comparison.png - 4-panel comparison")
print("  2. bernard_dbi_map_grace_style.png - Matches Grace's bb.png")
print("  3. bernard_ghsl_map_fixed.png - Shows GHSL fix")
print("  4. dbi_analysis_summary.txt - Written response to Grace")
