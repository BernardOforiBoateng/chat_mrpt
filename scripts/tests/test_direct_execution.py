"""
Test direct code execution to debug the issue
"""

import requests
import time
import json

STAGING_URL = "http://3.21.167.170:8080"

def test_direct_execution():
    """Test with explicit code that should work."""
    
    session_id = f'debug_{int(time.time())}'
    
    # Upload data
    print("Uploading data...")
    with open('www/adamawa_tpr_cleaned.csv', 'rb') as f:
        files = {'file': ('test_data.csv', f, 'text/csv')}
        data = {'session_id': session_id}
        
        response = requests.post(
            f"{STAGING_URL}/api/data-analysis/upload",
            files=files,
            data=data,
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"Upload failed: {response.status_code}")
            return
    
    print("✅ Data uploaded")
    time.sleep(2)
    
    # Test 1: Simple column listing
    print("\n1. Testing column listing...")
    response = requests.post(
        f"{STAGING_URL}/api/v1/data-analysis/chat",
        json={
            'message': "Execute this exact code: print(df.columns.tolist())",
            'session_id': session_id
        },
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result.get('success')}")
        message = result.get('message', '')
        print(f"Response length: {len(message)} chars")
        if len(message) > 0:
            print(f"Response preview: {message[:500]}")
    
    # Test 2: Ask for specific groupby
    print("\n2. Testing explicit groupby...")
    response = requests.post(
        f"{STAGING_URL}/api/v1/data-analysis/chat",
        json={
            'message': """Execute this code:
# Group by healthfacility column
result = df.groupby('healthfacility').size().sort_values(ascending=False).head(10)
print("Top 10 facilities:")
for i, (facility, count) in enumerate(result.items(), 1):
    print(f"{i}. {facility}: {count} records")
""",
            'session_id': session_id
        },
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result.get('success')}")
        message = result.get('message', '')
        print(f"Response length: {len(message)} chars")
        if "Top 10" in message:
            # Extract the numbered items
            lines = message.split('\n')
            for line in lines:
                if line.strip().startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.')):
                    print(f"  {line.strip()}")

if __name__ == "__main__":
    test_direct_execution()