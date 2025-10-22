#!/usr/bin/env python3
"""
Comprehensive test script for TPR to risk analysis transition on AWS production.
Tests the complete workflow from data upload through TPR to risk analysis transition.
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration for AWS production
BASE_URL = "https://d225ar6c86586s.cloudfront.net"  # CloudFront URL
# Fallback to ALB if CloudFront fails
ALB_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"

# Generate unique session ID for this test
SESSION_ID = f"test_tpr_{int(time.time())}"

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_step(step_num, message):
    """Print a formatted step message."""
    print(f"\n{BLUE}Step {step_num}:{RESET} {message}")
    print("-" * 60)

def print_success(message):
    """Print success message in green."""
    print(f"{GREEN}✓ {message}{RESET}")

def print_error(message):
    """Print error message in red."""
    print(f"{RED}✗ {message}{RESET}")

def print_info(message):
    """Print info message in yellow."""
    print(f"{YELLOW}ℹ {message}{RESET}")

def test_tpr_transition():
    """Test the complete TPR to risk analysis transition."""
    
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}TPR to Risk Analysis Transition Test{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Test URL: {BASE_URL}")
    print(f"Session ID: {SESSION_ID}")
    
    try:
        # Test connectivity first
        print_step(0, "Testing connectivity to production server")
        try:
            response = requests.get(f"{BASE_URL}/ping", timeout=5)
            if response.status_code == 200:
                print_success(f"Server is reachable (status: {response.status_code})")
                url = BASE_URL
            else:
                raise Exception(f"Server returned status {response.status_code}")
        except Exception as e:
            print_error(f"CloudFront not accessible: {e}")
            print_info("Trying ALB directly...")
            response = requests.get(f"{ALB_URL}/ping", timeout=5)
            if response.status_code == 200:
                print_success("ALB is reachable")
                url = ALB_URL
            else:
                raise Exception("Neither CloudFront nor ALB accessible")
        
        # Step 1: Upload test data
        print_step(1, "Uploading test data file")
        
        # Read the test data file
        with open('test_tpr_data.csv', 'rb') as f:
            files = {'files': ('test_data.csv', f, 'text/csv')}
            data = {'session_id': SESSION_ID}
            
            response = requests.post(
                f"{url}/api/data-analysis/upload", 
                files=files, 
                data=data,
                timeout=30
            )
        
        if response.status_code != 200:
            print_error(f"Upload failed with status {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
        
        upload_result = response.json()
        print_success(f"Data uploaded successfully")
        print_info(f"Backend session: {upload_result.get('session_id', SESSION_ID)}")
        
        # Use the backend session ID if provided
        session_id = upload_result.get('session_id', SESSION_ID)
        
        # Step 2: Trigger initial data analysis
        print_step(2, "Triggering data analysis mode")
        
        response = requests.post(
            f"{url}/api/v1/data-analysis/chat",
            json={
                'message': '__DATA_UPLOADED__',
                'session_id': session_id
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print_error(f"Failed to trigger data analysis: {response.status_code}")
            return False
        
        result = response.json()
        print_success("Data analysis mode activated")
        
        # Step 3: Start TPR workflow (select option 2)
        print_step(3, "Starting TPR workflow (selecting option 2)")
        
        response = requests.post(
            f"{url}/api/v1/data-analysis/chat",
            json={
                'message': '2',
                'session_id': session_id
            },
            timeout=30
        )
        
        result = response.json()
        stage = result.get('stage', '')
        print_success(f"TPR workflow started")
        print_info(f"Current stage: {stage}")
        
        # Step 4: Handle state selection if needed
        if stage == 'state_selection':
            print_step(4, "Selecting state (option 1)")
            
            response = requests.post(
                f"{url}/api/v1/data-analysis/chat",
                json={
                    'message': '1',
                    'session_id': session_id
                },
                timeout=30
            )
            
            result = response.json()
            print_success("State selected")
            print_info(f"Stage: {result.get('stage', '')}")
        
        # Step 5: Select facility level
        print_step(5, "Selecting facility level (primary)")
        
        response = requests.post(
            f"{url}/api/v1/data-analysis/chat",
            json={
                'message': '1',  # Select primary
                'session_id': session_id
            },
            timeout=30
        )
        
        result = response.json()
        print_success("Facility level selected: Primary")
        print_info(f"Stage: {result.get('stage', '')}")
        
        # Step 6: Select age group
        print_step(6, "Selecting age group (under 5)")
        
        response = requests.post(
            f"{url}/api/v1/data-analysis/chat",
            json={
                'message': '1',  # Select under 5
                'session_id': session_id
            },
            timeout=30
        )
        
        result = response.json()
        stage = result.get('stage', '')
        print_success("Age group selected: Under 5")
        print_info(f"Stage: {stage}")
        
        # Check if TPR calculation completed
        if stage == 'complete':
            print_success("TPR calculation completed successfully!")
        else:
            print_info("Waiting for TPR calculation to complete...")
            time.sleep(3)
        
        # Step 7: THE CRITICAL TEST - Send "yes" to transition
        print_step(7, "Testing transition with 'yes' response")
        print_info("This is the critical test - sending 'yes' to proceed to risk analysis")
        
        response = requests.post(
            f"{url}/api/v1/data-analysis/chat",
            json={
                'message': 'yes',
                'session_id': session_id
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print_error(f"Request failed with status {response.status_code}")
            return False
        
        result = response.json()
        
        # Check for successful transition indicators
        print("\n" + "="*60)
        print("TRANSITION RESPONSE ANALYSIS:")
        print("="*60)
        
        success_indicators = {
            'exit_data_analysis_mode': result.get('exit_data_analysis_mode'),
            'trigger_analysis': result.get('trigger_analysis'),
            'success': result.get('success'),
            'has_message': bool(result.get('message')),
            'redirect_message': result.get('redirect_message')
        }
        
        for key, value in success_indicators.items():
            if value:
                print_success(f"{key}: {value}")
            else:
                print_error(f"{key}: {value}")
        
        # Check if message contains risk analysis menu
        message = result.get('message', '')
        if 'risk analysis' in message.lower() or 'what would you like' in message.lower():
            print_success("Risk analysis menu detected in response!")
            print_info(f"Message preview: {message[:200]}...")
        else:
            print_error("Risk analysis menu NOT found in response")
            print_info(f"Message: {message[:500]}")
        
        # Determine overall success
        transition_successful = (
            result.get('exit_data_analysis_mode') == True or
            result.get('trigger_analysis') == True or
            'risk analysis' in message.lower()
        )
        
        print("\n" + "="*60)
        if transition_successful:
            print(f"{GREEN}✓✓✓ TEST PASSED! ✓✓✓{RESET}")
            print(f"{GREEN}TPR to risk analysis transition is working correctly!{RESET}")
            print("="*60)
            return True
        else:
            print(f"{RED}✗✗✗ TEST FAILED! ✗✗✗{RESET}")
            print(f"{RED}Transition did not occur as expected{RESET}")
            print("="*60)
            print("\nFull response for debugging:")
            print(json.dumps(result, indent=2))
            return False
            
    except requests.exceptions.Timeout:
        print_error("Request timed out - server may be slow or unresponsive")
        return False
    except requests.exceptions.ConnectionError as e:
        print_error(f"Connection error: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print(f"{BLUE}Starting TPR Transition Test Suite{RESET}")
    print(f"Testing against AWS production environment")
    
    success = test_tpr_transition()
    
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Test Suite Complete{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    
    if success:
        print(f"{GREEN}Result: ALL TESTS PASSED{RESET}")
        sys.exit(0)
    else:
        print(f"{RED}Result: TESTS FAILED{RESET}")
        sys.exit(1)