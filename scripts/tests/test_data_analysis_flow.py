#!/usr/bin/env python
"""
Test the complete Data Analysis V3 flow
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
TEST_FILE = "tests/test_data/abia_tpr_data.xlsx"

def test_upload_and_analyze():
    """Test uploading a file and triggering analysis"""
    
    print("="*60)
    print("Testing Data Analysis V3 Flow")
    print("="*60)
    
    # Step 1: Upload file
    print("\n1. Uploading test file...")
    
    with open(TEST_FILE, 'rb') as f:
        files = {'file': ('test_data.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        data = {'session_id': 'test_flow_' + str(int(time.time()))}
        
        response = requests.post(
            f"{BASE_URL}/api/data-analysis/upload",
            files=files,
            data=data
        )
    
    if response.status_code != 200:
        print(f"❌ Upload failed: {response.status_code}")
        print(response.text)
        return False
    
    upload_result = response.json()
    session_id = upload_result.get('session_id')
    print(f"✅ File uploaded successfully")
    print(f"   Session ID: {session_id}")
    print(f"   File: {upload_result.get('filename')}")
    
    # Step 2: Trigger analysis via chat endpoint
    print("\n2. Triggering data analysis...")
    
    chat_data = {
        'message': 'analyze uploaded data',
        'session_id': session_id
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/data-analysis/chat",
        json=chat_data,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Analysis failed: {response.status_code}")
        print("Response content:")
        try:
            error_data = response.json()
            print(json.dumps(error_data, indent=2))
            if 'traceback' in error_data:
                print("\nTraceback:")
                print(error_data['traceback'])
        except:
            print(response.text[:500])
        return False
    
    # Step 3: Check the response
    print("✅ Analysis completed successfully!")
    
    result = response.json()
    
    if result.get('success'):
        print("\n3. Analysis Result:")
        print("-" * 40)
        message = result.get('message', '')
        # Print first 500 chars of the message
        print(message[:500])
        if len(message) > 500:
            print("\n... [truncated]")
        
        # Check if it contains our new dynamic summary elements
        if "Dataset Overview:" in message:
            print("\n✅ Dynamic summary detected!")
        if "What would you like to do" in message:
            print("✅ User choices presented!")
        if "rows" in message and "columns" in message:
            print("✅ Data shape information included!")
            
        return True
    else:
        print(f"❌ Analysis returned success=False")
        print(f"Error: {result.get('error')}")
        return False

if __name__ == "__main__":
    # First check if test file exists
    import os
    if not os.path.exists(TEST_FILE):
        # Try alternate path
        TEST_FILE = "www/NMEP Malaria Adamawa_Kwara_Osun_Test Postivity Rate_2022_2024.xlsx"
        if not os.path.exists(TEST_FILE):
            print(f"❌ Test file not found: {TEST_FILE}")
            print("Available Excel files:")
            os.system("ls -la www/*.xlsx | head -5")
            # Use first available Excel file
            import glob
            excel_files = glob.glob("www/*.xlsx")
            if excel_files:
                TEST_FILE = excel_files[0]
                print(f"Using: {TEST_FILE}")
    
    success = test_upload_and_analyze()
    
    print("\n" + "="*60)
    if success:
        print("✅ ALL TESTS PASSED!")
        print("The Data Analysis V3 flow is working correctly.")
    else:
        print("❌ TEST FAILED")
        print("Please check the error messages above.")
    print("="*60)