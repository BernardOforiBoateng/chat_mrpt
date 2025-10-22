"""
Main analysis Lambda function.
Orchestrates malaria risk analysis workflows.
"""
import json
import boto3
import os
from typing import Dict, Any, List
from datetime import datetime
import uuid


s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
stepfunctions = boto3.client('stepfunctions')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main analysis handler.
    Routes requests to appropriate analysis type.

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API response
    """
    print(f"Analysis request received: {json.dumps(event)}")

    try:
        # Parse request
        body = json.loads(event.get('body', '{}'))
        analysis_type = body.get('analysis_type')
        user_id = event['requestContext']['authorizer']['claims']['sub']
        session_id = body.get('session_id', str(uuid.uuid4()))

        # Validate request
        if not analysis_type:
            return _error_response(400, "Analysis type is required")

        # Route to appropriate handler
        if analysis_type == 'composite_scoring':
            result = handle_composite_scoring(body, user_id, session_id)
        elif analysis_type == 'pca':
            result = handle_pca_analysis(body, user_id, session_id)
        elif analysis_type == 'vulnerability_ranking':
            result = handle_vulnerability_ranking(body, user_id, session_id)
        elif analysis_type == 'settlement_analysis':
            result = handle_settlement_analysis(body, user_id, session_id)
        else:
            return _error_response(400, f"Unknown analysis type: {analysis_type}")

        return _success_response(result)

    except Exception as e:
        print(f"Error in analysis handler: {str(e)}")
        return _error_response(500, str(e))


def handle_composite_scoring(request: Dict[str, Any], user_id: str, session_id: str) -> Dict[str, Any]:
    """
    Handle composite scoring analysis.
    """
    print(f"Processing composite scoring for session {session_id}")

    # Create analysis record
    analysis_id = _create_analysis_record(user_id, session_id, 'composite_scoring', request)

    # Get data files from S3
    data_path = f"uploads/{session_id}/raw_data.csv"
    shapefile_path = f"uploads/{session_id}/shapefile/"

    # Start Step Functions workflow for async processing
    workflow_input = {
        'analysis_id': analysis_id,
        'user_id': user_id,
        'session_id': session_id,
        'analysis_type': 'composite_scoring',
        'data_path': data_path,
        'shapefile_path': shapefile_path,
        'parameters': request.get('parameters', {})
    }

    execution_arn = _start_workflow('composite-scoring', workflow_input)

    return {
        'analysis_id': analysis_id,
        'session_id': session_id,
        'status': 'processing',
        'execution_arn': execution_arn,
        'message': 'Composite scoring analysis started'
    }


def handle_pca_analysis(request: Dict[str, Any], user_id: str, session_id: str) -> Dict[str, Any]:
    """
    Handle PCA analysis.
    """
    print(f"Processing PCA analysis for session {session_id}")

    # Create analysis record
    analysis_id = _create_analysis_record(user_id, session_id, 'pca', request)

    # Get data files
    data_path = f"uploads/{session_id}/raw_data.csv"

    # Start workflow
    workflow_input = {
        'analysis_id': analysis_id,
        'user_id': user_id,
        'session_id': session_id,
        'analysis_type': 'pca',
        'data_path': data_path,
        'parameters': request.get('parameters', {
            'n_components': 3,
            'standardize': True
        })
    }

    execution_arn = _start_workflow('pca-analysis', workflow_input)

    return {
        'analysis_id': analysis_id,
        'session_id': session_id,
        'status': 'processing',
        'execution_arn': execution_arn,
        'message': 'PCA analysis started'
    }


def handle_vulnerability_ranking(request: Dict[str, Any], user_id: str, session_id: str) -> Dict[str, Any]:
    """
    Handle vulnerability ranking analysis.
    """
    print(f"Processing vulnerability ranking for session {session_id}")

    # Create analysis record
    analysis_id = _create_analysis_record(user_id, session_id, 'vulnerability_ranking', request)

    # Get indicators from request
    indicators = request.get('indicators', [])
    if not indicators:
        raise ValueError("Indicators are required for vulnerability ranking")

    # Start workflow
    workflow_input = {
        'analysis_id': analysis_id,
        'user_id': user_id,
        'session_id': session_id,
        'analysis_type': 'vulnerability_ranking',
        'data_path': f"uploads/{session_id}/raw_data.csv",
        'indicators': indicators,
        'parameters': request.get('parameters', {})
    }

    execution_arn = _start_workflow('vulnerability-ranking', workflow_input)

    return {
        'analysis_id': analysis_id,
        'session_id': session_id,
        'status': 'processing',
        'execution_arn': execution_arn,
        'message': 'Vulnerability ranking started'
    }


def handle_settlement_analysis(request: Dict[str, Any], user_id: str, session_id: str) -> Dict[str, Any]:
    """
    Handle settlement footprint analysis.
    """
    print(f"Processing settlement analysis for session {session_id}")

    # Create analysis record
    analysis_id = _create_analysis_record(user_id, session_id, 'settlement_analysis', request)

    # Get region from request
    region = request.get('region')
    if not region:
        raise ValueError("Region is required for settlement analysis")

    # Start workflow
    workflow_input = {
        'analysis_id': analysis_id,
        'user_id': user_id,
        'session_id': session_id,
        'analysis_type': 'settlement_analysis',
        'region': region,
        'shapefile_path': f"uploads/{session_id}/shapefile/",
        'parameters': request.get('parameters', {})
    }

    execution_arn = _start_workflow('settlement-analysis', workflow_input)

    return {
        'analysis_id': analysis_id,
        'session_id': session_id,
        'status': 'processing',
        'execution_arn': execution_arn,
        'message': 'Settlement analysis started'
    }


def _create_analysis_record(user_id: str, session_id: str, analysis_type: str, request: Dict[str, Any]) -> str:
    """Create analysis record in DynamoDB."""
    table = dynamodb.Table(os.environ.get('ANALYSES_TABLE', 'chatmrpt-analyses-prod'))
    analysis_id = str(uuid.uuid4())

    record = {
        'user_id': user_id,
        'analysis_id': analysis_id,
        'session_id': session_id,
        'analysis_type': analysis_type,
        'status': 'pending',
        'created_at': int(datetime.now().timestamp()),
        'updated_at': int(datetime.now().timestamp()),
        'request': request,
        'ttl': int((datetime.now().timestamp())) + (30 * 24 * 60 * 60)  # 30 days
    }

    table.put_item(Item=record)
    print(f"Created analysis record {analysis_id}")
    return analysis_id


def _start_workflow(workflow_name: str, workflow_input: Dict[str, Any]) -> str:
    """Start Step Functions workflow."""
    state_machine_arn = os.environ.get(
        f'STATE_MACHINE_{workflow_name.upper().replace("-", "_")}_ARN',
        f"arn:aws:states:us-east-2:123456789012:stateMachine:{workflow_name}"
    )

    response = stepfunctions.start_execution(
        stateMachineArn=state_machine_arn,
        name=f"{workflow_name}-{workflow_input['analysis_id']}",
        input=json.dumps(workflow_input)
    )

    print(f"Started workflow {workflow_name}: {response['executionArn']}")
    return response['executionArn']


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