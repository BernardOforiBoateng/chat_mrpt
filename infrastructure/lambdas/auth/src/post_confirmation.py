"""
Post-confirmation Lambda trigger for Cognito User Pool.
Creates user profile in DynamoDB and assigns default permissions.
"""
import json
import boto3
from datetime import datetime
from typing import Dict, Any
import uuid


dynamodb = boto3.resource('dynamodb')
cognito = boto3.client('cognito-idp')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Post-confirmation handler to set up new user.

    Args:
        event: Cognito trigger event
        context: Lambda context

    Returns:
        Event (unmodified)
    """
    print(f"Post-confirmation trigger for user: {event.get('userName')}")

    try:
        # Extract user information
        user_pool_id = event['userPoolId']
        username = event['userName']
        user_attributes = event['request']['userAttributes']

        # Create user profile in DynamoDB
        _create_user_profile(username, user_attributes)

        # Assign user to appropriate group based on role
        role = user_attributes.get('custom:role', 'viewer')
        _assign_user_to_group(user_pool_id, username, role)

        # Send welcome notification (optional)
        _send_welcome_notification(user_attributes.get('email'))

        # Log successful user setup
        print(f"Successfully set up user {username} with role {role}")

    except Exception as e:
        print(f"Error in post-confirmation: {str(e)}")
        # Don't raise exception - allow user to be confirmed even if setup fails
        # We can handle incomplete setup through a background job

    return event


def _create_user_profile(username: str, attributes: Dict[str, Any]) -> None:
    """Create user profile in DynamoDB."""
    import os
    table_name = os.environ.get('USERS_TABLE', 'chatmrpt-users-prod')
    table = dynamodb.Table(table_name)

    # Generate user ID (could also use Cognito sub)
    user_id = attributes.get('sub', str(uuid.uuid4()))

    # Prepare user profile
    profile = {
        'user_id': user_id,
        'username': username,
        'email': attributes.get('email', '').lower(),
        'organization': attributes.get('custom:organization', ''),
        'role': attributes.get('custom:role', 'viewer'),
        'region': attributes.get('custom:region', ''),
        'created_at': int(datetime.now().timestamp()),
        'last_login': int(datetime.now().timestamp()),
        'status': 'active',
        'preferences': {
            'theme': 'light',
            'notifications': True,
            'language': 'en'
        },
        'usage_stats': {
            'analyses_count': 0,
            'last_analysis': None,
            'total_data_processed_mb': 0
        }
    }

    # Store in DynamoDB
    table.put_item(Item=profile)
    print(f"Created user profile for {username}")


def _assign_user_to_group(user_pool_id: str, username: str, role: str) -> None:
    """Assign user to Cognito group based on role."""
    # Map roles to group names
    role_to_group = {
        'admin': 'Administrators',
        'researcher': 'Researchers',
        'field_officer': 'FieldOfficers',
        'viewer': 'Researchers'  # Default viewers to Researchers group
    }

    group_name = role_to_group.get(role, 'Researchers')

    try:
        cognito.admin_add_user_to_group(
            UserPoolId=user_pool_id,
            Username=username,
            GroupName=group_name
        )
        print(f"Added {username} to group {group_name}")
    except cognito.exceptions.ResourceNotFoundException:
        print(f"Group {group_name} not found - skipping group assignment")
    except Exception as e:
        print(f"Error adding user to group: {str(e)}")


def _send_welcome_notification(email: str) -> None:
    """Send welcome email to new user (optional)."""
    # This would integrate with SES or another email service
    # For now, just log the action
    print(f"Welcome notification would be sent to {email}")