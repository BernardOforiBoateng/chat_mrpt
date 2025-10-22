#!/usr/bin/env python3
"""
Test the full flow: simulate TPR workflow completion then test tool routing
This mimics what happens when a user exits data analysis mode
"""

import requests
import json
import time

def test_full_flow():
    """Test the complete flow from data upload through tool requests"""

    base_url = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"

    print("=" * 80)
    print("FULL FLOW TEST: TPR → Exit Data Analysis → Tool Requests")
    print("=" * 80)

    # Create a session to maintain cookies
    session = requests.Session()

    # Step 1: Simulate session with data loaded (as if TPR workflow completed)
    print("\n📊 Step 1: Setting up session with data...")

    # First, send a message to establish session
    response = session.post(
        f"{base_url}/send_message_streaming",
        json={"message": "hi"},
        headers={"Content-Type": "application/json"},
        stream=True
    )

    # Read streaming response to establish session
    for line in response.iter_lines():
        if line:
            pass  # Just consume the response

    print("   ✓ Session established")

    # Step 2: Test tool requests that should work after data is loaded
    print("\n📊 Step 2: Testing tool requests after data load...")
    print("-" * 60)

    test_cases = [
        ("Plot me the map distribution for the evi variable", "Variable distribution visualization"),
        ("Tell me about the variables in my data", "Data summary request"),
        ("Run the risk analysis", "Analysis execution"),
        ("Show me the top 5 high-risk wards", "Results query"),
        ("Plan ITN distribution for 1000 nets", "ITN planning"),
    ]

    for message, description in test_cases:
        print(f"\n📝 Test: {description}")
        print(f"   Message: '{message}'")

        try:
            # Send request
            response = session.post(
                f"{base_url}/send_message_streaming",
                json={"message": message},
                headers={"Content-Type": "application/json"},
                stream=True,
                timeout=20
            )

            if response.status_code == 200:
                # Read streaming response
                full_response = ""
                workflow = ""
                tools_used = []

                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            try:
                                data = json.loads(line_str[6:])
                                if 'content' in data:
                                    full_response += data['content']
                                if 'workflow' in data:
                                    workflow = data['workflow']
                                if 'tools_used' in data:
                                    tools_used = data['tools_used']
                            except json.JSONDecodeError:
                                pass

                # Analyze response
                response_lower = full_response.lower()

                # Determine routing
                if tools_used:
                    print(f"   ✅ Routed to TOOLS: {tools_used}")
                elif 'upload' in response_lower and 'dataset' in response_lower:
                    print(f"   ❌ Got 'upload data' response (should have routed to tools)")
                elif 'arena' in workflow.lower():
                    print(f"   ❌ Routed to Arena (should have routed to tools)")
                else:
                    print(f"   ⚠️  Unknown routing")

                # Show response preview
                print(f"   Response preview: {full_response[:150]}...")

            else:
                print(f"   ❌ Error: HTTP {response.status_code}")

        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

        time.sleep(2)

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("\nExpected: All requests should route to tools after data is loaded")
    print("If requests still return 'upload data', the session flags aren't persisting")
    print("=" * 80)

if __name__ == "__main__":
    test_full_flow()