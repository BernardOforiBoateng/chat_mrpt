"""
Test to see the actual full response from agent
"""

import requests
import time
import json

STAGING_URL = "http://3.21.167.170:8080"

session_id = f'debug_{int(time.time())}'

# Upload data
print("Uploading data...")
with open('www/adamawa_tpr_cleaned.csv', 'rb') as f:
    response = requests.post(
        f"{STAGING_URL}/api/data-analysis/upload",
        files={'file': ('test_data.csv', f, 'text/csv')},
        data={'session_id': session_id},
        timeout=60
    )

print("✅ Data uploaded")
time.sleep(2)

# Make request
print("\nSending query...")
response = requests.post(
    f"{STAGING_URL}/api/v1/data-analysis/chat",
    json={
        'message': "List the top 10 health facilities by number of records",
        'session_id': session_id
    },
    timeout=120
)

print(f"\nStatus Code: {response.status_code}")
print("\nFull Response:")
print("="*60)
print(json.dumps(response.json(), indent=2))
print("="*60)