#!/usr/bin/env python3
"""
Implement sticky sessions for Data Analysis V3
This ensures upload and chat go to the same instance
"""

import hashlib
from flask import request, make_response
import logging

logger = logging.getLogger(__name__)

def get_or_create_instance_affinity():
    """
    Get or create instance affinity cookie.
    This ensures the same user goes to the same instance.
    """
    # Check for existing affinity cookie
    instance_id = request.cookies.get('AWSALBAPP')
    
    if not instance_id:
        # Generate instance affinity based on session ID
        session_id = request.form.get('session_id') or request.json.get('session_id', '')
        if session_id:
            # Hash session ID to determine instance affinity
            hash_val = hashlib.md5(session_id.encode()).hexdigest()
            # This will consistently route same session to same instance
            instance_id = hash_val
            logger.info(f"🔒 Created instance affinity for session {session_id}")
    
    return instance_id

def add_sticky_session_cookie(response, session_id=None):
    """
    Add sticky session cookie to response.
    This helps ALB route to the same instance.
    """
    if session_id:
        # Set a cookie that ALB can use for stickiness
        response.set_cookie(
            'ChatMRPT-Session',
            value=session_id,
            max_age=3600,  # 1 hour
            httponly=True,
            samesite='Lax',
            path='/'
        )
        
        # Also set instance hint
        import socket
        hostname = socket.gethostname()
        response.set_cookie(
            'ChatMRPT-Instance',
            value=hostname,
            max_age=3600,
            httponly=True,
            samesite='Lax',
            path='/'
        )
        
        logger.info(f"🔒 Set sticky session cookies for {session_id} on {hostname}")
    
    return response