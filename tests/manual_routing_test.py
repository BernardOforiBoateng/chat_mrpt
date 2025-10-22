#!/usr/bin/env python3
"""
Manual test to verify routing behavior with actual API calls.
Tests the key problematic cases from the browser console.
"""

import requests
import json
import uuid

# Configuration
BASE_URL = "https://d225ar6c86586s.cloudfront.net"
session_id = str(uuid.uuid4())

def test_message(message, endpoint="/api/chat"):
    """Test a single message and print the response."""
    
    print(f"\n{'='*60}")
    print(f"Testing: {message}")
    print(f"Session: {session_id}")
    print(f"Endpoint: {endpoint}")
    print('='*60)
    
    url = f"{BASE_URL}{endpoint}"
    
    # Prepare request
    payload = {
        'message': message,
        'session_id': session_id
    }
    
    # Add session flags to simulate uploaded data
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'session={session_id}; csv_loaded=true; analysis_complete=true'
    }
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # Try to detect which mode was used
            response_text = response.text.lower()
            
            print(f"Response Length: {len(response_text)} chars")
            
            # Check for Arena indicators
            if any(word in response_text for word in ['arena', 'llama3', 'mistral', 'phi3', 'comparing']):
                print("✅ Detected: ARENA MODE")
            # Check for Tool indicators  
            elif any(word in response_text for word in ['analysis', 'vulnerability', 'pca', 'composite', 'quality', 'ranking']):
                print("✅ Detected: TOOLS MODE")
            else:
                print("❓ Mode: UNCLEAR")
            
            # Print first 500 chars of response
            print(f"\nFirst 500 chars of response:")
            print(response_text[:500])
            
        else:
            print(f"❌ Error: Status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def main():
    print("\n" + "="*60)
    print("MANUAL ROUTING TEST")
    print("Testing problematic cases from browser console")
    print("="*60)
    
    # Test critical cases that were failing
    test_cases = [
        # These SHOULD go to tools (with data uploaded)
        ("Run the malaria risk analysis", "Should route to TOOLS"),
        ("Check data quality", "Should route to TOOLS"),
        ("plot vulnerability map", "Should route to TOOLS"),
        ("show ward rankings", "Should route to TOOLS"),
        
        # These SHOULD go to arena (general questions)
        ("What is malaria?", "Should route to ARENA"),
        ("How does climate affect mosquitoes?", "Should route to ARENA"),
    ]
    
    # First, try to find the correct endpoint
    print("\nTesting different endpoint paths...")
    for endpoint in ["/send_message", "/send_message_streaming", "/api/v1/data-analysis/chat"]:
        print(f"\nTrying endpoint: {endpoint}")
        url = f"{BASE_URL}{endpoint}"
        try:
            response = requests.post(
                url,
                json={'message': 'test', 'session_id': session_id},
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                print(f"  ✅ Found working endpoint: {endpoint}")
                working_endpoint = endpoint
                break
        except Exception as e:
            print(f"  Error: {e}")
    else:
        print("\n❌ No working endpoint found!")
        working_endpoint = "/send_message"  # Try default anyway
    
    # Now test the actual messages
    print(f"\nUsing endpoint: {working_endpoint}")
    
    for message, expected in test_cases:
        print(f"\n{'='*60}")
        print(f"Test: {message}")
        print(f"Expected: {expected}")
        test_message(message, working_endpoint)
        
        # Small delay between tests
        import time
        time.sleep(1)

if __name__ == "__main__":
    main()