#!/usr/bin/env python
"""
Simple test for TPR workflow without file upload
Assumes data is already uploaded or uses mock session
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"

def test_tpr_chat_flow():
    """Test TPR workflow through chat only."""
    
    print("="*60)
    print("Testing TPR Workflow - Chat Only")
    print("="*60)
    
    # Use a known session with data already uploaded
    session_id = 'test_tpr_dynamic'
    
    # Step 1: Initial greeting
    print("\n1. Initial interaction...")
    response = requests.post(
        f"{BASE_URL}/api/v1/data-analysis/chat",
        json={
            'message': 'I have uploaded TPR data from Nigeria with states like Adamawa, Kwara, and Osun',
            'session_id': session_id
        },
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Failed: {response.status_code}")
        return False
    
    result = response.json()
    print(f"✅ Success: {result.get('success')}")
    
    # Step 2: Request TPR calculation
    print("\n2. Requesting TPR calculation...")
    response = requests.post(
        f"{BASE_URL}/api/v1/data-analysis/chat",
        json={
            'message': 'I want you to guide me through the TPR calculation',
            'session_id': session_id
        },
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Failed: {response.status_code}")
        return False
    
    result = response.json()
    message = result.get('message', '')
    
    # Check if asking for state
    if "state" in message.lower() or "adamawa" in message.lower():
        print("✅ State selection requested")
        
        # Check for contextual info
        if any(word in message.lower() for word in ['facilities', 'records', 'tests']):
            print("✅ Contextual statistics provided")
        else:
            print("⚠️ No contextual statistics")
    
    # Step 3: Select state
    print("\n3. Selecting state: Adamawa...")
    response = requests.post(
        f"{BASE_URL}/api/v1/data-analysis/chat",
        json={
            'message': 'Adamawa',
            'session_id': session_id
        },
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Failed: {response.status_code}")
        return False
    
    result = response.json()
    message = result.get('message', '')
    
    # Should ask for facility level
    if "facility" in message.lower():
        print("✅ Facility level selection requested")
    elif "confirm" in message.lower():
        print("❌ AMNESIA: Asking for confirmation")
        return False
    
    # Step 4: Select facility level
    print("\n4. Selecting facility: All facilities...")
    response = requests.post(
        f"{BASE_URL}/api/v1/data-analysis/chat",
        json={
            'message': 'all facilities',
            'session_id': session_id
        },
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Failed: {response.status_code}")
        return False
    
    result = response.json()
    message = result.get('message', '')
    
    # Should ask for age group
    if "age" in message.lower():
        print("✅ Age group selection requested")
        
        # Should NOT ask for test method
        if "method" in message.lower() and ("rdt" in message.lower() or "microscopy" in message.lower()):
            print("❌ ERROR: Asking for test method")
            return False
    
    # Step 5: Select age group
    print("\n5. Selecting age group: Under 5...")
    response = requests.post(
        f"{BASE_URL}/api/v1/data-analysis/chat",
        json={
            'message': 'under 5',
            'session_id': session_id
        },
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Failed: {response.status_code}")
        return False
    
    result = response.json()
    message = result.get('message', '')
    
    # Should start calculating
    if any(word in message.lower() for word in ['calculating', 'complete', 'analysis', 'tpr']):
        print("✅ TPR calculation started")
    elif "method" in message.lower():
        print("❌ ERROR: Still asking for test method")
        return False
    elif "confirm" in message.lower():
        print("❌ AMNESIA: Asking for confirmation")
        return False
    
    print("\n" + "="*60)
    print("✅ TPR WORKFLOW TEST PASSED")
    print("="*60)
    return True

if __name__ == "__main__":
    success = test_tpr_chat_flow()
    if not success:
        print("\n❌ Test failed")
