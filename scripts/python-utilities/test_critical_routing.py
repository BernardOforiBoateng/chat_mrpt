#!/usr/bin/env python3
"""
Test the specific routing cases that were failing
"""

import requests
import json
import time

def test_critical_routes():
    """Test the two specific failing routes"""

    base_url = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"

    print("=" * 80)
    print("TESTING CRITICAL ROUTING FIXES")
    print("=" * 80)

    # Critical test cases that were failing
    test_cases = [
        ("Plot me the map distribution for the evi variable", "Should route to TOOLS"),
        ("Tell me about the variables in my data", "Should route to TOOLS"),
        ("run malaria risk analysis", "Should route to TOOLS (without 'the')"),
        ("hi", "Should route to ARENA"),
    ]

    print("\nTesting with session that has data...")
    print("-" * 60)

    # First, let's create a session and indicate data exists
    # We'll use a test message that establishes context

    for message, expected in test_cases:
        print(f"\n📝 Test: '{message}'")
        print(f"   Expected: {expected}")

        try:
            # Send request
            response = requests.post(
                f"{base_url}/send_message",
                json={
                    "message": message,
                    # Simulate having data by including session context
                    "has_data": True
                },
                headers={"Content-Type": "application/json"},
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()

                # Analyze the response to determine routing
                response_text = data.get('response', '').lower()
                tools_used = data.get('tools_used', [])
                workflow = data.get('workflow', '')

                # Determine actual routing
                if tools_used:
                    actual = "TOOLS (executed)"
                elif 'arena' in workflow.lower():
                    actual = "ARENA"
                elif 'please upload' in response_text or 'provide data' in response_text:
                    actual = "ARENA (asking for data)"
                elif 'arena comparison' in response_text:
                    actual = "ARENA (comparison mode)"
                else:
                    # Check response content
                    if any(word in response_text for word in ['hello', 'hi', 'greet', 'assist']):
                        actual = "ARENA (greeting)"
                    else:
                        actual = "UNKNOWN"

                # Check if it matches expected
                matches = False
                if "TOOLS" in expected and "TOOLS" in actual:
                    matches = True
                elif "ARENA" in expected and "ARENA" in actual:
                    matches = True

                status = "✅" if matches else "❌"
                print(f"   Actual: {actual} {status}")

                if not matches:
                    print(f"   Response preview: {response_text[:150]}...")

            else:
                print(f"   ❌ Error: HTTP {response.status_code}")

        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

        time.sleep(1)  # Be nice to the server

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("Note: Without actual uploaded data, some routes may still default to Arena")
    print("The key is whether the improved fallback logic catches visualization/data requests")
    print("=" * 80)

if __name__ == "__main__":
    test_critical_routes()