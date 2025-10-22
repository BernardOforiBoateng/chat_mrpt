"""
Data processing Lambda function.
Handles CSV/Excel uploads and shapefile processing.
"""
import json
import boto3
import os
import pandas as pd
import geopandas as gpd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import uuid
import zipfile
import tempfile


s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Process uploaded data files.

    Args:
        event: S3 event or API Gateway event
        context: Lambda context

    Returns:
        Processing result
    """
    print(f"Data processing request: {json.dumps(event)}")

    try:
        # Determine event source
        if 'Records' in event:
            # S3 trigger
            return handle_s3_trigger(event, context)
        else:
            # API Gateway trigger
            return handle_api_trigger(event, context)

    except Exception as e:
        print(f"Error in data processing: {str(e)}")
        return _error_response(500, str(e))


def handle_s3_trigger(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle S3 upload trigger."""
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        print(f"Processing S3 object: {bucket}/{key}")

        # Extract session_id from key (uploads/session_id/filename)
        parts = key.split('/')
        if len(parts) < 3 or parts[0] != 'uploads':
            print(f"Skipping non-upload file: {key}")
            continue

        session_id = parts[1]
        filename = parts[2]

        # Process based on file type
        if filename.endswith('.csv'):
            process_csv_file(bucket, key, session_id)
        elif filename.endswith(('.xlsx', '.xls')):
            process_excel_file(bucket, key, session_id)
        elif filename.endswith('.zip'):
            process_shapefile_zip(bucket, key, session_id)
        else:
            print(f"Unsupported file type: {filename}")

    return {'statusCode': 200, 'body': 'Processing complete'}


def handle_api_trigger(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle direct API call for data processing."""
    body = json.loads(event.get('body', '{}'))
    action = body.get('action')
    session_id = body.get('session_id')

    if not action or not session_id:
        return _error_response(400, "Action and session_id required")

    if action == 'validate_data':
        return validate_uploaded_data(session_id)
    elif action == 'get_columns':
        return get_data_columns(session_id)
    elif action == 'get_summary':
        return get_data_summary(session_id)
    else:
        return _error_response(400, f"Unknown action: {action}")


def process_csv_file(bucket: str, key: str, session_id: str) -> None:
    """
    Process uploaded CSV file.
    """
    print(f"Processing CSV: {key}")

    # Download file to temp location
    with tempfile.NamedTemporaryFile(suffix='.csv') as tmp:
        s3_client.download_file(bucket, key, tmp.name)

        # Read and validate CSV
        df = pd.read_csv(tmp.name)
        print(f"CSV shape: {df.shape}")

        # Validate required columns
        validation = validate_dataframe(df)
        if not validation['valid']:
            _store_validation_error(session_id, validation['errors'])
            return

        # Clean and standardize data
        df = clean_dataframe(df)

        # Save processed version
        processed_key = key.replace('raw_', 'processed_')
        df.to_csv(tmp.name, index=False)
        s3_client.upload_file(tmp.name, bucket, processed_key)

        # Store metadata
        _store_data_metadata(session_id, {
            'file_type': 'csv',
            'original_key': key,
            'processed_key': processed_key,
            'rows': len(df),
            'columns': list(df.columns),
            'dtypes': df.dtypes.astype(str).to_dict()
        })


def process_excel_file(bucket: str, key: str, session_id: str) -> None:
    """
    Process uploaded Excel file.
    """
    print(f"Processing Excel: {key}")

    with tempfile.NamedTemporaryFile(suffix='.xlsx') as tmp:
        s3_client.download_file(bucket, key, tmp.name)

        # Read Excel file (first sheet by default)
        df = pd.read_excel(tmp.name, sheet_name=0)
        print(f"Excel shape: {df.shape}")

        # Validate and clean
        validation = validate_dataframe(df)
        if not validation['valid']:
            _store_validation_error(session_id, validation['errors'])
            return

        df = clean_dataframe(df)

        # Save as CSV for easier processing
        csv_key = key.replace('.xlsx', '.csv').replace('.xls', '.csv').replace('raw_', 'processed_')
        with tempfile.NamedTemporaryFile(suffix='.csv', mode='w') as csv_tmp:
            df.to_csv(csv_tmp.name, index=False)
            s3_client.upload_file(csv_tmp.name, bucket, csv_key)

        # Store metadata
        _store_data_metadata(session_id, {
            'file_type': 'excel',
            'original_key': key,
            'processed_key': csv_key,
            'rows': len(df),
            'columns': list(df.columns),
            'dtypes': df.dtypes.astype(str).to_dict()
        })


def process_shapefile_zip(bucket: str, key: str, session_id: str) -> None:
    """
    Process uploaded shapefile ZIP.
    """
    print(f"Processing shapefile ZIP: {key}")

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, 'shapefile.zip')
        s3_client.download_file(bucket, key, zip_path)

        # Extract ZIP
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)

        # Find .shp file
        shp_files = [f for f in os.listdir(tmpdir) if f.endswith('.shp')]
        if not shp_files:
            _store_validation_error(session_id, ["No .shp file found in ZIP"])
            return

        shp_path = os.path.join(tmpdir, shp_files[0])

        # Read shapefile
        gdf = gpd.read_file(shp_path)
        print(f"Shapefile shape: {gdf.shape}")
        print(f"CRS: {gdf.crs}")

        # Validate shapefile
        validation = validate_shapefile(gdf)
        if not validation['valid']:
            _store_validation_error(session_id, validation['errors'])
            return

        # Reproject to WGS84 if needed
        if gdf.crs and gdf.crs != 'EPSG:4326':
            gdf = gdf.to_crs('EPSG:4326')

        # Upload all shapefile components
        shapefile_dir = f"uploads/{session_id}/shapefile/"
        for file in os.listdir(tmpdir):
            if not file.endswith('.zip'):
                file_path = os.path.join(tmpdir, file)
                s3_key = f"{shapefile_dir}{file}"
                s3_client.upload_file(file_path, bucket, s3_key)

        # Store metadata
        _store_data_metadata(session_id, {
            'file_type': 'shapefile',
            'original_key': key,
            'shapefile_dir': shapefile_dir,
            'features': len(gdf),
            'geometry_type': gdf.geometry.type.unique().tolist(),
            'columns': list(gdf.columns),
            'crs': 'EPSG:4326',
            'bounds': gdf.total_bounds.tolist()
        })


def validate_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate uploaded dataframe."""
    errors = []

    # Check if empty
    if df.empty:
        errors.append("Dataset is empty")

    # Check for required identifier column
    id_columns = ['ward', 'Ward', 'ward_name', 'Ward_Name', 'lga', 'LGA']
    if not any(col in df.columns for col in id_columns):
        errors.append(f"No identifier column found. Expected one of: {id_columns}")

    # Check for numeric columns
    numeric_cols = df.select_dtypes(include=['number']).columns
    if len(numeric_cols) < 2:
        errors.append("Dataset must contain at least 2 numeric columns for analysis")

    # Check for excessive missing data
    missing_pct = df.isnull().sum() / len(df)
    high_missing = missing_pct[missing_pct > 0.5]
    if len(high_missing) > 0:
        errors.append(f"Columns with >50% missing data: {high_missing.index.tolist()}")

    return {'valid': len(errors) == 0, 'errors': errors}


def validate_shapefile(gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
    """Validate shapefile."""
    errors = []

    # Check geometry validity
    invalid_geoms = ~gdf.geometry.is_valid
    if invalid_geoms.any():
        errors.append(f"{invalid_geoms.sum()} invalid geometries found")

    # Check for empty geometries
    empty_geoms = gdf.geometry.is_empty
    if empty_geoms.any():
        errors.append(f"{empty_geoms.sum()} empty geometries found")

    # Check CRS
    if gdf.crs is None:
        errors.append("No coordinate reference system defined")

    return {'valid': len(errors) == 0, 'errors': errors}


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize dataframe."""
    # Remove leading/trailing spaces from column names
    df.columns = df.columns.str.strip()

    # Standardize common column names
    rename_map = {
        'Ward': 'ward',
        'Ward_Name': 'ward_name',
        'LGA': 'lga',
        'State': 'state'
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Convert string columns to proper case
    for col in df.select_dtypes(include=['object']).columns:
        if col in ['ward', 'ward_name', 'lga', 'state']:
            df[col] = df[col].str.strip().str.title()

    # Handle missing values in numeric columns
    numeric_cols = df.select_dtypes(include=['number']).columns
    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())

    return df


def validate_uploaded_data(session_id: str) -> Dict[str, Any]:
    """Validate all uploaded data for a session."""
    metadata = _get_data_metadata(session_id)

    if not metadata:
        return _error_response(404, "No data found for session")

    validation_result = {
        'session_id': session_id,
        'valid': True,
        'csv_uploaded': False,
        'shapefile_uploaded': False,
        'errors': [],
        'warnings': []
    }

    # Check for CSV/Excel data
    if any(m.get('file_type') in ['csv', 'excel'] for m in metadata):
        validation_result['csv_uploaded'] = True
    else:
        validation_result['valid'] = False
        validation_result['errors'].append("No tabular data (CSV/Excel) uploaded")

    # Check for shapefile
    if any(m.get('file_type') == 'shapefile' for m in metadata):
        validation_result['shapefile_uploaded'] = True
    else:
        validation_result['warnings'].append("No shapefile uploaded - spatial analysis limited")

    return _success_response(validation_result)


def get_data_columns(session_id: str) -> Dict[str, Any]:
    """Get column information for uploaded data."""
    metadata = _get_data_metadata(session_id)

    if not metadata:
        return _error_response(404, "No data found for session")

    # Find CSV/Excel metadata
    data_meta = next((m for m in metadata if m.get('file_type') in ['csv', 'excel']), None)

    if not data_meta:
        return _error_response(404, "No tabular data found")

    columns = data_meta.get('columns', [])
    dtypes = data_meta.get('dtypes', {})

    # Categorize columns
    result = {
        'all_columns': columns,
        'numeric_columns': [col for col, dtype in dtypes.items() if 'float' in dtype or 'int' in dtype],
        'text_columns': [col for col, dtype in dtypes.items() if 'object' in dtype],
        'identifier_columns': [col for col in columns if col in ['ward', 'ward_name', 'lga', 'state']],
        'row_count': data_meta.get('rows', 0)
    }

    return _success_response(result)


def get_data_summary(session_id: str) -> Dict[str, Any]:
    """Get summary statistics for uploaded data."""
    # This would download and analyze the processed data
    # For Lambda, we might want to limit this or make it async
    return _success_response({
        'message': 'Summary generation queued',
        'session_id': session_id
    })


def _store_data_metadata(session_id: str, metadata: Dict[str, Any]) -> None:
    """Store data metadata in DynamoDB."""
    table = dynamodb.Table(os.environ.get('SESSIONS_TABLE', 'chatmrpt-sessions-prod'))

    table.update_item(
        Key={'session_token': session_id},
        UpdateExpression='SET data_metadata = list_append(if_not_exists(data_metadata, :empty_list), :new_meta)',
        ExpressionAttributeValues={
            ':empty_list': [],
            ':new_meta': [metadata]
        }
    )


def _get_data_metadata(session_id: str) -> List[Dict[str, Any]]:
    """Get data metadata from DynamoDB."""
    table = dynamodb.Table(os.environ.get('SESSIONS_TABLE', 'chatmrpt-sessions-prod'))

    response = table.get_item(Key={'session_token': session_id})
    if 'Item' in response:
        return response['Item'].get('data_metadata', [])
    return []


def _store_validation_error(session_id: str, errors: List[str]) -> None:
    """Store validation errors."""
    table = dynamodb.Table(os.environ.get('SESSIONS_TABLE', 'chatmrpt-sessions-prod'))

    table.update_item(
        Key={'session_token': session_id},
        UpdateExpression='SET validation_errors = :errors, validation_status = :status',
        ExpressionAttributeValues={
            ':errors': errors,
            ':status': 'failed'
        }
    )


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