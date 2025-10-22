"""
Pre-signup Lambda trigger for Cognito User Pool.
Validates user registration and enforces business rules.
"""
import json
import re
from typing import Dict, Any


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Pre-signup validation for new user registration.

    Args:
        event: Cognito trigger event
        context: Lambda context

    Returns:
        Modified event or raises exception to deny signup
    """
    print(f"Pre-signup trigger for user: {event.get('userName')}")

    # Extract user attributes
    user_attributes = event['request'].get('userAttributes', {})
    email = user_attributes.get('email', '').lower()
    organization = user_attributes.get('custom:organization', '')
    role = user_attributes.get('custom:role', '')

    # Validate email format and domain
    if not _validate_email(email):
        raise Exception("Invalid email format")

    # Check if email domain is allowed (optional - customize as needed)
    allowed_domains = _get_allowed_domains()
    if allowed_domains and not _check_domain_allowed(email, allowed_domains):
        raise Exception(f"Email domain not authorized for registration")

    # Validate custom attributes
    if organization and len(organization) > 100:
        raise Exception("Organization name too long (max 100 characters)")

    if role and role not in ['admin', 'researcher', 'field_officer', 'viewer']:
        raise Exception(f"Invalid role: {role}")

    # Auto-confirm email for specific domains (optional)
    trusted_domains = ['who.int', 'unicef.org', 'gov.ng']
    if any(email.endswith(f'@{domain}') for domain in trusted_domains):
        event['response']['autoConfirmUser'] = True
        event['response']['autoVerifyEmail'] = True

    # Log registration attempt
    print(f"Registration approved for {email} from {organization}")

    return event


def _validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def _get_allowed_domains() -> list:
    """
    Get list of allowed email domains from environment or SSM.
    Returns empty list if no restrictions.
    """
    import os
    domains = os.environ.get('ALLOWED_DOMAINS', '')
    return [d.strip() for d in domains.split(',') if d.strip()]


def _check_domain_allowed(email: str, allowed_domains: list) -> bool:
    """Check if email domain is in allowed list."""
    domain = email.split('@')[1].lower()
    return domain in allowed_domains