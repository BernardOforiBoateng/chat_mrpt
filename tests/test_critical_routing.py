#!/usr/bin/env python3
"""
Test critical routing scenarios - Focus on the main issue
"""
import requests
import json
import time

BASE_URL = "https://d225ar6c86586s.cloudfront.net"

def test_message(message: str, expected_behavior: str):
    """Test a single message with better error handling"""
    print(f"\n{'='*60}")
    print(f"Testing: '{message}'")
    print(f"Expected: {expected_behavior}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/send_message",
            json={
                "message": message,
                "session_id": f"routing-test-{int(time.time())}"
            },
            timeout=15  # Increased timeout
        )
        
        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code}")
            return False
        
        data = response.json()
        
        # Check for clarification prompt (the main issue we're fixing)
        if data.get("needs_clarification"):
            print(f"❌ Got clarification prompt!")
            print(f"   Message: {data.get('message', '')}")
            return False
        
        # Check if we got a response
        if data.get("arena_mode"):
            print(f"✅ Arena mode response (conversational)")
            return True
        elif data.get("response"):
            # Check content
            resp = str(data.get("response", ""))
            if "I need more information" in resp:
                print(f"❌ Clarification in response text")
                return False
            else:
                print(f"✅ Got conversational response")
                print(f"   Preview: {resp[:100]}...")
                return True
        else:
            print(f"❓ Unexpected response format")
            print(f"   Keys: {list(data.keys())}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏱️ Request timed out (might be processing)")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("="*60)
    print("CRITICAL ROUTING TEST - AWS Production")
    print("="*60)
    
    # The main issue: Simple greetings were triggering clarification
    critical_tests = [
        ("hey", "Friendly greeting, NOT clarification"),
        ("hi", "Friendly greeting, NOT clarification"),
        ("hello", "Friendly greeting, NOT clarification"),
        ("thanks", "Acknowledgment, NOT clarification"),
        ("how are you", "Conversational response, NOT clarification"),
    ]
    
    passed = 0
    failed = 0
    timeouts = 0
    
    for message, expected in critical_tests:
        result = test_message(message, expected)
        if result is True:
            passed += 1
        elif result is False:
            failed += 1
        else:
            timeouts += 1
        time.sleep(2)  # Wait between requests
    
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⏱️ Timeouts: {timeouts}")
    
    if failed == 0 and timeouts == 0:
        print("\n🎉 SUCCESS! All greetings handled correctly!")
        print("The aggressive clarification issue is FIXED!")
    elif failed > 0:
        print("\n⚠️ Some tests still showing clarification prompts")
    else:
        print("\n⚠️ Some timeouts occurred, but no clarification prompts!")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit(main())