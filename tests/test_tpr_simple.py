#!/usr/bin/env python
"""
Simple TPR Workflow Test - Direct API calls
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:3094"

def test_tpr_workflow():
    """Test TPR workflow with direct API calls."""
    
    # 1. Start a session
    print("1. Starting session...")
    s = requests.Session()
    response = s.get(f"{BASE_URL}/")
    print(f"   Session started: {response.status_code}")
    
    # 2. Try a simple greeting (without streaming)
    print("\n2. Testing simple greeting...")
    try:
        # Let's test the analysis endpoint directly
        response = s.post(
            f"{BASE_URL}/analyze",
            json={"message": "hello"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {data.get('response', 'No response')[:100]}...")
        else:
            print(f"   Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # 3. Upload TPR file
    print("\n3. Uploading TPR file...")
    with open("instance/uploads/6e90b139-5d30-40fd-91ad-4af66fec5f00/tpr_data.xlsx", "rb") as f:
        files = {"csv_file": ("test_tpr_data.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        response = s.post(f"{BASE_URL}/upload", files=files)
        
    if response.status_code == 200:
        data = response.json()
        print(f"   Upload successful!")
        print(f"   Type: {data.get('upload_type', 'Unknown')}")
        print(f"   TPR Summary present: {'tpr_summary' in data}")
        if 'tpr_summary' in data:
            print(f"   Summary preview: {data['tpr_summary'][:200]}...")
    else:
        print(f"   Upload failed: {response.status_code}")
        print(f"   Error: {response.text[:500]}")
        
    # 4. Test TPR conversation (use analyze endpoint for non-streaming)
    print("\n4. Testing TPR conversation...")
    messages = [
        "I'd like to analyze Osun State",
        "Yes, proceed",
        "1",  # Primary facilities
        "under 5"
    ]
    
    for i, msg in enumerate(messages):
        print(f"\n   Step {i+1}: {msg}")
        try:
            response = s.post(
                f"{BASE_URL}/analyze",
                json={"message": msg},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                resp = data.get('response', 'No response')
                print(f"   Response: {resp[:150]}...")
            else:
                print(f"   Error: {response.status_code}")
                break
        except Exception as e:
            print(f"   Exception: {e}")
            break
        
        time.sleep(1)  # Give server time between requests
    
    print("\nTest completed!")

if __name__ == "__main__":
    # Check server
    try:
        response = requests.get(f"{BASE_URL}/ping", timeout=2)
        if response.status_code != 200:
            print("Server not responding properly")
            sys.exit(1)
    except:
        print(f"Server not running at {BASE_URL}")
        sys.exit(1)
    
    test_tpr_workflow()