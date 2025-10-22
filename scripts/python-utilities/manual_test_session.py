#!/usr/bin/env python3
"""
Manual test to check session synchronization
"""

import requests
import json

BASE_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"

# The session from your console logs
session_id = "2fa2a8c8-911c-4825-8e71-e3f876851987"

# Create a session and try to access data
session = requests.Session()

# Make a request to check data
response = session.post(
    f"{BASE_URL}/send_message_streaming",
    json={"message": "Show me what data columns I have"},
    cookies={"session_id": session_id}  # Try to use existing session
)

print(f"Status: {response.status_code}")

if response.status_code == 200:
    # Collect first part of response
    content = ""
    for i, line in enumerate(response.iter_lines()):
        if i > 20:  # Just get first 20 lines
            break
        if line:
            try:
                chunk = json.loads(line.decode('utf-8').replace('data: ', ''))
                if 'content' in chunk:
                    content += chunk['content']
            except:
                pass
    
    print("\nResponse preview:")
    print(content[:500])
    
    # Check indicators
    if "no data" in content.lower() or "upload" in content.lower():
        print("\n❌ Session not recognizing data!")
    elif "wardname" in content.lower() or "tpr" in content.lower() or "columns" in content.lower():
        print("\n✅ Session has access to data!")
    else:
        print("\n⚠️ Unclear response")
else:
    print(f"Error: {response.status_code}")