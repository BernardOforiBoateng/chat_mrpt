#!/usr/bin/env python3
"""
Test Data Analysis V3 with Instance Sync
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
SESSION_ID = f"sync_test_{int(time.time())}"

# Create a session to maintain cookies
session = requests.Session()

print("=" * 60)
print("Testing Data Analysis V3 with Instance Sync")
print("=" * 60)
print(f"Session ID: {SESSION_ID}\n")

# Step 1: Upload file
print("1. Uploading test CSV...")
csv_content = """State,TestPositivityRate,Population,HealthFacilities
Kano,65.2,15000000,450
Lagos,42.1,21000000,850
Kaduna,71.8,8200000,380
Abuja,38.5,3500000,320"""

files = {'file': ('malaria_data.csv', csv_content, 'text/csv')}
data = {'session_id': SESSION_ID}

response = session.post(f"{BASE_URL}/api/data-analysis/upload", files=files, data=data, timeout=60)
if response.status_code == 200:
    result = response.json()
    print(f"✅ Upload successful to instance: {result.get('instance', 'unknown')}")
    print(f"   Session: {SESSION_ID}")
    print(f"   File: {result.get('filename')}")
else:
    print(f"❌ Upload failed: {response.status_code}")
    exit(1)

# Step 2: Wait for sync
print("\n2. Waiting for inter-instance sync...")
time.sleep(3)

# Step 3: Send multiple chat requests to test cross-instance
print("\n3. Testing analysis (may hit different instance)...")

for i in range(3):
    print(f"\n   Attempt {i+1}:")
    
    payload = {
        'message': f"What are the test positivity rates for each state? List them all. (Request {i+1})",
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
        has_71 = '71' in message
        
        if has_kano and has_lagos and has_kaduna:
            print(f"   ✅ SUCCESS! Got actual data analysis")
            print(f"      Mentions Kano: {has_kano}")
            print(f"      Mentions Lagos: {has_lagos}")
            print(f"      Mentions Kaduna: {has_kaduna}")
            print(f"      Has values: 65.2={has_65}, 71.8={has_71}")
            print(f"   Response preview: {message[:200]}...")
            break
        else:
            print(f"   ⚠️ Got generic response (sync may be in progress)")
            if i < 2:
                print(f"   Retrying in 2 seconds...")
                time.sleep(2)
    else:
        print(f"   ❌ Request failed: {response.status_code}")

# Step 4: Test visualization
print("\n4. Testing visualization generation...")
payload = {
    'message': "Create a bar chart showing test positivity rates by state",
    'session_id': SESSION_ID
}

response = session.post(f"{BASE_URL}/send_message", json=payload, timeout=60)
if response.status_code == 200:
    result = response.json()
    has_viz = 'visualizations' in result and result['visualizations']
    print(f"   Visualizations generated: {has_viz}")
    if has_viz:
        print(f"   ✅ Visualization working!")

print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)

if has_kano and has_lagos and has_kaduna:
    print("✅ Instance sync is WORKING!")
    print("   Files are being shared between instances")
    print("   Data Analysis V3 is functional!")
else:
    print("⚠️ Instance sync may need more time or manual check")
    print("   Check /home/ec2-user/ChatMRPT/instance/uploads/ on both instances")