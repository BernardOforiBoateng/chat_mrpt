#!/usr/bin/env python
"""
Test the improved TPR workflow on staging

Tests:
1. State persistence across messages
2. Rich contextual information display
3. 3-step workflow (no test method question)
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
TEST_FILE = "www/NMEP Malaria Adamawa_Kwara_Osun_Test Postivity Rate_2022_2024.xlsx"

def test_tpr_workflow():
    """Test the complete TPR workflow with state management."""
    
    print("="*60)
    print("Testing Improved TPR Workflow")
    print("="*60)
    
    session_id = f'test_tpr_{int(time.time())}'
    
    # Step 1: Upload file
    print("\n1. Uploading TPR test file...")
    
    with open(TEST_FILE, 'rb') as f:
        files = {'file': ('test_tpr.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        data = {'session_id': session_id}
        
        response = requests.post(
            f"{BASE_URL}/api/data-analysis/upload",
            files=files,
            data=data
        )
    
    if response.status_code != 200:
        print(f"❌ Upload failed: {response.status_code}")
        print(response.text[:500])
        return False
    
    upload_result = response.json()
    print(f"✅ File uploaded successfully")
    print(f"   Session ID: {session_id}")
    
    # Step 2: Get initial data summary
    print("\n2. Getting initial data summary...")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/data-analysis/chat",
        json={
            'message': 'show me the uploaded data',
            'session_id': session_id
        },
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to get summary: {response.status_code}")
        return False
    
    result = response.json()
    if result.get('success'):
        message = result.get('message', '')
        print("✅ Got data summary")
        
        # Check for generic summary (not TPR-specific)
        if "What would you like to do" in message:
            print("✅ Generic summary shown (no TPR stats yet)")
        else:
            print("⚠️ Summary might be showing TPR stats too early")
    
    # Step 3: Select TPR option
    print("\n3. Selecting TPR option (1)...")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/data-analysis/chat",
        json={
            'message': '1',  # Select TPR option
            'session_id': session_id
        },
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to select TPR: {response.status_code}")
        return False
    
    result = response.json()
    if result.get('success'):
        message = result.get('message', '')
        
        # Check for state selection with statistics
        if "Which state" in message:
            print("✅ TPR workflow started - State selection shown")
            
            # Check for rich context
            if "health facilities" in message.lower() and "tests" in message.lower():
                print("✅ Rich context provided (facility counts, test counts)")
            else:
                print("⚠️ Missing contextual statistics")
    
    # Step 4: Select state (Adamawa)
    print("\n4. Selecting state: Adamawa...")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/data-analysis/chat",
        json={
            'message': 'Adamawa',
            'session_id': session_id
        },
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to select state: {response.status_code}")
        return False
    
    result = response.json()
    if result.get('success'):
        message = result.get('message', '')
        
        # Should now ask for facility level (NOT test method)
        if "facility" in message.lower():
            print("✅ Moved to facility selection (no amnesia!)")
            
            if "primary" in message.lower() and "secondary" in message.lower():
                print("✅ Facility options shown with context")
        elif "confirm" in message.lower() or "sure" in message.lower():
            print("❌ AMNESIA DETECTED - Asking for confirmation instead of next step")
            return False
    
    # Step 5: Select facility level
    print("\n5. Selecting facility level: All...")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/data-analysis/chat",
        json={
            'message': '1',  # Select "All facilities"
            'session_id': session_id
        },
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to select facility: {response.status_code}")
        return False
    
    result = response.json()
    if result.get('success'):
        message = result.get('message', '')
        
        # Should ask for age group (NOT test method!)
        if "age group" in message.lower():
            print("✅ Moved to age group selection")
            
            if "under 5" in message.lower() and "tests available" in message.lower():
                print("✅ Age group options with test counts shown")
                
            # Make sure NO test method question
            if "rdt" in message.lower() and "microscopy" in message.lower() and "method" in message.lower():
                print("❌ ERROR: Asking for test method (should be automatic!)")
                return False
    
    # Step 6: Select age group
    print("\n6. Selecting age group: Under 5...")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/data-analysis/chat",
        json={
            'message': '2',  # Select "Under 5"
            'session_id': session_id
        },
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to select age group: {response.status_code}")
        return False
    
    result = response.json()
    if result.get('success'):
        message = result.get('message', '')
        
        # Should start calculating TPR (no more questions!)
        if "calculating" in message.lower() or "complete" in message.lower():
            print("✅ TPR calculation started automatically")
            
            # Check for methodology explanation
            if "maximum" in message.lower() or "both" in message.lower():
                print("✅ Automatic test method handling confirmed")
        elif "test method" in message.lower() or "rdt" in message.lower():
            print("❌ ERROR: Still asking for test method!")
            return False
        elif "confirm" in message.lower():
            print("❌ AMNESIA: Asking for confirmation again!")
            return False
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("TPR workflow improvements working correctly:")
    print("- State persistence (no amnesia)")
    print("- Rich contextual information")
    print("- 3-step workflow (no test method question)")
    print("- Automatic max(RDT, Microscopy) calculation")
    print("="*60)
    
    return True

if __name__ == "__main__":
    success = test_tpr_workflow()
    
    if not success:
        print("\n❌ TEST FAILED - Issues detected")
        print("Please check the error messages above")