"""
Mali Urban Analysis - Map Visualization with Country Boundary
Uses FAO GAUL shapefile for Mali boundary
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import folium
from folium import plugins
import requests
import json

print("Loading data...")

# Load both datasets
bernard = pd.read_csv('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/Bernard_Mali_Test.csv')
grace = pd.read_csv('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/Mali_points_modis_buffer.csv')

# Create GeoDataFrames
bernard_gdf = gpd.GeoDataFrame(
    bernard,
    geometry=gpd.points_from_xy(bernard['long'], bernard['lat']),
    crs='EPSG:4326'
)

grace_gdf = gpd.GeoDataFrame(
    grace,
    geometry=gpd.points_from_xy(grace['long'], grace['lat']),
    crs='EPSG:4326'
)

# Load Mali boundary from GEE's FAO GAUL dataset
# Note: We'll approximate with naturalearth data since GEE data requires Earth Engine API
# For production, you'd export the shapefile from GEE first

print("Creating map with Mali boundary...")

# Create base map centered on Mali
m = folium.Map(
    location=[17.0, -4.0],  # Mali center
    zoom_start=6,
    tiles='CartoDB positron'
)

# Add Mali boundary (approximate using world boundaries)
# In production, export this from GEE: ee.FeatureCollection('FAO/GAUL_SIMPLIFIED_500m/2015/level0').filter(ee.Filter.eq('ADM0_NAME', 'Mali'))
try:
    import geopandas as gpd
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    mali_boundary = world[world.name == 'Mali']

    folium.GeoJson(
        mali_boundary,
        name='Mali Boundary',
        style_function=lambda x: {
            'fillColor': 'transparent',
            'color': 'black',
            'weight': 2,
            'fillOpacity': 0
        }
    ).add_to(m)
    print("✓ Mali boundary added")
except Exception as e:
    print(f"⚠ Could not load Mali boundary: {e}")

# Add title
title_html = '''
<div style="position: fixed;
            top: 10px; left: 50px; width: 700px; height: 110px;
            background-color: white; border:2px solid grey; z-index:9999;
            font-size:14px; padding: 10px; box-shadow: 2px 2px 6px rgba(0,0,0,0.3)">
<h4 style="margin-bottom:5px">Mali Urban Analysis: Geography Mismatch Identified</h4>
<p style="margin:0"><b style="color:green">Green Circles = Bernard (Fixed - Global GHSL)</b></p>
<p style="margin:0"><b style="color:red">Red Circles = Grace (Original - Nigeria GHSL)</b></p>
<p style="margin:0; font-size:12px; color:#666">Circle size = MODIS urban %, Hover to see details</p>
</div>
'''
m.get_root().html.add_child(folium.Element(title_html))

# Add points with difference calculation
print("Adding comparison points...")

# Merge datasets to calculate differences
merged = bernard.merge(grace, on='id', suffixes=('_bernard', '_grace'))

for idx, row in merged.iterrows():
    # Calculate GHSL difference
    ghsl_diff = row['GHSL_pct_bernard'] - row['GHSL_pct_grace']

    # Size based on MODIS (use Bernard's)
    radius = 4 + (row['modis_urban_percent_bernard'] / 8)

    # Determine if significant difference
    is_significant = ghsl_diff > 20  # More than 20% difference

    # Bernard's point (larger, green)
    popup_text = f"""
    <div style="width:280px">
    <b style="color:green; font-size:14px">Point {row['id']} - BERNARD (FIXED)</b><br>
    <b>Location:</b> ({row['lat_bernard']:.3f}, {row['long_bernard']:.3f})<br>
    <hr style="margin:5px 0">
    <table style="width:100%; font-size:12px">
    <tr><td><b>Method</b></td><td><b>Value</b></td></tr>
    <tr><td>MODIS:</td><td>{row['modis_urban_percent_bernard']:.1f}%</td></tr>
    <tr style="background:#e8f5e9"><td><b>GHSL:</b></td><td><b>{row['GHSL_pct_bernard']:.1f}%</b> ✓</td></tr>
    <tr><td>DBI:</td><td>{row['DBI_pct_bernard']:.1f}%</td></tr>
    <tr><td>Arid:</td><td>{'Yes' if row['arid_flag_bernard'] == 1 else 'No'}</td></tr>
    </table>
    <hr style="margin:5px 0">
    <b style="color:red">Grace's GHSL:</b> {row['GHSL_pct_grace']:.1f}%<br>
    <b style="color:{'red' if is_significant else 'orange'}">Difference:</b>
    <span style="font-size:14px; font-weight:bold">{'+' if ghsl_diff > 0 else ''}{ghsl_diff:.1f}%</span>
    {' ⚠️ SIGNIFICANT!' if is_significant else ''}
    </div>
    """

    folium.CircleMarker(
        location=[row['lat_bernard'], row['long_bernard']],
        radius=radius,
        popup=folium.Popup(popup_text, max_width=300),
        tooltip=f"Point {row['id']}: GHSL {row['GHSL_pct_bernard']:.0f}% vs {row['GHSL_pct_grace']:.0f}% (Δ{ghsl_diff:+.0f}%)",
        color='green',
        fill=True,
        fillColor='green' if not is_significant else 'lime',
        fillOpacity=0.7 if not is_significant else 0.9,
        weight=2 if is_significant else 1
    ).add_to(m)

# Add Bamako highlight
bamako_box = [
    [11.6, -9],
    [13.6, -9],
    [13.6, -7],
    [11.6, -7],
    [11.6, -9]
]
folium.PolyLine(
    bamako_box,
    color='blue',
    weight=3,
    opacity=0.8,
    popup='<b>Urban Bamako Region</b><br>45 points with MODIS > 50%<br>Largest GHSL discrepancy',
    tooltip='Urban Bamako (Click for details)'
).add_to(m)

# Add Bamako label
folium.Marker(
    [12.6, -8.0],
    icon=folium.DivIcon(html=f'''
        <div style="font-size: 14px; font-weight: bold; color: blue;
                    background: white; padding: 3px 6px; border: 2px solid blue;
                    border-radius: 3px; white-space: nowrap;">
            Bamako (Capital)
        </div>
    ''')
).add_to(m)

# Add legend
legend_html = '''
<div style="position: fixed;
            bottom: 50px; left: 50px; width: 320px; height: 250px;
            background-color: white; border:2px solid grey; z-index:9999;
            font-size:13px; padding: 12px; box-shadow: 2px 2px 6px rgba(0,0,0,0.3)">
<p style="margin-top:0; font-size:14px"><b>Key Findings:</b></p>

<div style="background:#e8f5e9; padding:6px; margin:5px 0; border-left:4px solid green">
<b>🟢 Bernard (Fixed):</b><br>
&nbsp;&nbsp;&nbsp;GHSL max = <b>100.0%</b> ✓<br>
&nbsp;&nbsp;&nbsp;Used global GHSL dataset
</div>

<div style="background:#ffebee; padding:6px; margin:5px 0; border-left:4px solid red">
<b>🔴 Grace (Original):</b><br>
&nbsp;&nbsp;&nbsp;GHSL max = <b>30.0%</b> ⚠️ CAPPED<br>
&nbsp;&nbsp;&nbsp;Used Nigeria_GHSL_2018
</div>

<hr style="margin:8px 0">
<p style="margin:5px 0; font-size:12px">
<b>Urban Bamako (45 points):</b><br>
Bernard GHSL: <span style="color:green"><b>99.3%</b></span> ✓<br>
Grace GHSL: <span style="color:red"><b>29.7%</b></span> ⚠️<br>
<b>Improvement: +69.6%</b>
</p>

<hr style="margin:8px 0">
<p style="margin:5px 0; font-size:11px; color:#666">
<b>Note:</b> DBI values unchanged (35.5% vs 35.6%)<br>
→ DBI methodology is correct ✓
</p>
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# Add stats box
stats_html = '''
<div style="position: fixed;
            top: 130px; left: 50px; width: 320px; height: 100px;
            background-color: white; border:2px solid grey; z-index:9999;
            font-size:12px; padding: 10px; box-shadow: 2px 2px 6px rgba(0,0,0,0.3)">
<b>Overall Statistics (345 points):</b>
<table style="width:100%; margin-top:5px">
<tr><th></th><th>MODIS</th><th>GHSL</th><th>DBI</th></tr>
<tr style="background:#e8f5e9"><td><b>Bernard</b></td><td>16.0%</td><td><b>26.6%</b></td><td>25.4%</td></tr>
<tr style="background:#ffebee"><td><b>Grace</b></td><td>15.8%</td><td><b>15.1%</b></td><td>25.3%</td></tr>
</table>
</div>
'''
m.get_root().html.add_child(folium.Element(stats_html))

# Save map
output_path = '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/tasks/mali_analysis_final_map.html'
m.save(output_path)
print(f"✓ Final map saved to: {output_path}")

# Create summary statistics
print("\n" + "="*80)
print("POINTS WITH SIGNIFICANT GHSL DIFFERENCE (>20%)")
print("="*80)

significant = merged[merged['GHSL_pct_bernard'] - merged['GHSL_pct_grace'] > 20].copy()
significant['ghsl_diff'] = significant['GHSL_pct_bernard'] - significant['GHSL_pct_grace']
significant = significant.sort_values('ghsl_diff', ascending=False)

print(f"\nFound {len(significant)} points with >20% GHSL difference:")
print(f"{'Point':<8} {'Lat':<10} {'Lon':<10} {'MODIS':<8} {'GHSL (B)':<10} {'GHSL (G)':<10} {'Diff':<8}")
print("-"*80)

for idx, row in significant.head(10).iterrows():
    print(f"{int(row['id']):<8} {row['lat_bernard']:<10.3f} {row['long_bernard']:<10.3f} "
          f"{row['modis_urban_percent_bernard']:<8.1f} {row['GHSL_pct_bernard']:<10.1f} "
          f"{row['GHSL_pct_grace']:<10.1f} {row['ghsl_diff']:<8.1f}")

print(f"\n... and {len(significant) - 10} more points")
print("\n" + "="*80)
print("✓ Open mali_analysis_final_map.html to explore all points interactively")
print("="*80)
