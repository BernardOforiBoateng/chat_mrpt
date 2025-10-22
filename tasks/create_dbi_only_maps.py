"""
DBI-Only Interactive Maps
Show DBI values with MODIS comparison to highlight the mismatch
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import folium
from folium import plugins

bernard = pd.read_csv('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/Bernard_Mali_Test.csv')
grace = pd.read_csv('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/Mali_points_modis_buffer.csv')

# Merge for comparison
merged = bernard.merge(grace, on='id', suffixes=('_bernard', '_grace'))

print("Creating DBI-focused interactive maps...")

# Load Mali boundary
try:
    world = gpd.read_file('https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip')
    mali_boundary = world[world.NAME == 'Mali']
    has_boundary = True
except:
    has_boundary = False

# ========================================================
# MAP 1: DBI Values with MODIS Comparison
# ========================================================

m = folium.Map(
    location=[13, -5],
    zoom_start=6,
    tiles='CartoDB positron'
)

# Add title
title_html = '''
<div style="position: fixed;
            top: 10px; left: 50px; width: 700px; height: 130px;
            background-color: white; border:2px solid grey; z-index:9999;
            font-size:14px; padding: 12px; box-shadow: 2px 2px 6px rgba(0,0,0,0.3)">
<h3 style="margin:0 0 8px 0; color:#d32f2f">DBI Issue Confirmed: Low Values in Non-Arid Urban Areas</h3>
<p style="margin:3px 0; font-size:12px"><b>Grace's DBI = Bernard's DBI</b> (99.4% identical) - Both show same LOW values</p>
<p style="margin:3px 0; font-size:12px"><b>Problem:</b> Non-arid Bamako shows <span style="color:#d32f2f">27% DBI</span> but <span style="color:#2e7d32">49% MODIS urban</span></p>
<p style="margin:3px 0; font-size:11px; color:#666">Circle size = MODIS urban %, Color = DBI % (plasma scale)</p>
<p style="margin:3px 0; font-size:11px; color:#666">Click points to see DBI vs MODIS mismatch</p>
</div>
'''
m.get_root().html.add_child(folium.Element(title_html))

# Add points colored by DBI, sized by MODIS
for idx, row in merged.iterrows():
    # Size based on MODIS urban
    modis_pct = row['modis_urban_percent_bernard']
    radius = 4 + (modis_pct / 10)

    # Color by DBI
    dbi_pct = row['DBI_pct_bernard']

    # Calculate mismatch (MODIS - DBI)
    mismatch = modis_pct - dbi_pct
    is_major_mismatch = mismatch > 30  # MODIS 30%+ higher than DBI

    # Determine color intensity
    if dbi_pct < 20:
        color_hex = '#440154'  # Dark purple
    elif dbi_pct < 40:
        color_hex = '#31688e'  # Blue
    elif dbi_pct < 60:
        color_hex = '#35b779'  # Green
    elif dbi_pct < 80:
        color_hex = '#fde724'  # Yellow
    else:
        color_hex = '#440154'  # Dark purple

    arid_status = 'Arid' if row['arid_flag_bernard'] == 1 else 'Non-arid'
    arid_color = '#d8b365' if row['arid_flag_bernard'] == 1 else '#4575b4'

    popup_html = f"""
    <div style="width:320px; font-family:Arial">
    <h4 style="margin:0 0 8px 0; color:#1976d2">Point {int(row['id'])}</h4>
    <p style="margin:3px 0"><b>Location:</b> ({row['lat_bernard']:.3f}, {row['long_bernard']:.3f})</p>
    <p style="margin:3px 0"><b>Region:</b> <span style="color:{arid_color}; font-weight:bold">{arid_status}</span></p>
    <hr style="margin:8px 0">

    <table style="width:100%; border-collapse:collapse">
    <tr style="background:#f5f5f5">
        <th style="text-align:left; padding:4px">Method</th>
        <th style="text-align:right; padding:4px">Value</th>
    </tr>
    <tr>
        <td style="padding:4px"><b>MODIS Urban:</b></td>
        <td style="text-align:right; padding:4px; font-size:16px; color:#2e7d32"><b>{modis_pct:.1f}%</b></td>
    </tr>
    <tr style="background:#ffebee">
        <td style="padding:4px"><b>DBI (Grace):</b></td>
        <td style="text-align:right; padding:4px; font-size:16px; color:#d32f2f"><b>{row['DBI_pct_grace']:.1f}%</b></td>
    </tr>
    <tr style="background:#fff3e0">
        <td style="padding:4px"><b>DBI (Bernard):</b></td>
        <td style="text-align:right; padding:4px; font-size:16px; color:#f57c00"><b>{row['DBI_pct_bernard']:.1f}%</b></td>
    </tr>
    <tr>
        <td style="padding:4px"><b>DBI Difference:</b></td>
        <td style="text-align:right; padding:4px">{abs(row['DBI_pct_bernard'] - row['DBI_pct_grace']):.2f}%</td>
    </tr>
    </table>

    <hr style="margin:8px 0">
    <div style="background:{'#ffebee' if is_major_mismatch else '#f5f5f5'}; padding:8px; border-radius:4px">
        <p style="margin:0; font-size:13px"><b>MODIS - DBI Gap:</b>
        <span style="font-size:18px; font-weight:bold; color:{'#d32f2f' if is_major_mismatch else '#666'}">
        {mismatch:+.1f}%
        </span>
        {'<br><b style="color:#d32f2f">⚠️ MAJOR MISMATCH!</b>' if is_major_mismatch else ''}
        </p>
    </div>
    </div>
    """

    tooltip = f"Point {int(row['id'])}: MODIS={modis_pct:.0f}%, DBI={dbi_pct:.0f}% (Gap: {mismatch:+.0f}%)"

    folium.CircleMarker(
        location=[row['lat_bernard'], row['long_bernard']],
        radius=radius,
        popup=folium.Popup(popup_html, max_width=350),
        tooltip=tooltip,
        color='black' if is_major_mismatch else 'gray',
        fill=True,
        fillColor=color_hex,
        fillOpacity=0.7,
        weight=2 if is_major_mismatch else 1
    ).add_to(m)

# Add Bamako highlight
bamako_box = [
    [11.6, -9], [13.6, -9], [13.6, -7], [11.6, -7], [11.6, -9]
]
folium.PolyLine(
    bamako_box,
    color='red',
    weight=3,
    opacity=0.8,
    popup='<b>Non-Arid Bamako Region</b><br>86 points: MODIS=49%, DBI=27%<br>Gap: -22%',
    tooltip='Bamako (Major DBI underestimation)'
).add_to(m)

# Legend
legend_html = '''
<div style="position: fixed;
            bottom: 50px; left: 50px; width: 340px; height: 320px;
            background-color: white; border:2px solid grey; z-index:9999;
            font-size:12px; padding: 12px; box-shadow: 2px 2px 6px rgba(0,0,0,0.3)">
<p style="margin:0 0 8px 0; font-size:14px"><b>Key Findings:</b></p>

<div style="background:#e8f5e9; padding:8px; margin:6px 0; border-left:4px solid #4caf50">
<b>✓ DBI Values Are IDENTICAL:</b><br>
&nbsp;&nbsp;Grace's DBI = Bernard's DBI<br>
&nbsp;&nbsp;99.4% of points match exactly
</div>

<div style="background:#ffebee; padding:8px; margin:6px 0; border-left:4px solid #f44336">
<b>⚠️ DBI Underestimates Urban:</b><br>
&nbsp;&nbsp;Non-arid Bamako (86 pts):<br>
&nbsp;&nbsp;&nbsp;&nbsp;MODIS: <b>49%</b> urban<br>
&nbsp;&nbsp;&nbsp;&nbsp;DBI: <b>27%</b> urban<br>
&nbsp;&nbsp;&nbsp;&nbsp;Gap: <b>-22%</b>
</div>

<div style="background:#fff3e0; padding:8px; margin:6px 0; border-left:4px solid #ff9800">
<b>Why DBI is Low:</b><br>
• Bamako = non-arid<br>
• DBI designed for arid regions<br>
• Vegetation → high NDVI → low DBI
</div>

<hr style="margin:8px 0">

<p style="margin:4px 0; font-size:11px"><b>Circle Size:</b> MODIS urban %</p>
<p style="margin:4px 0; font-size:11px"><b>Circle Color:</b> DBI % (plasma)</p>
<p style="margin:4px 0; font-size:11px"><b>Black border:</b> Gap > 30%</p>
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# Stats box
stats_html = '''
<div style="position: fixed;
            top: 150px; left: 50px; width: 340px; height: 140px;
            background-color: white; border:2px solid grey; z-index:9999;
            font-size:11px; padding: 10px; box-shadow: 2px 2px 6px rgba(0,0,0,0.3)">
<b style="font-size:13px">DBI by Region (All 345 points):</b>
<table style="width:100%; margin-top:6px; font-size:11px">
<tr style="background:#f5f5f5; font-weight:bold">
    <th style="padding:4px; text-align:left">Region</th>
    <th style="padding:4px; text-align:center">Points</th>
    <th style="padding:4px; text-align:center">MODIS</th>
    <th style="padding:4px; text-align:center">DBI</th>
    <th style="padding:4px; text-align:center">Gap</th>
</tr>
<tr style="background:#ffebee">
    <td style="padding:4px">Non-arid SW</td>
    <td style="padding:4px; text-align:center">86</td>
    <td style="padding:4px; text-align:center">49%</td>
    <td style="padding:4px; text-align:center">27%</td>
    <td style="padding:4px; text-align:center; color:#d32f2f"><b>-22%</b></td>
</tr>
<tr style="background:#e8f5e9">
    <td style="padding:4px">Arid North</td>
    <td style="padding:4px; text-align:center">43</td>
    <td style="padding:4px; text-align:center">6%</td>
    <td style="padding:4px; text-align:center">49%</td>
    <td style="padding:4px; text-align:center; color:#4caf50"><b>+43%</b></td>
</tr>
<tr>
    <td style="padding:4px">Other</td>
    <td style="padding:4px; text-align:center">216</td>
    <td style="padding:4px; text-align:center">10%</td>
    <td style="padding:4px; text-align:center">22%</td>
    <td style="padding:4px; text-align:center">+12%</td>
</tr>
</table>
<p style="margin:6px 0 0 0; font-size:10px; color:#666">
<b>Note:</b> DBI overestimates in arid regions, underestimates in non-arid urban
</p>
</div>
'''
m.get_root().html.add_child(folium.Element(stats_html))

output_path = '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/tasks/dbi_only_interactive_map.html'
m.save(output_path)
print(f"✓ DBI-focused map saved: {output_path}")

# ========================================================
# MAP 2: Side-by-side DBI vs MODIS
# ========================================================

m_dual = plugins.DualMap(
    location=[13, -5],
    zoom_start=6,
    tiles='CartoDB positron'
)

# Left map: DBI values
for idx, row in merged.iterrows():
    dbi_pct = row['DBI_pct_bernard']
    radius = 3 + (dbi_pct / 8)

    if dbi_pct < 20:
        color = '#440154'
    elif dbi_pct < 40:
        color = '#31688e'
    elif dbi_pct < 60:
        color = '#35b779'
    else:
        color = '#fde724'

    popup = f"<b>Point {int(row['id'])}</b><br>DBI: {dbi_pct:.1f}%"

    folium.CircleMarker(
        location=[row['lat_bernard'], row['long_bernard']],
        radius=radius,
        popup=popup,
        tooltip=f"DBI: {dbi_pct:.0f}%",
        color='black',
        fill=True,
        fillColor=color,
        fillOpacity=0.7,
        weight=1
    ).add_to(m_dual.m1)

# Right map: MODIS values
for idx, row in merged.iterrows():
    modis_pct = row['modis_urban_percent_bernard']
    radius = 3 + (modis_pct / 8)

    if modis_pct < 20:
        color = '#440154'
    elif modis_pct < 40:
        color = '#31688e'
    elif modis_pct < 60:
        color = '#35b779'
    else:
        color = '#fde724'

    popup = f"<b>Point {int(row['id'])}</b><br>MODIS: {modis_pct:.1f}%"

    folium.CircleMarker(
        location=[row['lat_bernard'], row['long_bernard']],
        radius=radius,
        popup=popup,
        tooltip=f"MODIS: {modis_pct:.0f}%",
        color='black',
        fill=True,
        fillColor=color,
        fillOpacity=0.7,
        weight=1
    ).add_to(m_dual.m2)

# Add Bamako box to both
for m_side in [m_dual.m1, m_dual.m2]:
    folium.PolyLine(bamako_box, color='red', weight=2, opacity=0.7).add_to(m_side)

output_dual = '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/tasks/dbi_vs_modis_sidebyside.html'
m_dual.save(output_dual)
print(f"✓ Side-by-side map saved: {output_dual}")

print()
print("="*80)
print("DBI ANALYSIS COMPLETE")
print("="*80)
print()
print("Maps created:")
print("  1. dbi_only_interactive_map.html - Main DBI analysis with mismatch highlighting")
print("  2. dbi_vs_modis_sidebyside.html - Compare DBI (left) vs MODIS (right)")
print()
print("Key finding:")
print("  ✓ Grace's DBI = Bernard's DBI (identical)")
print("  ⚠️ DBI underestimates non-arid urban Bamako by ~22%")
print("  ⚠️ DBI overestimates arid northern Mali by ~43%")
print()
print("DBI is not a good urban indicator for Mali - use GHSL or MODIS instead")
print("="*80)
