#!/usr/bin/env python3
"""
Test that sticky sessions are working on production ALB.
"""

import requests
import pandas as pd
import io
from datetime import datetime

PRODUCTION_URL = "http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"

print("="*60)
print("   STICKY SESSIONS TEST")
print("="*60)

session = requests.Session()

# Step 1: Check for sticky cookie
print("\n1. Getting initial cookie...")
response = session.get(PRODUCTION_URL, timeout=10)
cookies = session.cookies.get_dict()

if 'AWSALB' in cookies or 'AWSALBTG' in cookies:
    print("✅ Sticky session cookie found!")
else:
    print("⚠️ No ALB cookie - sticky sessions may not be enabled")

# Step 2: Upload test file
print("\n2. Uploading test data...")
data = {
    'State': ['Test'],
    'LGA': ['Test LGA'],
    'WardName': ['Test Ward'],
    'Persons presenting with fever & tested by RDT <5yrs': [100],
    'Persons presenting with fever & tested by RDT ≥5yrs (excl PW)': [200],
    'Persons presenting with fever & tested by RDT Preg Women (PW)': [50]
}

df = pd.DataFrame(data)
csv_buffer = io.StringIO()
df.to_csv(csv_buffer, index=False)
csv_bytes = csv_buffer.getvalue().encode('utf-8')

files = {'file': ('test.csv', csv_bytes, 'text/csv')}
upload_response = session.post(
    f"{PRODUCTION_URL}/api/data-analysis/upload",
    files=files,
    timeout=30
)

if upload_response.status_code == 200:
    session_id = upload_response.json().get('session_id')
    print(f"✅ Upload successful: {session_id}")
    
    # Step 3: Test numeric selection
    print("\n3. Testing numeric selection '2'...")
    
    # First get menu
    session.post(
        f"{PRODUCTION_URL}/api/v1/data-analysis/chat",
        json={'message': 'analyze', 'session_id': session_id},
        timeout=30
    )
    
    # Then send "2"
    response = session.post(
        f"{PRODUCTION_URL}/api/v1/data-analysis/chat",
        json={'message': '2', 'session_id': session_id},
        timeout=30
    )
    
    if response.status_code == 200:
        message = response.json().get('message', '').lower()
        if 'tpr' in message or 'facility' in message:
            print("✅ SUCCESS! '2' understood as TPR selection")
            print("\n🎉 STICKY SESSIONS WORKING!")
        else:
            print("❌ System confused by '2'")
            print(f"Response: {message[:100]}...")
else:
    print(f"❌ Upload failed: {upload_response.status_code}")

print("\n" + "="*60)
