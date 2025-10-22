#!/usr/bin/env python3
"""Test session update mechanism"""

import requests
import json

# Base URL for local testing
BASE_URL = "http://127.0.0.1:5000"

def test_session_persistence():
    """Test if session persists across requests"""
    
    # Start a session
    session = requests.Session()
    
    # 1. Check initial session state
    print("1. Checking initial session state...")
    response = session.get(f"{BASE_URL}/debug/session_state")
    print(f"Initial state: {response.json()}")
    initial_session_id = response.json().get('session_id')
    
    # 2. Send a message via streaming endpoint
    print("\n2. Sending test message via streaming...")
    headers = {'Content-Type': 'application/json'}
    data = {'message': 'hello'}
    
    response = session.post(
        f"{BASE_URL}/send_message_streaming", 
        headers=headers,
        json=data,
        stream=True
    )
    
    print("Streaming response received")
    
    # 3. Check session state after streaming
    print("\n3. Checking session state after streaming...")
    response = session.get(f"{BASE_URL}/debug/session_state")
    after_state = response.json()
    print(f"After streaming: {after_state}")
    
    # Verify session ID remained the same
    if after_state.get('session_id') == initial_session_id:
        print(f"\n✅ Session ID persisted: {initial_session_id}")
    else:
        print(f"\n❌ Session ID changed! Initial: {initial_session_id}, After: {after_state.get('session_id')}")
    
    # 4. Test with regular endpoint
    print("\n4. Testing regular endpoint...")
    response = session.post(
        f"{BASE_URL}/send_message",
        headers=headers,
        json=data
    )
    
    print("Regular response received")
    
    # 5. Final session check
    print("\n5. Final session state check...")
    response = session.get(f"{BASE_URL}/debug/session_state")
    final_state = response.json()
    print(f"Final state: {final_state}")
    
    return initial_session_id, after_state.get('session_id'), final_state.get('session_id')

if __name__ == "__main__":
    test_session_persistence()