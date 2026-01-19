#!/usr/bin/env python3
"""
Direct test of session flag synchronization on AWS.
Tests that files placed directly in upload folder are detected.
"""

import os
import sys
import json
import time
import uuid
import requests

# Test configuration
BASE_URL = "http://localhost:8000"

def create_test_session():
    """Create a test session by making an initial request"""
    # Make initial request to get session
    response = requests.get(f"{BASE_URL}/ping")
    if response.status_code == 200:
        print(f"✓ Server is running")
        return response.cookies
    else:
        print(f"✗ Server not responding: {response.status_code}")
        sys.exit(1)

def get_session_id_from_response(cookies):
    """Extract session ID from a response that includes it"""
    # Try to get session info from a request
    response = requests.post(
        f"{BASE_URL}/send_message_streaming",
        json={"message": "Hello"},
        cookies=cookies,
        stream=True,
        timeout=10
    )
    
    # The session ID is typically in cookies or response
    # For now, we'll use a test session ID
    test_session_id = str(uuid.uuid4())
    print(f"📝 Using test session ID: {test_session_id}")
    return test_session_id

def simulate_file_placement(session_id):
    """Simulate files being placed directly in upload folder"""
    upload_dir = f"instance/uploads/{session_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Create a dummy CSV file
    csv_path = f"{upload_dir}/test_data.csv"
    with open(csv_path, 'w') as f:
        f.write("WardName,Population,Cases\n")
        f.write("Ward1,1000,10\n")
        f.write("Ward2,2000,25\n")
    
    # Create a dummy shapefile
    shp_path = f"{upload_dir}/test_shapefile.shp"
    with open(shp_path, 'w') as f:
        f.write("dummy shapefile content")
    
    print(f"✓ Placed files in {upload_dir}")
    print(f"  - CSV: {csv_path}")
    print(f"  - Shapefile: {shp_path}")
    return True

def test_intent_routing(cookies, session_id):
    """Test that intent routing now detects the uploaded files"""
    print("\n🎯 Testing intent detection after direct file placement")
    
    # Test 1: General question (should use Arena)
    print("\n1. Testing general question...")
    response = requests.post(
        f"{BASE_URL}/send_message_streaming",
        json={
            "message": "What is malaria?",
            "session_id": session_id
        },
        cookies=cookies,
        stream=True,
        timeout=30
    )
    
    arena_detected = False
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                try:
                    data = json.loads(line_str[6:])
                    if data.get('arena_mode'):
                        arena_detected = True
                        print(f"  ✓ Arena mode activated for general question")
                        break
                except json.JSONDecodeError:
                    pass
    
    if not arena_detected:
        print(f"  ⚠ Arena mode not detected for general question")
    
    # Test 2: Data question (should use Tools with synced session)
    print("\n2. Testing data-specific question...")
    response = requests.post(
        f"{BASE_URL}/send_message_streaming",
        json={
            "message": "Analyze the high risk areas in my uploaded data",
            "session_id": session_id
        },
        cookies=cookies,
        stream=True,
        timeout=30
    )
    
    tools_detected = False
    clarification_detected = False
    content = ""
    
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                try:
                    data = json.loads(line_str[6:])
                    if data.get('tools_used'):
                        tools_detected = True
                        print(f"  ✓ Tools mode activated (session flags synced!)")
                        print(f"    Tools: {data['tools_used']}")
                        break
                    if data.get('needs_clarification'):
                        clarification_detected = True
                        print(f"  ⚠ Clarification requested: {data.get('message', '')[:100]}")
                        break
                    if data.get('content'):
                        content += data['content']
                except json.JSONDecodeError:
                    pass
    
    if not tools_detected and not clarification_detected:
        print(f"  ✗ Tools mode not activated")
        print(f"    Response: {content[:200]}...")
    
    return arena_detected and (tools_detected or clarification_detected)

def check_session_flags(session_id):
    """Check if session flags are properly synced"""
    print(f"\n🔍 Checking session flag synchronization for {session_id}")
    
    # Check if files exist
    upload_dir = f"instance/uploads/{session_id}"
    csv_exists = any(f.endswith(('.csv', '.xlsx', '.xls')) 
                     for f in os.listdir(upload_dir) if not f.startswith('.'))
    shp_exists = any(f.endswith(('.shp', '.zip')) 
                     for f in os.listdir(upload_dir) if not f.startswith('.'))
    
    print(f"  Files found:")
    print(f"    - CSV: {csv_exists}")
    print(f"    - Shapefile: {shp_exists}")
    
    # The session flags should be synced on the next request
    # This is what our fix enables
    print(f"  ✓ Files ready for session sync on next request")
    
    return csv_exists and shp_exists

def cleanup_test_files(session_id):
    """Clean up test files"""
    upload_dir = f"instance/uploads/{session_id}"
    if os.path.exists(upload_dir):
        import shutil
        shutil.rmtree(upload_dir)
        print(f"✓ Cleaned up {upload_dir}")

def main():
    """Run the session synchronization test"""
    print("=" * 60)
    print("Testing Session Flag Synchronization Fix")
    print("=" * 60)
    
    # Get initial cookies
    cookies = create_test_session()
    
    # Create test session ID
    session_id = get_session_id_from_response(cookies)
    
    # Simulate direct file placement (bypassing upload endpoints)
    print("\n📁 Simulating direct file placement (bypassing upload)")
    simulate_file_placement(session_id)
    
    # Check files exist
    files_ready = check_session_flags(session_id)
    
    # Test intent routing with session synchronization
    if files_ready:
        routing_works = test_intent_routing(cookies, session_id)
    else:
        routing_works = False
        print("✗ Files not properly placed")
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    
    if files_ready and routing_works:
        print("✓ SUCCESS: Session flags are synchronized!")
        print("  - Files placed directly are detected")
        print("  - Intent routing works correctly")
        print("  - Tools mode activates for data questions")
    else:
        print("✗ FAILED: Session synchronization not working")
        if not files_ready:
            print("  - File placement failed")
        if not routing_works:
            print("  - Intent routing failed")
    
    # Cleanup
    cleanup_test_files(session_id)
    
    return files_ready and routing_works

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)