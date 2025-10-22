#!/usr/bin/env python3
"""Test to simulate the browser session flow"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:5015"  # Using the current port

def simulate_browser_flow():
    """Simulate the exact flow from the browser"""
    
    session = requests.Session()
    
    # 1. Initialize session (like opening the page)
    print("1. Opening homepage...")
    response = session.get(f"{BASE_URL}/")
    print(f"   Status: {response.status_code}")
    
    # 2. Upload files (simulate the upload)
    print("\n2. Simulating file upload...")
    # In real browser, this would be file upload, but we'll simulate with message
    
    # 3. Send the exact message: "Run malaria risk analysis to rank wards"
    print("\n3. Sending: 'Run malaria risk analysis to rank wards'")
    
    response = session.post(
        f"{BASE_URL}/send_message_streaming",
        json={'message': 'Run malaria risk analysis to rank wards'},
        headers={'Content-Type': 'application/json'},
        stream=True
    )
    
    tools_used = []
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                try:
                    chunk = json.loads(line_str[6:])
                    if chunk.get('tools_used'):
                        tools_used.extend(chunk['tools_used'])
                        print(f"   Tools used: {chunk['tools_used']}")
                except:
                    pass
    
    print(f"\n   Total tools used: {tools_used}")
    
    # 4. Check session state
    print("\n4. Checking session state...")
    response = session.get(f"{BASE_URL}/debug/session_state")
    state = response.json()
    print(f"   Analysis complete: {state['session_state']['analysis_complete']}")
    
    return state

if __name__ == "__main__":
    simulate_browser_flow()