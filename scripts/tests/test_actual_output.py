"""
Test to see what's actually in the 1399 char output
"""

import requests
import time
import json

STAGING_URL = "http://3.21.167.170:8080"

# Test directly
session_id = f'raw_{int(time.time())}'

# Upload
with open('www/adamawa_tpr_cleaned.csv', 'rb') as f:
    requests.post(
        f"{STAGING_URL}/api/data-analysis/upload",
        files={'file': ('test.csv', f, 'text/csv')},
        data={'session_id': session_id}
    )

time.sleep(2)

# Make request
response = requests.post(
    f"{STAGING_URL}/api/v1/data-analysis/chat",
    json={
        'message': "Execute this code and show me the raw output: print(df.columns.tolist()); print('healthfacility' in df.columns)",
        'session_id': session_id
    },
    timeout=120
)

result = response.json()
print("Success:", result.get('success'))
print("\nMessage length:", len(result.get('message', '')))
print("\nFull message:")
print("="*60)
print(result.get('message', 'No message'))
print("="*60)
