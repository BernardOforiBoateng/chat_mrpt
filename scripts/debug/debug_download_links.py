#!/usr/bin/env python3
"""
Add debug logging to TPR download links endpoint
"""
import re

# Read the file
with open('app/web/routes/tpr_routes.py', 'r') as f:
    content = f.read()

# Find the get_tpr_download_links function and add more logging
old_function = '''def get_tpr_download_links():
    """Get TPR download links for current session."""
    session_id = session.get('session_id')
    
    # Get download links from session
    download_links = session.get('tpr_download_links', [])
    
    logger.info(f"TPR download links request for session {session_id}: Found {len(download_links)} links in session")'''

new_function = '''def get_tpr_download_links():
    """Get TPR download links for current session."""
    session_id = session.get('session_id')
    
    # Debug: Log all session keys
    logger.info(f"Session keys available: {list(session.keys())}")
    
    # Get download links from session
    download_links = session.get('tpr_download_links', [])
    
    logger.info(f"TPR download links request for session {session_id}: Found {len(download_links)} links in session")
    logger.info(f"Download links content: {download_links}")'''

content = content.replace(old_function, new_function)

# Write the updated file
with open('app/web/routes/tpr_routes.py', 'w') as f:
    f.write(content)

print("Added debug logging to download links endpoint")