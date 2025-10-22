"""
WebSocket connection handler Lambda.
Handles new WebSocket connections and authentication.
"""
import json
import boto3
import os
import jwt
from datetime import datetime
from typing import Dict, Any

dynamodb = boto3.resource('dynamodb')
cognito = boto3.client('cognito-idp')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle WebSocket connection requests.

    Args:
        event: API Gateway WebSocket event
        context: Lambda context

    Returns:
        API Gateway response
    """
    print(f"Connection request: {json.dumps(event)}")

    connection_id = event['requestContext']['connectionId']

    try:
        # Extract token from query string
        query_params = event.get('queryStringParameters', {})
        token = query_params.get('token')

        if not token:
            return {
                'statusCode': 401,
                'body': json.dumps({'message': 'Authentication token required'})
            }

        # Validate JWT token
        user_info = validate_token(token)
        if not user_info:
            return {
                'statusCode': 401,
                'body': json.dumps({'message': 'Invalid or expired token'})
            }

        # Store connection in DynamoDB
        store_connection(connection_id, user_info)

        print(f"WebSocket connected: {connection_id} for user {user_info['user_id']}")

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Connected successfully'})
        }

    except Exception as e:
        print(f"Error handling connection: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error'})
        }


def validate_token(token: str) -> Dict[str, Any]:
    """
    Validate JWT token with Cognito.

    Args:
        token: JWT token

    Returns:
        User information if valid, None otherwise
    """
    try:
        # Get Cognito configuration
        user_pool_id = os.environ.get('USER_POOL_ID')
        region = os.environ.get('AWS_REGION', 'us-east-2')

        # Get JWT keys from Cognito
        jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"

        # For production, implement proper JWT validation with public keys
        # For now, decode without verification (NOT for production!)
        decoded = jwt.decode(token, options={"verify_signature": False})

        return {
            'user_id': decoded.get('sub'),
            'email': decoded.get('email'),
            'username': decoded.get('cognito:username'),
            'groups': decoded.get('cognito:groups', [])
        }

    except jwt.ExpiredSignatureError:
        print("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"Invalid token: {str(e)}")
        return None
    except Exception as e:
        print(f"Error validating token: {str(e)}")
        return None


def store_connection(connection_id: str, user_info: Dict[str, Any]) -> None:
    """
    Store WebSocket connection in DynamoDB.

    Args:
        connection_id: WebSocket connection ID
        user_info: User information
    """
    table_name = os.environ.get('CONNECTIONS_TABLE', 'chatmrpt-websocket-connections')
    table = dynamodb.Table(table_name)

    # Store connection with TTL (8 hours)
    ttl = int(datetime.now().timestamp()) + (8 * 60 * 60)

    table.put_item(
        Item={
            'connection_id': connection_id,
            'user_id': user_info['user_id'],
            'email': user_info['email'],
            'connected_at': int(datetime.now().timestamp()),
            'ttl': ttl,
            'status': 'connected'
        }
    )

    # Also store reverse mapping for user -> connections
    user_connections_table = os.environ.get('USER_CONNECTIONS_TABLE', 'chatmrpt-user-connections')
    user_table = dynamodb.Table(user_connections_table)

    user_table.put_item(
        Item={
            'user_id': user_info['user_id'],
            'connection_id': connection_id,
            'connected_at': int(datetime.now().timestamp()),
            'ttl': ttl
        }
    )