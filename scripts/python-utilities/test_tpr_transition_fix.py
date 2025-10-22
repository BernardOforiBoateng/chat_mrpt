#!/usr/bin/env python3
"""
Test script to verify TPR to risk analysis transition works correctly.
"""

import requests
import json
import time
import sys

# Configuration
BASE_URL = "http://127.0.0.1:5000"
SESSION_ID = f"test_session_{int(time.time())}"

def test_tpr_transition():
    """Test the TPR to risk analysis transition."""
    
    print(f"Testing TPR transition with session: {SESSION_ID}")
    print("-" * 50)
    
    # Step 1: Upload test data
    print("1. Uploading test data...")
    files = {
        'files': ('test_data.csv', open('app/sample_data/mock_nigeria_malaria_data.csv', 'rb'), 'text/csv')
    }
    data = {'session_id': SESSION_ID}
    
    response = requests.post(f"{BASE_URL}/api/data-analysis/upload", files=files, data=data)
    print(f"   Upload response: {response.status_code}")
    if response.status_code != 200:
        print(f"   Error: {response.text}")
        return False
    
    upload_result = response.json()
    print(f"   Session ID: {upload_result.get('session_id')}")
    
    # Step 2: Start TPR workflow
    print("\n2. Starting TPR workflow...")
    chat_data = {
        'message': '2',  # Select option 2 for TPR
        'session_id': SESSION_ID
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/data-analysis/chat", 
                            json=chat_data,
                            headers={'Content-Type': 'application/json'})
    print(f"   TPR start response: {response.status_code}")
    result = response.json()
    print(f"   Stage: {result.get('stage')}")
    
    # Step 3: Select state (if needed)
    if result.get('stage') == 'state_selection':
        print("\n3. Selecting state...")
        chat_data = {
            'message': '1',  # Select first state
            'session_id': SESSION_ID
        }
        response = requests.post(f"{BASE_URL}/api/v1/data-analysis/chat", 
                                json=chat_data,
                                headers={'Content-Type': 'application/json'})
        result = response.json()
        print(f"   Stage after state: {result.get('stage')}")
    
    # Step 4: Select facility level
    print("\n4. Selecting facility level...")
    chat_data = {
        'message': '1',  # Select primary
        'session_id': SESSION_ID
    }
    response = requests.post(f"{BASE_URL}/api/v1/data-analysis/chat", 
                            json=chat_data,
                            headers={'Content-Type': 'application/json'})
    result = response.json()
    print(f"   Stage after facility: {result.get('stage')}")
    
    # Step 5: Select age group
    print("\n5. Selecting age group...")
    chat_data = {
        'message': '1',  # Select first age group
        'session_id': SESSION_ID
    }
    response = requests.post(f"{BASE_URL}/api/v1/data-analysis/chat", 
                            json=chat_data,
                            headers={'Content-Type': 'application/json'})
    result = response.json()
    print(f"   Stage after age: {result.get('stage')}")
    print(f"   TPR complete: {result.get('stage') == 'complete'}")
    
    # Wait for TPR calculation to complete
    time.sleep(2)
    
    # Step 6: Test transition with "yes"
    print("\n6. Testing transition with 'yes'...")
    chat_data = {
        'message': 'yes',
        'session_id': SESSION_ID
    }
    response = requests.post(f"{BASE_URL}/api/v1/data-analysis/chat", 
                            json=chat_data,
                            headers={'Content-Type': 'application/json'})
    result = response.json()
    
    print(f"   Response status: {response.status_code}")
    print(f"   Success: {result.get('success')}")
    print(f"   Has exit_data_analysis_mode: {result.get('exit_data_analysis_mode')}")
    print(f"   Has message: {bool(result.get('message'))}")
    print(f"   Has redirect_message: {result.get('redirect_message')}")
    
    if result.get('exit_data_analysis_mode'):
        print("\n✅ SUCCESS: Transition response received correctly!")
        print(f"   Message preview: {result.get('message', '')[:100]}...")
        return True
    else:
        print("\n❌ FAILURE: No transition response!")
        print(f"   Full response: {json.dumps(result, indent=2)}")
        return False

if __name__ == "__main__":
    try:
        success = test_tpr_transition()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
