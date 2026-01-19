"""
TPR Analysis Report Generator.

Generates comprehensive reports documenting the entire TPR analysis workflow,
including results, visualizations, and recommendations for stakeholder presentation.
"""

import os
import json
from datetime import datetime
from pathlib import Path
import pandas as pd
import geopandas as gpd
from typing import Dict, Any, Optional
import logging
from jinja2 import Template
import base64

logger = logging.getLogger(__name__)

class TPRReportGenerator:
    """Generate comprehensive TPR analysis reports."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.output_dir = Path(f'instance/uploads/{session_id}')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_report(self, 
                       analysis_results: Dict[str, Any],
                       tpr_data: pd.DataFrame,
                       metadata: Dict[str, Any]) -> str:
        """
        Generate comprehensive TPR analysis report.
        
        Args:
            analysis_results: Results from TPR pipeline
            tpr_data: Final TPR data with all calculations
            metadata: Analysis metadata (filters, parameters, etc.)
            
        Returns:
            Path to generated report
        """
        logger.info("Generating TPR analysis report")
        
        # Prepare report data
        report_data = self._prepare_report_data(analysis_results, tpr_data, metadata)
        
        # Generate HTML report
        html_content = self._generate_html_report(report_data)
        
        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"TPR_Analysis_Report_{report_data['state_name']}_{timestamp}.html"
        report_path = self.output_dir / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"TPR report generated: {report_path}")
        return str(report_path)
    
    def _prepare_report_data(self, analysis_results, tpr_data, metadata):
        """Prepare all data needed for the report."""
        # Basic information
        state_name = metadata.get('state_name', 'Unknown')
        
        # Calculate key metrics
        tpr_values = tpr_data['TPR'].dropna()
        
        # Identify high-risk wards
        high_risk_threshold = 50
        very_high_risk_threshold = 70
        high_risk_wards = tpr_data[tpr_data['TPR'] > high_risk_threshold]
        very_high_risk_wards = tpr_data[tpr_data['TPR'] > very_high_risk_threshold]
        
        # Get environmental variables if present
        env_vars = []
        env_columns = ['rainfall', 'temp', 'temperature', 'evi', 'ndvi', 'ndmi', 'ndwi', 
                      'elevation', 'distance_to_water', 'soil_wetness', 'nighttime_lights',
                      'housing_quality', 'flood', 'pfpr']
        for col in tpr_data.columns:
            if col.lower() in env_columns:
                coverage = tpr_data[col].notna().sum() / len(tpr_data) * 100
                env_vars.append({
                    'name': col.replace('_', ' ').title(),
                    'coverage': f"{coverage:.1f}%"
                })
        
        # Testing method breakdown
        method_counts = {}
        if 'Method' in tpr_data.columns:
            method_counts = tpr_data['Method'].value_counts().to_dict()
        
        # Load TPR map if exists
        map_path = None
        # Check multiple possible locations for the map
        map_search_paths = [
            self.output_dir,
            self.output_dir / 'visualizations',
            self.output_dir.parent / 'visualizations'  # Check sibling directory
        ]
        
        for search_dir in map_search_paths:
            if search_dir.exists():
                for file in search_dir.glob("*_ward_tpr_map_*.html"):
                    map_path = file
                    logger.info(f"Found TPR map at: {map_path}")
                    break
            if map_path:
                break
        
        # Try to read map content for embedding
        map_content = None
        if map_path and map_path.exists():
            try:
                with open(map_path, 'r', encoding='utf-8') as f:
                    map_html = f.read()
                    # Extract just the plotly div and script content
                    # Look for the div containing the plot
                    import re
                    div_match = re.search(r'<div id="[^"]*".*?</div>', map_html, re.DOTALL)
                    script_match = re.search(r'<script type="text/javascript">.*?Plotly\.newPlot.*?</script>', map_html, re.DOTALL)
                    
                    if div_match and script_match:
                        map_content = div_match.group(0) + '\n' + script_match.group(0)
                        logger.info("Successfully extracted map content for embedding")
            except Exception as e:
                logger.warning(f"Could not read map content: {e}")
        
        # Get threshold recommendations from analysis results
        recommendations = []
        if 'threshold_results' in analysis_results:
            thresh_data = analysis_results['threshold_results']
            if thresh_data.get('recommendations'):
                recommendations = thresh_data['recommendations']
        
        return {
            'state_name': state_name,
            'generation_date': datetime.now().strftime('%B %d, %Y'),
            'generation_time': datetime.now().strftime('%I:%M %p'),
            'source_file': metadata.get('source_file', 'Unknown'),
            'data_year': metadata.get('year', 'Unknown'),
            'data_month': metadata.get('month', 'Unknown'),
            'facility_level': metadata.get('facility_level', 'All'),
            'age_group': metadata.get('age_group', 'All ages'),
            'total_wards': len(tpr_data),
            'wards_with_data': len(tpr_values),
            'mean_tpr': f"{tpr_values.mean():.1f}%",
            'median_tpr': f"{tpr_values.median():.1f}%",
            'min_tpr': f"{tpr_values.min():.1f}%",
            'max_tpr': f"{tpr_values.max():.1f}%",
            'high_risk_count': len(high_risk_wards),
            'very_high_risk_count': len(very_high_risk_wards),
            'high_risk_wards': high_risk_wards.nlargest(10, 'TPR')[['WardName', 'LGA', 'TPR']].to_dict('records'),
            'env_vars': env_vars,
            'method_counts': method_counts,
            'recommendations': recommendations,
            'map_path': str(map_path) if map_path else None,
            'map_content': map_content,
            'pipeline_duration': analysis_results.get('pipeline_duration', 'Unknown')
        }
    
    def _generate_html_report(self, data):
        """Generate HTML report using template."""
        template_str = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>TPR Analysis Report - {{ state_name }}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        h1, h2, h3 {
            color: #333;
        }
        h1 {
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }
        h2 {
            margin-top: 30px;
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
        }
        .header-info {
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
            color: #666;
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .metric-box {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            text-align: center;
            border: 1px solid #e9ecef;
        }
        .metric-value {
            font-size: 28px;
            font-weight: bold;
            color: #007bff;
        }
        .metric-label {
            color: #666;
            font-size: 14px;
            margin-top: 5px;
        }
        .alert {
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }
        .alert-warning {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
        }
        .alert-danger {
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        .map-container {
            width: 100%;
            height: 600px;
            border: 1px solid #ddd;
            margin: 20px 0;
        }
        .workflow-step {
            padding: 10px;
            margin: 10px 0;
            background-color: #f8f9fa;
            border-left: 4px solid #007bff;
        }
        .recommendation {
            padding: 15px;
            margin: 10px 0;
            background-color: #e7f3ff;
            border-left: 4px solid #007bff;
        }
        @media print {
            body {
                background-color: white;
            }
            .container {
                box-shadow: none;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Test Positivity Rate (TPR) Analysis Report</h1>
        <h2>{{ state_name }} State</h2>
        
        <div class="header-info">
            <div>
                <strong>Data Source:</strong> {{ source_file }}<br>
                <strong>Data Period:</strong> {{ data_month }}/{{ data_year }}<br>
                <strong>Analysis Date:</strong> {{ generation_date }}
            </div>
            <div>
                <strong>Facility Level:</strong> {{ facility_level }}<br>
                <strong>Age Group:</strong> {{ age_group }}<br>
                <strong>Report Time:</strong> {{ generation_time }}
            </div>
        </div>
        
        <h2>Executive Summary</h2>
        <div class="metric-grid">
            <div class="metric-box">
                <div class="metric-value">{{ mean_tpr }}</div>
                <div class="metric-label">Mean TPR</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{{ total_wards }}</div>
                <div class="metric-label">Total Wards</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{{ high_risk_count }}</div>
                <div class="metric-label">High Risk Wards (>50%)</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{{ very_high_risk_count }}</div>
                <div class="metric-label">Very High Risk (>70%)</div>
            </div>
        </div>
        
        {% if very_high_risk_count > 0 %}
        <div class="alert alert-danger">
            <strong>Alert:</strong> {{ very_high_risk_count }} wards have very high TPR (>70%), indicating severe malaria burden requiring immediate intervention.
        </div>
        {% elif high_risk_count > 0 %}
        <div class="alert alert-warning">
            <strong>Warning:</strong> {{ high_risk_count }} wards have high TPR (>50%), indicating significant malaria burden.
        </div>
        {% endif %}
        
        <h2>Analysis Workflow</h2>
        <div class="workflow-step">
            <strong>Step 1:</strong> Loaded NMEP data from {{ source_file }}
        </div>
        <div class="workflow-step">
            <strong>Step 2:</strong> Filtered data for {{ state_name }} State
        </div>
        <div class="workflow-step">
            <strong>Step 3:</strong> Applied facility level filter: {{ facility_level }}
        </div>
        <div class="workflow-step">
            <strong>Step 4:</strong> Applied age group filter: {{ age_group }}
        </div>
        <div class="workflow-step">
            <strong>Step 5:</strong> Calculated TPR for {{ wards_with_data }} wards with sufficient data
        </div>
        <div class="workflow-step">
            <strong>Step 6:</strong> Extracted environmental variables for epidemiological context
        </div>
        <div class="workflow-step">
            <strong>Step 7:</strong> Generated recommendations based on TPR thresholds
        </div>
        
        <h2>TPR Statistics</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Mean TPR</td>
                <td>{{ mean_tpr }}</td>
            </tr>
            <tr>
                <td>Median TPR</td>
                <td>{{ median_tpr }}</td>
            </tr>
            <tr>
                <td>Minimum TPR</td>
                <td>{{ min_tpr }}</td>
            </tr>
            <tr>
                <td>Maximum TPR</td>
                <td>{{ max_tpr }}</td>
            </tr>
        </table>
        
        {% if method_counts %}
        <h3>Testing Methods Used</h3>
        <table>
            <tr>
                <th>Method</th>
                <th>Count</th>
            </tr>
            {% for method, count in method_counts.items() %}
            <tr>
                <td>{{ method }}</td>
                <td>{{ count }}</td>
            </tr>
            {% endfor %}
        </table>
        {% endif %}
        
        <h2>High Risk Wards (Top 10)</h2>
        <table>
            <tr>
                <th>Ward Name</th>
                <th>LGA</th>
                <th>TPR (%)</th>
            </tr>
            {% for ward in high_risk_wards %}
            <tr>
                <td>{{ ward.WardName }}</td>
                <td>{{ ward.LGA }}</td>
                <td>{{ "%.1f"|format(ward.TPR) }}%</td>
            </tr>
            {% endfor %}
        </table>
        
        {% if env_vars %}
        <h2>Environmental Variables Extracted</h2>
        <p>The following environmental variables were extracted to provide epidemiological context:</p>
        <table>
            <tr>
                <th>Variable</th>
                <th>Coverage</th>
            </tr>
            {% for var in env_vars %}
            <tr>
                <td>{{ var.name }}</td>
                <td>{{ var.coverage }}</td>
            </tr>
            {% endfor %}
        </table>
        <p><em>Note: Environmental data is averaged across all available years to ensure robust analysis.</em></p>
        {% endif %}
        
        {% if recommendations %}
        <h2>Recommendations</h2>
        {% for rec in recommendations %}
        <div class="recommendation">
            {{ rec }}
        </div>
        {% endfor %}
        {% endif %}
        
        {% if map_content %}
        <h2>TPR Distribution Map</h2>
        <p>The map below shows the spatial distribution of TPR across wards in {{ state_name }} State.</p>
        <div class="map-container">
            {{ map_content|safe }}
        </div>
        {% elif map_path %}
        <h2>TPR Distribution Map</h2>
        <p>The TPR distribution map has been generated separately and can be viewed at:</p>
        <p><a href="{{ map_path }}" target="_blank">{{ map_path }}</a></p>
        {% endif %}
        
        <h2>Methodology Notes</h2>
        <ul>
            <li><strong>TPR Calculation:</strong> Test Positivity Rate = (Positive Tests / Total Tests) × 100</li>
            <li><strong>Data Sources:</strong> National Malaria Elimination Programme (NMEP) routine data</li>
            <li><strong>Environmental Data:</strong> Extracted from multi-temporal raster datasets using ward centroids</li>
            <li><strong>Risk Thresholds:</strong> High risk (>50%), Very high risk (>70%)</li>
        </ul>
        
        <hr style="margin-top: 50px;">
        <p style="text-align: center; color: #666; font-size: 12px;">
            Generated by ChatMRPT TPR Analysis Module | {{ generation_date }} at {{ generation_time }}
        </p>
    </div>
</body>
</html>'''
        
        template = Template(template_str)
        return template.render(**data)
    
    def generate_pdf_report(self, html_path: str) -> Optional[str]:
        """
        Convert HTML report to PDF (requires wkhtmltopdf or similar).
        This is a placeholder for PDF generation functionality.
        """
        # TODO: Implement PDF generation using wkhtmltopdf, weasyprint, or similar
        logger.info("PDF generation not yet implemented")
        return None