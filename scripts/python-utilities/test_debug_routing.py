#!/usr/bin/env python3
"""
Test routing with debug logging to identify exact failure points
"""

import requests
import json
import time

def test_debug_routing():
    """Test routing to see debug logs"""

    base_url = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"

    print("=" * 80)
    print("DEBUG ROUTING TEST")
    print("=" * 80)

    # Test cases that should route to tools but go to Arena
    test_cases = [
        ("Plot me the map distribution for the evi variable", "Should route to TOOLS"),
        ("Tell me about the variables in my data", "Should route to TOOLS"),
        ("run malaria risk analysis", "Should route to TOOLS"),
    ]

    print("\nSending test messages to trigger debug logs...")
    print("-" * 60)

    # Create a session with data indicated
    session_headers = {}

    for message, expected in test_cases:
        print(f"\n📝 Test: '{message}'")
        print(f"   Expected: {expected}")

        try:
            # Send request to the streaming endpoint (which frontend uses)
            response = requests.post(
                f"{base_url}/send_message_streaming",
                json={
                    "message": message,
                    "has_data": True,  # Indicate data exists
                    "session_id": "debug_test_session"
                },
                headers={"Content-Type": "application/json"},
                cookies=session_headers,
                timeout=15,
                stream=True  # Enable streaming
            )

            # Save cookies for session persistence
            if response.cookies:
                session_headers = response.cookies

            if response.status_code == 200:
                data = response.json()

                # Check response
                response_text = data.get('response', '').lower()
                workflow = data.get('workflow', '')
                tools_used = data.get('tools_used', [])

                # Log result
                if tools_used:
                    print(f"   → Routed to: TOOLS ✅")
                elif 'arena' in workflow.lower():
                    print(f"   → Routed to: ARENA ❌")
                elif 'clarification' in response_text:
                    print(f"   → Routed to: NEEDS_CLARIFICATION ⚠️")
                else:
                    print(f"   → Unknown routing")

                print(f"   Response preview: {response_text[:100]}...")

            else:
                print(f"   ❌ Error: HTTP {response.status_code}")
                if response.text:
                    print(f"   Error details: {response.text[:200]}")

        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

        time.sleep(2)  # Give time between requests

    print("\n" + "=" * 80)
    print("CHECK SERVER LOGS FOR DEBUG OUTPUT")
    print("Run on server: sudo journalctl -u chatmrpt -n 100 | grep CRITICAL")
    print("=" * 80)

if __name__ == "__main__":
    test_debug_routing()