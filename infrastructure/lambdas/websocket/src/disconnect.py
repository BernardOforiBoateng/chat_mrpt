"""
WebSocket disconnection handler Lambda.
Cleans up WebSocket connections when clients disconnect.
"""
import json
import boto3
import os
from datetime import datetime
from typing import Dict, Any

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle WebSocket disconnection.

    Args:
        event: API Gateway WebSocket event
        context: Lambda context

    Returns:
        API Gateway response
    """
    print(f"Disconnection request: {json.dumps(event)}")

    connection_id = event['requestContext']['connectionId']

    try:
        # Remove connection from DynamoDB
        remove_connection(connection_id)

        print(f"WebSocket disconnected: {connection_id}")

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Disconnected successfully'})
        }

    except Exception as e:
        print(f"Error handling disconnection: {str(e)}")
        # Still return success to avoid retry
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Disconnection processed'})
        }


def remove_connection(connection_id: str) -> None:
    """
    Remove WebSocket connection from DynamoDB.

    Args:
        connection_id: WebSocket connection ID
    """
    # Remove from connections table
    connections_table = os.environ.get('CONNECTIONS_TABLE', 'chatmrpt-websocket-connections')
    table = dynamodb.Table(connections_table)

    # Get connection details first
    response = table.get_item(Key={'connection_id': connection_id})

    if 'Item' in response:
        item = response['Item']
        user_id = item.get('user_id')

        # Delete connection
        table.delete_item(Key={'connection_id': connection_id})

        # Remove from user connections table
        if user_id:
            user_connections_table = os.environ.get('USER_CONNECTIONS_TABLE', 'chatmrpt-user-connections')
            user_table = dynamodb.Table(user_connections_table)

            user_table.delete_item(
                Key={
                    'user_id': user_id,
                    'connection_id': connection_id
                }
            )

        # Log disconnection for audit
        log_disconnection(connection_id, user_id)


def log_disconnection(connection_id: str, user_id: str) -> None:
    """
    Log disconnection event for audit.

    Args:
        connection_id: WebSocket connection ID
        user_id: User ID
    """
    try:
        audit_table = os.environ.get('AUDIT_TABLE', 'chatmrpt-audit-prod')
        table = dynamodb.Table(audit_table)

        table.put_item(
            Item={
                'user_id': user_id or 'unknown',
                'timestamp': int(datetime.now().timestamp()),
                'action_type': 'websocket_disconnect',
                'details': {
                    'connection_id': connection_id,
                    'disconnected_at': datetime.now().isoformat()
                }
            }
        )
    except Exception as e:
        print(f"Error logging disconnection: {str(e)}")