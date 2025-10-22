"""
Mali Urban Analysis - Interactive Map Visualization
Shows Bernard (Fixed) vs Grace (Original) results side-by-side
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import folium
from folium import plugins
import json

# Load both datasets
bernard = pd.read_csv('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/Bernard_Mali_Test.csv')
grace = pd.read_csv('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/Mali_points_modis_buffer.csv')

print("Creating interactive map...")

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

# Create base map centered on Mali
m = folium.Map(
    location=[17.0, -4.0],  # Mali center
    zoom_start=6,
    tiles='CartoDB positron'
)

# Add title
title_html = '''
<div style="position: fixed;
            top: 10px; left: 50px; width: 600px; height: 90px;
            background-color: white; border:2px solid grey; z-index:9999;
            font-size:14px; padding: 10px">
<h4 style="margin-bottom:5px">Mali Urban Analysis: Bernard (Fixed) vs Grace (Original)</h4>
<p style="margin:0"><b style="color:green">Green = Bernard (Fixed)</b> | <b style="color:red">Red = Grace (Original)</b></p>
<p style="margin:0; font-size:12px">Size = MODIS urban %, Color intensity = GHSL %</p>
</div>
'''
m.get_root().html.add_child(folium.Element(title_html))

# Add Bernard's points (Fixed - Green)
for idx, row in bernard_gdf.iterrows():
    # Size based on MODIS
    radius = 3 + (row['modis_urban_percent'] / 10)

    # Color intensity based on GHSL
    ghsl_intensity = min(row['GHSL_pct'] / 100, 1.0)
    color = f'rgba(0, {int(255 * ghsl_intensity)}, 0, 0.6)'

    popup_text = f"""
    <b>Point {row['id']} - BERNARD (FIXED)</b><br>
    <b>Location:</b> ({row['lat']:.3f}, {row['long']:.3f})<br>
    <hr>
    <b>MODIS:</b> {row['modis_urban_percent']:.1f}%<br>
    <b>GHSL:</b> {row['GHSL_pct']:.1f}% ✓<br>
    <b>DBI:</b> {row['DBI_pct']:.1f}%<br>
    <b>Arid:</b> {'Yes' if row['arid_flag'] == 1 else 'No'}
    """

    folium.CircleMarker(
        location=[row['lat'], row['long']],
        radius=radius,
        popup=folium.Popup(popup_text, max_width=250),
        color='green',
        fill=True,
        fillColor='green',
        fillOpacity=0.6,
        weight=1
    ).add_to(m)

# Add Grace's points (Original - Red) - smaller and behind
for idx, row in grace_gdf.iterrows():
    radius = 2 + (row['modis_urban_percent'] / 15)

    ghsl_intensity = min(row['GHSL_pct'] / 100, 1.0)

    popup_text = f"""
    <b>Point {row['id']} - GRACE (ORIGINAL)</b><br>
    <b>Location:</b> ({row['lat']:.3f}, {row['long']:.3f})<br>
    <hr>
    <b>MODIS:</b> {row['modis_urban_percent']:.1f}%<br>
    <b>GHSL:</b> {row['GHSL_pct']:.1f}% ⚠️ CAPPED<br>
    <b>DBI:</b> {row['DBI_pct']:.1f}%<br>
    <b>Arid:</b> {'Yes' if row['arid_flag'] == 1 else 'No'}
    """

    folium.CircleMarker(
        location=[row['lat'], row['long']],
        radius=radius,
        popup=folium.Popup(popup_text, max_width=250),
        color='red',
        fill=True,
        fillColor='red',
        fillOpacity=0.4,
        weight=1
    ).add_to(m)

# Add Bamako highlight box
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
    popup='Urban Bamako Region (MODIS > 50%)'
).add_to(m)

# Add legend
legend_html = '''
<div style="position: fixed;
            bottom: 50px; left: 50px; width: 280px; height: 200px;
            background-color: white; border:2px solid grey; z-index:9999;
            font-size:13px; padding: 10px">
<p style="margin-top:0"><b>Key Findings:</b></p>
<p style="margin:5px 0">🟢 <b>Bernard (Fixed):</b><br>
&nbsp;&nbsp;&nbsp;GHSL max = <b>100%</b> ✓</p>
<p style="margin:5px 0">🔴 <b>Grace (Original):</b><br>
&nbsp;&nbsp;&nbsp;GHSL max = <b>30%</b> ⚠️ CAPPED</p>
<hr>
<p style="margin:5px 0; font-size:11px">
<b>Urban Bamako (45 points):</b><br>
Bernard: GHSL = 99.3% ✓<br>
Grace: GHSL = 29.7% ⚠️
</p>
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# Save map
output_path = '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/tasks/mali_comparison_map.html'
m.save(output_path)
print(f"✓ Interactive map saved to: {output_path}")

# Also create a side-by-side comparison map
from folium import plugins

# Create dual map
m_dual = plugins.DualMap(
    location=[17.0, -4.0],
    zoom_start=6,
    tiles='CartoDB positron'
)

# Add Bernard's points to left map
for idx, row in bernard_gdf.iterrows():
    radius = 3 + (row['modis_urban_percent'] / 10)

    popup_text = f"""
    <b>BERNARD (FIXED)</b><br>
    Point {row['id']}<br>
    MODIS: {row['modis_urban_percent']:.1f}%<br>
    GHSL: {row['GHSL_pct']:.1f}%<br>
    DBI: {row['DBI_pct']:.1f}%
    """

    folium.CircleMarker(
        location=[row['lat'], row['long']],
        radius=radius,
        popup=popup_text,
        color='green',
        fill=True,
        fillColor='green',
        fillOpacity=0.7,
        weight=1
    ).add_to(m_dual.m1)

# Add Grace's points to right map
for idx, row in grace_gdf.iterrows():
    radius = 3 + (row['modis_urban_percent'] / 10)

    popup_text = f"""
    <b>GRACE (ORIGINAL)</b><br>
    Point {row['id']}<br>
    MODIS: {row['modis_urban_percent']:.1f}%<br>
    GHSL: {row['GHSL_pct']:.1f}% ⚠️<br>
    DBI: {row['DBI_pct']:.1f}%
    """

    folium.CircleMarker(
        location=[row['lat'], row['long']],
        radius=radius,
        popup=popup_text,
        color='red',
        fill=True,
        fillColor='red',
        fillOpacity=0.7,
        weight=1
    ).add_to(m_dual.m2)

# Add Bamako box to both maps
for m_side in [m_dual.m1, m_dual.m2]:
    folium.PolyLine(bamako_box, color='blue', weight=2, opacity=0.7).add_to(m_side)

output_dual = '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/tasks/mali_comparison_sidebyside.html'
m_dual.save(output_dual)
print(f"✓ Side-by-side map saved to: {output_dual}")
print()
print("Open both maps in browser to visualize the differences!")
