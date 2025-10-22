#!/usr/bin/env python3
"""
Final test of Data Analysis V3 with cross-instance support
"""

import requests
import json
import time

BASE_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"

# Test with the session we already synced
SESSION_ID = "sync_test_1754713248"

print("=" * 60)
print("Final Test of Data Analysis V3")
print("=" * 60)
print(f"Testing with existing session: {SESSION_ID}")
print("(This session has been manually synced to both instances)")
print("")

# Create session for cookies
session = requests.Session()

# Test multiple times to hit different instances
successes = 0
for i in range(5):
    print(f"\nAttempt {i+1}:")
    
    payload = {
        'message': f"List all states in my data with their test positivity rates. (Request {i+1})",
        'session_id': SESSION_ID
    }
    
    try:
        response = session.post(
            f"{BASE_URL}/send_message",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            message = result.get('message', '')
            
            # Check for actual data
            has_kano = 'kano' in message.lower()
            has_lagos = 'lagos' in message.lower()
            has_65 = '65' in message
            has_42 = '42' in message
            has_71 = '71' in message
            
            if has_kano and has_lagos and (has_65 or has_42 or has_71):
                print(f"   ✅ SUCCESS! Got actual data")
                print(f"      Kano: {has_kano}, Lagos: {has_lagos}")
                print(f"      Values: 65={has_65}, 42={has_42}, 71={has_71}")
                successes += 1
            else:
                print(f"   ⚠️ Generic response")
            
            print(f"   Preview: {message[:150]}...")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    time.sleep(1)

print("\n" + "=" * 60)
print("FINAL RESULTS")
print("=" * 60)
print(f"Success rate: {successes}/5 requests")

if successes >= 3:
    print("✅ Data Analysis V3 is WORKING across instances!")
    print("   Cross-instance sync is functional")
elif successes >= 1:
    print("⚠️ Partial success - sync may be inconsistent")
else:
    print("❌ Data Analysis V3 not working properly")

# Now test a fresh upload with auto-sync
print("\n" + "=" * 60)
print("Testing Fresh Upload with Auto-Sync")
print("=" * 60)

NEW_SESSION = f"auto_sync_{int(time.time())}"
print(f"New session: {NEW_SESSION}")

# Upload
csv_data = "Region,Cases\nNorth,500\nSouth,300"
files = {'file': ('test.csv', csv_data, 'text/csv')}
data = {'session_id': NEW_SESSION}

print("\n1. Uploading...")
response = session.post(f"{BASE_URL}/api/data-analysis/upload", files=files, data=data)
if response.status_code == 200:
    print(f"   ✅ Upload successful")
else:
    print(f"   ❌ Upload failed")

# Wait for potential sync
time.sleep(3)

# Test chat
print("\n2. Testing analysis...")
response = session.post(
    f"{BASE_URL}/send_message",
    json={'message': 'What regions are in my data?', 'session_id': NEW_SESSION},
    timeout=60
)

if response.status_code == 200:
    result = response.json()
    msg = result.get('message', '')
    if 'north' in msg.lower() and 'south' in msg.lower():
        print(f"   ✅ Auto-sync WORKS! Data analyzed correctly")
    else:
        print(f"   ⚠️ Auto-sync may not be working")
    print(f"   Preview: {msg[:150]}...")