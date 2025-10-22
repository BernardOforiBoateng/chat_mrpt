#!/usr/bin/env python3
"""
Create Interactive Visualizations for Urban Validation Analysis
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from folium import plugins
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

OUTPUT_DIR = Path('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/urban_validation_outputs')
DATA_PATH = Path('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/validation_urban_validation_final_2025-09-03.csv')

print("=" * 70)
print("GENERATING URBAN VALIDATION VISUALIZATIONS")
print("=" * 70)

# Load data
df = pd.read_csv(DATA_PATH)
state_analysis = pd.read_csv(OUTPUT_DIR / 'state_analysis_complete.csv')

# ========== 1. METHOD CORRELATION HEATMAP ==========
print("\n[1/8] Creating method correlation heatmap...")

methods = ['control_urban', 'ndbi_urban', 'ghsl_urban', 'ebbi_urban']
corr_matrix = df[methods].corr()

# Rename for display
display_names = {
    'control_urban': 'Control (HLS)',
    'ndbi_urban': 'NDBI (Sentinel-2)',
    'ghsl_urban': 'GHSL (UN)',
    'ebbi_urban': 'EBBI (Landsat)'
}

corr_display = corr_matrix.rename(index=display_names, columns=display_names)

fig_corr = go.Figure(data=go.Heatmap(
    z=corr_display.values,
    x=corr_display.columns,
    y=corr_display.columns,
    colorscale='RdBu',
    zmid=0,
    text=np.round(corr_display.values, 2),
    texttemplate='%{text}',
    textfont={"size": 12},
    colorbar=dict(title="Correlation")
))

fig_corr.update_layout(
    title="Method Agreement: Correlation Matrix",
    xaxis_title="",
    yaxis_title="",
    width=600,
    height=500
)

fig_corr.write_html(OUTPUT_DIR / 'method_correlation_heatmap.html')
print("✓ Correlation heatmap created")

# ========== 2. STATE CLASSIFICATION OVERVIEW ==========
print("\n[2/8] Creating state classification overview...")

# Prepare data for stacked bar chart
state_class = []
for state in df['StateName'].unique():
    state_df = df[df['StateName'] == state]
    total = len(state_df)
    state_class.append({
        'State': state,
        'Urban': (state_df['classification'] == 'Urban').sum() / total * 100,
        'Peri-urban': (state_df['classification'] == 'Peri-urban').sum() / total * 100,
        'Rural': (state_df['classification'] == 'Rural').sum() / total * 100
    })

state_class_df = pd.DataFrame(state_class).sort_values('Urban', ascending=False)

fig_stack = go.Figure()
fig_stack.add_trace(go.Bar(name='Urban', x=state_class_df['State'], y=state_class_df['Urban'],
                           marker_color='#e74c3c'))
fig_stack.add_trace(go.Bar(name='Peri-urban', x=state_class_df['State'], y=state_class_df['Peri-urban'],
                           marker_color='#f39c12'))
fig_stack.add_trace(go.Bar(name='Rural', x=state_class_df['State'], y=state_class_df['Rural'],
                           marker_color='#27ae60'))

fig_stack.update_layout(
    barmode='stack',
    title='Ward Classification Distribution by State',
    xaxis_title='State',
    yaxis_title='Percentage of Wards',
    height=600,
    showlegend=True,
    hovermode='x unified'
)

fig_stack.write_html(OUTPUT_DIR / 'state_classification_distribution.html')
print("✓ State classification chart created")

# ========== 3. MISCLASSIFICATION ANALYSIS CHART ==========
print("\n[3/8] Creating misclassification analysis chart...")

# Get misclassification data
misclass_data = state_analysis[['State', 'Marked_Urban_But_Rural', 'Marked_Rural_But_Urban', 
                                'Total_Misclassifications']].copy()
misclass_data = misclass_data[misclass_data['Total_Misclassifications'] > 0]
misclass_data = misclass_data.sort_values('Total_Misclassifications', ascending=True)

fig_misclass = go.Figure()
fig_misclass.add_trace(go.Bar(
    y=misclass_data['State'],
    x=misclass_data['Marked_Urban_But_Rural'],
    name='Marked Urban but <30% Satellite',
    orientation='h',
    marker_color='#e74c3c'
))
fig_misclass.add_trace(go.Bar(
    y=misclass_data['State'],
    x=misclass_data['Marked_Rural_But_Urban'],
    name='Marked Rural but >50% Satellite',
    orientation='h',
    marker_color='#3498db'
))

fig_misclass.update_layout(
    barmode='stack',
    title='Potential Misclassifications by State',
    xaxis_title='Number of Misclassified Wards',
    yaxis_title='',
    height=max(400, len(misclass_data) * 25),
    showlegend=True,
    hovermode='y unified'
)

fig_misclass.write_html(OUTPUT_DIR / 'misclassification_analysis.html')
print("✓ Misclassification chart created")

# ========== 4. METHOD COMPARISON SCATTER PLOTS ==========
print("\n[4/8] Creating method comparison scatter plots...")

fig_scatter = make_subplots(
    rows=2, cols=2,
    subplot_titles=('Control vs GHSL (UN Standard)', 'NDBI vs GHSL (UN Standard)',
                    'EBBI vs GHSL (UN Standard)', 'Control vs NDBI'),
    horizontal_spacing=0.15,
    vertical_spacing=0.15
)

# Sample data for performance (every 10th ward)
df_sample = df.iloc[::10].copy()

# Control vs GHSL
fig_scatter.add_trace(
    go.Scatter(x=df_sample['ghsl_urban'], y=df_sample['control_urban'],
               mode='markers', marker=dict(size=3, opacity=0.5),
               name='Control vs GHSL'),
    row=1, col=1
)

# NDBI vs GHSL
fig_scatter.add_trace(
    go.Scatter(x=df_sample['ghsl_urban'], y=df_sample['ndbi_urban'],
               mode='markers', marker=dict(size=3, opacity=0.5, color='#e74c3c'),
               name='NDBI vs GHSL'),
    row=1, col=2
)

# EBBI vs GHSL
fig_scatter.add_trace(
    go.Scatter(x=df_sample['ghsl_urban'], y=df_sample['ebbi_urban'],
               mode='markers', marker=dict(size=3, opacity=0.5, color='#27ae60'),
               name='EBBI vs GHSL'),
    row=2, col=1
)

# Control vs NDBI
fig_scatter.add_trace(
    go.Scatter(x=df_sample['ndbi_urban'], y=df_sample['control_urban'],
               mode='markers', marker=dict(size=3, opacity=0.5, color='#f39c12'),
               name='Control vs NDBI'),
    row=2, col=2
)

# Add diagonal reference lines
for i in range(1, 3):
    for j in range(1, 3):
        fig_scatter.add_shape(
            type="line", x0=0, y0=0, x1=100, y1=100,
            line=dict(color="gray", width=1, dash="dash"),
            row=i, col=j
        )

fig_scatter.update_xaxes(title_text="Urban %", range=[0, 100])
fig_scatter.update_yaxes(title_text="Urban %", range=[0, 100])
fig_scatter.update_layout(
    title_text="Method Comparison: Scatter Plots",
    showlegend=False,
    height=800,
    width=900
)

fig_scatter.write_html(OUTPUT_DIR / 'method_comparison_scatter.html')
print("✓ Method comparison scatter plots created")

# ========== 5. CONSISTENTLY RURAL WARDS BY STATE ==========
print("\n[5/8] Creating consistently rural wards chart...")

rural_by_state = df[df['consistently_rural'] == 'YES'].groupby('StateName').size().reset_index(name='count')
rural_by_state = rural_by_state.sort_values('count', ascending=True)

fig_rural = go.Figure(go.Bar(
    y=rural_by_state['StateName'],
    x=rural_by_state['count'],
    orientation='h',
    text=rural_by_state['count'],
    textposition='outside',
    marker_color='#27ae60'
))

fig_rural.update_layout(
    title='Consistently Rural Wards by State (All 4 Methods <30%)',
    xaxis_title='Number of Consistently Rural Wards',
    yaxis_title='',
    height=max(400, len(rural_by_state) * 30),
    showlegend=False
)

fig_rural.write_html(OUTPUT_DIR / 'consistently_rural_by_state.html')
print("✓ Consistently rural wards chart created")

# ========== 6. DELTA STATE DETAILED VISUALIZATION ==========
print("\n[6/8] Creating Delta State analysis visualization...")

delta_df = df[df['StateName'] == 'Delta'].copy()

# Create box plot for Delta wards
fig_delta = go.Figure()

for method, color in zip(['control_urban', 'ndbi_urban', 'ghsl_urban', 'ebbi_urban'],
                         ['#3498db', '#e74c3c', '#27ae60', '#f39c12']):
    fig_delta.add_trace(go.Box(
        y=delta_df[method],
        name=method.replace('_urban', '').upper(),
        marker_color=color,
        boxpoints='outliers'
    ))

fig_delta.update_layout(
    title='Delta State: Urban Percentage Distribution by Method',
    yaxis_title='Urban Percentage',
    xaxis_title='Detection Method',
    height=500,
    showlegend=False
)

# Add threshold lines
fig_delta.add_hline(y=30, line_dash="dash", line_color="red",
                    annotation_text="Rural Threshold (30%)")
fig_delta.add_hline(y=50, line_dash="dash", line_color="orange",
                    annotation_text="Urban Threshold (50%)")

fig_delta.write_html(OUTPUT_DIR / 'delta_state_analysis.html')
print("✓ Delta State visualization created")

# ========== 7. NATIONAL PRIORITY HEATMAP ==========
print("\n[7/8] Creating national priority heatmap...")

# Create priority matrix
priority_matrix = state_analysis[['State', 'Total_Misclassifications', 'Consistently_Rural_Percent', 
                                  'Method_Disagreement_Mean']].copy()

fig_priority = px.scatter(priority_matrix, 
                          x='Total_Misclassifications', 
                          y='Method_Disagreement_Mean',
                          size='Consistently_Rural_Percent',
                          color='Total_Misclassifications',
                          hover_data=['State', 'Consistently_Rural_Percent'],
                          text='State',
                          title='State Priority Matrix for NMEP Review',
                          labels={'Total_Misclassifications': 'Total Misclassifications',
                                 'Method_Disagreement_Mean': 'Method Disagreement (Mean STD)',
                                 'Consistently_Rural_Percent': 'Consistently Rural %'},
                          color_continuous_scale='Reds')

fig_priority.update_traces(textposition='top center', textfont_size=8)
fig_priority.update_layout(height=600, width=900)

# Add quadrant lines
fig_priority.add_vline(x=5, line_dash="dash", line_color="gray", opacity=0.5)
fig_priority.add_hline(y=priority_matrix['Method_Disagreement_Mean'].median(), 
                       line_dash="dash", line_color="gray", opacity=0.5)

# Add annotations for quadrants
fig_priority.add_annotation(x=15, y=28, text="HIGH PRIORITY<br>High misclass, High disagreement",
                            showarrow=False, bgcolor="rgba(255,0,0,0.1)")
fig_priority.add_annotation(x=2, y=20, text="LOW PRIORITY<br>Low misclass, Low disagreement",
                            showarrow=False, bgcolor="rgba(0,255,0,0.1)")

fig_priority.write_html(OUTPUT_DIR / 'state_priority_matrix.html')
print("✓ State priority matrix created")

# ========== 8. CREATE SUMMARY DASHBOARD ==========
print("\n[8/8] Creating executive dashboard...")

# Create multi-panel dashboard
fig_dashboard = make_subplots(
    rows=3, cols=2,
    subplot_titles=('National Classification Overview', 'Top 10 States by Misclassifications',
                    'Method Urban % Distribution', 'Consistently Rural Distribution',
                    'Delta State Analysis', 'Method Agreement'),
    specs=[[{'type': 'pie'}, {'type': 'bar'}],
           [{'type': 'box'}, {'type': 'bar'}],
           [{'type': 'bar'}, {'type': 'scatter'}]],
    vertical_spacing=0.12,
    horizontal_spacing=0.15
)

# Panel 1: National classification pie
class_counts = df['classification'].value_counts()
fig_dashboard.add_trace(
    go.Pie(labels=class_counts.index, values=class_counts.values,
           marker_colors=['#e74c3c', '#f39c12', '#27ae60']),
    row=1, col=1
)

# Panel 2: Top misclassifications
top_misclass = state_analysis.nlargest(10, 'Total_Misclassifications')
fig_dashboard.add_trace(
    go.Bar(x=top_misclass['State'], y=top_misclass['Total_Misclassifications'],
           marker_color='#e74c3c'),
    row=1, col=2
)

# Panel 3: Method distributions
for method, color in zip(methods, ['#3498db', '#e74c3c', '#27ae60', '#f39c12']):
    fig_dashboard.add_trace(
        go.Box(y=df[method], name=method.replace('_urban', '').upper(),
               marker_color=color),
        row=2, col=1
    )

# Panel 4: Consistently rural
rural_counts = state_analysis.nlargest(10, 'Consistently_Rural')
fig_dashboard.add_trace(
    go.Bar(x=rural_counts['State'], y=rural_counts['Consistently_Rural'],
           marker_color='#27ae60'),
    row=2, col=2
)

# Panel 5: Delta specific
delta_class = delta_df['classification'].value_counts()
fig_dashboard.add_trace(
    go.Bar(x=delta_class.index, y=delta_class.values,
           marker_color=['#e74c3c', '#f39c12', '#27ae60']),
    row=3, col=1
)

# Panel 6: Method correlations
corr_values = []
corr_labels = []
for i, m1 in enumerate(methods):
    for m2 in methods[i+1:]:
        corr_values.append(corr_matrix.loc[m1, m2])
        corr_labels.append(f"{m1[:4]}-{m2[:4]}")

fig_dashboard.add_trace(
    go.Scatter(x=corr_labels, y=corr_values, mode='markers+lines',
               marker=dict(size=10, color=corr_values, colorscale='RdBu')),
    row=3, col=2
)

fig_dashboard.update_layout(
    title_text="Urban Validation Executive Dashboard",
    showlegend=False,
    height=1200,
    width=1200
)

fig_dashboard.write_html(OUTPUT_DIR / 'executive_dashboard.html')
print("✓ Executive dashboard created")

print("\n" + "=" * 70)
print("VISUALIZATION GENERATION COMPLETE")
print("=" * 70)
print(f"\nAll visualizations saved to: {OUTPUT_DIR}")
print("\nGenerated visualizations:")
print("  1. method_correlation_heatmap.html")
print("  2. state_classification_distribution.html")
print("  3. misclassification_analysis.html")
print("  4. method_comparison_scatter.html")
print("  5. consistently_rural_by_state.html")
print("  6. delta_state_analysis.html")
print("  7. state_priority_matrix.html")
print("  8. executive_dashboard.html")