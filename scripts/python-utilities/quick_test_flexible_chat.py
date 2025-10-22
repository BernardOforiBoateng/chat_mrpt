#!/usr/bin/env python3
"""Quick test of flexible chat functionality"""

import requests
import time

BASE_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"

def test_greeting():
    """Test greeting without data"""
    print("\n1. Testing greeting in Data Analysis tab (should work without data):")
    print("-" * 60)
    
    response = requests.post(
        f"{BASE_URL}/send_message",
        json={
            'message': 'Hello, who are you?',
            'session_id': f'test_greeting_{int(time.time())}',
            'is_data_analysis': True,
            'tab_context': 'data-analysis'
        },
        timeout=10
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result.get('success', False)}")
        response_text = result.get('response', result.get('message', ''))
        print(f"Response: {response_text[:200]}...")
        
        # Check if it's asking for upload
        if 'upload' in response_text.lower() and 'data' in response_text.lower():
            print("❌ FAILED: Still requiring data upload for greeting")
            return False
        else:
            print("✅ PASSED: Greeting works without data")
            return True
    else:
        print(f"❌ ERROR: {response.text[:200]}")
        return False

def test_malaria_knowledge():
    """Test malaria knowledge question"""
    print("\n2. Testing malaria knowledge question (should work without data):")
    print("-" * 60)
    
    response = requests.post(
        f"{BASE_URL}/send_message",
        json={
            'message': 'What is malaria?',
            'session_id': f'test_knowledge_{int(time.time())}',
            'is_data_analysis': True,
            'tab_context': 'data-analysis'
        },
        timeout=10
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result.get('success', False)}")
        response_text = result.get('response', result.get('message', ''))
        print(f"Response: {response_text[:200]}...")
        
        # Check if it's providing malaria info
        if 'malaria' in response_text.lower() and 'upload' not in response_text.lower():
            print("✅ PASSED: Malaria knowledge works without data")
            return True
        else:
            print("❌ FAILED: Not providing malaria information properly")
            return False
    else:
        print(f"❌ ERROR: {response.text[:200]}")
        return False

def test_analysis_request():
    """Test analysis request without data"""
    print("\n3. Testing analysis request without data (should guide to upload):")
    print("-" * 60)
    
    response = requests.post(
        f"{BASE_URL}/send_message",
        json={
            'message': 'Analyze my data',
            'session_id': f'test_analysis_{int(time.time())}',
            'is_data_analysis': True,
            'tab_context': 'data-analysis'
        },
        timeout=10
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result.get('success', False)}")
        response_text = result.get('response', result.get('message', ''))
        print(f"Response: {response_text[:200]}...")
        
        # Should guide to upload
        if 'upload' in response_text.lower() or 'csv' in response_text.lower():
            print("✅ PASSED: Properly guides to upload for analysis")
            return True
        else:
            print("❌ FAILED: Not guiding to upload properly")
            return False
    else:
        print(f"❌ ERROR: {response.text[:200]}")
        return False

def main():
    print("\n" + "="*70)
    print("QUICK TEST: Flexible Chat Functionality")
    print("="*70)
    print(f"Testing: {BASE_URL}")
    
    results = []
    
    # Test 1: Greeting
    results.append(test_greeting())
    time.sleep(2)
    
    # Test 2: Malaria knowledge
    results.append(test_malaria_knowledge())
    time.sleep(2)
    
    # Test 3: Analysis request
    results.append(test_analysis_request())
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ ALL TESTS PASSED - Flexible chat is working!")
    elif passed > 0:
        print("⚠️ PARTIAL SUCCESS - Some features working")
    else:
        print("❌ ALL TESTS FAILED - System needs attention")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)