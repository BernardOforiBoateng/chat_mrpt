#!/usr/bin/env python3
"""
Quick routing test for AWS - Testing key scenarios
Following CLAUDE.md testing guidelines
"""
import requests
import json
import time
import sys

# Test against CloudFront
BASE_URL = "https://d225ar6c86586s.cloudfront.net"

def test_routing(message: str, test_name: str) -> dict:
    """Test a single message"""
    print(f"\n{'='*50}")
    print(f"Test: {test_name}")
    print(f"Message: '{message}'")
    
    try:
        response = requests.post(
            f"{BASE_URL}/send_message",
            json={
                "message": message,
                "session_id": f"test-{int(time.time())}"
            },
            timeout=10
        )
        
        result = response.json()
        
        # Check what type of response we got
        if result.get("needs_clarification"):
            response_type = "❌ CLARIFICATION PROMPT"
        elif result.get("arena_mode"):
            response_type = "✅ ARENA MODE"
        elif result.get("tools_used"):
            response_type = "✅ TOOLS USED"
        elif result.get("response"):
            # Check if it's a greeting or conversation
            resp_text = str(result.get("response", "")).lower()
            if "i need more information" in resp_text:
                response_type = "❌ CLARIFICATION (embedded)"
            else:
                response_type = "✅ CONVERSATIONAL"
        else:
            response_type = "❓ UNKNOWN"
        
        print(f"Result: {response_type}")
        
        # Show preview of response
        if result.get("response"):
            preview = str(result.get("response"))[:150]
            print(f"Preview: {preview}...")
        
        return {
            "success": "❌" not in response_type,
            "type": response_type,
            "message": message
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return {
            "success": False,
            "type": "ERROR",
            "message": message
        }

def main():
    """Run quick routing tests"""
    print(f"{'#'*50}")
    print(f"# Quick Routing Test on AWS")
    print(f"# URL: {BASE_URL}")
    print(f"{'#'*50}")
    
    tests = [
        ("hey", "Simple greeting - should NOT show clarification"),
        ("hello", "Another greeting - should be conversational"),
        ("thanks", "Small talk - should be conversational"),
        ("what is malaria", "General knowledge - should use Arena"),
        ("ok", "Short response - should NOT clarify"),
        ("analyze", "Ambiguous single word - might clarify or converse"),
    ]
    
    results = []
    for message, test_name in tests:
        result = test_routing(message, test_name)
        results.append(result)
        time.sleep(1)  # Small delay between requests
    
    # Summary
    print(f"\n{'#'*50}")
    print("# SUMMARY")
    print(f"{'#'*50}")
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed < total:
        print("\nFailed tests:")
        for r in results:
            if not r["success"]:
                print(f"  - '{r['message']}': {r['type']}")
    
    # Key checks
    print(f"\n{'#'*50}")
    print("# KEY CHECKS")
    print(f"{'#'*50}")
    
    hey_test = results[0]
    if hey_test["success"]:
        print("✅ 'hey' does NOT trigger clarification - GOOD!")
    else:
        print("❌ 'hey' triggers clarification - NEEDS FIX!")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())