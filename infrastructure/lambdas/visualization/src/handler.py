"""
Visualization Lambda function.
Generates maps and charts for malaria risk analysis.
"""
import json
import boto3
import os
import pandas as pd
import geopandas as gpd
import folium
from folium import plugins
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List, Optional
from datetime import datetime
import tempfile
import uuid


s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Generate visualizations based on analysis results.

    Args:
        event: API Gateway event or Step Functions input
        context: Lambda context

    Returns:
        Visualization URLs
    """
    print(f"Visualization request: {json.dumps(event)}")

    try:
        # Parse request
        if 'body' in event:
            # API Gateway
            body = json.loads(event['body'])
        else:
            # Step Functions
            body = event

        visualization_type = body.get('visualization_type')
        session_id = body.get('session_id')
        analysis_id = body.get('analysis_id')

        if not visualization_type or not session_id:
            return _error_response(400, "visualization_type and session_id required")

        # Route to appropriate handler
        if visualization_type == 'risk_map':
            result = generate_risk_map(body, session_id, analysis_id)
        elif visualization_type == 'ranking_chart':
            result = generate_ranking_chart(body, session_id, analysis_id)
        elif visualization_type == 'composite_dashboard':
            result = generate_composite_dashboard(body, session_id, analysis_id)
        elif visualization_type == 'settlement_map':
            result = generate_settlement_map(body, session_id, analysis_id)
        else:
            return _error_response(400, f"Unknown visualization type: {visualization_type}")

        return _success_response(result)

    except Exception as e:
        print(f"Error in visualization handler: {str(e)}")
        return _error_response(500, str(e))


def generate_risk_map(request: Dict[str, Any], session_id: str, analysis_id: str) -> Dict[str, Any]:
    """
    Generate interactive risk map.
    """
    print(f"Generating risk map for session {session_id}")

    # Get analysis results
    results_key = f"results/{session_id}/analysis_{analysis_id}.csv"
    shapefile_dir = f"uploads/{session_id}/shapefile/"

    # Download data
    with tempfile.TemporaryDirectory() as tmpdir:
        # Download CSV results
        csv_path = os.path.join(tmpdir, 'results.csv')
        s3_client.download_file(
            os.environ.get('DATA_BUCKET', 'chatmrpt-data-prod'),
            results_key,
            csv_path
        )
        df = pd.read_csv(csv_path)

        # Download shapefile
        shapefile_path = _download_shapefile(shapefile_dir, tmpdir)
        if shapefile_path:
            gdf = gpd.read_file(shapefile_path)

            # Merge data with shapefile
            merge_col = _find_merge_column(df, gdf)
            if merge_col:
                gdf = gdf.merge(df, left_on=merge_col['shapefile'], right_on=merge_col['data'], how='left')
        else:
            # Create point geometries from coordinates if available
            if 'longitude' in df.columns and 'latitude' in df.columns:
                gdf = gpd.GeoDataFrame(
                    df,
                    geometry=gpd.points_from_xy(df.longitude, df.latitude),
                    crs='EPSG:4326'
                )
            else:
                return _error_response(400, "No spatial data available for mapping")

        # Create folium map
        map_obj = create_folium_map(gdf, request.get('indicator', 'risk_score'))

        # Save map
        map_html = map_obj._repr_html_()
        map_key = f"visualizations/{session_id}/risk_map_{analysis_id}.html"

        s3_client.put_object(
            Bucket=os.environ.get('DATA_BUCKET', 'chatmrpt-data-prod'),
            Key=map_key,
            Body=map_html,
            ContentType='text/html'
        )

        # Generate signed URL
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': os.environ.get('DATA_BUCKET'), 'Key': map_key},
            ExpiresIn=3600
        )

        return {
            'visualization_type': 'risk_map',
            'url': url,
            'key': map_key,
            'features_count': len(gdf)
        }


def generate_ranking_chart(request: Dict[str, Any], session_id: str, analysis_id: str) -> Dict[str, Any]:
    """
    Generate ranking bar chart.
    """
    print(f"Generating ranking chart for session {session_id}")

    # Get analysis results
    results_key = f"results/{session_id}/analysis_{analysis_id}.csv"

    with tempfile.NamedTemporaryFile(suffix='.csv') as tmp:
        s3_client.download_file(
            os.environ.get('DATA_BUCKET', 'chatmrpt-data-prod'),
            results_key,
            tmp.name
        )
        df = pd.read_csv(tmp.name)

        # Get indicator and ward columns
        indicator = request.get('indicator', 'risk_score')
        ward_col = _find_ward_column(df)

        if not ward_col or indicator not in df.columns:
            return _error_response(400, f"Required columns not found")

        # Sort by indicator
        df_sorted = df.nlargest(request.get('top_n', 20), indicator)

        # Create plotly chart
        fig = px.bar(
            df_sorted,
            x=indicator,
            y=ward_col,
            orientation='h',
            title=f"Top {len(df_sorted)} Wards by {indicator.replace('_', ' ').title()}",
            labels={indicator: indicator.replace('_', ' ').title(), ward_col: 'Ward'},
            color=indicator,
            color_continuous_scale='RdYlGn_r'
        )

        fig.update_layout(
            height=600,
            margin=dict(l=150, r=50, t=50, b=50),
            showlegend=False
        )

        # Save chart
        chart_html = fig.to_html(include_plotlyjs='cdn')
        chart_key = f"visualizations/{session_id}/ranking_chart_{analysis_id}.html"

        s3_client.put_object(
            Bucket=os.environ.get('DATA_BUCKET', 'chatmrpt-data-prod'),
            Key=chart_key,
            Body=chart_html,
            ContentType='text/html'
        )

        # Generate signed URL
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': os.environ.get('DATA_BUCKET'), 'Key': chart_key},
            ExpiresIn=3600
        )

        return {
            'visualization_type': 'ranking_chart',
            'url': url,
            'key': chart_key,
            'wards_shown': len(df_sorted)
        }


def generate_composite_dashboard(request: Dict[str, Any], session_id: str, analysis_id: str) -> Dict[str, Any]:
    """
    Generate composite dashboard with multiple visualizations.
    """
    print(f"Generating composite dashboard for session {session_id}")

    # Get analysis results
    results_key = f"results/{session_id}/analysis_{analysis_id}.csv"

    with tempfile.NamedTemporaryFile(suffix='.csv') as tmp:
        s3_client.download_file(
            os.environ.get('DATA_BUCKET', 'chatmrpt-data-prod'),
            results_key,
            tmp.name
        )
        df = pd.read_csv(tmp.name)

        # Create subplots
        from plotly.subplots import make_subplots

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Risk Distribution', 'Top 10 High Risk Wards',
                          'Indicator Correlation', 'Risk Categories'),
            specs=[[{"type": "histogram"}, {"type": "bar"}],
                   [{"type": "heatmap"}, {"type": "pie"}]]
        )

        # 1. Risk distribution histogram
        if 'risk_score' in df.columns:
            fig.add_trace(
                go.Histogram(x=df['risk_score'], nbinsx=20, name='Risk Score'),
                row=1, col=1
            )

        # 2. Top 10 wards bar chart
        ward_col = _find_ward_column(df)
        if ward_col and 'risk_score' in df.columns:
            top_10 = df.nlargest(10, 'risk_score')
            fig.add_trace(
                go.Bar(x=top_10[ward_col], y=top_10['risk_score'], name='Top Wards'),
                row=1, col=2
            )

        # 3. Correlation heatmap
        numeric_cols = df.select_dtypes(include=['number']).columns[:10]  # Limit to 10 for readability
        if len(numeric_cols) > 1:
            corr = df[numeric_cols].corr()
            fig.add_trace(
                go.Heatmap(z=corr.values, x=corr.columns, y=corr.columns, colorscale='RdBu'),
                row=2, col=1
            )

        # 4. Risk categories pie chart
        if 'risk_category' in df.columns:
            category_counts = df['risk_category'].value_counts()
            fig.add_trace(
                go.Pie(labels=category_counts.index, values=category_counts.values),
                row=2, col=2
            )

        fig.update_layout(height=800, showlegend=False, title_text="Malaria Risk Analysis Dashboard")

        # Save dashboard
        dashboard_html = fig.to_html(include_plotlyjs='cdn')
        dashboard_key = f"visualizations/{session_id}/dashboard_{analysis_id}.html"

        s3_client.put_object(
            Bucket=os.environ.get('DATA_BUCKET', 'chatmrpt-data-prod'),
            Key=dashboard_key,
            Body=dashboard_html,
            ContentType='text/html'
        )

        # Generate signed URL
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': os.environ.get('DATA_BUCKET'), 'Key': dashboard_key},
            ExpiresIn=3600
        )

        return {
            'visualization_type': 'composite_dashboard',
            'url': url,
            'key': dashboard_key
        }


def generate_settlement_map(request: Dict[str, Any], session_id: str, analysis_id: str) -> Dict[str, Any]:
    """
    Generate settlement classification map.
    """
    print(f"Generating settlement map for session {session_id}")

    # This would integrate with settlement footprint data
    # For now, return a placeholder
    return {
        'visualization_type': 'settlement_map',
        'message': 'Settlement map generation queued',
        'session_id': session_id
    }


def create_folium_map(gdf: gpd.GeoDataFrame, indicator: str) -> folium.Map:
    """Create folium choropleth map."""
    # Get bounds
    bounds = gdf.total_bounds
    center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]

    # Create map
    m = folium.Map(location=center, zoom_start=8, tiles='OpenStreetMap')

    # Add choropleth
    if indicator in gdf.columns:
        # Normalize values for coloring
        vmin = gdf[indicator].min()
        vmax = gdf[indicator].max()

        folium.Choropleth(
            geo_data=gdf.to_json(),
            data=gdf,
            columns=[gdf.index[0], indicator],
            key_on='feature.id',
            fill_color='YlOrRd',
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name=indicator.replace('_', ' ').title(),
            smooth_factor=0
        ).add_to(m)

        # Add tooltips
        style_function = lambda x: {
            'fillColor': '#ffffff',
            'color': '#000000',
            'fillOpacity': 0.1,
            'weight': 0.1
        }

        highlight_function = lambda x: {
            'fillColor': '#000000',
            'color': '#000000',
            'fillOpacity': 0.50,
            'weight': 0.1
        }

        ward_col = _find_ward_column(gdf)
        if ward_col:
            tooltip = folium.features.GeoJsonTooltip(
                fields=[ward_col, indicator],
                aliases=['Ward:', f'{indicator.replace("_", " ").title()}:'],
                style=('background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;')
            )

            folium.features.GeoJson(
                gdf.to_json(),
                style_function=style_function,
                highlight_function=highlight_function,
                tooltip=tooltip
            ).add_to(m)

    # Add fullscreen control
    plugins.Fullscreen().add_to(m)

    return m


def _download_shapefile(shapefile_dir: str, tmpdir: str) -> Optional[str]:
    """Download shapefile from S3."""
    bucket = os.environ.get('DATA_BUCKET', 'chatmrpt-data-prod')

    # List files in shapefile directory
    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=shapefile_dir)

    if 'Contents' not in response:
        return None

    # Download all shapefile components
    shp_path = None
    for obj in response['Contents']:
        key = obj['Key']
        filename = os.path.basename(key)
        local_path = os.path.join(tmpdir, filename)

        s3_client.download_file(bucket, key, local_path)

        if filename.endswith('.shp'):
            shp_path = local_path

    return shp_path


def _find_merge_column(df: pd.DataFrame, gdf: gpd.GeoDataFrame) -> Optional[Dict[str, str]]:
    """Find matching columns between dataframe and geodataframe."""
    # Common ward/admin columns
    candidates = ['ward', 'Ward', 'ward_name', 'Ward_Name', 'NAME', 'name', 'ADM3_EN']

    for df_col in df.columns:
        if df_col in candidates:
            for gdf_col in gdf.columns:
                if gdf_col in candidates:
                    # Check if values match
                    df_vals = set(df[df_col].dropna().str.upper())
                    gdf_vals = set(gdf[gdf_col].dropna().str.upper())
                    if len(df_vals & gdf_vals) > 0:
                        return {'data': df_col, 'shapefile': gdf_col}

    return None


def _find_ward_column(df: pd.DataFrame) -> Optional[str]:
    """Find ward/admin column in dataframe."""
    candidates = ['ward', 'Ward', 'ward_name', 'Ward_Name', 'lga', 'LGA', 'NAME']
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _success_response(data: Any) -> Dict[str, Any]:
    """Create successful API response."""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(data)
    }


def _error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Create error API response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'error': message})
    }