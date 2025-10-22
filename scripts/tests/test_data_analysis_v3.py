#\!/usr/bin/env python3
"""
Test Data Analysis V3 functionality end-to-end
"""
import requests
import json
import time

# Base URL for staging
BASE_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"

def test_data_analysis_v3():
    """Test the complete Data Analysis V3 flow."""
    
    # Start a session to maintain cookies
    session = requests.Session()
    
    print("=" * 60)
    print("Testing Data Analysis V3 Workflow")
    print("=" * 60)
    
    # Step 1: Upload a test file
    print("\n1. Uploading test data file...")
    
    # Create test data
    test_csv = """State,Ward,Population,Cases,TestPositivity
Kano,Ward_A,10000,50,0.45
Kano,Ward_B,15000,20,0.23
Kano,Ward_C,8000,5,0.12
Lagos,Ward_D,12000,30,0.38
Lagos,Ward_E,20000,100,0.52"""
    
    files = {'file': ('test_data.csv', test_csv, 'text/csv')}
    response = session.post(f"{BASE_URL}/api/data-analysis/upload", files=files)
    
    if response.status_code == 200:
        upload_result = response.json()
        print(f"✅ Upload successful\!")
        print(f"   Session ID: {upload_result.get('session_id')}")
        print(f"   Metadata: {upload_result.get('metadata', {})}")
    else:
        print(f"❌ Upload failed: {response.status_code}")
        print(response.text)
        return
    
    # Step 2: Activate Data Analysis mode
    print("\n2. Activating Data Analysis mode...")
    response = session.post(f"{BASE_URL}/api/data-analysis/activate-mode")
    if response.status_code == 200:
        print("✅ Data Analysis mode activated")
    else:
        print(f"⚠️ Activation response: {response.status_code}")
    
    # Step 3: Test basic query
    print("\n3. Testing 'What's in my data?' query...")
    
    query = {"message": "What's in my data?"}
    
    start_time = time.time()
    response = session.post(
        f"{BASE_URL}/send_message",
        json=query,
        timeout=45
    )
    elapsed = time.time() - start_time
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Query successful (took {elapsed:.1f}s)")
        print(f"   Response: {result.get('response', 'No response')[:500]}...")
        
        # Check if it actually analyzed the data
        if "Ward" in result.get('response', '') or "Population" in result.get('response', ''):
            print("   ✅ Agent analyzed actual data\!")
        else:
            print("   ⚠️ Response seems generic, not analyzing uploaded data")
            
        if result.get('tools_used'):
            print(f"   Tools used: {result.get('tools_used')}")
    else:
        print(f"❌ Query failed: {response.status_code}")
        print(response.text[:500])
    
    print("\n" + "=" * 60)
    print("Test Complete\!")
    print("=" * 60)

if __name__ == "__main__":
    test_data_analysis_v3()
EOF < /dev/null
