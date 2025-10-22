#!/usr/bin/env python3
"""
Check what columns the agent sees
"""

import requests
import time

STAGING_URL = "http://3.21.167.170:8080"

# Upload data
session_id = f"colcheck_{int(time.time())}"
print(f"Session: {session_id}")

print("\n1. Uploading data...")
with open('www/adamawa_tpr_cleaned.csv', 'rb') as f:
    files = {'file': ('adamawa_tpr_cleaned.csv', f)}
    data = {'session_id': session_id}
    
    response = requests.post(
        f"{STAGING_URL}/api/data-analysis/upload",
        files=files,
        data=data,
        timeout=30
    )
    
    print(f"Upload status: {response.status_code}")

time.sleep(3)

# Ask about columns
print("\n2. Checking column names...")
response = requests.post(
    f"{STAGING_URL}/api/v1/data-analysis/chat",
    json={
        "message": "List all column names exactly as they appear",
        "session_id": session_id
    },
    timeout=30
)

if response.status_code == 200:
    result = response.json()
    message = result.get("message", "")
    
    print("\n📊 Column names from agent:")
    print("-" * 60)
    print(message[:2000])
    print("-" * 60)
    
    # Check for sanitization
    if '≥' in message:
        print("\n⚠️ Special character ≥ still present!")
    elif '<' in message and '5' in message:
        print("\n⚠️ Special character < might still be present!")
    else:
        print("\n✅ Columns appear to be sanitized")

# Now test a simple aggregation
print("\n3. Testing simple aggregation...")
response = requests.post(
    f"{STAGING_URL}/api/v1/data-analysis/chat",
    json={
        "message": "How many unique health facilities are in the data?",
        "session_id": session_id
    },
    timeout=30
)

if response.status_code == 200:
    result = response.json()
    message = result.get("message", "")
    print("\nUnique facilities response:")
    print(message[:500])