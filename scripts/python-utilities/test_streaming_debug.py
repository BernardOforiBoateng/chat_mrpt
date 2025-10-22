#!/usr/bin/env python3
"""
Test routing with the streaming endpoint to identify exact failure points
"""

import requests
import json
import time

def test_streaming_debug():
    """Test routing to see debug logs with streaming endpoint"""

    base_url = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"

    print("=" * 80)
    print("STREAMING ENDPOINT DEBUG TEST")
    print("=" * 80)

    # Test cases that should route to tools but go to Arena
    test_cases = [
        ("hi", "Should route to ARENA (greeting)"),
        ("Plot me the map distribution for the evi variable", "Should route to TOOLS"),
        ("Tell me about the variables in my data", "Should route to TOOLS"),
        ("run malaria risk analysis", "Should route to TOOLS"),
    ]

    print("\nSending test messages to streaming endpoint...")
    print("-" * 60)

    # Create a session
    session = requests.Session()

    for message, expected in test_cases:
        print(f"\n📝 Test: '{message}'")
        print(f"   Expected: {expected}")

        try:
            # Send request to the streaming endpoint
            response = session.post(
                f"{base_url}/send_message_streaming",
                json={
                    "message": message,
                },
                headers={"Content-Type": "application/json"},
                timeout=15,
                stream=True
            )

            if response.status_code == 200:
                # Read streaming response
                full_response = ""
                workflow = ""

                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            try:
                                data = json.loads(line_str[6:])  # Remove "data: " prefix
                                if 'content' in data:
                                    full_response += data['content']
                                if 'workflow' in data:
                                    workflow = data['workflow']
                                if 'arena_battle' in data:
                                    workflow = 'arena'
                            except json.JSONDecodeError:
                                pass

                # Determine routing
                if 'arena' in workflow.lower() or 'arena' in full_response.lower()[:200]:
                    print(f"   → Routed to: ARENA {'✅' if 'ARENA' in expected else '❌'}")
                elif workflow == 'tools' or 'tools' in workflow:
                    print(f"   → Routed to: TOOLS {'✅' if 'TOOLS' in expected else '❌'}")
                else:
                    print(f"   → Unknown routing (workflow: {workflow})")

                print(f"   Response preview: {full_response[:100]}...")

            else:
                print(f"   ❌ Error: HTTP {response.status_code}")
                print(f"   Response: {response.text[:200]}")

        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

        time.sleep(2)

    print("\n" + "=" * 80)
    print("CHECK SERVER LOGS FOR DEBUG OUTPUT:")
    print("ssh to server and run:")
    print("sudo journalctl -u chatmrpt --since '2 minutes ago' | grep -E 'CRITICAL|route_with_mistral'")
    print("=" * 80)

if __name__ == "__main__":
    test_streaming_debug()