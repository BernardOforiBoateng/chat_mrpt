#!/usr/bin/env python3
import requests
import time
from datetime import datetime

# Direct to instance 2 (bypassing load balancer)
BASE_URL = "http://172.31.43.200:5000"
session = requests.Session()

print(f"\n🎯 Testing TPR on Instance 2 directly")
print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
print("="*60)

try:
    # Upload file
    print("\n📤 Uploading adamawa_tpr_cleaned.csv...")
    with open('adamawa_tpr_cleaned.csv', 'rb') as f:
        files = {'file': ('adamawa_tpr_cleaned.csv', f, 'text/csv')}
        r = session.post(f"{BASE_URL}/api/data-analysis/upload", files=files, timeout=30)
    
    if r.status_code != 200:
        print(f"❌ Upload failed: {r.status_code}")
        exit(1)
    
    session_id = r.json()['session_id']
    print(f"✅ Upload successful. Session ID: {session_id}")
    
    # Run through TPR workflow
    for msg in ["2", "primary", "Under 5 Years"]:
        print(f"\n📍 Sending: {msg}")
        r = session.post(f"{BASE_URL}/api/v1/data-analysis/chat",
                         json={'message': msg, 'session_id': session_id},
                         timeout=60)
        if r.status_code == 200:
            result = r.json()
            # Check for map
            if "TPR Calculation Complete" in result.get('message', ''):
                print("✅ TPR calculation completed")
                if "tpr_distribution_map" in result.get('message', ''):
                    print("🗺️  ✅ Map generated!")
                else:
                    print("🗺️  ❌ No map generated")
        time.sleep(1)
    
    # Test risk transition
    print("\n🔄 Testing risk transition...")
    r = session.post(f"{BASE_URL}/api/v1/data-analysis/chat",
                     json={'message': 'yes', 'session_id': session_id},
                     timeout=60)
    if r.status_code == 200:
        msg = r.json().get('message', '')
        if "Error: TPR data file not found" in msg:
            print("❌ Risk transition failed: TPR data file not found")
        else:
            print("✅ Risk transition successful!")
            
except Exception as e:
    print(f"❌ Error: {e}")
