#!/usr/bin/env python3
"""
Test Data Analysis V3 with proper session handling
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
SESSION_ID = f"test_{int(time.time())}"

# Create a session to maintain cookies
session = requests.Session()

print("=" * 60)
print("Testing Data Analysis V3 with Session Handling")
print("=" * 60)
print(f"Session ID: {SESSION_ID}\n")

# Step 1: Upload file
print("1. Uploading test CSV...")
csv_content = """State,TestPositivityRate,Population,HealthFacilities
Kano,65.2,15000000,450
Lagos,42.1,21000000,850
Kaduna,71.8,8200000,380"""

files = {'file': ('test_data.csv', csv_content, 'text/csv')}
data = {'session_id': SESSION_ID}

response = session.post(f"{BASE_URL}/api/data-analysis/upload", files=files, data=data)
if response.status_code == 200:
    print(f"✅ Upload successful")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
else:
    print(f"❌ Upload failed: {response.status_code}")
    exit(1)

# Step 2: Check session status
print("\n2. Checking session status...")
response = session.get(f"{BASE_URL}/api/data-analysis/status")
if response.status_code == 200:
    status = response.json()
    print(f"   Has data file: {status.get('has_data_analysis_file', False)}")
    print(f"   Session ID: {status.get('session_id', 'unknown')}")

# Step 3: Send chat message
print("\n3. Sending analysis request...")
payload = {
    'message': "What data do I have? List all the states and their test positivity rates.",
    'session_id': SESSION_ID
}

response = session.post(f"{BASE_URL}/send_message", json=payload, timeout=60)
if response.status_code == 200:
    result = response.json()
    message = result.get('message', '')
    
    # Check for actual data
    has_kano = 'kano' in message.lower()
    has_lagos = 'lagos' in message.lower()
    has_kaduna = 'kaduna' in message.lower()
    has_65 = '65' in message
    
    print(f"✅ Response received")
    print(f"   Analysis type: {result.get('analysis_type', 'unknown')}")
    print(f"   Mentions Kano: {has_kano}")
    print(f"   Mentions Lagos: {has_lagos}")
    print(f"   Mentions Kaduna: {has_kaduna}")
    print(f"   Has actual values: {has_65}")
    
    if has_kano and has_lagos and has_kaduna:
        print("\n🎉 SUCCESS! Data Analysis V3 is working!")
        print("   The agent analyzed the actual uploaded data")
    else:
        print("\n⚠️  FAILED! Agent gave generic response")
        print("   Not analyzing the uploaded data")
    
    print(f"\n   Response preview:")
    print(f"   {message[:500]}...")
else:
    print(f"❌ Chat failed: {response.status_code}")

print("\n" + "=" * 60)