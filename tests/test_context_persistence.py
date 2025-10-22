#!/usr/bin/env python3
"""
Test context persistence across messages
"""

import requests
import json
import time

def test_context_persistence():
    """Test if ChatMRPT remembers previous conversation context"""

    print("\n🔬 CONTEXT PERSISTENCE TEST")
    print("=" * 50)

    url = "https://d225ar6c86586s.cloudfront.net/send_message"
    session_id = f"context-test-{int(time.time())}"

    print(f"Session: {session_id}")
    print(f"Endpoint: {url}")
    print("=" * 50)

    # Test sequence
    tests = [
        ("I'm working with malaria data from Kaduna state", "setup"),
        ("How many facilities did I mention?", "recall_missing"),  # Didn't mention number
        ("Actually I have 250 health facilities", "provide_info"),
        ("What state am I working with?", "recall_state"),  # Should remember Kaduna
        ("How many facilities do I have?", "recall_facilities"),  # Should remember 250
        ("What kind of data am I analyzing?", "recall_type"),  # Should remember malaria
    ]

    context_maintained = 0
    total_recall_tests = 0

    for i, (message, test_type) in enumerate(tests, 1):
        print(f"\n📝 Test {i}: {test_type}")
        print(f"   Message: {message}")

        try:
            response = requests.post(
                url,
                json={"message": message, "session_id": session_id},
                headers={"Content-Type": "application/json"},
                timeout=30,
                stream=True
            )

            if response.status_code == 200:
                # Collect full response
                responses = {'a': '', 'b': ''}

                for line in response.iter_lines():
                    if line:
                        decoded = line.decode('utf-8')
                        if decoded.startswith('data: '):
                            data_str = decoded[6:]
                            if data_str.strip() not in ['[DONE]', '']:
                                try:
                                    data = json.loads(data_str)
                                    if 'delta' in data and 'side' in data:
                                        if data['side'] == 'a':
                                            responses['a'] += data['delta']
                                        elif data['side'] == 'b':
                                            responses['b'] += data['delta']
                                except:
                                    pass

                print("   ✅ Response received")

                # Check context maintenance
                if test_type in ['recall_state', 'recall_facilities', 'recall_type', 'recall_missing']:
                    total_recall_tests += 1

                    # Check both model responses
                    for side, resp in responses.items():
                        if resp:
                            resp_lower = resp.lower()
                            print(f"\n   Model {side.upper()} analysis:")
                            print(f"   Response preview: {resp[:150]}...")

                            # Check for context markers
                            if test_type == "recall_state":
                                if "kaduna" in resp_lower:
                                    print(f"   ✅ Remembered Kaduna state!")
                                    context_maintained += 0.5  # Each model contributes half
                                else:
                                    print(f"   ❌ Forgot Kaduna state")

                            elif test_type == "recall_facilities":
                                if "250" in resp:
                                    print(f"   ✅ Remembered 250 facilities!")
                                    context_maintained += 0.5
                                else:
                                    print(f"   ❌ Forgot facility count")

                            elif test_type == "recall_type":
                                if "malaria" in resp_lower:
                                    print(f"   ✅ Remembered malaria data!")
                                    context_maintained += 0.5
                                else:
                                    print(f"   ❌ Forgot data type")

                            elif test_type == "recall_missing":
                                if "didn't" in resp_lower or "not mentioned" in resp_lower or "don't" in resp_lower:
                                    print(f"   ✅ Correctly noted info wasn't provided!")
                                    context_maintained += 0.5
                                else:
                                    print(f"   ⚠️ May have hallucinated a number")

            else:
                print(f"   ❌ HTTP {response.status_code}")

        except requests.Timeout:
            print(f"   ⏱️ Timeout")
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}")

        time.sleep(2)  # Rate limit

    print("\n" + "=" * 50)
    print("📊 CONTEXT PERSISTENCE RESULTS")
    print("=" * 50)

    if total_recall_tests > 0:
        success_rate = (context_maintained / (total_recall_tests * 2)) * 100  # *2 for both models
        print(f"Context Maintenance: {context_maintained:.1f}/{total_recall_tests * 2}")
        print(f"Success Rate: {success_rate:.1f}%")

        if success_rate >= 75:
            print("✅ EXCELLENT - Strong context persistence!")
        elif success_rate >= 50:
            print("⚠️ MODERATE - Some context maintained")
        else:
            print("❌ POOR - Context frequently lost")
    else:
        print("No recall tests performed")

    print("\n💡 Context persistence is crucial for ChatGPT-like conversation.")
    print("If context is maintained well, users can have natural multi-turn chats.")

if __name__ == "__main__":
    test_context_persistence()