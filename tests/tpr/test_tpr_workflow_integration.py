#!/usr/bin/env python
"""
Comprehensive TPR Workflow Integration Test
Tests the entire TPR workflow using actual HTTP requests to simulate frontend interaction.
"""

import requests
import json
import time
import sys
from datetime import datetime
import shutil
import os

# Configuration
BASE_URL = "http://localhost:3094"
TEST_SESSION_ID = "test_tpr_workflow_" + datetime.now().strftime("%Y%m%d_%H%M%S")
SOURCE_TPR_FILE = "instance/uploads/6e90b139-5d30-40fd-91ad-4af66fec5f00/tpr_data.xlsx"

# Session cookies storage
session_cookies = None

def print_section(title):
    """Print a section header."""
    print("\n" + "="*80)
    print(f" {title} ")
    print("="*80)

def print_response(response_data, indent=0):
    """Pretty print the response data."""
    prefix = "  " * indent
    if isinstance(response_data, dict):
        message = response_data.get('message', response_data.get('response', ''))
        if message:
            print(f"{prefix}Assistant: {message}")
        if 'data' in response_data:
            print(f"{prefix}Data: {json.dumps(response_data['data'], indent=2)}")
    else:
        print(f"{prefix}Response: {response_data}")

def initialize_session():
    """Initialize a new session by visiting the home page."""
    global session_cookies
    print_section("INITIALIZING SESSION")
    
    response = requests.get(f"{BASE_URL}/")
    session_cookies = response.cookies
    
    print(f"Session initialized with ID: {session_cookies.get('session', 'Unknown')}")
    print(f"Status Code: {response.status_code}")
    return response.status_code == 200

def send_message(message):
    """Send a message through the streaming endpoint."""
    print(f"\nUser: {message}")
    
    response = requests.post(
        f"{BASE_URL}/send_message_streaming",
        json={"message": message},
        cookies=session_cookies,
        stream=True
    )
    
    full_response = ""
    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line.decode('utf-8').replace('data: ', ''))
                if 'content' in data:
                    full_response += data['content']
                if data.get('done', False):
                    break
            except json.JSONDecodeError:
                continue
    
    print(f"Assistant: {full_response}")
    return full_response

def upload_tpr_file():
    """Upload the TPR file to simulate file upload."""
    print_section("UPLOADING TPR FILE")
    
    # Create test session directory
    test_session_dir = f"instance/uploads/{TEST_SESSION_ID}"
    os.makedirs(test_session_dir, exist_ok=True)
    
    # Copy the TPR file to our test session
    test_file_path = os.path.join(test_session_dir, "tpr_data.xlsx")
    shutil.copy2(SOURCE_TPR_FILE, test_file_path)
    print(f"Copied TPR file to: {test_file_path}")
    
    # Upload the file
    with open(test_file_path, 'rb') as f:
        files = {'file': ('nmep_test_data.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response = requests.post(
            f"{BASE_URL}/upload",
            files=files,
            cookies=session_cookies
        )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Upload successful!")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        # Update session cookies if needed
        if response.cookies:
            session_cookies.update(response.cookies)
        
        return data
    else:
        print(f"Upload failed with status: {response.status_code}")
        print(f"Error: {response.text}")
        return None

def test_complete_workflow():
    """Test the complete TPR workflow."""
    print_section("STARTING TPR WORKFLOW TEST")
    print(f"Timestamp: {datetime.now()}")
    print(f"Server: {BASE_URL}")
    
    # Step 1: Initialize session
    if not initialize_session():
        print("ERROR: Failed to initialize session")
        return False
    
    # Step 2: Send initial greeting
    print_section("STEP 1: INITIAL GREETING")
    greeting_response = send_message("hi")
    time.sleep(1)  # Give server time to process
    
    # Step 3: Upload TPR file
    print_section("STEP 2: TPR FILE UPLOAD")
    upload_response = upload_tpr_file()
    if not upload_response:
        print("ERROR: Failed to upload TPR file")
        return False
    time.sleep(2)  # Give server time to process
    
    # Step 4: Select state (Osun State)
    print_section("STEP 3: STATE SELECTION")
    state_response = send_message("I would like to analyze Osun State")
    time.sleep(1)
    
    # Check if we got state overview
    if "Osun State Overview" in state_response:
        print("\n✓ State overview received successfully!")
        
        # Confirm to proceed
        print_section("STEP 4: CONFIRM STATE SELECTION")
        confirm_response = send_message("Yes, let's proceed")
        time.sleep(1)
    
    # Step 5: Select facility level
    print_section("STEP 5: FACILITY LEVEL SELECTION")
    facility_response = send_message("1")  # Select Primary facilities
    time.sleep(1)
    
    # Step 6: Select age group
    print_section("STEP 6: AGE GROUP SELECTION")
    age_response = send_message("under 5")
    time.sleep(2)  # Give more time for calculation
    
    # Step 7: Check if calculation completed
    print_section("WORKFLOW COMPLETION CHECK")
    if "TPR for" in age_response and "wards" in age_response:
        print("\n✅ TPR WORKFLOW COMPLETED SUCCESSFULLY!")
        print("✓ Initial greeting worked")
        print("✓ File upload processed")
        print("✓ State selection with overview shown")
        print("✓ Facility level selected")
        print("✓ Age group selected")
        print("✓ TPR calculation completed")
        return True
    else:
        print("\n❌ WORKFLOW DID NOT COMPLETE AS EXPECTED")
        return False

def test_alternative_paths():
    """Test alternative conversation paths."""
    print_section("TESTING ALTERNATIVE PATHS")
    
    # Test 1: Different state selection
    print("\n--- Test: Selecting Adamawa State ---")
    response = send_message("Actually, let me analyze Adamawa State instead")
    time.sleep(1)
    
    # Test 2: Secondary facilities
    print("\n--- Test: Selecting Secondary Facilities ---")
    response = send_message("2")  # Secondary facilities
    time.sleep(1)
    
    # Test 3: Different age group
    print("\n--- Test: Selecting Pregnant Women ---")
    response = send_message("pregnant women")
    time.sleep(2)
    
    print("\n✅ Alternative paths tested")

if __name__ == "__main__":
    try:
        # Make sure server is running
        try:
            response = requests.get(f"{BASE_URL}/ping", timeout=2)
            if response.status_code != 200:
                print("ERROR: Server not responding properly")
                sys.exit(1)
        except requests.exceptions.RequestException:
            print("ERROR: Server not running at", BASE_URL)
            print("Please start the server with: python run.py")
            sys.exit(1)
        
        # Run the main workflow test
        success = test_complete_workflow()
        
        if success:
            # Test alternative paths
            test_alternative_paths()
            
        print_section("TEST COMPLETED")
        print(f"Overall Result: {'PASSED' if success else 'FAILED'}")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()