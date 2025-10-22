#!/usr/bin/env python3
"""
Test helper for simulating file uploads and testing Arena vs Tools mode routing.
Tests the session flag synchronization fix.
"""

import os
import sys
import json
import time
import shutil
import requests
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:8000"
SESSION_ID = None  # Will be set after login

def login():
    """Login and get session"""
    global SESSION_ID
    
    # Login to get a session
    response = requests.post(f"{BASE_URL}/api/login", json={
        "username": "test_user",
        "email": "test@example.com"
    })
    
    if response.status_code == 200:
        data = response.json()
        SESSION_ID = data.get('session_id')
        print(f"✓ Logged in with session: {SESSION_ID}")
        return response.cookies
    else:
        print(f"✗ Login failed: {response.status_code}")
        sys.exit(1)

def simulate_file_placement(cookies):
    """Simulate files being placed directly in upload folder (bypassing upload endpoint)"""
    if not SESSION_ID:
        print("✗ No session ID available")
        return False
    
    upload_dir = f"instance/uploads/{SESSION_ID}"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Create a dummy CSV file
    csv_path = f"{upload_dir}/test_data.csv"
    with open(csv_path, 'w') as f:
        f.write("WardName,Population,Cases\n")
        f.write("Ward1,1000,10\n")
        f.write("Ward2,2000,25\n")
        f.write("Ward3,1500,15\n")
    
    # Create a dummy shapefile (just a marker file for testing)
    shp_path = f"{upload_dir}/test_shapefile.shp"
    with open(shp_path, 'w') as f:
        f.write("dummy shapefile content")
    
    print(f"✓ Placed files in {upload_dir}")
    return True

def test_general_question(cookies, question="What is malaria?"):
    """Test a general question that should trigger Arena mode"""
    print(f"\n🎯 Testing general question: '{question}'")
    
    response = requests.post(
        f"{BASE_URL}/send_message_streaming",
        json={"message": question, "session_id": SESSION_ID},
        cookies=cookies,
        stream=True
    )
    
    if response.status_code == 200:
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        if data.get('arena_mode'):
                            print(f"✓ Arena mode activated")
                            print(f"  - Model A response: {data.get('response_a', '')[:100]}...")
                            print(f"  - Model B response: {data.get('response_b', '')[:100]}...")
                            return True
                        elif data.get('needs_clarification'):
                            print(f"⚠ Clarification requested: {data.get('message')}")
                            return 'clarification'
                        elif data.get('done'):
                            print(f"✗ Single response (not Arena): {data.get('content', '')[:100]}...")
                            return False
                    except json.JSONDecodeError:
                        pass
    else:
        print(f"✗ Request failed: {response.status_code}")
    
    return False

def test_data_question(cookies, question="Analyze my data for high risk areas"):
    """Test a data-related question that should trigger Tools mode"""
    print(f"\n🎯 Testing data question: '{question}'")
    
    response = requests.post(
        f"{BASE_URL}/send_message_streaming",
        json={"message": question, "session_id": SESSION_ID},
        cookies=cookies,
        stream=True
    )
    
    if response.status_code == 200:
        tools_used = []
        content = ""
        arena_mode = False
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        if data.get('arena_mode'):
                            arena_mode = True
                            print(f"⚠ Arena mode activated (unexpected for data question)")
                            return False
                        if data.get('tools_used'):
                            tools_used.extend(data['tools_used'])
                        if data.get('content'):
                            content += data['content']
                        if data.get('needs_clarification'):
                            print(f"⚠ Clarification requested: {data.get('message')}")
                            return 'clarification'
                    except json.JSONDecodeError:
                        pass
        
        if tools_used:
            print(f"✓ Tools mode activated")
            print(f"  - Tools used: {tools_used}")
            print(f"  - Response: {content[:200]}...")
            return True
        else:
            print(f"✗ No tools used (response: {content[:100]}...)")
            return False
    else:
        print(f"✗ Request failed: {response.status_code}")
    
    return False

def test_clarification_flow(cookies):
    """Test the clarification flow for ambiguous requests"""
    print(f"\n🎯 Testing clarification flow with ambiguous request")
    
    # Send ambiguous message
    response = requests.post(
        f"{BASE_URL}/send_message_streaming",
        json={"message": "Show me the results", "session_id": SESSION_ID},
        cookies=cookies,
        stream=True
    )
    
    if response.status_code == 200:
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        if data.get('needs_clarification'):
                            print(f"✓ Clarification requested")
                            print(f"  - Message: {data.get('message')}")
                            print(f"  - Options: {data.get('options')}")
                            
                            # Respond with Tools option
                            print("\n  Responding with 'Analyze my uploaded data'...")
                            response2 = requests.post(
                                f"{BASE_URL}/send_message_streaming",
                                json={"message": "Analyze my uploaded data", "session_id": SESSION_ID},
                                cookies=cookies,
                                stream=True
                            )
                            
                            tools_used = []
                            for line2 in response2.iter_lines():
                                if line2:
                                    line2_str = line2.decode('utf-8')
                                    if line2_str.startswith('data: '):
                                        try:
                                            data2 = json.loads(line2_str[6:])
                                            if data2.get('tools_used'):
                                                tools_used.extend(data2['tools_used'])
                                        except json.JSONDecodeError:
                                            pass
                            
                            if tools_used:
                                print(f"  ✓ Tools mode activated after clarification")
                                print(f"    - Tools: {tools_used}")
                                return True
                            else:
                                print(f"  ✗ No tools activated after clarification")
                                return False
                    except json.JSONDecodeError:
                        pass
    
    return False

def cleanup_test_files():
    """Clean up test files"""
    if SESSION_ID:
        upload_dir = f"instance/uploads/{SESSION_ID}"
        if os.path.exists(upload_dir):
            shutil.rmtree(upload_dir)
            print(f"✓ Cleaned up {upload_dir}")

def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Upload Simulation and Intent Routing")
    print("=" * 60)
    
    # Login
    cookies = login()
    
    # Simulate file placement (bypassing upload endpoint)
    print("\n📁 Simulating direct file placement (testing session sync fix)")
    simulate_file_placement(cookies)
    
    # Test 1: General question should use Arena
    result1 = test_general_question(cookies, "What causes malaria?")
    
    # Test 2: Data question should use Tools (with synced session flags)
    time.sleep(1)  # Small delay to ensure session is synced
    result2 = test_data_question(cookies, "What are the high risk areas in my data?")
    
    # Test 3: Ambiguous question should trigger clarification
    result3 = test_clarification_flow(cookies)
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    tests = [
        ("General question → Arena mode", result1 == True),
        ("Data question → Tools mode", result2 == True),
        ("Ambiguous → Clarification → Tools", result3 == True)
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for name, result in tests:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    # Cleanup
    cleanup_test_files()
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)