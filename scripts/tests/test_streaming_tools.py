#!/usr/bin/env python3
"""Test if streaming endpoint properly tracks tools_used"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"

def test_streaming_tools():
    """Test if tools_used is properly tracked in streaming"""
    
    session = requests.Session()
    
    # 1. Initialize session and upload test data
    print("1. Initializing session...")
    response = session.get(f"{BASE_URL}/")
    
    # 2. Upload test files (simulate data upload)
    print("\n2. Simulating data upload...")
    # This would normally be done through file upload, but we'll simulate with message
    response = session.post(
        f"{BASE_URL}/send_message",
        json={'message': '__DATA_UPLOADED__'},
        headers={'Content-Type': 'application/json'}
    )
    print(f"Data upload simulation: {response.status_code}")
    
    # 3. Send analysis request via streaming
    print("\n3. Sending analysis request via streaming...")
    response = session.post(
        f"{BASE_URL}/send_message_streaming",
        json={'message': 'Run malaria risk analysis to rank wards'},
        headers={'Content-Type': 'application/json'},
        stream=True
    )
    
    tools_used = []
    final_chunk = None
    
    print("Streaming response chunks:")
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                try:
                    chunk = json.loads(line_str[6:])
                    if chunk.get('tools_used'):
                        tools_used.extend(chunk['tools_used'])
                        print(f"  - Tools in chunk: {chunk['tools_used']}")
                    if chunk.get('done'):
                        final_chunk = chunk
                        print(f"  - Final chunk received with done=True")
                        if chunk.get('tools_used'):
                            print(f"  - Final chunk tools: {chunk['tools_used']}")
                except json.JSONDecodeError:
                    pass
    
    print(f"\nTotal tools tracked: {tools_used}")
    
    # 4. Check session state
    print("\n4. Checking session state after streaming...")
    response = session.get(f"{BASE_URL}/debug/session_state")
    state = response.json()
    print(f"Session state: {json.dumps(state, indent=2)}")
    
    # 5. Verify analysis_complete
    if state['session_state']['analysis_complete']:
        print("\n✅ SUCCESS: analysis_complete is True!")
    else:
        print("\n❌ FAILURE: analysis_complete is still False!")
        print(f"Tools were used: {tools_used}")
    
    return state['session_state']['analysis_complete']

if __name__ == "__main__":
    # Wait a bit for Flask to be ready
    time.sleep(2)
    test_streaming_tools()