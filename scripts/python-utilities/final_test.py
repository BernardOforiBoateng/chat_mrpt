#!/usr/bin/env python3
import requests
import time

BASE_URL = "http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"

print("Final Production Test")
print("=" * 50)

# Test 1: Basic connectivity
print("\n1. Testing load balancer connectivity...")
for i in range(5):
    try:
        r = requests.get(f"{BASE_URL}/ping", timeout=5)
        if r.status_code == 200:
            print(f"   Request {i+1}: ✅")
        else:
            print(f"   Request {i+1}: ❌ (status {r.status_code})")
    except Exception as e:
        print(f"   Request {i+1}: ❌ ({e})")

# Test 2: File upload and TPR workflow
print("\n2. Testing TPR workflow...")
session = requests.Session()

try:
    # Upload file
    with open('adamawa_tpr_cleaned.csv', 'rb') as f:
        files = {'file': ('adamawa_tpr_cleaned.csv', f, 'text/csv')}
        r = session.post(f"{BASE_URL}/api/data-analysis/upload", files=files, timeout=30)
    
    if r.status_code == 200:
        session_id = r.json()['session_id']
        print(f"   Upload: ✅ (Session: {session_id})")
        
        # Run TPR workflow
        steps = [
            ("2", "Option 2"),
            ("primary", "Primary facilities"),
            ("Under 5 Years", "Age group")
        ]
        
        for msg, desc in steps:
            r = session.post(f"{BASE_URL}/api/v1/data-analysis/chat",
                           json={'message': msg, 'session_id': session_id},
                           timeout=60)
            if r.status_code == 200:
                print(f"   {desc}: ✅")
                if "TPR Calculation Complete" in r.json().get('message', ''):
                    print(f"   TPR Calculation: ✅ COMPLETED!")
            else:
                print(f"   {desc}: ❌ (status {r.status_code})")
            time.sleep(1)
    else:
        print(f"   Upload: ❌ (status {r.status_code})")
        
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "=" * 50)
print("Test completed!")
