"""
WebSocket message handler Lambda.
Processes incoming WebSocket messages and broadcasts updates.
"""
import json
import boto3
import os
from datetime import datetime
from typing import Dict, Any, List

dynamodb = boto3.resource('dynamodb')
api_gateway = boto3.client('apigatewaymanagementapi')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle WebSocket messages.

    Args:
        event: API Gateway WebSocket event
        context: Lambda context

    Returns:
        API Gateway response
    """
    print(f"Message received: {json.dumps(event)}")

    connection_id = event['requestContext']['connectionId']
    domain = event['requestContext']['domainName']
    stage = event['requestContext']['stage']

    # Set API Gateway endpoint for sending messages
    api_gateway_endpoint = f"https://{domain}/{stage}"
    global api_gateway
    api_gateway = boto3.client('apigatewaymanagementapi', endpoint_url=api_gateway_endpoint)

    try:
        # Parse message body
        body = json.loads(event.get('body', '{}'))
        action = body.get('action')

        # Route based on action
        if action == 'ping':
            return handle_ping(connection_id)
        elif action == 'subscribe':
            return handle_subscribe(connection_id, body)
        elif action == 'unsubscribe':
            return handle_unsubscribe(connection_id, body)
        elif action == 'broadcast':
            return handle_broadcast(connection_id, body)
        elif action == 'analysis_status':
            return handle_analysis_status(connection_id, body)
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': f'Unknown action: {action}'})
            }

    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Invalid JSON in request body'})
        }
    except Exception as e:
        print(f"Error handling message: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error'})
        }


def handle_ping(connection_id: str) -> Dict[str, Any]:
    """
    Handle ping message.

    Args:
        connection_id: WebSocket connection ID

    Returns:
        API Gateway response
    """
    # Send pong response
    send_message(connection_id, {
        'action': 'pong',
        'timestamp': datetime.now().isoformat()
    })

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Pong sent'})
    }


def handle_subscribe(connection_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Subscribe connection to updates for a session/analysis.

    Args:
        connection_id: WebSocket connection ID
        body: Message body with subscription details

    Returns:
        API Gateway response
    """
    session_id = body.get('session_id')
    analysis_id = body.get('analysis_id')

    if not session_id:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'session_id required'})
        }

    # Store subscription
    subscriptions_table = os.environ.get('SUBSCRIPTIONS_TABLE', 'chatmrpt-websocket-subscriptions')
    table = dynamodb.Table(subscriptions_table)

    table.put_item(
        Item={
            'subscription_key': f"{session_id}#{analysis_id or 'all'}",
            'connection_id': connection_id,
            'subscribed_at': int(datetime.now().timestamp()),
            'ttl': int(datetime.now().timestamp()) + (8 * 60 * 60)
        }
    )

    # Send confirmation
    send_message(connection_id, {
        'action': 'subscribed',
        'session_id': session_id,
        'analysis_id': analysis_id
    })

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Subscribed successfully'})
    }


def handle_unsubscribe(connection_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Unsubscribe connection from updates.

    Args:
        connection_id: WebSocket connection ID
        body: Message body with subscription details

    Returns:
        API Gateway response
    """
    session_id = body.get('session_id')
    analysis_id = body.get('analysis_id')

    if not session_id:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'session_id required'})
        }

    # Remove subscription
    subscriptions_table = os.environ.get('SUBSCRIPTIONS_TABLE', 'chatmrpt-websocket-subscriptions')
    table = dynamodb.Table(subscriptions_table)

    table.delete_item(
        Key={
            'subscription_key': f"{session_id}#{analysis_id or 'all'}",
            'connection_id': connection_id
        }
    )

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Unsubscribed successfully'})
    }


def handle_broadcast(connection_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Broadcast message to subscribed connections.

    Args:
        connection_id: Sender's connection ID
        body: Message to broadcast

    Returns:
        API Gateway response
    """
    session_id = body.get('session_id')
    analysis_id = body.get('analysis_id')
    message = body.get('message', {})

    if not session_id:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'session_id required'})
        }

    # Get all subscribed connections
    connections = get_subscribed_connections(session_id, analysis_id)

    # Broadcast to all connections
    broadcast_count = 0
    for conn_id in connections:
        if conn_id != connection_id:  # Don't send back to sender
            try:
                send_message(conn_id, {
                    'action': 'update',
                    'session_id': session_id,
                    'analysis_id': analysis_id,
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                })
                broadcast_count += 1
            except Exception as e:
                print(f"Error broadcasting to {conn_id}: {str(e)}")
                # Remove stale connection
                remove_stale_connection(conn_id)

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Broadcast to {broadcast_count} connections'
        })
    }


def handle_analysis_status(connection_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send analysis status update.

    Args:
        connection_id: Connection ID
        body: Status update details

    Returns:
        API Gateway response
    """
    analysis_id = body.get('analysis_id')
    status = body.get('status')

    if not analysis_id or not status:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'analysis_id and status required'})
        }

    # Get analysis details from DynamoDB
    analyses_table = os.environ.get('ANALYSES_TABLE', 'chatmrpt-analyses-prod')
    table = dynamodb.Table(analyses_table)

    # Send status update
    send_message(connection_id, {
        'action': 'analysis_status',
        'analysis_id': analysis_id,
        'status': status,
        'timestamp': datetime.now().isoformat()
    })

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Status sent'})
    }


def get_subscribed_connections(session_id: str, analysis_id: str = None) -> List[str]:
    """
    Get all connections subscribed to a session/analysis.

    Args:
        session_id: Session ID
        analysis_id: Optional analysis ID

    Returns:
        List of connection IDs
    """
    subscriptions_table = os.environ.get('SUBSCRIPTIONS_TABLE', 'chatmrpt-websocket-subscriptions')
    table = dynamodb.Table(subscriptions_table)

    connections = []

    # Query for specific analysis subscriptions
    if analysis_id:
        response = table.query(
            KeyConditionExpression='subscription_key = :key',
            ExpressionAttributeValues={
                ':key': f"{session_id}#{analysis_id}"
            }
        )
        connections.extend([item['connection_id'] for item in response.get('Items', [])])

    # Query for session-wide subscriptions
    response = table.query(
        KeyConditionExpression='subscription_key = :key',
        ExpressionAttributeValues={
            ':key': f"{session_id}#all"
        }
    )
    connections.extend([item['connection_id'] for item in response.get('Items', [])])

    # Remove duplicates
    return list(set(connections))


def send_message(connection_id: str, message: Dict[str, Any]) -> None:
    """
    Send message to WebSocket connection.

    Args:
        connection_id: WebSocket connection ID
        message: Message to send
    """
    try:
        api_gateway.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(message)
        )
    except api_gateway.exceptions.GoneException:
        # Connection no longer exists
        print(f"Connection {connection_id} is gone")
        remove_stale_connection(connection_id)
        raise
    except Exception as e:
        print(f"Error sending message to {connection_id}: {str(e)}")
        raise


def remove_stale_connection(connection_id: str) -> None:
    """
    Remove stale connection from all tables.

    Args:
        connection_id: WebSocket connection ID
    """
    try:
        # Remove from connections table
        connections_table = os.environ.get('CONNECTIONS_TABLE', 'chatmrpt-websocket-connections')
        table = dynamodb.Table(connections_table)
        table.delete_item(Key={'connection_id': connection_id})

        # Note: Subscriptions will expire via TTL
    except Exception as e:
        print(f"Error removing stale connection: {str(e)}")