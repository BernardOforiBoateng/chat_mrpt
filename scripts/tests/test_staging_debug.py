#!/usr/bin/env python3
"""
Debug what's happening on staging
"""

import requests
import time

STAGING_URL = "http://3.21.167.170:8080"

# Upload data
session_id = f"debug_{int(time.time())}"
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
    if response.status_code == 200:
        print("✅ Upload successful")
    else:
        print(f"❌ Upload failed: {response.text}")

time.sleep(3)

print("\n2. Testing top facilities query...")
response = requests.post(
    f"{STAGING_URL}/api/v1/data-analysis/chat",
    json={
        "message": "Show me the top 10 facilities by total testing volume",
        "session_id": session_id
    },
    timeout=60
)

print(f"Query status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    message = result.get("message", "")
    
    print("\n📊 Response:")
    print("-" * 60)
    print(message[:1500])
    print("-" * 60)
    
    # Check for issues
    if "difficulty" in message.lower():
        print("\n⚠️ Still having difficulty!")
    elif "issue" in message.lower():
        print("\n⚠️ Still reporting issues!")
    else:
        print("\n✅ No error indicators found")
        
    # Count facility references
    facility_keywords = ["Hospital", "Clinic", "Centre", "Center", "Health"]
    found = sum(1 for kw in facility_keywords if kw in message)
    print(f"\n📍 Facility keyword matches: {found}")
    
else:
    print(f"❌ Query failed: {response.text}")