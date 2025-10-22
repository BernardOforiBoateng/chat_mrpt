#!/usr/bin/env python3
"""
Check what the agent is actually returning
"""

import requests
import time

STAGING_URL = "http://3.21.167.170:8080"

session_id = f"check_{int(time.time())}"

# Upload
print("Uploading data...")
with open('www/adamawa_tpr_cleaned.csv', 'rb') as f:
    files = {'file': ('test.csv', f)}
    data = {'session_id': session_id}
    
    response = requests.post(
        f"{STAGING_URL}/api/data-analysis/upload",
        files=files,
        data=data,
        timeout=30
    )
    print(f"Upload: {response.status_code}")

time.sleep(3)

# Ask for top 10
print("\nAsking for top 10...")
response = requests.post(
    f"{STAGING_URL}/api/v1/data-analysis/chat",
    json={
        "message": "Show me the top 10 health facilities by total testing volume. List all 10 with names and counts.",
        "session_id": session_id
    },
    timeout=60
)

if response.status_code == 200:
    result = response.json()
    message = result.get("message", "")
    
    print("\n" + "="*60)
    print("FULL RESPONSE:")
    print("="*60)
    print(message)
    print("="*60)
    
    # Check what's in the response
    import re
    
    # Look for numbered items
    numbered = re.findall(r'^\s*(\d+)\.\s+(.+)$', message, re.MULTILINE)
    print(f"\nFound {len(numbered)} numbered items:")
    for num, content in numbered[:5]:
        print(f"  {num}. {content[:50]}...")
else:
    print(f"Error: {response.status_code}")