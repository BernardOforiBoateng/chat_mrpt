"""
Pre-authentication Lambda trigger for Cognito User Pool.
Validates login attempts and enforces security policies.
"""
import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, Any


dynamodb = boto3.resource('dynamodb')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Pre-authentication validation and logging.

    Args:
        event: Cognito trigger event
        context: Lambda context

    Returns:
        Event (can deny authentication by raising exception)
    """
    print(f"Pre-authentication trigger for user: {event.get('userName')}")

    username = event['userName']
    user_pool_id = event['userPoolId']

    try:
        # Check if user is blocked or suspended
        if _is_user_blocked(username):
            raise Exception("Account has been suspended. Please contact support.")

        # Check for rate limiting (prevent brute force)
        if _check_rate_limit_exceeded(username):
            raise Exception("Too many login attempts. Please try again later.")

        # Log authentication attempt
        _log_authentication_attempt(username, event)

        # Update last login time
        _update_last_login(username)

        print(f"Authentication approved for {username}")

    except Exception as e:
        # Log failed authentication
        _log_failed_authentication(username, str(e))
        raise

    return event


def _is_user_blocked(username: str) -> bool:
    """Check if user account is blocked or suspended."""
    import os
    table_name = os.environ.get('USERS_TABLE', 'chatmrpt-users-prod')
    table = dynamodb.Table(table_name)

    try:
        # Query by email (username attribute)
        response = table.query(
            IndexName='email-index',
            KeyConditionExpression='email = :email',
            ExpressionAttributeValues={':email': username.lower()}
        )

        if response['Items']:
            user = response['Items'][0]
            return user.get('status') in ['blocked', 'suspended']

    except Exception as e:
        print(f"Error checking user status: {str(e)}")

    return False


def _check_rate_limit_exceeded(username: str) -> bool:
    """Check if user has exceeded login rate limit."""
    import os
    table_name = os.environ.get('AUDIT_TABLE', 'chatmrpt-audit-prod')
    table = dynamodb.Table(table_name)

    # Check login attempts in last 5 minutes
    five_minutes_ago = int((datetime.now() - timedelta(minutes=5)).timestamp())

    try:
        response = table.query(
            KeyConditionExpression='user_id = :user_id AND #ts > :timestamp',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={
                ':user_id': username,
                ':timestamp': five_minutes_ago
            },
            FilterExpression='action_type = :action',
            ExpressionAttributeValues={':action': 'login_attempt'}
        )

        # Allow max 5 attempts per 5 minutes
        return len(response.get('Items', [])) >= 5

    except Exception as e:
        print(f"Error checking rate limit: {str(e)}")

    return False


def _log_authentication_attempt(username: str, event: Dict[str, Any]) -> None:
    """Log authentication attempt to audit table."""
    import os
    table_name = os.environ.get('AUDIT_TABLE', 'chatmrpt-audit-prod')
    table = dynamodb.Table(table_name)

    audit_entry = {
        'user_id': username,
        'timestamp': int(datetime.now().timestamp()),
        'action_type': 'login_attempt',
        'details': {
            'ip_address': event.get('request', {}).get('userContextData', {}).get('sourceIp'),
            'device_key': event.get('request', {}).get('deviceKey'),
            'user_agent': event.get('request', {}).get('userContextData', {}).get('userAgent'),
            'event_type': event.get('triggerSource')
        }
    }

    try:
        table.put_item(Item=audit_entry)
    except Exception as e:
        print(f"Error logging authentication attempt: {str(e)}")


def _log_failed_authentication(username: str, reason: str) -> None:
    """Log failed authentication attempt."""
    import os
    table_name = os.environ.get('AUDIT_TABLE', 'chatmrpt-audit-prod')
    table = dynamodb.Table(table_name)

    audit_entry = {
        'user_id': username,
        'timestamp': int(datetime.now().timestamp()),
        'action_type': 'login_failed',
        'details': {
            'reason': reason
        }
    }

    try:
        table.put_item(Item=audit_entry)
    except Exception as e:
        print(f"Error logging failed authentication: {str(e)}")


def _update_last_login(username: str) -> None:
    """Update user's last login timestamp."""
    import os
    table_name = os.environ.get('USERS_TABLE', 'chatmrpt-users-prod')
    table = dynamodb.Table(table_name)

    try:
        # Query by email first to get user_id
        response = table.query(
            IndexName='email-index',
            KeyConditionExpression='email = :email',
            ExpressionAttributeValues={':email': username.lower()}
        )

        if response['Items']:
            user_id = response['Items'][0]['user_id']
            table.update_item(
                Key={'user_id': user_id},
                UpdateExpression='SET last_login = :timestamp',
                ExpressionAttributeValues={
                    ':timestamp': int(datetime.now().timestamp())
                }
            )
    except Exception as e:
        print(f"Error updating last login: {str(e)}")