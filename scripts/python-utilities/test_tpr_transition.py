#!/usr/bin/env python3
"""
Test TPR workflow and transition to risk analysis.
This simulates the complete flow from upload through TPR to risk analysis transition.
"""

import requests
import json
import time
import sys

BASE_URL = "http://127.0.0.1:5000"

def test_tpr_workflow():
    print("=== Testing TPR Workflow and Transition ===\n")
    
    # Step 1: Upload a CSV file with TPR data
    print("1. Uploading TPR data file...")
    with open('adamawa_tpr_cleaned.csv', 'rb') as f:
        files = {'file': ('tpr_test.csv', f, 'text/csv')}
        data = {'upload_type': 'data_analysis'}
        
        response = requests.post(f'{BASE_URL}/api/v1/data-analysis/upload', files=files, data=data)
        upload_result = response.json()
        
        if not upload_result.get('success'):
            print(f"❌ Upload failed: {upload_result}")
            return False
            
        session_id = upload_result.get('session_id')
        print(f"✅ Upload successful. Session ID: {session_id}")
        print(f"   Message: {upload_result.get('message', '')[:200]}...")
    
    # Step 2: Select option 2 for TPR
    print("\n2. Selecting option 2 for TPR calculation...")
    chat_data = {
        'message': '2',
        'session_id': session_id
    }
    
    response = requests.post(f'{BASE_URL}/api/v1/data-analysis/chat', json=chat_data)
    tpr_start = response.json()
    
    if not tpr_start.get('success'):
        print(f"❌ Failed to start TPR: {tpr_start}")
        return False
    
    print(f"✅ TPR workflow started")
    print(f"   Response: {tpr_start.get('message', '')[:200]}...")
    
    # Step 3: Handle state selection (if needed)
    if 'state' in tpr_start.get('message', '').lower() or 'which state' in tpr_start.get('message', '').lower():
        print("\n3. Selecting state (auto-selecting first)...")
        chat_data['message'] = '1'  # Select first state
        response = requests.post(f'{BASE_URL}/api/v1/data-analysis/chat', json=chat_data)
        state_response = response.json()
        print(f"   State selected: {state_response.get('message', '')[:100]}...")
    
    # Step 4: Select facility level (primary)
    print("\n4. Selecting facility level (primary)...")
    chat_data['message'] = '1'  # Primary
    response = requests.post(f'{BASE_URL}/api/v1/data-analysis/chat', json=chat_data)
    facility_response = response.json()
    print(f"   Facility level selected: {facility_response.get('message', '')[:100]}...")
    
    # Step 5: Select age group (all ages)
    print("\n5. Selecting age group (all ages)...")
    chat_data['message'] = '1'  # Usually first option
    response = requests.post(f'{BASE_URL}/api/v1/data-analysis/chat', json=chat_data)
    age_response = response.json()
    
    print(f"   Age group selected, TPR calculating...")
    print(f"   Message preview: {age_response.get('message', '')[:200]}...")
    
    # Check if we have visualizations
    if age_response.get('visualizations'):
        print(f"   ✅ Visualization created: {len(age_response['visualizations'])} visualization(s)")
    
    # Step 6: Check for transition prompt
    print("\n6. Checking for transition prompt...")
    message = age_response.get('message', '')
    
    if 'Would you like' in message and 'risk analysis' in message:
        print("   ✅ TRANSITION PROMPT FOUND!")
        print(f"   Prompt: {message[message.find('Would you like'):message.find('Would you like')+100]}...")
    else:
        print("   ❌ NO TRANSITION PROMPT FOUND")
        print("   Full message end:")
        print(f"   ...{message[-300:]}")
        return False
    
    # Step 7: Test saying "yes" to transition
    print("\n7. Testing transition (saying 'yes')...")
    chat_data['message'] = 'yes'
    response = requests.post(f'{BASE_URL}/api/v1/data-analysis/chat', json=chat_data)
    transition_response = response.json()
    
    print(f"   Transition response: {transition_response.get('message', '')[:200]}...")
    
    # Check if we exited data analysis mode
    if transition_response.get('exit_data_analysis_mode'):
        print("   ✅ Exited data analysis mode as expected")
    
    # Check if we got the menu
    if 'What would you like to do?' in transition_response.get('message', ''):
        print("   ✅ Got standard menu as expected")
        print("   Menu includes risk analysis option:", 
              'risk analysis' in transition_response.get('message', ''))
        return True
    else:
        print("   ❌ Did not get expected menu")
        return False

if __name__ == "__main__":
    try:
        success = test_tpr_workflow()
        if success:
            print("\n✅ ALL TESTS PASSED - Transition working correctly!")
        else:
            print("\n❌ TEST FAILED - Check the output above")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)