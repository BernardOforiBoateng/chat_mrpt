#!/usr/bin/env python3
"""
Simple test to verify routing is actually using semantic understanding
Tests directly through the web API
"""

import requests
import json
import time

def test_routing_via_api():
    """Test routing through the actual API endpoints"""

    # Use the production URL
    base_url = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"

    print("=" * 80)
    print("SEMANTIC ROUTING TEST VIA API")
    print("=" * 80)

    # Test messages
    test_cases = [
        ("hi", "Greeting"),
        ("run malaria risk analysis", "Analysis WITHOUT 'the'"),
        ("run the malaria risk analysis", "Analysis WITH 'the'"),
        ("create vulnerability map", "Visualization request"),
        ("show me variable distributions", "Distribution request"),
        ("what is malaria", "Knowledge question"),
        ("explain composite score", "Explanation request"),
    ]

    print("\nTesting routing responses...")
    print("-" * 60)

    for message, description in test_cases:
        print(f"\n📝 Test: {description}")
        print(f"   Message: '{message}'")

        try:
            # Send request
            response = requests.post(
                f"{base_url}/send_message",
                json={"message": message},
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                # Check what type of response we got
                if 'tools_used' in data and data['tools_used']:
                    print(f"   → Routed to: TOOLS (used: {data['tools_used']})")
                elif 'arena' in data.get('workflow', '').lower():
                    print(f"   → Routed to: ARENA")
                else:
                    # Analyze response content to infer routing
                    response_text = data.get('response', '').lower()
                    if 'upload' in response_text or 'provide data' in response_text:
                        print(f"   → Response: Asking for data (likely Arena)")
                    elif any(word in response_text for word in ['hello', 'hi', 'greet', 'assist']):
                        print(f"   → Response: Greeting (Arena)")
                    else:
                        print(f"   → Response: {response_text[:100]}...")
            else:
                print(f"   ❌ Error: HTTP {response.status_code}")

        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

        time.sleep(1)  # Be nice to the server

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print("\nNOTE: Without session context (uploaded data), most requests")
    print("will route to Arena. The key test is whether 'run malaria risk")
    print("analysis' works the same as 'run THE malaria risk analysis'")

if __name__ == "__main__":
    test_routing_via_api()