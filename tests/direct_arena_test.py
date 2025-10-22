#!/usr/bin/env python3
"""
Direct Arena Test - Test the actual Arena response
"""

import requests
import json
import time

def test_arena_directly():
    """Test Arena endpoint directly"""

    print("\n🔬 DIRECT ARENA TEST")
    print("="*50)

    url = "https://d225ar6c86586s.cloudfront.net/send_message"

    # Test messages
    tests = [
        ("Hello ChatMRPT", "identity"),
        ("What is malaria?", "knowledge"),
        ("I have data from Lagos", "context_setup"),
        ("What challenges are there?", "context_recall")
    ]

    session_id = f"direct-test-{int(time.time())}"

    for message, test_type in tests:
        print(f"\n📤 Test: {test_type}")
        print(f"   Message: {message}")

        try:
            # Send with streaming
            response = requests.post(
                url,
                json={"message": message, "session_id": session_id},
                headers={"Content-Type": "application/json"},
                timeout=20,
                stream=True
            )

            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                # Read first 500 chars of stream
                content = ""
                arena_detected = False
                models = {}

                for i, line in enumerate(response.iter_lines()):
                    if i > 20:  # Limit lines to prevent hanging
                        break
                    if line:
                        decoded = line.decode('utf-8')
                        content += decoded[:100] + "\n"

                        # Check for arena markers
                        if "arena_mode" in decoded:
                            arena_detected = True
                        if "model_a" in decoded:
                            try:
                                data = json.loads(decoded[6:])
                                models['a'] = data.get('model_a')
                                models['b'] = data.get('model_b')
                            except:
                                pass

                print(f"   ✅ Response received")
                print(f"   Arena detected: {arena_detected}")
                if models:
                    print(f"   Models: {models}")
                print(f"   Content preview: {content[:200]}...")

            else:
                print(f"   ❌ HTTP {response.status_code}")

        except requests.Timeout:
            print(f"   ⏱️ Timeout after 20s")
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}")

        time.sleep(2)  # Rate limit

    print("\n" + "="*50)
    print("Test completed")

if __name__ == "__main__":
    test_arena_directly()